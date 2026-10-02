"""
The core agentic loop: a LangGraph state machine that ties
retrieve -> grade -> (retry or generate) together, with a bounded number
of retries and a fallback when evidence is never found.

Extended for the comparison study: which domain to search and which
grading strategy to use are now part of the state, not hardcoded, so the
exact same compiled graph can run any (domain, grader) combination --
that's what run_comparison.py sweeps over.

Graph shape:

    retrieve -> grade -> [sufficient?] -> generate -> END
                            |
                            |-- no, retries left --> rewrite -> retrieve (loop)
                            |
                            `-- no, retries exhausted --> fallback -> END
"""
import sys
from pathlib import Path
from typing import TypedDict

from langgraph.graph import StateGraph, END

sys.path.append(str(Path(__file__).parent.parent))
from config import MAX_RETRIES, DEFAULT_GRADER, RELEVANCE_THRESHOLD
from src.retriever import retrieve
from src.graders import get_grader
from src.generate import generate_answer, call_ollama
from src.schema import Chunk


class RAGState(TypedDict):
    query: str                    # current search query (mutates on retry)
    original_query: str           # the user's actual question, never changes
    domain: str                   # which document collection to search
    grader_name: str              # which grading strategy to use ("llm" / "crossencoder" / "threshold")
    chunks: list[Chunk]
    relevant_chunks: list[Chunk]
    relevant_fraction: float
    retries: int
    answer: str
    used_fallback: bool


REWRITE_PROMPT_TEMPLATE = (
    "The search query '{query}' did not return relevant results for the "
    "question '{original_query}'. Rewrite it as a different, more specific "
    "search query that might retrieve better matching passages. "
    "Return only the rewritten query, nothing else."
)


def rewrite_query(query: str, original_query: str) -> str:
    prompt = REWRITE_PROMPT_TEMPLATE.format(query=query, original_query=original_query)
    try:
        return call_ollama(prompt)
    except Exception as e:
        print(f"[graph] rewrite call failed, reusing original query: {e}")
        return original_query


def fallback_response(query: str) -> str:
    """Simplest version: an honest 'insufficient evidence' message instead
    of guessing. Stretch goal: plug a free web-search API in here instead."""
    return "I don't have enough reliable evidence in the document collection to answer that question."


# ---------------- LangGraph nodes ----------------

def retrieve_node(state: RAGState) -> dict:
    chunks = retrieve(state["query"], domain=state["domain"])
    return {"chunks": chunks}


def grade_node(state: RAGState) -> dict:
    grader = get_grader(state["grader_name"])
    relevant, fraction = grader.grade_chunks(state["original_query"], state["chunks"])
    return {"relevant_chunks": relevant, "relevant_fraction": fraction}


def decide_after_grade(state: RAGState) -> str:
    if state["relevant_fraction"] >= RELEVANCE_THRESHOLD:
        return "generate"
    if state["retries"] < MAX_RETRIES:
        return "rewrite"
    return "fallback"


def rewrite_node(state: RAGState) -> dict:
    new_query = rewrite_query(state["query"], state["original_query"])
    return {"query": new_query, "retries": state["retries"] + 1}


def generate_node(state: RAGState) -> dict:
    answer = generate_answer(state["original_query"], state["relevant_chunks"])
    return {"answer": answer, "used_fallback": False}


def fallback_node(state: RAGState) -> dict:
    return {"answer": fallback_response(state["original_query"]), "used_fallback": True}


# ---------------- Build + compile the graph ----------------

def build_graph():
    graph = StateGraph(RAGState)

    graph.add_node("retrieve", retrieve_node)
    graph.add_node("grade", grade_node)
    graph.add_node("rewrite", rewrite_node)
    graph.add_node("generate", generate_node)
    graph.add_node("fallback", fallback_node)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "grade")
    graph.add_conditional_edges(
        "grade",
        decide_after_grade,
        {"generate": "generate", "rewrite": "rewrite", "fallback": "fallback"},
    )
    graph.add_edge("rewrite", "retrieve")
    graph.add_edge("generate", END)
    graph.add_edge("fallback", END)

    return graph.compile()


_compiled_graph = None


def run_rag(query: str, domain: str = "hotpotqa", grader_name: str = DEFAULT_GRADER) -> RAGState:
    """Main entry point used by app.py, eval_end_to_end.py, and run_comparison.py.
    One compiled graph is reused across every (domain, grader) combination --
    those are just values passed in through the initial state."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()

    initial_state: RAGState = {
        "query": query,
        "original_query": query,
        "domain": domain,
        "grader_name": grader_name,
        "chunks": [],
        "relevant_chunks": [],
        "relevant_fraction": 0.0,
        "retries": 0,
        "answer": "",
        "used_fallback": False,
    }
    return _compiled_graph.invoke(initial_state)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("question", type=str)
    parser.add_argument("--domain", type=str, default="hotpotqa")
    parser.add_argument("--grader", type=str, default=DEFAULT_GRADER, choices=["llm", "crossencoder", "threshold"])
    args = parser.parse_args()

    result = run_rag(args.question, domain=args.domain, grader_name=args.grader)
    print(f"\nDomain: {args.domain} | Grader: {args.grader}")
    print(f"Retries used: {result['retries']}")
    print(f"Fallback triggered: {result['used_fallback']}")
    print(f"\nAnswer: {result['answer']}")

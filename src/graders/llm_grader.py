"""
Strategy A: an LLM is prompted directly to judge relevance (yes/no).
Flexible and needs no extra model, but slow and the most expensive of the
three strategies to run at scale (one LLM call per chunk per query).
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from src.generate import call_ollama
from src.schema import Chunk

GRADE_PROMPT_TEMPLATE = (
    "You are judging whether a passage is useful for answering a question.\n\n"
    "Question: {query}\n\n"
    "Passage: {passage}\n\n"
    "Does this passage contain information that helps answer the question? "
    "Answer with exactly one word: yes or no."
)


def score_chunk(query: str, chunk: Chunk) -> float:
    """Returns 1.0 (relevant) or 0.0 (not relevant). Kept as a float, not a
    bool, so all three graders share the same score_chunk() signature --
    this is what run_comparison.py relies on to score every strategy
    against the gold-labeled set the same way."""
    prompt = GRADE_PROMPT_TEMPLATE.format(query=query, passage=chunk.text)
    try:
        response = call_ollama(prompt)
    except Exception as e:
        print(f"[llm_grader] Ollama call failed, treating chunk as irrelevant: {e}")
        return 0.0

    first_word = response.strip().lower().split()[0] if response.strip() else ""
    return 1.0 if first_word.startswith("yes") else 0.0


def grade_chunks(query: str, chunks: list[Chunk]) -> tuple[list[Chunk], float]:
    if not chunks:
        return [], 0.0
    relevant = [c for c in chunks if score_chunk(query, c) >= 0.5]
    fraction = len(relevant) / len(chunks)
    return relevant, fraction

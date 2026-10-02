"""
Calls the local LLM (via Ollama) to produce a grounded answer from the
query and the relevant chunks, and builds the prompt used both here and
by src/graders/llm_grader.py's relevance-judging call.
"""
import sys
from pathlib import Path

import requests

sys.path.append(str(Path(__file__).parent.parent))
from config import OLLAMA_BASE_URL, OLLAMA_MODEL
from src.schema import Chunk


def call_ollama(prompt: str) -> str:
    """Sends a prompt to your local Ollama server and returns the generated
    text. Requires `ollama serve` running locally and the model already
    pulled (see README)."""
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["response"].strip()


def build_prompt(query: str, chunks: list[Chunk]) -> str:
    """
    Builds the grounded-generation prompt. Explicitly instructing the model
    to say it doesn't know when the context is insufficient is the key
    design choice here — worth an ablation in your report: compare
    hallucination rate with vs without that instruction.
    """
    context = "\n\n".join(f"[Source: {c.source}]\n{c.text}" for c in chunks)
    return (
        "Answer the question using ONLY the information in the context below. "
        "Do not use any outside knowledge. If the context does not contain "
        "enough information to answer, say exactly: "
        "\"I don't have enough information to answer that.\"\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {query}\n\n"
        "Answer (cite the source in brackets after each claim, e.g. [Source: X]):"
    )


def generate_answer(query: str, chunks: list[Chunk]) -> str:
    """Main entry point used by graph.py."""
    if not chunks:
        return "I don't have enough information to answer that."
    prompt = build_prompt(query, chunks)
    return call_ollama(prompt)

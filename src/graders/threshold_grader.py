"""
Strategy C: no separate grading model at all -- just threshold the raw
cosine similarity score already produced by the retriever. The cheapest
possible option (zero extra compute), included specifically to test
whether a dedicated grading step is worth its cost at all.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from config import SIMILARITY_THRESHOLD
from src.schema import Chunk


def score_chunk(query: str, chunk: Chunk) -> float:
    """query is unused here -- the similarity score was already computed
    against the query at retrieval time and is stored on the chunk. Kept
    as a parameter so this function matches the shared score_chunk(query,
    chunk) signature used by the other two graders."""
    return chunk.score


def grade_chunks(query: str, chunks: list[Chunk]) -> tuple[list[Chunk], float]:
    if not chunks:
        return [], 0.0
    relevant = [c for c in chunks if c.score >= SIMILARITY_THRESHOLD]
    fraction = len(relevant) / len(chunks)
    return relevant, fraction

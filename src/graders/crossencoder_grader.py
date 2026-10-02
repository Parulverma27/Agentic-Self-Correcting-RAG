"""
Strategy B: a pretrained cross-encoder trained specifically for
query-passage relevance ranking (MS MARCO), not a general LLM. Runs
locally on CPU, needs no separate LLM server, and is much faster than
Strategy A -- this is the "purpose-built, cheap" option in the comparison.
"""
import sys
import math
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from config import CROSSENCODER_MODEL, CROSSENCODER_THRESHOLD
from src.schema import Chunk

_model = None


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import CrossEncoder
        _model = CrossEncoder(CROSSENCODER_MODEL)
    return _model


def _sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def score_chunk(query: str, chunk: Chunk) -> float:
    """Returns a 0-1 relevance score (raw cross-encoder logit passed
    through sigmoid)."""
    model = get_model()
    raw_score = model.predict([(query, chunk.text)])[0]
    return _sigmoid(float(raw_score))


def grade_chunks(query: str, chunks: list[Chunk]) -> tuple[list[Chunk], float]:
    if not chunks:
        return [], 0.0
    model = get_model()
    pairs = [(query, c.text) for c in chunks]
    raw_scores = model.predict(pairs)
    scores = [_sigmoid(float(s)) for s in raw_scores]

    relevant = [c for c, s in zip(chunks, scores) if s >= CROSSENCODER_THRESHOLD]
    fraction = len(relevant) / len(chunks)
    return relevant, fraction

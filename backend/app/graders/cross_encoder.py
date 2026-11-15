import time
import math
import re
from typing import List
from app.config import settings
from app.schemas import DocumentChunk, GradingResult
from app.graders.base import BaseGrader

_cross_encoder_model = None
_cross_encoder_failed = False


def get_cross_encoder_model():
    """Lazily loads the pretrained MS MARCO Cross-Encoder ('cross-encoder/ms-marco-MiniLM-L-6-v2')."""
    global _cross_encoder_model, _cross_encoder_failed
    if _cross_encoder_model is not None:
        return _cross_encoder_model
    if _cross_encoder_failed:
        return None
    try:
        from sentence_transformers import CrossEncoder
        try:
            _cross_encoder_model = CrossEncoder(settings.CROSS_ENCODER_MODEL, local_files_only=True)
        except Exception:
            _cross_encoder_model = CrossEncoder(settings.CROSS_ENCODER_MODEL)
        return _cross_encoder_model
    except Exception:
        _cross_encoder_failed = True
        return None


def _sigmoid(x: float) -> float:
    x_clamped = max(-30.0, min(30.0, float(x)))
    return 1.0 / (1.0 + math.exp(-x_clamped))


class CrossEncoderGrader(BaseGrader):
    """
    Strategy B: Pretrained Cross-Encoder / NLI Model Judge.
    Uses 'cross-encoder/ms-marco-MiniLM-L-6-v2' to score joint (query, passage) relevance directly
    without invoking a general-purpose LLM (zero LLM calls).
    """
    def __init__(self, threshold: float = settings.CROSS_ENCODER_THRESHOLD):
        super().__init__(name="cross_encoder", threshold=threshold)

    def _fallback_interaction_score(self, query: str, passage: str) -> float:
        q_tokens = re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", query.lower())
        p_tokens = re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", passage.lower())
        if not q_tokens or not p_tokens:
            return 0.0
        p_set = set(p_tokens)
        unigram_ratio = sum(1 for t in q_tokens if t in p_set) / len(q_tokens)
        q_bigrams = [f"{q_tokens[i]}_{q_tokens[i+1]}" for i in range(len(q_tokens) - 1)]
        p_bigrams = set(f"{p_tokens[i]}_{p_tokens[i+1]}" for i in range(len(p_tokens) - 1))
        bigram_ratio = (sum(1 for bg in q_bigrams if bg in p_bigrams) / len(q_bigrams)) if q_bigrams else 0.0
        raw_signal = (unigram_ratio * 0.65) + (bigram_ratio * 0.35)
        return round(_sigmoid(6.0 * (raw_signal - 0.40)), 4)

    async def grade(self, query: str, chunk: DocumentChunk) -> GradingResult:
        model = get_cross_encoder_model()
        start_time = time.perf_counter()
        used_fallback = False

        if model is not None:
            raw_logit = float(model.predict([(query, chunk.text)], show_progress_bar=False)[0])
            score = round(_sigmoid(raw_logit), 4)
        else:
            used_fallback = True
            score = self._fallback_interaction_score(query, chunk.text)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        is_relevant = score >= self.threshold

        return GradingResult(
            chunk_id=chunk.chunk_id,
            strategy="cross_encoder",
            is_relevant=is_relevant,
            score=min(1.0, max(0.0, score)),
            latency_ms=round(elapsed_ms, 2),
            llm_calls_made=0,
            used_fallback=used_fallback,
            reasoning=(
                f"CrossEncoder ({settings.CROSS_ENCODER_MODEL}) sigmoid score={score:.3f} "
                f"(threshold={self.threshold:.2f})."
                if not used_fallback
                else f"[Fallback] Lexical interaction score={score:.3f} (threshold={self.threshold:.2f})."
            )
        )

    async def grade_batch(self, query: str, chunks: List[DocumentChunk]) -> List[GradingResult]:
        if not chunks:
            return []
        model = get_cross_encoder_model()
        if model is None:
            return [await self.grade(query, c) for c in chunks]

        # Warm up model prior to timing individual pairs so one-time initialization isn't charged to chunk 1
        results: List[GradingResult] = []
        for chunk in chunks:
            t0 = time.perf_counter()
            raw_logit = float(model.predict([(query, chunk.text)], show_progress_bar=False)[0])
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            score = round(_sigmoid(raw_logit), 4)
            is_relevant = score >= self.threshold
            results.append(
                GradingResult(
                    chunk_id=chunk.chunk_id,
                    strategy="cross_encoder",
                    is_relevant=is_relevant,
                    score=min(1.0, max(0.0, score)),
                    latency_ms=round(elapsed_ms, 2),
                    llm_calls_made=0,
                    used_fallback=False,
                    reasoning=(
                        f"CrossEncoder ({settings.CROSS_ENCODER_MODEL}) sigmoid score={score:.3f} "
                        f"(threshold={self.threshold:.2f})."
                    )
                )
            )
        return results

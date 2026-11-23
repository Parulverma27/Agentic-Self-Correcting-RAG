import time
from typing import List
from app.config import settings
from app.schemas import DocumentChunk, GradingResult
from app.graders.base import BaseGrader
from app.graders.cross_encoder import CrossEncoderGrader
from app.graders.llm_grader import LLMGrader
from app.vector_store import vector_store


class HybridCascadeGrader(BaseGrader):
    """
    Strategy D: Uncertainty-Gated Hybrid Cascade Grader (Novel Algorithmic Contribution).
    Combines all three grading paradigms into an adaptive 3-stage decision cascade:
      - Stage 1 (Cosine Pre-Filter): Rejects obvious noise if s_cos(q, c) < τ_cos_min (0.30) in ~0 ms.
      - Stage 2 (Cross-Encoder Primary Gate): Scores (q, c) with ms-marco-MiniLM-L-6-v2 (~31 ms).
          * If s_B >= τ_high (0.65): High-confidence ACCEPT (0 LLM calls).
          * If s_B <= τ_low (0.35): High-confidence REJECT (0 LLM calls).
      - Stage 3 (Selective LLM Escalation): Only when s_B falls in the ambiguous uncertainty band
        (0.35 < s_B < 0.65), escalates to Ollama qwen2.5:3b (1 LLM call) and computes a calibrated
        ensemble score s_D = 0.55 * s_B + 0.45 * s_A.
    """
    def __init__(
        self,
        threshold: float = 0.50,
        cosine_min: float = settings.CASCADE_COSINE_MIN,
        ce_low: float = settings.CASCADE_CE_LOW,
        ce_high: float = settings.CASCADE_CE_HIGH
    ):
        super().__init__(name="hybrid_cascade", threshold=threshold)
        self.cosine_min = cosine_min
        self.ce_low = ce_low
        self.ce_high = ce_high
        self.ce_grader = CrossEncoderGrader(threshold=threshold)
        self.llm_grader = LLMGrader(threshold=threshold)

    async def grade(self, query: str, chunk: DocumentChunk) -> GradingResult:
        t0 = time.perf_counter()
        if chunk.similarity_score is not None:
            cos_sim = float(chunk.similarity_score)
        else:
            cos_sim = vector_store.compute_pair_similarity(query, chunk.text)

        # Stage 1: Fast Bi-Encoder Cosine Pre-Filter
        if cos_sim < self.cosine_min:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            cal_score = round(max(0.0, min(1.0, cos_sim * 0.5)), 4)
            return GradingResult(
                chunk_id=chunk.chunk_id,
                strategy="hybrid_cascade",
                is_relevant=False,
                score=cal_score,
                latency_ms=round(elapsed_ms, 4),
                llm_calls_made=0,
                used_fallback=False,
                reasoning=(
                    f"[Stage 1: Cosine Gate Reject] similarity={cos_sim:.3f} < {self.cosine_min:.2f} "
                    "(filtered in 0 LLM calls)."
                )
            )

        # Stage 2: Cross-Encoder Primary Gate
        ce_res = await self.ce_grader.grade(query, chunk)
        s_b = float(ce_res.score)

        if s_b >= self.ce_high:
            return GradingResult(
                chunk_id=chunk.chunk_id,
                strategy="hybrid_cascade",
                is_relevant=True,
                score=round(s_b, 4),
                latency_ms=round(ce_res.latency_ms, 2),
                llm_calls_made=0,
                used_fallback=ce_res.used_fallback,
                reasoning=(
                    f"[Stage 2: Cross-Encoder High-Conf Accept] s_B={s_b:.3f} >= {self.ce_high:.2f} "
                    "(0 LLM calls)."
                )
            )

        if s_b <= self.ce_low:
            return GradingResult(
                chunk_id=chunk.chunk_id,
                strategy="hybrid_cascade",
                is_relevant=False,
                score=round(s_b, 4),
                latency_ms=round(ce_res.latency_ms, 2),
                llm_calls_made=0,
                used_fallback=ce_res.used_fallback,
                reasoning=(
                    f"[Stage 2: Cross-Encoder Low-Conf Reject] s_B={s_b:.3f} <= {self.ce_low:.2f} "
                    "(0 LLM calls)."
                )
            )

        # Stage 3: Ambiguous Uncertainty Band (ce_low < s_B < ce_high) -> Escalate to LLM Judge
        llm_res = await self.llm_grader.grade(query, chunk)
        s_a = float(llm_res.score)
        ensemble_score = round((0.55 * s_b) + (0.45 * s_a), 4)
        is_rel = ensemble_score >= self.threshold
        total_lat = round(ce_res.latency_ms + llm_res.latency_ms, 2)

        return GradingResult(
            chunk_id=chunk.chunk_id,
            strategy="hybrid_cascade",
            is_relevant=is_rel,
            score=min(1.0, max(0.0, ensemble_score)),
            latency_ms=total_lat,
            llm_calls_made=llm_res.llm_calls_made,
            used_fallback=ce_res.used_fallback or llm_res.used_fallback,
            reasoning=(
                f"[Stage 3: Uncertainty Escalated to LLM] s_B={s_b:.3f} in ({self.ce_low:.2f}, {self.ce_high:.2f}), "
                f"s_A={s_a:.2f} -> ensemble s_D={ensemble_score:.3f}."
            )
        )

    async def grade_batch(self, query: str, chunks: List[DocumentChunk]) -> List[GradingResult]:
        results: List[GradingResult] = []
        for chunk in chunks:
            results.append(await self.grade(query, chunk))
        return results

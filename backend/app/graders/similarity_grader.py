import time
from app.config import settings
from app.schemas import DocumentChunk, GradingResult
from app.graders.base import BaseGrader
from app.vector_store import vector_store


class SimilarityThresholdGrader(BaseGrader):
    """
    Strategy C: Direct Similarity Threshold Baseline.
    No separate grading model or inference step: the cosine similarity score
    from the dense vector retriever ('all-MiniLM-L6-v2') is thresholded directly.
    Cheapest possible baseline to test whether dedicated grading is worth the added cost.
    """
    def __init__(self, threshold: float = settings.SIMILARITY_THRESHOLD):
        super().__init__(name="similarity_threshold", threshold=threshold)

    async def grade(self, query: str, chunk: DocumentChunk) -> GradingResult:
        start_time = time.perf_counter()

        # If chunk already carries its retrieval cosine similarity, threshold it directly;
        # otherwise compute true dense embedding cosine similarity via vector_store.
        if chunk.similarity_score is not None:
            score = float(chunk.similarity_score)
        else:
            score = vector_store.compute_pair_similarity(query, chunk.text)

        is_relevant = score >= self.threshold
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return GradingResult(
            chunk_id=chunk.chunk_id,
            strategy="similarity_threshold",
            is_relevant=is_relevant,
            score=round(min(1.0, max(0.0, score)), 4),
            latency_ms=round(elapsed_ms, 4),
            llm_calls_made=0,
            used_fallback=False,
            reasoning=f"Dense cosine similarity {score:.3f} checked against threshold {self.threshold:.2f}."
        )

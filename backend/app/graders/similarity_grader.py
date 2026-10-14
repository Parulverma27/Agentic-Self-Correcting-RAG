import time
from app.config import settings
from app.schemas import DocumentChunk, GradingResult
from app.graders.base import BaseGrader

class SimilarityThresholdGrader(BaseGrader):
    """
    Strategy C: Direct Similarity Threshold Baseline.
    No separate grading model or inference step at all: the raw cosine similarity score
    obtained directly from the initial vector retrieval is thresholded.
    Cheapest baseline to test whether a dedicated grading step is worth the complexity.
    """
    def __init__(self, threshold: float = settings.SIMILARITY_THRESHOLD):
        super().__init__(name="similarity_threshold", threshold=threshold)

    async def grade(self, query: str, chunk: DocumentChunk) -> GradingResult:
        start_time = time.perf_counter()
        
        # Take the raw retrieval similarity score (default to 0.0 if not set)
        score = float(chunk.similarity_score if chunk.similarity_score is not None else 0.0)
        is_relevant = score >= self.threshold
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        
        return GradingResult(
            chunk_id=chunk.chunk_id,
            strategy="similarity_threshold",
            is_relevant=is_relevant,
            score=min(1.0, max(0.0, score)),
            latency_ms=round(max(0.05, elapsed_ms), 3),
            llm_calls_made=0,
            reasoning=f"Raw cosine similarity {score:.3f} checked against threshold {self.threshold}."
        )

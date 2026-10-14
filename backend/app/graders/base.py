from abc import ABC, abstractmethod
from typing import List
from app.schemas import DocumentChunk, GradingResult, StrategyType

class BaseGrader(ABC):
    """
    Abstract Base Class for Relevance Graders in Corrective RAG.
    All strategies adhere strictly to this shared interface.
    """
    def __init__(self, name: StrategyType, threshold: float = 0.50):
        self.name: StrategyType = name
        self.threshold: float = threshold

    @abstractmethod
    async def grade(self, query: str, chunk: DocumentChunk) -> GradingResult:
        """
        Judge the relevance of a single candidate document chunk against a query.
        Returns a structured GradingResult.
        """
        pass

    async def grade_batch(self, query: str, chunks: List[DocumentChunk]) -> List[GradingResult]:
        """
        Grade a list of candidate chunks.
        Default implementation grades each sequentially or concurrently.
        """
        results: List[GradingResult] = []
        for chunk in chunks:
            res = await self.grade(query, chunk)
            results.append(res)
        return results

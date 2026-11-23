from app.schemas import StrategyType
from app.graders.base import BaseGrader
from app.graders.llm_grader import LLMGrader
from app.graders.cross_encoder import CrossEncoderGrader
from app.graders.similarity_grader import SimilarityThresholdGrader
from app.graders.hybrid_cascade import HybridCascadeGrader


def get_grader(strategy: StrategyType) -> BaseGrader:
    """Factory helper to obtain the instantiated grader by strategy identifier."""
    if strategy == "llm":
        return LLMGrader()
    elif strategy == "cross_encoder":
        return CrossEncoderGrader()
    elif strategy == "similarity_threshold":
        return SimilarityThresholdGrader()
    elif strategy == "hybrid_cascade":
        return HybridCascadeGrader()
    else:
        raise ValueError(f"Unknown grading strategy: {strategy}")


__all__ = [
    "BaseGrader",
    "LLMGrader",
    "CrossEncoderGrader",
    "SimilarityThresholdGrader",
    "HybridCascadeGrader",
    "get_grader"
]

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

# Domain type definition
DomainType = Literal["hotpotqa", "legal"]
StrategyType = Literal["llm", "cross_encoder", "similarity_threshold"]

class DocumentChunk(BaseModel):
    chunk_id: str
    text: str
    domain: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    similarity_score: Optional[float] = None

class GradingResult(BaseModel):
    chunk_id: str
    strategy: StrategyType
    is_relevant: bool
    score: float = Field(ge=0.0, le=1.0)
    latency_ms: float
    llm_calls_made: int
    used_fallback: bool = False
    reasoning: Optional[str] = None

class PipelineTraceStep(BaseModel):
    step: str
    details: Dict[str, Any]

class PipelineResponse(BaseModel):
    query: str
    domain: str
    strategy: StrategyType
    retrieved_chunks_count: int
    graded_relevant_count: int
    reformulation_retries: int
    reformulated_queries: List[str]
    final_answer: str
    used_chunks: List[DocumentChunk]
    grading_results: List[GradingResult]
    total_latency_ms: float
    grading_latency_ms: float
    total_llm_calls: int
    pipeline_trace: List[PipelineTraceStep]

class SideBySideComparisonResponse(BaseModel):
    query: str
    domain: str
    results: Dict[StrategyType, PipelineResponse]

class QueryRequest(BaseModel):
    query: str
    domain: DomainType = "hotpotqa"
    strategy: StrategyType = "llm"
    top_k: Optional[int] = 4

class CompareQueryRequest(BaseModel):
    query: str
    domain: DomainType = "hotpotqa"
    top_k: Optional[int] = 4

class DocQARequest(BaseModel):
    query: str
    domain: str = "report"
    strategy: StrategyType = "llm"
    top_k: Optional[int] = 4

class DocUploadRequest(BaseModel):
    doc_name: str
    doc_text: str
    domain: str = "custom_doc"

class GoldBenchmarkItem(BaseModel):
    pair_id: str
    query_id: str
    query: str
    chunk_id: str
    chunk_text: str
    domain: str
    ground_truth_relevance: bool
    ground_truth_answer: str

class StrategyMetrics(BaseModel):
    strategy: StrategyType
    domain: str
    sample_count: int

    # Grading Accuracy against Hand-Labelled Gold Standard
    precision: float
    recall: float
    f1_score: float
    accuracy: float
    specificity: float

    # Downstream End-to-End Metrics
    exact_match: float
    token_f1: float
    retry_rate: float
    avg_grading_latency_ms: float
    avg_total_latency_ms: float
    avg_llm_calls_per_query: float

class StatisticalComparison(BaseModel):
    strategy_a: StrategyType
    strategy_b: StrategyType
    metric_name: str
    mean_a: float
    mean_b: float
    difference: float
    t_statistic: float
    p_value: float
    p_value_holm: Optional[float] = None
    bootstrap_p_value: Optional[float] = None
    bootstrap_ci_95: Optional[List[float]] = None
    cohens_d: Optional[float] = None
    statistically_significant: bool  # p < 0.05 (after Holm / bootstrap verification)
    confidence_interval_95: List[float]
    interpretation: str

class EvaluationReport(BaseModel):
    domains_evaluated: List[str]
    strategies_evaluated: List[StrategyType]
    matrix: List[StrategyMetrics]
    statistical_significance: List[StatisticalComparison]
    summary_findings: str
    timestamp: Optional[str] = None
    total_gold_pairs: Optional[int] = None

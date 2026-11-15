import time
from typing import List, Optional
from app.config import settings
from app.schemas import (
    DocumentChunk,
    GradingResult,
    PipelineResponse,
    PipelineTraceStep,
    StrategyType,
    DomainType
)
from app.vector_store import vector_store
from app.graders import get_grader, BaseGrader
from app.pipeline.generation import generator


class CRAGPipeline:
    """
    Corrective Retrieval-Augmented Generation (CRAG) Pipeline.
    Supports pluggable grading strategies behind BaseGrader:
      - 'llm': Strategy A (LLM Prompt Judge via Ollama qwen2.5:3b)
      - 'cross_encoder': Strategy B (Pretrained Cross-Encoder ms-marco-MiniLM-L-6-v2)
      - 'similarity_threshold': Strategy C (Dense Cosine Similarity Threshold)
    """
    def __init__(self, top_k: int = settings.TOP_K, max_retries: int = settings.MAX_REFORMULATION_RETRIES):
        self.top_k = top_k
        self.max_retries = max_retries
        self.min_relevant = settings.MIN_RELEVANT_CHUNKS

    async def execute(
        self,
        query: str,
        domain: DomainType = "hotpotqa",
        strategy: StrategyType = "llm",
        top_k: Optional[int] = None
    ) -> PipelineResponse:
        start_time = time.perf_counter()
        if not vector_store.chunks:
            from app.data.loader import load_initial_corpora
            load_initial_corpora()
        k = top_k or self.top_k
        grader: BaseGrader = get_grader(strategy)

        trace: List[PipelineTraceStep] = []
        total_llm_calls = 0
        total_grading_latency = 0.0
        reformulated_queries: List[str] = []
        retries_count = 0

        current_query = query
        all_retrieved_chunks: List[DocumentChunk] = []
        all_grading_results: List[GradingResult] = []
        relevant_chunks: List[DocumentChunk] = []

        # -----------------------------------------------------------------
        # Core Pipeline Loop: Retrieve -> Grade -> Check Sufficiency -> Retry
        # -----------------------------------------------------------------
        for attempt in range(self.max_retries + 1):
            trace.append(PipelineTraceStep(
                step=f"Retrieval Attempt {attempt + 1}",
                details={
                    "query_used": current_query,
                    "attempt_number": attempt + 1,
                    "domain": domain,
                    "top_k": k
                }
            ))

            # Step 1: Retrieval from Dense Vector Store (using current/reformulated query)
            candidate_chunks = vector_store.retrieve(query=current_query, domain=domain, top_k=k)
            all_retrieved_chunks = candidate_chunks

            # Step 2: Relevance Grading via pluggable strategy
            # Always grade candidate chunks against the original user question to prevent relevance drift
            grading_results = await grader.grade_batch(query=query, chunks=candidate_chunks)
            all_grading_results = grading_results

            attempt_grading_latency = sum(r.latency_ms for r in grading_results)
            total_grading_latency += attempt_grading_latency
            total_llm_calls += sum(r.llm_calls_made for r in grading_results)

            # Filter relevant chunks
            graded_relevant: List[DocumentChunk] = [
                c for c, res in zip(candidate_chunks, grading_results) if res.is_relevant
            ]
            relevant_chunks = graded_relevant

            trace.append(PipelineTraceStep(
                step=f"Grading Phase {attempt + 1}",
                details={
                    "strategy": strategy,
                    "total_chunks_graded": len(candidate_chunks),
                    "relevant_count": len(graded_relevant),
                    "grading_results": [r.model_dump() for r in grading_results]
                }
            ))

            # Step 3: Check if sufficiency condition is met
            if len(relevant_chunks) >= self.min_relevant:
                break

            # If insufficient evidence and retries remain, trigger correction loop
            if attempt < self.max_retries:
                retries_count += 1
                new_query, reform_llm_calls = await generator.reformulate_query(
                    original_query=query,
                    attempt=retries_count,
                    domain=domain
                )
                total_llm_calls += reform_llm_calls
                reformulated_queries.append(new_query)
                current_query = new_query

                trace.append(PipelineTraceStep(
                    step=f"Query Reformulation {retries_count}",
                    details={
                        "reason": f"Only {len(graded_relevant)} relevant chunks found (minimum required: {self.min_relevant})",
                        "reformulated_query": new_query
                    }
                ))

        # -----------------------------------------------------------------
        # Step 4: Downstream Generation
        # -----------------------------------------------------------------
        final_answer, gen_llm_calls = await generator.generate_answer(
            query=query,
            relevant_chunks=relevant_chunks,
            domain=domain
        )
        total_llm_calls += gen_llm_calls

        wall_ms = (time.perf_counter() - start_time) * 1000.0
        total_latency_ms = max(wall_ms, total_grading_latency + min(wall_ms, 5.0))

        trace.append(PipelineTraceStep(
            step="Final Generation",
            details={
                "relevant_chunks_used": [c.chunk_id for c in relevant_chunks],
                "final_answer": final_answer,
                "generation_llm_calls": gen_llm_calls
            }
        ))

        return PipelineResponse(
            query=query,
            domain=domain,
            strategy=strategy,
            retrieved_chunks_count=len(all_retrieved_chunks),
            graded_relevant_count=len(relevant_chunks),
            reformulation_retries=retries_count,
            reformulated_queries=reformulated_queries,
            final_answer=final_answer,
            used_chunks=relevant_chunks,
            grading_results=all_grading_results,
            total_latency_ms=round(total_latency_ms, 2),
            grading_latency_ms=round(total_grading_latency, 2),
            total_llm_calls=total_llm_calls,
            pipeline_trace=trace
        )


crag_pipeline = CRAGPipeline()

import pytest
from app.data.loader import load_initial_corpora
from app.pipeline.crag_pipeline import crag_pipeline

@pytest.fixture(autouse=True)
def setup_vector_store():
    load_initial_corpora()

@pytest.mark.asyncio
async def test_pipeline_execution_all_strategies():
    query = "Who commissioned the Roman Colosseum?"
    domain = "hotpotqa"

    for strategy in ["llm", "cross_encoder", "similarity_threshold"]:
        resp = await crag_pipeline.execute(
            query=query,
            domain=domain,
            strategy=strategy,
            top_k=3
        )
        assert resp.query == query
        assert resp.strategy == strategy
        assert resp.domain == domain
        assert resp.retrieved_chunks_count > 0
        assert len(resp.grading_results) > 0
        assert resp.final_answer != ""
        assert resp.total_latency_ms > 0

        if strategy == "similarity_threshold":
            assert resp.grading_results[0].llm_calls_made == 0
        elif strategy == "cross_encoder":
            assert resp.grading_results[0].llm_calls_made == 0
        elif strategy == "llm":
            assert resp.grading_results[0].llm_calls_made == 1

@pytest.mark.asyncio
async def test_pipeline_legal_domain():
    query = "What is the limitation of liability under the contract?"
    resp = await crag_pipeline.execute(
        query=query,
        domain="legal",
        strategy="cross_encoder",
        top_k=3
    )
    assert resp.domain == "legal"
    assert resp.strategy == "cross_encoder"
    assert "liability" in resp.final_answer.lower() or "fees" in resp.final_answer.lower()

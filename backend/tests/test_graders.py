import pytest
from app.schemas import DocumentChunk
from app.graders import get_grader, LLMGrader, CrossEncoderGrader, SimilarityThresholdGrader

@pytest.mark.asyncio
async def test_llm_grader_relevance():
    grader = get_grader("llm")
    assert isinstance(grader, LLMGrader)

    # This chunk explicitly contains key terms from the query for the proxy fallback scorer
    relevant_chunk = DocumentChunk(
        chunk_id="test_01",
        domain="hotpotqa",
        text="Alan Turing worked at Bletchley Park during World War II, where he cracked Enigma coded messages with the team."
    )
    result = await grader.grade("Where did Alan Turing work to crack Enigma codes?", relevant_chunk)
    assert result.strategy == "llm"
    assert result.is_relevant is True
    assert result.score > 0.50
    assert result.llm_calls_made == 1
    assert result.latency_ms > 0

    irrelevant_chunk = DocumentChunk(
        chunk_id="test_02",
        domain="hotpotqa",
        text="The Great Barrier Reef is the world's largest coral reef system composed of over 2,900 individual reefs in Australia."
    )
    res_irr = await grader.grade("Where did Alan Turing work to crack Enigma codes?", irrelevant_chunk)
    assert res_irr.is_relevant is False
    assert res_irr.score < 0.50
    assert res_irr.llm_calls_made == 1

@pytest.mark.asyncio
async def test_cross_encoder_grader():
    grader = get_grader("cross_encoder")
    assert isinstance(grader, CrossEncoderGrader)

    chunk = DocumentChunk(
        chunk_id="test_leg_01",
        domain="legal",
        text="Section 8.1: In no event shall either party's aggregate liability exceed the total fees paid in the preceding 12 months."
    )
    result = await grader.grade("What is the aggregate liability cap in the contract?", chunk)
    assert result.strategy == "cross_encoder"
    assert result.is_relevant is True
    assert result.llm_calls_made == 0  # Zero LLM calls for cross-encoder
    assert result.latency_ms > 0

@pytest.mark.asyncio
async def test_similarity_threshold_grader():
    grader = get_grader("similarity_threshold")
    assert isinstance(grader, SimilarityThresholdGrader)

    high_sim_chunk = DocumentChunk(
        chunk_id="test_sim_01",
        domain="hotpotqa",
        text="Mount Everest is Earth's highest peak.",
        similarity_score=0.78
    )
    res_high = await grader.grade("What is Earth's highest peak?", high_sim_chunk)
    assert res_high.is_relevant is True
    assert res_high.llm_calls_made == 0

    low_sim_chunk = DocumentChunk(
        chunk_id="test_sim_02",
        domain="hotpotqa",
        text="Unrelated text about baking.",
        similarity_score=0.25
    )
    res_low = await grader.grade("What is Earth's highest peak?", low_sim_chunk)
    assert res_low.is_relevant is False
    assert res_low.llm_calls_made == 0

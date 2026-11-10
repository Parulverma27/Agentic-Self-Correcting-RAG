import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.data.loader import load_initial_corpora

@pytest.fixture(autouse=True)
def setup_corpus():
    """Ensure the vector store is loaded before every API test."""
    load_initial_corpora()

@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "hotpotqa" in data["domains_indexed"]
        assert "legal" in data["domains_indexed"]

@pytest.mark.asyncio
async def test_graders_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/graders")
        assert resp.status_code == 200
        data = resp.json()
        strategies = [s["id"] for s in data["strategies"]]
        assert "llm" in strategies
        assert "cross_encoder" in strategies
        assert "similarity_threshold" in strategies

@pytest.mark.asyncio
async def test_crag_query_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/crag/query",
            json={
                "query": "Who commissioned the Roman Colosseum?",
                "domain": "hotpotqa",
                "strategy": "cross_encoder",
                "top_k": 3
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["strategy"] == "cross_encoder"
        assert data["final_answer"] != ""
        assert len(data["pipeline_trace"]) > 0

@pytest.mark.asyncio
async def test_compare_live_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/crag/compare-live",
            json={
                "query": "What is the liability limitation clause?",
                "domain": "legal",
                "top_k": 3
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "llm" in data["results"]
        assert "cross_encoder" in data["results"]
        assert "similarity_threshold" in data["results"]

@pytest.mark.asyncio
async def test_domains_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/domains")
        assert resp.status_code == 200
        data = resp.json()
        assert "hotpotqa" in data["domains"]
        assert data["domains"]["hotpotqa"]["chunk_count"] > 0

@pytest.mark.asyncio
async def test_gold_dataset_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/dataset/gold?domain=hotpotqa")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        assert data[0]["domain"] == "hotpotqa"

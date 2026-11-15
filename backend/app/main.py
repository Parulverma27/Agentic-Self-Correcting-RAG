from contextlib import asynccontextmanager
import re
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.schemas import (
    QueryRequest,
    CompareQueryRequest,
    DocQARequest,
    DocUploadRequest,
    PipelineResponse,
    SideBySideComparisonResponse,
    EvaluationReport,
    GoldBenchmarkItem,
    StrategyType
)
from app.vector_store import vector_store
from app.pipeline.crag_pipeline import crag_pipeline
from app.evaluation.evaluator import evaluation_engine
from app.data.loader import load_initial_corpora, load_gold_benchmark, save_gold_benchmark_item


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_initial_corpora()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for Comparative Evaluation of Relevance-Grading Strategies in CRAG Systems.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _normalize_domain(domain: str) -> str:
    d = (domain or "hotpotqa").strip().lower()
    if d in ("bioasq", "legal text", "contracts"):
        return "legal"
    return d


@app.get("/api/health")
async def health_check():
    """Health check endpoint providing service status and system info."""
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "domains_indexed": list(vector_store.chunks.keys()),
        "strategies_available": ["llm", "cross_encoder", "similarity_threshold"],
        "models": {
            "llm": settings.OLLAMA_LLM_MODEL,
            "cross_encoder": settings.CROSS_ENCODER_MODEL,
            "embedding": settings.EMBEDDING_MODEL
        }
    }


@app.get("/api/domains")
async def get_domains():
    """Lists available domains, chunk counts, and metadata."""
    domains_info = {}
    for d, chunks in vector_store.chunks.items():
        domains_info[d] = {
            "chunk_count": len(chunks),
            "sample_chunk_ids": [c.chunk_id for c in chunks[:3]],
            "description": (
                "General Knowledge / Multi-hop questions (HotpotQA)"
                if d == "hotpotqa"
                else "Specialized Dense Legal & Contractual Clauses"
                if d == "legal"
                else "Project Report & Uploaded Document Collection"
            )
        }
    return {"domains": domains_info}


@app.get("/api/graders")
async def get_graders():
    """Lists the 3 interchangeable relevance grading strategies under comparison."""
    return {
        "strategies": [
            {
                "id": "llm",
                "name": "Strategy A: LLM-Prompt Judge",
                "model": f"Ollama ({settings.OLLAMA_LLM_MODEL})",
                "description": "Local general-purpose LLM prompted directly with query and passage to judge relevance (yes/no).",
                "cost_profile": "High (1 LLM call per graded candidate chunk)",
                "latency_profile": "High (~2,500–3,500 ms per chunk on local CPU)",
                "threshold": settings.LLM_GRADER_THRESHOLD
            },
            {
                "id": "cross_encoder",
                "name": "Strategy B: Cross-Encoder / NLI Model",
                "model": settings.CROSS_ENCODER_MODEL,
                "description": "Pretrained MS MARCO Cross-Encoder scoring joint query-passage cross-attention logits via sigmoid.",
                "cost_profile": "Zero LLM calls (purpose-built local transformer)",
                "latency_profile": "Low (~10–25 ms per chunk on CPU)",
                "threshold": settings.CROSS_ENCODER_THRESHOLD
            },
            {
                "id": "similarity_threshold",
                "name": "Strategy C: Raw Similarity Threshold",
                "model": f"SentenceTransformer ({settings.EMBEDDING_MODEL}) + FAISS",
                "description": "Baseline thresholding raw dense cosine similarity from initial retrieval with no separate grading step.",
                "cost_profile": "Zero LLM calls, Zero auxiliary grading inference",
                "latency_profile": "Negligible (< 0.1 ms)",
                "threshold": settings.SIMILARITY_THRESHOLD
            }
        ]
    }


@app.post("/api/crag/query", response_model=PipelineResponse)
async def execute_crag_query(request: QueryRequest):
    """Executes a single query through the Corrective RAG pipeline using the selected grading strategy."""
    domain = _normalize_domain(request.domain)
    if domain not in vector_store.chunks:
        raise HTTPException(status_code=400, detail=f"Domain '{domain}' is not indexed.")

    response = await crag_pipeline.execute(
        query=request.query,
        domain=domain,
        strategy=request.strategy,
        top_k=request.top_k
    )
    return response


@app.post("/api/crag/compare-live", response_model=SideBySideComparisonResponse)
async def compare_query_live(request: CompareQueryRequest):
    """Executes the exact same query across all 3 grading strategies for side-by-side viva comparison."""
    domain = _normalize_domain(request.domain)
    if domain not in vector_store.chunks:
        raise HTTPException(status_code=400, detail=f"Domain '{domain}' is not indexed.")

    strategies: List[StrategyType] = ["llm", "cross_encoder", "similarity_threshold"]
    results: Dict[StrategyType, PipelineResponse] = {}

    for strat in strategies:
        resp = await crag_pipeline.execute(
            query=request.query,
            domain=domain,
            strategy=strat,
            top_k=request.top_k
        )
        results[strat] = resp

    return SideBySideComparisonResponse(
        query=request.query,
        domain=domain,
        results=results
    )


@app.get("/api/eval/latest", response_model=EvaluationReport)
async def get_latest_evaluation():
    """Returns the latest persisted evaluation report (or runs the study if none exists yet)."""
    report = evaluation_engine.get_latest_report()
    if report is not None:
        return report
    return await evaluation_engine.run_full_study(
        domains=["hotpotqa", "legal"],
        strategies=["llm", "cross_encoder", "similarity_threshold"]
    )


@app.post("/api/eval/run", response_model=EvaluationReport)
async def run_evaluation(
    domains: List[str] = Body(default=["hotpotqa", "legal"]),
    strategies: List[StrategyType] = Body(default=["llm", "cross_encoder", "similarity_threshold"])
):
    """
    Runs the controlled comparative evaluation study across specified domains and grading strategies.
    Computes grading precision/recall/F1, answer EM/F1, latency, retry rate, LLM calls,
    and performs paired Student's t-test + 2,000-iteration bootstrap significance tests.
    """
    normalized_domains: List[str] = []
    for d in domains:
        d_clean = d.strip().lower()
        if "all" in d_clean:
            normalized_domains.extend(["hotpotqa", "legal"])
        else:
            normalized_domains.append(_normalize_domain(d_clean))
    normalized_domains = list(dict.fromkeys(normalized_domains)) or ["hotpotqa", "legal"]

    for d in normalized_domains:
        if d not in vector_store.chunks:
            raise HTTPException(status_code=400, detail=f"Domain '{d}' is not indexed.")

    report = await evaluation_engine.run_full_study(
        domains=normalized_domains,
        strategies=strategies
    )
    return report


@app.get("/api/dataset/gold", response_model=List[GoldBenchmarkItem])
async def get_gold_dataset(domain: Optional[str] = Query(None)):
    """Returns the curated 120-pair hand-labelled gold relevance dataset."""
    items = load_gold_benchmark()
    if domain:
        norm_d = _normalize_domain(domain)
        items = [i for i in items if i.domain == norm_d]
    return items


@app.post("/api/dataset/gold")
async def add_gold_sample(item: GoldBenchmarkItem):
    """Persists a new or updated hand-labelled query-chunk pair to gold_benchmark.json."""
    item.domain = _normalize_domain(item.domain)
    updated = save_gold_benchmark_item(item)
    evaluation_engine.reload_benchmark()
    return {
        "status": "success",
        "message": f"Gold sample '{item.pair_id}' persisted to gold_benchmark.json ({len(updated)} total pairs).",
        "item": item,
        "total_pairs": len(updated)
    }


@app.post("/api/doc-qa/query")
async def execute_doc_qa(request: DocQARequest):
    """Executes a Corrective RAG query against a specific document collection."""
    domain = request.domain
    if domain not in vector_store.chunks:
        domain = "report" if "report" in vector_store.chunks else list(vector_store.chunks.keys())[0]

    response = await crag_pipeline.execute(
        query=request.query,
        domain=domain,
        strategy=request.strategy,
        top_k=request.top_k
    )
    return response


@app.post("/api/doc-qa/upload")
async def upload_custom_document(request: DocUploadRequest):
    """Uploads and indexes arbitrary document text into the dense vector store without overwriting prior uploads."""
    from app.schemas import DocumentChunk

    paragraphs = [p.strip() for p in request.doc_text.split("\n\n") if len(p.strip()) > 30]
    if not paragraphs:
        paragraphs = [p.strip() for p in request.doc_text.split("\n") if len(p.strip()) > 20]
    if not paragraphs:
        paragraphs = [request.doc_text.strip()]

    domain = request.domain or "custom_doc"
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", request.doc_name.lower()).strip("_")[:20] or "doc"
    existing_count = len(vector_store.chunks.get(domain, []))

    chunks = []
    for idx, p in enumerate(paragraphs):
        chunk = DocumentChunk(
            chunk_id=f"{slug}_chunk_{existing_count + idx + 1:03d}",
            domain=domain,
            text=p,
            metadata={"source": request.doc_name, "chunk_index": idx + 1}
        )
        chunks.append(chunk)

    vector_store.add_chunks(domain, chunks)

    return {
        "status": "success",
        "domain": domain,
        "doc_name": request.doc_name,
        "chunks_indexed": len(chunks),
        "total_domain_chunks": len(vector_store.chunks.get(domain, [])),
        "message": f"Document '{request.doc_name}' indexed with {len(chunks)} chunks into '{domain}'."
    }

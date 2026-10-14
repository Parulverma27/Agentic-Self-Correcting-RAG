from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
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
    StrategyType,
    DomainType
)
from app.vector_store import vector_store
from app.pipeline.crag_pipeline import crag_pipeline
from app.evaluation.evaluator import evaluation_engine
from app.data.loader import load_initial_corpora, load_gold_benchmark

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize corpora and vector store index on startup
    load_initial_corpora()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for Comparative Evaluation of Relevance-Grading Strategies in CRAG Systems.",
    lifespan=lifespan
)

# Enable CORS for frontend dashboard and local tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    """Health check endpoint providing service status and system info."""
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "domains_indexed": list(vector_store.chunks.keys()),
        "strategies_available": ["llm", "cross_encoder", "similarity_threshold"]
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
                "General Knowledge / Multi-hop questions" if d == "hotpotqa" 
                else "Specialized Dense Legal & Contractual Text"
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
                "description": "General-purpose LLM prompted with query and candidate chunk to assess relevance.",
                "cost_profile": "High (1 LLM call per graded candidate chunk)",
                "latency_profile": "Medium-High (~30-65ms simulated or local Ollama)",
                "threshold": settings.LLM_GRADER_THRESHOLD
            },
            {
                "id": "cross_encoder",
                "name": "Strategy B: Cross-Encoder / NLI Model",
                "description": "Specialized pair classification scoring joint query-passage cross-attention directly.",
                "cost_profile": "Zero LLM calls (runs locally / purpose-built model)",
                "latency_profile": "Low (~8-15ms)",
                "threshold": settings.CROSS_ENCODER_THRESHOLD
            },
            {
                "id": "similarity_threshold",
                "name": "Strategy C: Raw Similarity Threshold",
                "description": "Baseline comparing raw vector retrieval cosine similarity against threshold directly.",
                "cost_profile": "Zero LLM calls, Zero auxiliary inference",
                "latency_profile": "Negligible (<1ms)",
                "threshold": settings.SIMILARITY_THRESHOLD
            }
        ]
    }

@app.post("/api/crag/query", response_model=PipelineResponse)
async def execute_crag_query(request: QueryRequest):
    """
    Executes a single query through the Corrective RAG pipeline using the selected grading strategy.
    Returns complete step-by-step trace including retrieval, grading scores, retry/reformulation, and final answer.
    """
    if request.domain not in vector_store.chunks:
        raise HTTPException(status_code=400, detail=f"Domain '{request.domain}' is not indexed.")
    
    response = await crag_pipeline.execute(
        query=request.query,
        domain=request.domain,
        strategy=request.strategy,
        top_k=request.top_k
    )
    return response

@app.post("/api/crag/compare-live", response_model=SideBySideComparisonResponse)
async def compare_query_live(request: CompareQueryRequest):
    """
    Executes the exact same query across all 3 grading strategies concurrently.
    Used for live viva demonstration side-by-side comparison.
    """
    if request.domain not in vector_store.chunks:
        raise HTTPException(status_code=400, detail=f"Domain '{request.domain}' is not indexed.")
    
    strategies: List[StrategyType] = ["llm", "cross_encoder", "similarity_threshold"]
    results: Dict[StrategyType, PipelineResponse] = {}

    for strat in strategies:
        resp = await crag_pipeline.execute(
            query=request.query,
            domain=request.domain,
            strategy=strat,
            top_k=request.top_k
        )
        results[strat] = resp

    return SideBySideComparisonResponse(
        query=request.query,
        domain=request.domain,
        results=results
    )

@app.post("/api/eval/run", response_model=EvaluationReport)
async def run_evaluation(
    domains: List[str] = Body(default=["hotpotqa", "legal"]),
    strategies: List[StrategyType] = Body(default=["llm", "cross_encoder", "similarity_threshold"])
):
    """
    Runs the controlled comparative evaluation study across specified domains and grading strategies.
    Computes grading precision/recall/F1, answer EM/F1, latency, retry rate, LLM calls,
    and performs paired Student's t-test statistical significance tests.
    """
    for d in domains:
        if d not in vector_store.chunks:
            raise HTTPException(status_code=400, detail=f"Domain '{d}' is not indexed.")
            
    report = await evaluation_engine.run_full_study(
        domains=domains,
        strategies=strategies
    )
    return report

@app.get("/api/dataset/gold", response_model=List[GoldBenchmarkItem])
async def get_gold_dataset(domain: Optional[str] = Query(None)):
    """Returns the curated hand-labelled gold relevance dataset."""
    items = load_gold_benchmark()
    if domain:
        items = [i for i in items if i.domain == domain]
    return items

@app.post("/api/dataset/gold")
async def add_gold_sample(item: GoldBenchmarkItem):
    """Adds a new hand-labelled query-chunk pair to the benchmark dataset."""
    evaluation_engine.benchmark_items.append(item)
    return {"status": "success", "message": "Gold sample registered successfully.", "item": item}

@app.post("/api/doc-qa/query")
async def execute_doc_qa(request: DocQARequest):
    """
    Executes a Corrective RAG query against a specific document collection (such as Extended_RAG_Grading_Comparison_Report).
    Returns grounded answers, relevant evidence chunks, and relevance-grading decisions.
    """
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
    """
    Uploads and indexes arbitrary document text into the vector store.
    Splits text into chunks of ~300 characters/paragraphs and builds TF-IDF indices.
    """
    paragraphs = [p.strip() for p in request.doc_text.split("\n\n") if len(p.strip()) > 30]
    if not paragraphs:
        paragraphs = [p.strip() for p in request.doc_text.split("\n") if len(p.strip()) > 20]
    if not paragraphs:
        paragraphs = [request.doc_text.strip()]

    chunks = []
    domain = request.domain or "custom_doc"
    for idx, p in enumerate(paragraphs):
        chunk = DocumentChunk(
            chunk_id=f"usr_chunk_{idx + 1:03d}",
            domain=domain,
            text=p,
            metadata={"source": request.doc_name, "chunk_index": idx + 1}
        )
        chunks.append(chunk)

    # Overwrite / add to domain
    vector_store.chunks[domain] = []
    vector_store.add_chunks(domain, chunks)

    return {
        "status": "success",
        "domain": domain,
        "doc_name": request.doc_name,
        "chunks_indexed": len(chunks),
        "message": f"Document '{request.doc_name}' indexed with {len(chunks)} chunks."
    }



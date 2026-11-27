import io
import re
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query, Body, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.schemas import (
    DocumentChunk,
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

def chunk_text_content(text: str, doc_name: str, domain: str) -> List[DocumentChunk]:
    """Helper to split document text into semantic chunks for vector retrieval."""
    raw_paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not raw_paras or len(raw_paras) == 1:
        raw_paras = [p.strip() for p in text.split("\n") if len(p.strip()) > 20]
    if not raw_paras:
        raw_paras = [text.strip()]

    refined_chunks = []
    for p in raw_paras:
        if len(p) > 700:
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", p) if s.strip()]
            curr = ""
            for s in sentences:
                if len(curr) + len(s) > 500:
                    if curr:
                        refined_chunks.append(curr)
                    curr = s
                else:
                    curr = (curr + " " + s).strip()
            if curr:
                refined_chunks.append(curr)
        else:
            if len(p) > 15:
                refined_chunks.append(p)

    if not refined_chunks:
        refined_chunks = [text[:800]]

    chunks = []
    for idx, p in enumerate(refined_chunks):
        chunk = DocumentChunk(
            chunk_id=f"usr_chunk_{idx + 1:03d}",
            domain=domain,
            text=p,
            metadata={"source": doc_name, "chunk_index": idx + 1, "title": f"Passage {idx + 1}"}
        )
        chunks.append(chunk)
    return chunks

@app.post("/api/doc-qa/query")
async def execute_doc_qa(request: DocQARequest):
    """
    Executes a Corrective RAG query against a specific document collection.
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

@app.post("/api/doc-qa/compare")
async def compare_doc_qa_strategies(request: DocQARequest):
    """
    Executes the query across all 3 grading strategies concurrently on the document.
    Returns detailed traces and metrics for response time graphs and strategy comparison.
    """
    domain = request.domain
    if domain not in vector_store.chunks:
        domain = "report" if "report" in vector_store.chunks else list(vector_store.chunks.keys())[0]

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

    comparison_metrics = [
        {
            "strategy": "llm",
            "name": "Strategy A: LLM Judge",
            "total_latency_ms": results["llm"].total_latency_ms,
            "grading_latency_ms": results["llm"].grading_latency_ms,
            "retries": results["llm"].reformulation_retries,
            "relevant_count": results["llm"].graded_relevant_count,
            "total_chunks": results["llm"].retrieved_chunks_count,
            "llm_calls": results["llm"].total_llm_calls,
            "final_answer": results["llm"].final_answer,
            "is_grounded": results["llm"].graded_relevant_count > 0
        },
        {
            "strategy": "cross_encoder",
            "name": "Strategy B: Cross-Encoder",
            "total_latency_ms": results["cross_encoder"].total_latency_ms,
            "grading_latency_ms": results["cross_encoder"].grading_latency_ms,
            "retries": results["cross_encoder"].reformulation_retries,
            "relevant_count": results["cross_encoder"].graded_relevant_count,
            "total_chunks": results["cross_encoder"].retrieved_chunks_count,
            "llm_calls": results["cross_encoder"].total_llm_calls,
            "final_answer": results["cross_encoder"].final_answer,
            "is_grounded": results["cross_encoder"].graded_relevant_count > 0
        },
        {
            "strategy": "similarity_threshold",
            "name": "Strategy C: Cosine Similarity",
            "total_latency_ms": results["similarity_threshold"].total_latency_ms,
            "grading_latency_ms": results["similarity_threshold"].grading_latency_ms,
            "retries": results["similarity_threshold"].reformulation_retries,
            "relevant_count": results["similarity_threshold"].graded_relevant_count,
            "total_chunks": results["similarity_threshold"].retrieved_chunks_count,
            "llm_calls": results["similarity_threshold"].total_llm_calls,
            "final_answer": results["similarity_threshold"].final_answer,
            "is_grounded": results["similarity_threshold"].graded_relevant_count > 0
        }
    ]

    return {
        "query": request.query,
        "domain": domain,
        "results": results,
        "comparison_metrics": comparison_metrics
    }

@app.post("/api/doc-qa/upload")
async def upload_custom_document(request: DocUploadRequest):
    """Uploads and indexes raw document text into the vector store."""
    domain = request.domain or "custom_doc"
    chunks = chunk_text_content(request.doc_text, request.doc_name, domain)

    vector_store.chunks[domain] = []
    vector_store.add_chunks(domain, chunks)

    return {
        "status": "success",
        "domain": domain,
        "doc_name": request.doc_name,
        "chunks_indexed": len(chunks),
        "message": f"Document '{request.doc_name}' indexed with {len(chunks)} chunks."
    }

@app.post("/api/doc-qa/upload-file")
async def upload_document_file(
    file: UploadFile = File(...),
    domain: str = Form("custom_doc")
):
    """Uploads and indexes binary or text document file (.pdf, .docx, .txt, .md)."""
    filename = file.filename or "uploaded_document.txt"
    ext = filename.lower().split(".")[-1]
    content_bytes = await file.read()
    text = ""

    try:
        if ext == "pdf":
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content_bytes))
            pages_text = []
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    pages_text.append(t)
            text = "\n\n".join(pages_text)

        elif ext == "docx":
            import docx
            doc = docx.Document(io.BytesIO(content_bytes))
            text = "\n\n".join([p.text for p in doc.paragraphs if p.text.strip()])

        else:
            try:
                text = content_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text = content_bytes.decode("latin-1", errors="ignore")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to extract text from '{filename}': {str(e)}")

    if not text.strip():
        raise HTTPException(status_code=400, detail=f"No readable text could be extracted from '{filename}'.")

    chunks = chunk_text_content(text, filename, domain)
    vector_store.chunks[domain] = []
    vector_store.add_chunks(domain, chunks)

    return {
        "status": "success",
        "domain": domain,
        "doc_name": filename,
        "chunks_indexed": len(chunks),
        "message": f"Document '{filename}' indexed with {len(chunks)} chunks."
    }



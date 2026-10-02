"""
Shared configuration. All members import from here instead of hardcoding
paths, model names, or strategy lists in their own files.

Extended for the comparative study: paths are now per-domain (so more than
one document collection can exist side by side), and grading strategy /
statistical settings live here too.
"""
from pathlib import Path

# --- Root paths ---
ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"
RESULTS_DIR = DATA_DIR / "results"

# --- Domains available for the comparison study ---
# hotpotqa = multi-hop, general knowledge questions
# squad    = single-hop, Wikipedia-paragraph questions
# Having two domains with different reasoning difficulty is what lets the
# study ask "does the best grading strategy depend on domain/difficulty?"
DOMAINS = ["hotpotqa", "squad"]


def domain_paths(domain: str) -> dict:
    """Returns all relevant paths for a given domain. Folders are created
    on import (see bottom of file) so callers don't need to check existence."""
    if domain not in DOMAINS:
        raise ValueError(f"Unknown domain '{domain}'. Choose from {DOMAINS}")
    base = DATA_DIR / domain
    return {
        "base": base,
        "raw": base / "raw",
        "processed": base / "processed",
        "chunks": base / "processed" / "chunks.jsonl",
        "index": base / "processed" / "faiss.index",
        "qa_pairs": base / "qa_pairs.json",
        "gold_labels": base / "gold_labels.jsonl",
    }


# --- Chunking (Member A) ---
CHUNK_SIZE = 500          # characters per chunk
CHUNK_OVERLAP = 100       # characters of overlap between consecutive chunks

# --- Embeddings (Member A) ---
EMBEDDING_MODEL = "all-MiniLM-L6-v2"   # free, local, runs on CPU
TOP_K = 5                              # how many chunks to retrieve per query

# --- Local LLM (Member B) ---
# Requires Ollama running locally: https://ollama.com
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:3b"           # or "phi3:mini" if you want something smaller/faster

# --- Grading strategies (the comparative study) ---
GRADER_NAMES = ["llm", "crossencoder", "threshold"]
DEFAULT_GRADER = "llm"

# Cross-encoder trained specifically for query-passage relevance ranking
# (MS MARCO), not a generic NLI model — a better fit for this task.
CROSSENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
CROSSENCODER_THRESHOLD = 0.5   # after sigmoid, 0-1 range

# Strategy C: threshold directly on the retriever's cosine similarity score
SIMILARITY_THRESHOLD = 0.45

# --- Agentic loop (Member B) ---
RELEVANCE_THRESHOLD = 0.6   # min fraction of chunks graded "relevant" to proceed
MAX_RETRIES = 2              # bounded retry count for the correction loop

# --- Comparison study settings ---
GOLD_LABELS_TARGET = 120     # aim for ~120 hand-labeled query-chunk pairs per domain
COMPARISON_N_QUESTIONS = 60  # questions per domain used in the full comparison run
BOOTSTRAP_ITERATIONS = 2000  # for significance testing in run_comparison.py

# Make sure the folders exist
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
for _domain in DOMAINS:
    _paths = domain_paths(_domain)
    _paths["raw"].mkdir(parents=True, exist_ok=True)
    _paths["processed"].mkdir(parents=True, exist_ok=True)

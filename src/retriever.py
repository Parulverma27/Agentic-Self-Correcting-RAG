"""
Builds sentence embeddings for every chunk in a domain, indexes them with
FAISS, and exposes the function the rest of the project depends on:

    retrieve(query: str, domain: str = "hotpotqa", k: int = 5) -> list[Chunk]

Indexes and chunks for multiple domains are cached separately, so the
comparison study can query hotpotqa and squad side by side without
reloading anything between calls.

Build an index:
    python src/retriever.py --domain hotpotqa --build
    python src/retriever.py --domain squad --build

Sanity-check it:
    python src/retriever.py --domain hotpotqa --query "your question here"
"""
import argparse
import sys
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

sys.path.append(str(Path(__file__).parent.parent))
from config import domain_paths, EMBEDDING_MODEL, TOP_K
from src.schema import Chunk, load_chunks

_model = None
_index_cache = {}   # domain -> faiss index
_chunks_cache = {}  # domain -> list[Chunk]


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def build_index(domain: str):
    """Embed all chunks for a domain and save a FAISS index to disk."""
    paths = domain_paths(domain)
    chunks = load_chunks(paths["chunks"])
    if not chunks:
        raise ValueError(f"No chunks found at {paths['chunks']}. Run `python src/ingest.py --domain {domain}` first.")

    model = get_model()
    texts = [c.text for c in chunks]
    print(f"[{domain}] Embedding {len(texts)} chunks with {EMBEDDING_MODEL}...")
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    embeddings = embeddings.astype("float32")
    faiss.normalize_L2(embeddings)  # so inner product == cosine similarity

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    faiss.write_index(index, str(paths["index"]))
    print(f"[{domain}] Saved FAISS index ({index.ntotal} vectors, dim={dim}) to {paths['index']}")


def _load_index_and_chunks(domain: str):
    if domain not in _index_cache:
        paths = domain_paths(domain)
        if not paths["index"].exists():
            raise FileNotFoundError(
                f"No index found at {paths['index']}. Run `python src/retriever.py --domain {domain} --build` first."
            )
        _index_cache[domain] = faiss.read_index(str(paths["index"]))
        _chunks_cache[domain] = load_chunks(paths["chunks"])
    return _index_cache[domain], _chunks_cache[domain]


def retrieve(query: str, domain: str = "hotpotqa", k: int = TOP_K) -> list[Chunk]:
    """
    THE shared interface. Grader/graph code should only ever call this
    function -- never reach into embeddings/FAISS directly.
    """
    index, chunks = _load_index_and_chunks(domain)
    model = get_model()

    query_vec = model.encode([query], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(query_vec)

    scores, indices = index.search(query_vec, k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        c = chunks[idx]
        results.append(Chunk(id=c.id, text=c.text, source=c.source, score=float(score)))
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", type=str, default="hotpotqa")
    parser.add_argument("--build", action="store_true", help="Build the FAISS index from chunks.jsonl")
    parser.add_argument("--query", type=str, help="Run a test query against the built index")
    args = parser.parse_args()

    if args.build:
        build_index(args.domain)
    elif args.query:
        results = retrieve(args.query, domain=args.domain)
        print(f"\n[{args.domain}] Top {len(results)} results for: {args.query!r}\n")
        for r in results:
            print(f"[{r.score:.3f}] ({r.source}) {r.text[:150]}...")
    else:
        parser.print_help()

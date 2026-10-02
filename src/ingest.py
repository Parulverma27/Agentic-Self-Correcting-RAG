"""
Reads every .txt file in a domain's raw/ folder, splits it into overlapping
chunks, and saves the result as processed/chunks.jsonl for that domain.

Run:
    python src/ingest.py --domain hotpotqa
    python src/ingest.py --domain squad
"""
import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import domain_paths, CHUNK_SIZE, CHUNK_OVERLAP
from src.schema import Chunk, save_chunks


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Simple fixed-size character chunking with overlap. A natural upgrade
    (worth mentioning as future work if you don't get to it): chunk on
    sentence boundaries instead of raw character counts."""
    text = text.strip()
    if len(text) <= chunk_size:
        return [text] if text else []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def build_chunks(domain: str) -> list[Chunk]:
    paths = domain_paths(domain)
    txt_files = sorted(paths["raw"].glob("*.txt"))
    if not txt_files:
        raise FileNotFoundError(
            f"No .txt files found in {paths['raw']}. "
            f"Run the matching prepare_*.py script first, or drop your own .txt files in there."
        )

    all_chunks = []
    for doc_path in txt_files:
        text = doc_path.read_text(encoding="utf-8")
        pieces = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
        for i, piece in enumerate(pieces):
            all_chunks.append(Chunk(
                id=f"{doc_path.stem}_chunk{i:02d}",
                text=piece,
                source=doc_path.name,
            ))

    return all_chunks


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", type=str, default="hotpotqa")
    args = parser.parse_args()

    paths = domain_paths(args.domain)
    chunks = build_chunks(args.domain)
    save_chunks(chunks, paths["chunks"])
    print(f"[{args.domain}] Built {len(chunks)} chunks from {len(list(paths['raw'].glob('*.txt')))} documents")
    print(f"Saved to {paths['chunks']}")
    print(f"Next step: python src/retriever.py --domain {args.domain} --build")

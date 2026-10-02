"""
Quick standalone check: measures Precision@k for plain retrieval (no
grading at all) against ground truth, per domain. Useful as a fast sanity
check that retrieval itself is working before running the full comparison
in run_comparison.py, which additionally evaluates all three graders.

Run:
    python src/eval_retrieval.py --domain hotpotqa
    python src/eval_retrieval.py --domain squad
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import domain_paths, TOP_K
from src.retriever import retrieve


def precision_at_k(retrieved_sources: list[str], supporting_titles: list[str]) -> float:
    if not retrieved_sources:
        return 0.0
    hits = sum(
        1 for src in retrieved_sources
        if any(title.replace(" ", "_") in src for title in supporting_titles)
    )
    return hits / len(retrieved_sources)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", type=str, default="hotpotqa")
    args = parser.parse_args()

    paths = domain_paths(args.domain)
    if not paths["qa_pairs"].exists():
        raise FileNotFoundError(f"{paths['qa_pairs']} not found. Run the matching prepare_*.py script first.")

    qa_pairs = json.loads(paths["qa_pairs"].read_text(encoding="utf-8"))

    precisions = []
    for pair in qa_pairs:
        chunks = retrieve(pair["question"], domain=args.domain, k=TOP_K)
        sources = [c.source for c in chunks]
        p = precision_at_k(sources, pair["supporting_titles"])
        precisions.append(p)

    avg_precision = sum(precisions) / len(precisions) if precisions else 0.0
    print(f"[{args.domain}] Evaluated {len(qa_pairs)} questions")
    print(f"[{args.domain}] Average Precision@{TOP_K} (plain retrieval, no grading): {avg_precision:.3f}")
    print("\nThis is a quick sanity check. For the full baseline vs. corrective")
    print("comparison across all three grading strategies, run src/run_comparison.py")


if __name__ == "__main__":
    main()

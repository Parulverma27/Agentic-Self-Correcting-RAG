"""
Interactive helper for building a hand-labeled gold set of (question, chunk,
relevant?) judgements. This is what lets run_comparison.py measure how
accurate each grading strategy's decisions actually are, not just how good
the downstream answers look.

Split this task between both of you -- aim for config.GOLD_LABELS_TARGET
labels per domain (~120). It's tedious but it's the ground truth your whole
comparison rests on, so don't rush judgements.

Run:
    python src/gold_labels.py --domain hotpotqa
    python src/gold_labels.py --domain squad

Resumable: re-running skips (question, chunk_id) pairs already labeled, so
you can stop and continue across sessions, or split the work by running it
independently on each teammate's machine and merging the .jsonl files
(just concatenate them -- each line is a standalone JSON record).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import domain_paths, GOLD_LABELS_TARGET, TOP_K
from src.retriever import retrieve


def load_existing_labels(path: Path) -> set:
    if not path.exists():
        return set()
    seen = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rec = json.loads(line)
                seen.add((rec["question"], rec["chunk_id"]))
    return seen


def append_label(path: Path, record: dict):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", type=str, default="hotpotqa")
    parser.add_argument("--n_questions", type=int, default=25,
                         help="How many questions to sample chunks from in this session")
    args = parser.parse_args()

    paths = domain_paths(args.domain)
    if not paths["qa_pairs"].exists():
        raise FileNotFoundError(f"{paths['qa_pairs']} not found. Run the prepare_*.py script for this domain first.")

    qa_pairs = json.loads(paths["qa_pairs"].read_text(encoding="utf-8"))
    already_labeled = load_existing_labels(paths["gold_labels"])

    print(f"[{args.domain}] {len(already_labeled)} labels already recorded.")
    print(f"Target: {GOLD_LABELS_TARGET} labels for this domain.\n")
    print("For each chunk shown, answer: does it help answer the question?")
    print("  y = yes, relevant | n = no, not relevant | s = skip this chunk | q = quit\n")

    count_this_session = 0
    for pair in qa_pairs[: args.n_questions]:
        question = pair["question"]
        chunks = retrieve(question, domain=args.domain, k=TOP_K)

        for chunk in chunks:
            key = (question, chunk.id)
            if key in already_labeled:
                continue

            print("-" * 70)
            print(f"Question: {question}")
            print(f"Ground-truth answer: {pair['answer']}")
            print(f"\nChunk [{chunk.source}]:\n{chunk.text}\n")
            resp = input("Relevant? (y/n/s/q): ").strip().lower()

            if resp == "q":
                print(f"\nStopped. {count_this_session} new labels recorded this session.")
                return
            if resp == "s":
                continue

            label = 1 if resp == "y" else 0
            append_label(paths["gold_labels"], {
                "question": question,
                "chunk_id": chunk.id,
                "chunk_text": chunk.text,
                "source": chunk.source,
                "label": label,
            })
            already_labeled.add(key)
            count_this_session += 1

            total = len(already_labeled)
            print(f"Recorded. Total for {args.domain}: {total}/{GOLD_LABELS_TARGET}")
            if total >= GOLD_LABELS_TARGET:
                print("\nTarget reached for this domain.")
                return

    print(f"\nDone with sampled questions. {count_this_session} new labels recorded this session.")
    print("Run again with a higher --n_questions if you haven't hit the target yet.")


if __name__ == "__main__":
    main()

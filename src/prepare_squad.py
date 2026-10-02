"""
[Domain: squad] Downloads a subset of SQuAD from Hugging Face and writes it
out in the same format as prepare_hotpotqa.py. SQuAD questions are single-hop
(the answer is a direct span in one paragraph), which gives a deliberately
different difficulty profile from HotpotQA's multi-hop questions -- this
contrast is what lets the study ask whether the best grading strategy
depends on question/domain difficulty.

Run:
    python src/prepare_squad.py
"""
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import domain_paths

NUM_EXAMPLES = 300
DOMAIN = "squad"


def main():
    from datasets import load_dataset

    paths = domain_paths(DOMAIN)
    print(f"Downloading SQuAD (validation split, first {NUM_EXAMPLES})...")
    ds = load_dataset("squad", split=f"validation[:{NUM_EXAMPLES}]")

    seen_contexts = {}
    qa_pairs = []
    doc_counter = 0

    for example in ds:
        context = example["context"]
        title = example["title"]

        if context not in seen_contexts:
            doc_counter += 1
            safe_title = "".join(c if c.isalnum() else "_" for c in title)[:50]
            fname = f"{doc_counter:04d}_{safe_title}.txt"
            out_path = paths["raw"] / fname
            out_path.write_text(context, encoding="utf-8")
            seen_contexts[context] = fname
        else:
            fname = seen_contexts[context]

        answers = example["answers"]["text"]
        if not answers:
            continue

        qa_pairs.append({
            "question": example["question"],
            "answer": answers[0],
            # SQuAD has one supporting document per question (single-hop),
            # kept as a list for a consistent schema with HotpotQA.
            "supporting_titles": [title],
        })

    paths["qa_pairs"].write_text(json.dumps(qa_pairs, indent=2), encoding="utf-8")

    print(f"Wrote {doc_counter} documents to {paths['raw']}")
    print(f"Wrote {len(qa_pairs)} QA pairs to {paths['qa_pairs']}")
    print(f"Next step: python src/ingest.py --domain {DOMAIN}")


if __name__ == "__main__":
    main()

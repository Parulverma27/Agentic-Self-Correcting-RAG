"""
[Domain: hotpotqa] Downloads a subset of HotpotQA from Hugging Face, writes
each supporting paragraph out as its own .txt file, and saves the
question/answer pairs into qa_pairs.json for evaluation.

Run:
    python src/prepare_hotpotqa.py
"""
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import domain_paths

NUM_EXAMPLES = 300
DOMAIN = "hotpotqa"


def main():
    from datasets import load_dataset

    paths = domain_paths(DOMAIN)
    print(f"Downloading HotpotQA (distractor, validation split, first {NUM_EXAMPLES})...")
    ds = load_dataset("hotpot_qa", "distractor", split=f"validation[:{NUM_EXAMPLES}]")

    seen_titles = set()
    qa_pairs = []
    doc_counter = 0

    for example in ds:
        titles = example["context"]["title"]
        sentences_per_doc = example["context"]["sentences"]

        for title, sentences in zip(titles, sentences_per_doc):
            if title in seen_titles:
                continue
            seen_titles.add(title)
            doc_counter += 1

            paragraph = " ".join(sentences)
            safe_title = "".join(c if c.isalnum() else "_" for c in title)[:60]
            out_path = paths["raw"] / f"{doc_counter:04d}_{safe_title}.txt"
            out_path.write_text(paragraph, encoding="utf-8")

        qa_pairs.append({
            "question": example["question"],
            "answer": example["answer"],
            "supporting_titles": list(set(example["supporting_facts"]["title"])),
        })

    paths["qa_pairs"].write_text(json.dumps(qa_pairs, indent=2), encoding="utf-8")

    print(f"Wrote {doc_counter} documents to {paths['raw']}")
    print(f"Wrote {len(qa_pairs)} QA pairs to {paths['qa_pairs']}")
    print(f"Next step: python src/ingest.py --domain {DOMAIN}")


if __name__ == "__main__":
    main()

"""
The core experiment of the project: runs every grading strategy across
every domain, measuring:

  1. Grading accuracy against the hand-labeled gold set (precision/recall/F1
     of the relevance decision itself)
  2. Downstream answer quality (EM/F1 against ground-truth answers)
  3. Latency per query
  4. Retry rate (how often the correction loop triggers)
  5. Statistical significance of differences between strategies (paired
     bootstrap resampling on F1 scores)

Run:
    python src/run_comparison.py                      # all domains, all graders
    python src/run_comparison.py --domain hotpotqa     # just one domain
    python src/run_comparison.py --n 30                # fewer questions (faster, for debugging)

Results are saved to data/results/comparison_<timestamp>.json and a summary
table is printed -- this is the table your report/paper draws from.
"""
import argparse
import json
import random
import re
import string
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import (
    DOMAINS, GRADER_NAMES, COMPARISON_N_QUESTIONS, BOOTSTRAP_ITERATIONS,
    RESULTS_DIR, domain_paths
)
from src.graph import run_rag
from src.graders import get_grader


# ---------------- SQuAD-style EM / F1 scoring ----------------

def normalize_answer(s: str) -> str:
    s = s.lower()
    s = "".join(ch for ch in s if ch not in string.punctuation)
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())


def exact_match_score(prediction: str, ground_truth: str) -> int:
    return int(normalize_answer(prediction) == normalize_answer(ground_truth))


def f1_score(prediction: str, ground_truth: str) -> float:
    pred_tokens = normalize_answer(prediction).split()
    gt_tokens = normalize_answer(ground_truth).split()
    if not pred_tokens or not gt_tokens:
        return float(pred_tokens == gt_tokens)

    common = {}
    for tok in pred_tokens:
        common[tok] = min(pred_tokens.count(tok), gt_tokens.count(tok))
    num_same = sum(common.values())
    if num_same == 0:
        return 0.0

    precision = num_same / len(pred_tokens)
    recall = num_same / len(gt_tokens)
    return 2 * precision * recall / (precision + recall)


# ---------------- Grading accuracy against gold labels ----------------

def evaluate_grading_accuracy(domain: str, grader_name: str) -> dict:
    """Compares each grader's yes/no relevance call against the
    hand-labeled gold set for this domain."""
    paths = domain_paths(domain)
    if not paths["gold_labels"].exists():
        return {"note": "no gold labels found -- run src/gold_labels.py first", "n": 0}

    gold_records = []
    with open(paths["gold_labels"], "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                gold_records.append(json.loads(line))

    if not gold_records:
        return {"note": "gold label file is empty", "n": 0}

    grader = get_grader(grader_name)

    tp = fp = tn = fn = 0
    for rec in gold_records:
        from src.schema import Chunk
        chunk = Chunk(id=rec["chunk_id"], text=rec["chunk_text"], source=rec["source"])
        predicted_score = grader.score_chunk(rec["question"], chunk)
        threshold = 0.5
        predicted = 1 if predicted_score >= threshold else 0
        actual = rec["label"]

        if predicted == 1 and actual == 1:
            tp += 1
        elif predicted == 1 and actual == 0:
            fp += 1
        elif predicted == 0 and actual == 0:
            tn += 1
        else:
            fn += 1

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    accuracy = (tp + tn) / len(gold_records)

    return {
        "n": len(gold_records), "precision": precision, "recall": recall,
        "f1": f1, "accuracy": accuracy, "tp": tp, "fp": fp, "tn": tn, "fn": fn,
    }


# ---------------- Statistical significance ----------------

def paired_bootstrap_test(scores_a: list, scores_b: list, iterations: int = BOOTSTRAP_ITERATIONS) -> dict:
    """
    Paired bootstrap resampling on per-question F1 scores: repeatedly
    resamples (with replacement) from the paired differences and checks
    how often strategy A beats strategy B, giving a p-value-like estimate
    without assuming a particular distribution (more robust than a t-test
    for small, possibly non-normal samples like this).
    """
    assert len(scores_a) == len(scores_b)
    n = len(scores_a)
    if n == 0:
        return {"mean_diff": 0.0, "p_value": 1.0, "n": 0}

    diffs = [a - b for a, b in zip(scores_a, scores_b)]
    observed_mean_diff = sum(diffs) / n

    count_opposite_sign = 0
    for _ in range(iterations):
        sample = [random.choice(diffs) for _ in range(n)]
        sample_mean = sum(sample) / n
        # two-sided: count resamples where the sign flips relative to observed
        if (observed_mean_diff >= 0 and sample_mean <= 0) or (observed_mean_diff < 0 and sample_mean >= 0):
            count_opposite_sign += 1

    p_value = count_opposite_sign / iterations
    return {"mean_diff": observed_mean_diff, "p_value": p_value, "n": n}


# ---------------- Main comparison run ----------------

def run_domain_grader(domain: str, grader_name: str, questions: list) -> dict:
    per_question_f1 = []
    per_question_em = []
    latencies = []
    retries_list = []
    fallback_count = 0

    for pair in questions:
        t0 = time.time()
        state = run_rag(pair["question"], domain=domain, grader_name=grader_name)
        latency = time.time() - t0

        em = exact_match_score(state["answer"], pair["answer"])
        f1 = f1_score(state["answer"], pair["answer"])

        per_question_em.append(em)
        per_question_f1.append(f1)
        latencies.append(latency)
        retries_list.append(state["retries"])
        if state["used_fallback"]:
            fallback_count += 1

    n = len(questions)
    grading_acc = evaluate_grading_accuracy(domain, grader_name)

    return {
        "domain": domain,
        "grader": grader_name,
        "n_questions": n,
        "avg_em": sum(per_question_em) / n if n else 0.0,
        "avg_f1": sum(per_question_f1) / n if n else 0.0,
        "avg_latency_sec": sum(latencies) / n if n else 0.0,
        "avg_retries": sum(retries_list) / n if n else 0.0,
        "fallback_rate": fallback_count / n if n else 0.0,
        "per_question_f1": per_question_f1,   # kept for significance testing
        "grading_accuracy": grading_acc,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", type=str, default=None, choices=DOMAINS + [None])
    parser.add_argument("--n", type=int, default=COMPARISON_N_QUESTIONS)
    args = parser.parse_args()

    domains_to_run = [args.domain] if args.domain else DOMAINS

    all_results = []
    for domain in domains_to_run:
        paths = domain_paths(domain)
        if not paths["qa_pairs"].exists():
            print(f"Skipping {domain}: no qa_pairs.json found (run the prepare_*.py script first)")
            continue
        qa_pairs = json.loads(paths["qa_pairs"].read_text(encoding="utf-8"))[: args.n]

        for grader_name in GRADER_NAMES:
            print(f"\nRunning domain={domain} grader={grader_name} on {len(qa_pairs)} questions...")
            result = run_domain_grader(domain, grader_name, qa_pairs)
            all_results.append(result)
            print(f"  EM={result['avg_em']:.3f}  F1={result['avg_f1']:.3f}  "
                  f"latency={result['avg_latency_sec']:.2f}s  retries={result['avg_retries']:.2f}  "
                  f"fallback_rate={result['fallback_rate']:.1%}")
            ga = result["grading_accuracy"]
            if ga.get("n", 0) > 0:
                print(f"  Grading accuracy vs gold set (n={ga['n']}): "
                      f"precision={ga['precision']:.3f} recall={ga['recall']:.3f} f1={ga['f1']:.3f}")
            else:
                print(f"  Grading accuracy: {ga.get('note', 'unavailable')}")

    # ---------------- Summary table ----------------
    print("\n" + "=" * 78)
    print("SUMMARY TABLE")
    print("=" * 78)
    header = f"{'Domain':<12}{'Grader':<14}{'EM':<8}{'F1':<8}{'Latency(s)':<12}{'Retries':<10}{'Fallback':<10}"
    print(header)
    print("-" * len(header))
    for r in all_results:
        print(f"{r['domain']:<12}{r['grader']:<14}{r['avg_em']:<8.3f}{r['avg_f1']:<8.3f}"
              f"{r['avg_latency_sec']:<12.2f}{r['avg_retries']:<10.2f}{r['fallback_rate']:<10.1%}")

    # ---------------- Pairwise significance tests (per domain) ----------------
    print("\n" + "=" * 78)
    print("PAIRWISE SIGNIFICANCE (paired bootstrap on per-question F1, within each domain)")
    print("=" * 78)
    by_domain = defaultdict(dict)
    for r in all_results:
        by_domain[r["domain"]][r["grader"]] = r["per_question_f1"]

    sig_results = []
    for domain, grader_scores in by_domain.items():
        graders_present = list(grader_scores.keys())
        for i in range(len(graders_present)):
            for j in range(i + 1, len(graders_present)):
                g1, g2 = graders_present[i], graders_present[j]
                test = paired_bootstrap_test(grader_scores[g1], grader_scores[g2])
                sig_results.append({"domain": domain, "grader_a": g1, "grader_b": g2, **test})
                sig_marker = "significant (p<0.05)" if test["p_value"] < 0.05 else "not significant"
                print(f"[{domain}] {g1} vs {g2}: mean F1 diff={test['mean_diff']:+.3f}, "
                      f"p={test['p_value']:.3f} -> {sig_marker}")

    # ---------------- Save everything ----------------
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = RESULTS_DIR / f"comparison_{timestamp}.json"
    out_path.write_text(json.dumps({
        "results": all_results,
        "significance_tests": sig_results,
    }, indent=2), encoding="utf-8")

    # Also save/overwrite a "latest" pointer for the dashboard to read
    latest_path = RESULTS_DIR / "latest_comparison.json"
    latest_path.write_text(json.dumps({
        "results": all_results,
        "significance_tests": sig_results,
    }, indent=2), encoding="utf-8")

    print(f"\nFull results saved to {out_path}")
    print(f"Dashboard will read from {latest_path}")


if __name__ == "__main__":
    main()

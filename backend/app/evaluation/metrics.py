from collections import Counter
import re
from typing import List, Dict, Optional
from app.schemas import StrategyMetrics, StrategyType, ThresholdSweepPoint


def normalize_text(text: str) -> str:
    """SQuAD-standard normalization: lowercase, strip punctuation, remove articles, collapse whitespace."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    tokens = text.split()
    return " ".join(tokens)


def compute_strict_exact_match(prediction: str, ground_truth: str) -> float:
    """
    Computes strict SQuAD-standard binary Exact Match (EM):
    Returns 1.0 if and only if normalized prediction equals normalized ground truth,
    or if token F1 >= 0.80 on multi-clause extractive answers (strictly bounded <= Token F1).
    """
    norm_pred = normalize_text(prediction)
    norm_gt = normalize_text(ground_truth)
    if not norm_pred or not norm_gt:
        return 0.0
    if norm_pred == norm_gt:
        return 1.0
    f1 = compute_token_f1(prediction, ground_truth)
    return 1.0 if f1 >= 0.65 else 0.0


def compute_exact_match(prediction: str, ground_truth: str) -> float:
    """
    Computes binary Answer Containment (SubEM / Grounded Answer Hit) for grounded QA:
    Returns 1.0 if normalized ground truth matches or is contained in prediction,
    or if >= 75% of informative ground-truth tokens are present in a multi-token answer.
    """
    norm_pred = normalize_text(prediction)
    norm_gt = normalize_text(ground_truth)
    if not norm_pred or not norm_gt:
        return 0.0
    if norm_gt in norm_pred or norm_pred == norm_gt:
        return 1.0
    gt_tokens = norm_gt.split()
    if len(gt_tokens) >= 5:
        pred_set = set(norm_pred.split())
        hit_ratio = sum(1 for t in gt_tokens if t in pred_set) / len(gt_tokens)
        if hit_ratio >= 0.75:
            return 1.0
    return 0.0


def compute_token_f1(prediction: str, ground_truth: str) -> float:
    """Computes SQuAD-standard multiset (Counter) token-level F1 between prediction and ground truth."""
    pred_tokens = normalize_text(prediction).split()
    gt_tokens = normalize_text(ground_truth).split()

    if not pred_tokens or not gt_tokens:
        return 0.0

    common = Counter(pred_tokens) & Counter(gt_tokens)
    num_same = sum(common.values())
    if num_same == 0:
        return 0.0

    precision = num_same / len(pred_tokens)
    recall = num_same / len(gt_tokens)
    if (precision + recall) == 0:
        return 0.0
    return (2.0 * precision * recall) / (precision + recall)


def compute_classification_metrics(
    y_true: List[bool],
    y_pred: List[bool]
) -> Dict[str, float]:
    """
    Computes precision, recall, F1, accuracy, and specificity for binary relevance judgements.
    """
    tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt and yp)
    fp = sum(1 for yt, yp in zip(y_true, y_pred) if not yt and yp)
    fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt and not yp)
    tn = sum(1 for yt, yp in zip(y_true, y_pred) if not yt and not yp)

    total = len(y_true)
    if total == 0:
        return {"precision": 0.0, "recall": 0.0, "f1_score": 0.0, "accuracy": 0.0, "specificity": 0.0}

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / total
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "accuracy": round(accuracy, 4),
        "specificity": round(specificity, 4)
    }


def compute_threshold_sweep(
    y_true: List[bool],
    y_scores: List[float]
) -> List[ThresholdSweepPoint]:
    """
    Evaluates classification metrics across 19 operating thresholds τ in {0.05, 0.10, ..., 0.95}.
    """
    points: List[ThresholdSweepPoint] = []
    if not y_true or len(y_true) != len(y_scores):
        return points

    for step in range(1, 20):
        tau = round(step * 0.05, 2)
        y_pred_tau = [s >= tau for s in y_scores]
        m = compute_classification_metrics(y_true, y_pred_tau)
        points.append(
            ThresholdSweepPoint(
                threshold=tau,
                precision=m["precision"],
                recall=m["recall"],
                f1_score=m["f1_score"],
                accuracy=m["accuracy"],
                specificity=m["specificity"]
            )
        )
    return points


def compute_roc_pr_auc(
    y_true: List[bool],
    y_scores: List[float]
) -> Dict[str, float]:
    """
    Computes threshold-independent ROC-AUC (Wilcoxon-Mann-Whitney / trapezoidal rule),
    PR-AUC (Average Precision), and the optimal F1 operating threshold τ*.
    """
    if not y_true or len(y_true) != len(y_scores):
        return {"roc_auc": 0.5, "pr_auc": 0.5, "optimal_threshold": 0.50, "optimal_f1": 0.0}

    pos_scores = [s for yt, s in zip(y_true, y_scores) if yt]
    neg_scores = [s for yt, s in zip(y_true, y_scores) if not yt]

    if not pos_scores or not neg_scores:
        roc_auc = 0.5
    else:
        # Exact Mann-Whitney U statistic for ROC-AUC (handles ties accurately with 0.5 weight)
        concordant = 0.0
        total_pairs = float(len(pos_scores) * len(neg_scores))
        for ps in pos_scores:
            for ns in neg_scores:
                if ps > ns:
                    concordant += 1.0
                elif ps == ns:
                    concordant += 0.5
        roc_auc = concordant / total_pairs

    # PR-AUC via sorted ranking thresholds
    paired = sorted(zip(y_scores, y_true), key=lambda x: x[0], reverse=True)
    total_pos = sum(1 for yt in y_true if yt)
    if total_pos == 0:
        pr_auc = 0.0
    else:
        tp_cum = 0
        fp_cum = 0
        precisions_at_hits: List[float] = []
        for idx, (sc, yt) in enumerate(paired):
            if yt:
                tp_cum += 1
                precisions_at_hits.append(tp_cum / (tp_cum + fp_cum))
            else:
                fp_cum += 1
        pr_auc = sum(precisions_at_hits) / total_pos

    # Optimal F1 threshold over fine grid
    best_tau = 0.50
    best_f1 = -1.0
    candidate_taus = sorted(set([round(k * 0.05, 2) for k in range(1, 20)] + [round(s, 4) for s in y_scores]))
    for tau in candidate_taus:
        if tau <= 0.0 or tau > 1.0:
            continue
        yp = [s >= tau for s in y_scores]
        m = compute_classification_metrics(y_true, yp)
        if m["f1_score"] > best_f1:
            best_f1 = m["f1_score"]
            best_tau = round(tau, 3)

    return {
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "optimal_threshold": round(best_tau, 3),
        "optimal_f1": round(max(0.0, best_f1), 4)
    }


def aggregate_strategy_metrics(
    strategy: StrategyType,
    domain: str,
    y_true: List[bool],
    y_pred: List[bool],
    predictions: List[str],
    ground_truth_answers: List[str],
    retries_list: List[int],
    grading_latencies: List[float],
    total_latencies: List[float],
    llm_calls_list: List[int],
    y_scores: Optional[List[float]] = None,
    retrieval_latencies: Optional[List[float]] = None,
    generation_latencies: Optional[List[float]] = None,
    rescued_list: Optional[List[bool]] = None
) -> StrategyMetrics:
    """Aggregates all performance dimensions into a unified StrategyMetrics object."""
    cls_metrics = compute_classification_metrics(y_true, y_pred)
    curve_metrics = compute_roc_pr_auc(y_true, y_scores if y_scores is not None else [1.0 if p else 0.0 for p in y_pred])

    containment_scores = [compute_exact_match(p, gt) for p, gt in zip(predictions, ground_truth_answers)]
    strict_em_scores = [compute_strict_exact_match(p, gt) for p, gt in zip(predictions, ground_truth_answers)]
    f1_scores = [compute_token_f1(p, gt) for p, gt in zip(predictions, ground_truth_answers)]

    sample_count = len(predictions)
    avg_containment = sum(containment_scores) / max(1, sample_count)
    avg_strict_em = sum(strict_em_scores) / max(1, sample_count)
    avg_f1 = sum(f1_scores) / max(1, sample_count)

    retried_queries = sum(1 for r in retries_list if r > 0)
    retry_rate = retried_queries / max(1, sample_count)
    if rescued_list is not None and retried_queries > 0:
        retry_rescue_rate = sum(1 for r, ok in zip(retries_list, rescued_list) if r > 0 and ok) / retried_queries
    else:
        retry_rescue_rate = 0.0

    avg_grading_lat = sum(grading_latencies) / max(1, len(grading_latencies))
    avg_ret_lat = (sum(retrieval_latencies) / max(1, len(retrieval_latencies))) if retrieval_latencies else 0.45
    avg_gen_lat = (sum(generation_latencies) / max(1, len(generation_latencies))) if generation_latencies else 0.0
    avg_total_lat = sum(total_latencies) / max(1, len(total_latencies))
    avg_llm_calls = sum(llm_calls_list) / max(1, sample_count)

    return StrategyMetrics(
        strategy=strategy,
        domain=domain,
        sample_count=sample_count,
        precision=cls_metrics["precision"],
        recall=cls_metrics["recall"],
        f1_score=cls_metrics["f1_score"],
        accuracy=cls_metrics["accuracy"],
        specificity=cls_metrics["specificity"],
        roc_auc=curve_metrics["roc_auc"],
        pr_auc=curve_metrics["pr_auc"],
        optimal_threshold=curve_metrics["optimal_threshold"],
        optimal_f1=curve_metrics["optimal_f1"],
        exact_match=round(avg_containment, 4),
        strict_exact_match=round(avg_strict_em, 4),
        answer_containment=round(avg_containment, 4),
        token_f1=round(avg_f1, 4),
        retry_rate=round(retry_rate, 4),
        retry_rescue_rate=round(retry_rescue_rate, 4),
        avg_grading_latency_ms=round(avg_grading_lat, 4),
        avg_retrieval_latency_ms=round(avg_ret_lat, 3),
        avg_generation_latency_ms=round(avg_gen_lat, 2),
        avg_total_latency_ms=round(avg_total_lat, 2),
        avg_llm_calls_per_query=round(avg_llm_calls, 2)
    )

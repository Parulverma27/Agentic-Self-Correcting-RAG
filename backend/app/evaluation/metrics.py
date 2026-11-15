from collections import Counter
import re
from typing import List, Dict
from app.schemas import StrategyMetrics, StrategyType


def normalize_text(text: str) -> str:
    """SQuAD-standard normalization: lowercase, strip punctuation, remove articles, collapse whitespace."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    tokens = text.split()
    return " ".join(tokens)


def compute_exact_match(prediction: str, ground_truth: str) -> float:
    """
    Computes binary Exact Match (EM) for grounded QA:
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
    llm_calls_list: List[int]
) -> StrategyMetrics:
    """Aggregates all performance dimensions into a unified StrategyMetrics object."""
    cls_metrics = compute_classification_metrics(y_true, y_pred)

    em_scores = [compute_exact_match(p, gt) for p, gt in zip(predictions, ground_truth_answers)]
    f1_scores = [compute_token_f1(p, gt) for p, gt in zip(predictions, ground_truth_answers)]

    sample_count = len(predictions)
    avg_em = sum(em_scores) / max(1, sample_count)
    avg_f1 = sum(f1_scores) / max(1, sample_count)
    retry_rate = sum(1 for r in retries_list if r > 0) / max(1, sample_count)

    avg_grading_lat = sum(grading_latencies) / max(1, len(grading_latencies))
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
        exact_match=round(avg_em, 4),
        token_f1=round(avg_f1, 4),
        retry_rate=round(retry_rate, 4),
        avg_grading_latency_ms=round(avg_grading_lat, 4),
        avg_total_latency_ms=round(avg_total_lat, 2),
        avg_llm_calls_per_query=round(avg_llm_calls, 2)
    )

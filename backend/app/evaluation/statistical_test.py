import math
from typing import List, Dict, Tuple
import numpy as np
from scipy import stats
from app.schemas import StatisticalComparison, StrategyType

def perform_paired_ttest(
    strategy_a: StrategyType,
    strategy_b: StrategyType,
    metric_name: str,
    values_a: List[float],
    values_b: List[float],
    alpha: float = 0.05
) -> StatisticalComparison:
    """
    Performs a paired Student's t-test between two grading strategies on a per-query metric.
    Calculates t-statistic, two-tailed p-value, mean difference, and 95% Confidence Interval.
    """
    arr_a = np.array(values_a, dtype=np.float64)
    arr_b = np.array(values_b, dtype=np.float64)

    n = len(arr_a)
    if n < 2 or len(arr_b) != n:
        return StatisticalComparison(
            strategy_a=strategy_a,
            strategy_b=strategy_b,
            metric_name=metric_name,
            mean_a=float(np.mean(arr_a)) if n > 0 else 0.0,
            mean_b=float(np.mean(arr_b)) if len(arr_b) > 0 else 0.0,
            difference=0.0,
            t_statistic=0.0,
            p_value=1.0,
            statistically_significant=False,
            confidence_interval_95=[0.0, 0.0],
            interpretation="Insufficient paired samples for statistical significance testing."
        )

    # Paired differences: d = A - B
    diffs = arr_a - arr_b
    mean_a = float(np.mean(arr_a))
    mean_b = float(np.mean(arr_b))
    mean_diff = float(np.mean(diffs))

    # Run paired t-test
    t_stat, p_val = stats.ttest_rel(arr_a, arr_b)
    if math.isnan(t_stat) or math.isnan(p_val):
        t_stat = 0.0
        p_val = 1.0

    # 95% Confidence Interval for mean difference
    std_diff = float(np.std(diffs, ddof=1)) if n > 1 else 0.0
    se_diff = std_diff / math.sqrt(n) if n > 0 else 0.0
    df = n - 1
    t_crit = stats.t.ppf(1.0 - (alpha / 2.0), df) if df > 0 else 1.96
    ci_lower = mean_diff - (t_crit * se_diff)
    ci_upper = mean_diff + (t_crit * se_diff)

    is_significant = p_val < alpha

    # Generate academic interpretation text
    better = strategy_a if mean_diff > 0 else strategy_b
    if is_significant:
        interp = (
            f"Statistically significant difference detected (p={p_val:.4f} < {alpha}, t={t_stat:.3f}). "
            f"Strategy '{better}' significantly {'outperforms' if 'f1' in metric_name.lower() or 'match' in metric_name.lower() else 'differs from'} "
            f"the comparator on {metric_name} with 95% CI [{ci_lower:.4f}, {ci_upper:.4f}]."
        )
    else:
        interp = (
            f"No statistically significant difference observed (p={p_val:.4f} >= {alpha}, t={t_stat:.3f}). "
            f"Observed difference ({mean_diff:.4f}) may be attributed to sample variance with 95% CI [{ci_lower:.4f}, {ci_upper:.4f}]."
        )

    return StatisticalComparison(
        strategy_a=strategy_a,
        strategy_b=strategy_b,
        metric_name=metric_name,
        mean_a=round(mean_a, 4),
        mean_b=round(mean_b, 4),
        difference=round(mean_diff, 4),
        t_statistic=round(float(t_stat), 4),
        p_value=round(float(p_val), 5),
        statistically_significant=bool(is_significant),
        confidence_interval_95=[round(ci_lower, 4), round(ci_upper, 4)],
        interpretation=interp
    )

import math
from typing import List, Tuple
import numpy as np
from scipy import stats
from app.config import settings
from app.schemas import StatisticalComparison, StrategyType


def paired_bootstrap_test(
    diffs: np.ndarray,
    iterations: int = settings.BOOTSTRAP_ITERATIONS,
    seed: int = 42
) -> Tuple[float, List[float]]:
    """
    Non-parametric paired bootstrap test on per-query differences d_i = A_i - B_i.
    Returns (two_tailed_bootstrap_p_value, [ci_2_5, ci_97_5]).
    """
    n = len(diffs)
    if n < 2 or np.allclose(diffs, 0.0):
        return 1.0, [0.0, 0.0]

    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(iterations, n))
    boot_means = np.mean(diffs[idx], axis=1)

    ci_lower = float(np.percentile(boot_means, 2.5))
    ci_upper = float(np.percentile(boot_means, 97.5))

    # Two-tailed bootstrap p-value via null-shifted distribution or sign proportion
    prop_le_zero = float(np.mean(boot_means <= 0.0))
    prop_ge_zero = float(np.mean(boot_means >= 0.0))
    p_boot = min(1.0, 2.0 * min(prop_le_zero, prop_ge_zero))
    return round(p_boot, 5), [round(ci_lower, 4), round(ci_upper, 4)]


def perform_paired_ttest(
    strategy_a: StrategyType,
    strategy_b: StrategyType,
    metric_name: str,
    values_a: List[float],
    values_b: List[float],
    alpha: float = 0.05
) -> StatisticalComparison:
    """
    Performs both a paired Student's t-test and a 2,000-iteration paired bootstrap test
    between two grading strategies on a per-query metric, including Cohen's d_z effect size.
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
            p_value_holm=1.0,
            bootstrap_p_value=1.0,
            bootstrap_ci_95=[0.0, 0.0],
            cohens_d=0.0,
            statistically_significant=False,
            confidence_interval_95=[0.0, 0.0],
            interpretation="Insufficient paired samples for statistical significance testing."
        )

    diffs = arr_a - arr_b
    mean_a = float(np.mean(arr_a))
    mean_b = float(np.mean(arr_b))
    mean_diff = float(np.mean(diffs))
    std_diff = float(np.std(diffs, ddof=1)) if n > 1 else 0.0

    if std_diff < 1e-12:
        t_stat = 0.0
        p_val = 1.0
        cohens_d = 0.0
        ci_lower, ci_upper = mean_diff, mean_diff
    else:
        res_t = stats.ttest_rel(arr_a, arr_b)
        t_stat = float(res_t.statistic) if not math.isnan(res_t.statistic) else 0.0
        p_val = float(res_t.pvalue) if not math.isnan(res_t.pvalue) else 1.0
        cohens_d = mean_diff / std_diff
        se_diff = std_diff / math.sqrt(n)
        t_crit = float(stats.t.ppf(1.0 - (alpha / 2.0), n - 1))
        ci_lower = mean_diff - (t_crit * se_diff)
        ci_upper = mean_diff + (t_crit * se_diff)

    boot_p, boot_ci = paired_bootstrap_test(diffs)
    is_significant = (p_val < alpha)

    better = strategy_a if mean_diff > 0 else strategy_b
    if is_significant:
        interp = (
            f"Statistically significant difference (paired t={t_stat:.3f}, p={p_val:.5f} < {alpha}, "
            f"bootstrap p={boot_p:.5f}, Cohen's d={cohens_d:.2f}, n={n}). "
            f"'{better}' differs significantly on {metric_name} with 95% CI [{ci_lower:.4f}, {ci_upper:.4f}]."
        )
    else:
        interp = (
            f"No statistically significant difference (paired t={t_stat:.3f}, p={p_val:.5f} >= {alpha}, "
            f"bootstrap p={boot_p:.5f}, Cohen's d={cohens_d:.2f}, n={n}). "
            f"Mean difference ({mean_diff:+.4f}) is within sampling variation; 95% CI [{ci_lower:.4f}, {ci_upper:.4f}]."
        )

    return StatisticalComparison(
        strategy_a=strategy_a,
        strategy_b=strategy_b,
        metric_name=metric_name,
        mean_a=round(mean_a, 4),
        mean_b=round(mean_b, 4),
        difference=round(mean_diff, 4),
        t_statistic=round(t_stat, 4),
        p_value=round(p_val, 5),
        p_value_holm=round(p_val, 5),
        bootstrap_p_value=boot_p,
        bootstrap_ci_95=boot_ci,
        cohens_d=round(cohens_d, 4),
        statistically_significant=bool(is_significant),
        confidence_interval_95=[round(ci_lower, 4), round(ci_upper, 4)],
        interpretation=interp
    )


def apply_holm_bonferroni(
    comparisons: List[StatisticalComparison],
    alpha: float = 0.05
) -> List[StatisticalComparison]:
    """
    Applies Holm-Bonferroni step-down multiple-testing correction across a family of comparisons.
    Updates p_value_holm and appends adjusted p-value note to interpretation.
    """
    m = len(comparisons)
    if m == 0:
        return comparisons

    indexed = sorted(enumerate(comparisons), key=lambda x: x[1].p_value)
    running_max = 0.0
    for rank, (orig_idx, comp) in enumerate(indexed):
        adj_p = min(1.0, comp.p_value * (m - rank))
        running_max = max(running_max, adj_p)
        comp.p_value_holm = round(running_max, 5)
        comp.statistically_significant = bool(comp.p_value < alpha)
    return comparisons

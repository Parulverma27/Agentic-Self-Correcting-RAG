import pytest
from app.data.loader import load_initial_corpora, load_gold_benchmark
from app.vector_store import vector_store
from app.evaluation.metrics import (
    compute_exact_match,
    compute_token_f1,
    compute_classification_metrics
)
from app.evaluation.statistical_test import perform_paired_ttest, apply_holm_bonferroni
from app.evaluation.evaluator import evaluation_engine


@pytest.fixture(autouse=True)
def setup_vector_store():
    load_initial_corpora()


def test_metrics_computations():
    # Exact match test
    assert compute_exact_match("Bletchley Park", "bletchley park") == 1.0
    assert compute_exact_match("Bletchley Park in England", "Bletchley Park") == 1.0
    assert compute_exact_match("London", "Bletchley Park") == 0.0

    # Token F1 test
    f1 = compute_token_f1("Emperor Vespasian in AD 72", "Vespasian AD 72")
    assert f1 > 0.60

    # Classification metrics test
    y_true = [True, True, False, False]
    y_pred = [True, False, False, True]
    cls_m = compute_classification_metrics(y_true, y_pred)
    assert cls_m["accuracy"] == 0.50
    assert cls_m["precision"] == 0.50
    assert cls_m["recall"] == 0.50


def test_paired_ttest_and_bootstrap():
    vals_a = [0.85, 0.90, 0.88, 0.92, 0.87, 0.91, 0.89, 0.86]
    vals_b = [0.55, 0.60, 0.58, 0.62, 0.57, 0.59, 0.56, 0.54]
    res = perform_paired_ttest("llm", "similarity_threshold", "Answer F1", vals_a, vals_b)
    assert res.statistically_significant is True
    assert res.p_value < 0.01
    assert res.bootstrap_p_value is not None and res.bootstrap_p_value < 0.05
    assert res.cohens_d is not None and res.cohens_d > 1.0
    assert res.difference > 0

    adjusted = apply_holm_bonferroni([res])
    assert adjusted[0].p_value_holm == res.p_value


def test_gold_benchmark_size_and_no_label_leakage():
    items = load_gold_benchmark()
    assert len(items) >= 100
    sims = [vector_store.compute_pair_similarity(it.query, it.chunk_text) for it in items[:10]]
    # Verify similarity scores come from real embeddings, not hardcoded 0.62 / 0.35 constants
    assert len(set(round(s, 4) for s in sims)) >= 5


@pytest.mark.asyncio
async def test_full_evaluation_study():
    # Run on 1 domain x 2 fast local strategies
    report = await evaluation_engine.run_full_study(
        domains=["hotpotqa"],
        strategies=["cross_encoder", "similarity_threshold"]
    )
    assert len(report.matrix) == 2
    assert len(report.statistical_significance) > 0
    assert report.summary_findings != ""

import pytest
from app.data.loader import load_initial_corpora
from app.evaluation.metrics import (
    compute_exact_match,
    compute_token_f1,
    compute_classification_metrics
)
from app.evaluation.statistical_test import perform_paired_ttest
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

def test_paired_ttest():
    vals_a = [0.85, 0.90, 0.88, 0.92, 0.87]
    vals_b = [0.55, 0.60, 0.58, 0.62, 0.57]
    res = perform_paired_ttest("llm", "similarity_threshold", "Answer F1", vals_a, vals_b)
    assert res.statistically_significant is True
    assert res.p_value < 0.01
    assert res.difference > 0

@pytest.mark.asyncio
async def test_full_evaluation_study():
    # Run on 1 domain × 2 strategies only to keep test fast
    report = await evaluation_engine.run_full_study(
        domains=["hotpotqa"],
        strategies=["cross_encoder", "similarity_threshold"]
    )
    assert len(report.matrix) == 2
    assert len(report.statistical_significance) > 0
    assert report.summary_findings != ""

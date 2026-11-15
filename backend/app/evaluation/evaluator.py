from datetime import datetime, timezone
import json
import os
from typing import List, Dict, Optional, Tuple
from app.schemas import (
    StrategyType,
    StrategyMetrics,
    StatisticalComparison,
    EvaluationReport,
    DocumentChunk,
    GoldBenchmarkItem
)
from app.graders import get_grader, BaseGrader
from app.pipeline.crag_pipeline import crag_pipeline
from app.data.loader import load_gold_benchmark
from app.vector_store import vector_store
from app.evaluation.metrics import aggregate_strategy_metrics, compute_token_f1
from app.evaluation.statistical_test import perform_paired_ttest, apply_holm_bonferroni

_LATEST_REPORT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "latest_evaluation.json")


class EvaluationEngine:
    """
    Orchestrates the controlled comparative evaluation of relevance-grading strategies
    across document domains with paired Student's t-test, paired bootstrap resampling,
    and Holm-Bonferroni multiple-comparison correction.
    """
    def __init__(self):
        self.benchmark_items = load_gold_benchmark()

    def reload_benchmark(self):
        self.benchmark_items = load_gold_benchmark()

    async def evaluate_strategy_on_domain(
        self,
        strategy: StrategyType,
        domain: str
    ) -> Tuple[StrategyMetrics, Dict[str, List[float]]]:
        """
        Runs evaluation for a specific strategy on a specific domain.
        1. Evaluates direct grading accuracy on all hand-labelled gold query-chunk pairs
           using REAL dense embedding cosine similarity (zero label leakage).
        2. Evaluates end-to-end Corrective RAG pipeline across all unique domain queries.
        """
        self.reload_benchmark()
        if not vector_store.chunks:
            from app.data.loader import load_initial_corpora
            load_initial_corpora()
        grader: BaseGrader = get_grader(strategy)
        domain_items = [item for item in self.benchmark_items if item.domain == domain]

        y_true: List[bool] = []
        y_pred: List[bool] = []
        grading_latencies: List[float] = []

        # 1. Direct Grading Accuracy on Gold Query-Chunk Pairs (NO label leakage)
        for item in domain_items:
            real_sim = vector_store.compute_pair_similarity(item.query, item.chunk_text)
            chunk = DocumentChunk(
                chunk_id=item.chunk_id,
                text=item.chunk_text,
                domain=item.domain,
                similarity_score=real_sim
            )
            res = await grader.grade(query=item.query, chunk=chunk)
            y_true.append(item.ground_truth_relevance)
            y_pred.append(res.is_relevant)
            grading_latencies.append(res.latency_ms)

        # 2. Downstream End-to-End Pipeline on Unique Queries
        unique_queries: Dict[str, GoldBenchmarkItem] = {}
        for item in domain_items:
            if item.query not in unique_queries and item.ground_truth_relevance:
                unique_queries[item.query] = item

        predictions: List[str] = []
        ground_truth_answers: List[str] = []
        retries_list: List[int] = []
        total_latencies: List[float] = []
        llm_calls_list: List[int] = []
        per_query_f1: List[float] = []

        for q_text, gold_item in unique_queries.items():
            pipeline_resp = await crag_pipeline.execute(
                query=q_text,
                domain=domain,
                strategy=strategy
            )
            ans = pipeline_resp.final_answer
            gt = gold_item.ground_truth_answer

            predictions.append(ans)
            ground_truth_answers.append(gt)
            retries_list.append(pipeline_resp.reformulation_retries)
            total_latencies.append(pipeline_resp.total_latency_ms)
            llm_calls_list.append(pipeline_resp.total_llm_calls)

            f1 = compute_token_f1(ans, gt)
            per_query_f1.append(f1)

        metrics = aggregate_strategy_metrics(
            strategy=strategy,
            domain=domain,
            y_true=y_true,
            y_pred=y_pred,
            predictions=predictions,
            ground_truth_answers=ground_truth_answers,
            retries_list=retries_list,
            grading_latencies=grading_latencies,
            total_latencies=total_latencies,
            llm_calls_list=llm_calls_list
        )

        raw_vectors = {
            "per_query_f1": per_query_f1,
            "total_latencies": total_latencies,
            "llm_calls": [float(x) for x in llm_calls_list]
        }

        return metrics, raw_vectors

    def _build_dynamic_summary(
        self,
        matrix: List[StrategyMetrics],
        significance_results: List[StatisticalComparison]
    ) -> str:
        if not matrix:
            return "No evaluation metrics computed."

        by_strat: Dict[str, List[StrategyMetrics]] = {}
        for m in matrix:
            by_strat.setdefault(m.strategy, []).append(m)

        parts = []
        for s_name, label in [
            ("llm", "Strategy A (LLM Judge - qwen2.5:3b)"),
            ("cross_encoder", "Strategy B (Cross-Encoder - ms-marco-MiniLM-L-6-v2)"),
            ("similarity_threshold", "Strategy C (Similarity Threshold - all-MiniLM-L6-v2)")
        ]:
            rows = by_strat.get(s_name, [])
            if rows:
                avg_g_f1 = sum(r.f1_score for r in rows) / len(rows)
                avg_ans_f1 = sum(r.token_f1 for r in rows) / len(rows)
                avg_lat = sum(r.avg_grading_latency_ms for r in rows) / len(rows)
                avg_llm = sum(r.avg_llm_calls_per_query for r in rows) / len(rows)
                parts.append(
                    f"{label}: grading F1={avg_g_f1*100:.1f}%, answer F1={avg_ans_f1*100:.1f}%, "
                    f"grading latency={avg_lat:.1f} ms/chunk, {avg_llm:.1f} LLM calls/query"
                )

        sig_count = sum(1 for s in significance_results if s.statistically_significant)
        return (
            f"Evaluated across {len(set(m.domain for m in matrix))} domain(s) "
            f"({sum(m.sample_count for m in matrix) // max(1, len(by_strat))} unique queries, "
            f"{len(self.benchmark_items)} gold query-chunk pairs). "
            + " | ".join(parts)
            + f". Across {len(significance_results)} pairwise hypothesis tests, "
            f"{sig_count} reached statistical significance (p < 0.05)."
        )

    async def run_full_study(
        self,
        domains: List[str] = ["hotpotqa", "legal"],
        strategies: List[StrategyType] = ["llm", "cross_encoder", "similarity_threshold"]
    ) -> EvaluationReport:
        matrix: List[StrategyMetrics] = []
        significance_results: List[StatisticalComparison] = []

        all_raw_data: Dict[Tuple[str, StrategyType], Dict[str, List[float]]] = {}

        for domain in domains:
            for strat in strategies:
                strat_metrics, raw_vecs = await self.evaluate_strategy_on_domain(strat, domain)
                matrix.append(strat_metrics)
                all_raw_data[(domain, strat)] = raw_vecs

        pairs_to_test = [
            ("llm", "cross_encoder"),
            ("llm", "similarity_threshold"),
            ("cross_encoder", "similarity_threshold")
        ]

        f1_tests: List[StatisticalComparison] = []
        lat_tests: List[StatisticalComparison] = []

        for domain in domains:
            for s_a, s_b in pairs_to_test:
                vecs_a = all_raw_data.get((domain, s_a))
                vecs_b = all_raw_data.get((domain, s_b))
                if vecs_a and vecs_b:
                    stat_f1 = perform_paired_ttest(
                        strategy_a=s_a,
                        strategy_b=s_b,
                        metric_name=f"Answer Token F1 ({domain})",
                        values_a=vecs_a["per_query_f1"],
                        values_b=vecs_b["per_query_f1"]
                    )
                    f1_tests.append(stat_f1)

                    stat_lat = perform_paired_ttest(
                        strategy_a=s_a,
                        strategy_b=s_b,
                        metric_name=f"End-to-End Latency ({domain})",
                        values_a=vecs_a["total_latencies"],
                        values_b=vecs_b["total_latencies"]
                    )
                    lat_tests.append(stat_lat)

        apply_holm_bonferroni(f1_tests)
        apply_holm_bonferroni(lat_tests)
        for f_t, l_t in zip(f1_tests, lat_tests):
            significance_results.append(f_t)
            significance_results.append(l_t)

        summary = self._build_dynamic_summary(matrix, significance_results)

        report = EvaluationReport(
            domains_evaluated=domains,
            strategies_evaluated=strategies,
            matrix=matrix,
            statistical_significance=significance_results,
            summary_findings=summary,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            total_gold_pairs=len(self.benchmark_items)
        )

        # Persist full study if both domains and all 3 strategies were evaluated
        if set(domains) >= {"hotpotqa", "legal"} and len(strategies) == 3:
            self.save_report(report)

        return report

    def save_report(self, report: EvaluationReport):
        try:
            os.makedirs(os.path.dirname(_LATEST_REPORT_PATH), exist_ok=True)
            with open(_LATEST_REPORT_PATH, "w", encoding="utf-8") as f:
                json.dump(report.model_dump(), f, indent=2)
        except Exception:
            pass

    def get_latest_report(self) -> Optional[EvaluationReport]:
        if os.path.exists(_LATEST_REPORT_PATH):
            try:
                with open(_LATEST_REPORT_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return EvaluationReport(**data)
            except Exception:
                return None
        return None


evaluation_engine = EvaluationEngine()

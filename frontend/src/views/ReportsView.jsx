import React, { useState, useEffect } from 'react';
import { FileText, Download, CheckCircle } from 'lucide-react';
import { fetchLatestEvaluation } from '../services/api';

const STRATEGY_NAMES = {
  llm: 'Strategy A: LLM-Prompt Judge (qwen2.5:3b)',
  cross_encoder: 'Strategy B: Cross-Encoder (ms-marco-MiniLM-L-6-v2)',
  similarity_threshold: 'Strategy C: Similarity Threshold (all-MiniLM-L6-v2)'
};

export default function ReportsView() {
  const [downloadSuccess, setDownloadSuccess] = useState('');
  const [report, setReport] = useState(null);

  useEffect(() => {
    fetchLatestEvaluation().then((data) => {
      if (data && data.matrix) {
        setReport(data);
      }
    });
  }, []);

  const sections = [
    { title: '1. Introduction', desc: 'Background on standard RAG blind retrieval trust and Corrective RAG grading loops.' },
    { title: '2. Motivation & Research Gap', desc: 'Why Self-RAG and CRAG leave open the cost-latency-accuracy comparison of grading strategies.' },
    { title: '3. Three Grading Strategies', desc: 'Shared BaseGrader interface for LLM Judge (qwen2.5:3b), Cross-Encoder (ms-marco-MiniLM-L-6-v2), and Cosine Similarity Threshold.' },
    { title: '4. Methodology & Gold Benchmark', desc: 'FAISS dense retrieval across HotpotQA & Legal domains with 120 hand-labelled query-chunk relevance pairs.' },
    { title: '5. Quantitative Results & Statistical Validation', desc: 'Full 3×2 Strategy × Domain matrix validated with paired Student’s t-test, Holm-Bonferroni correction, and 2,000-iteration bootstrap.' },
    { title: '6. Discussion & Conclusion', desc: 'Pareto frontier analysis and conditional domain deployment guidelines for practitioners.' }
  ];

  const handlePrintPdf = () => {
    window.print();
    setDownloadSuccess('Print / Save-as-PDF dialog opened!');
    setTimeout(() => setDownloadSuccess(''), 4000);
  };

  const handleDownloadMarkdown = () => {
    const matrixRows = (report?.matrix || [])
      .map((r) => {
        const acc = ((r.accuracy ?? r.grading_accuracy?.accuracy ?? 0) * 100).toFixed(1);
        const prec = ((r.precision ?? r.grading_accuracy?.precision ?? 0) * 100).toFixed(1);
        const rec = ((r.recall ?? r.grading_accuracy?.recall ?? 0) * 100).toFixed(1);
        const f1 = ((r.f1_score ?? r.grading_accuracy?.f1_score ?? 0) * 100).toFixed(1);
        const ansEm = ((r.exact_match ?? r.answer_quality?.exact_match ?? 0) * 100).toFixed(1);
        const ansF1 = ((r.token_f1 ?? r.answer_quality?.f1_score ?? 0) * 100).toFixed(1);
        const lat = (r.avg_grading_latency_ms ?? 0).toFixed(2);
        const retry = ((r.retry_rate ?? 0) * 100).toFixed(1);
        const calls = (r.avg_llm_calls_per_query ?? r.avg_llm_calls ?? 0).toFixed(2);
        return `| ${r.domain} | ${STRATEGY_NAMES[r.strategy] || r.strategy} | ${acc}% | ${prec}% | ${rec}% | ${f1}% | ${ansEm}% | ${ansF1}% | ${lat} ms | ${retry}% | ${calls} |`;
      })
      .join('\n');

    const statRows = (report?.statistical_significance || [])
      .map((st) => {
        const metric = st.metric_name || st.metric;
        const diff = (st.difference ?? st.mean_diff ?? 0).toFixed(4);
        const pVal = (st.p_value ?? 1).toFixed(4);
        const pHolm = (st.p_value_holm ?? st.p_value ?? 1).toFixed(4);
        const bootP = (st.bootstrap_p_value ?? 1).toFixed(4);
        const sig = (st.statistically_significant ?? st.significant) ? 'Yes (p < 0.05)' : 'No';
        return `| ${metric} | ${st.strategy_a} vs ${st.strategy_b} | ${diff} | ${st.t_statistic?.toFixed(3)} | ${pVal} | ${pHolm} | ${bootP} | ${sig} |`;
      })
      .join('\n');

    const mdContent = `# Comparative Evaluation of Relevance-Grading Strategies in Corrective Retrieval-Augmented Generation Systems
**Extended Major Project Report & Research Paper Draft — B.Tech CSE (AI/ML), Final Year**

## Abstract
Corrective Retrieval-Augmented Generation (CRAG) pipelines mitigate hallucination by grading retrieved document chunks for relevance before answer generation, triggering query reformulation when retrieved evidence is insufficient. While seminal works such as Self-RAG and CRAG each propose a specific grading mechanism, no controlled empirical study compares alternative grading paradigms across accuracy, latency, LLM call cost, and domain complexity. In this study, we implement three interchangeable relevance-grading strategies behind a unified interface—Strategy A (LLM-Prompt Judge via local Ollama \`qwen2.5:3b\`), Strategy B (Pretrained Cross-Encoder \`cross-encoder/ms-marco-MiniLM-L-6-v2\`), and Strategy C (Dense Cosine Similarity Threshold via \`all-MiniLM-L6-v2\` + FAISS)—and evaluate them across two distinct domains (HotpotQA multi-hop general knowledge and dense corporate Legal contracts) using a hand-labelled gold benchmark of 120 query-chunk pairs.

## Summary of Empirical Findings
${report?.summary_findings || 'See full quantitative matrix below.'}

## Quantitative Comparison Matrix (Strategy × Domain)
| Domain | Strategy | Grade Acc | Grade Prec | Grade Rec | Grade F1 | Answer EM | Answer F1 | Grade Latency | Retry Rate | LLM Calls/Q |
|---|---|---|---|---|---|---|---|---|---|---|
${matrixRows}

## Statistical Significance Validation (Paired t-Test, Holm-Bonferroni & 2,000-Iteration Bootstrap)
| Metric (Domain) | Strategy Pair | Mean Diff | t-Statistic | p-Value | p-Holm | Bootstrap p | Significant |
|---|---|---|---|---|---|---|---|
${statRows}
`;

    const blob = new Blob([mdContent], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'Comparative_CRAG_Grading_Research_Paper.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setDownloadSuccess('Downloaded Comparative_CRAG_Grading_Research_Paper.md!');
    setTimeout(() => setDownloadSuccess(''), 4000);
  };

  return (
    <div className="reports-view">
      {/* Title */}
      <div className="section-header">
        <h2 className="section-title">Research Report & Paper Draft</h2>
        <p className="section-subtitle">
          Export the B.Tech CSE (AI/ML) Extended Major Project Report and conference paper draft populated with live statistical evaluation results.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '55% 45%', gap: '22px' }}>
        {/* Left Column: Download Card */}
        <div>
          <div className="card-panel" style={{ padding: '28px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '18px' }}>
              <div
                style={{
                  width: '52px',
                  height: '52px',
                  borderRadius: '12px',
                  backgroundColor: '#eff6ff',
                  color: '#2563eb',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <FileText size={26} strokeWidth={2.2} />
              </div>
              <div>
                <h3 style={{ fontSize: '17px', fontWeight: 700, color: '#0f172a' }}>
                  Extended Major Project Report & Paper Draft
                </h3>
                <p style={{ fontSize: '13px', color: '#64748b' }}>
                  Includes 3×2 Strategy × Domain matrix, 120-pair gold benchmark evaluation, paired t-test & 2,000-iteration bootstrap tables.
                </p>
              </div>
            </div>

            {report?.summary_findings && (
              <div
                style={{
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: '10px',
                  padding: '12px 14px',
                  fontSize: '12.5px',
                  color: '#334155',
                  lineHeight: 1.55,
                  marginBottom: '18px'
                }}
              >
                <strong style={{ color: '#0f172a' }}>Live Executive Summary: </strong>
                {report.summary_findings}
              </div>
            )}

            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '22px' }}>
              <button
                id="btn-download-pdf-report"
                className="btn-primary"
                style={{ padding: '10px 20px', borderRadius: '9px', fontWeight: 600 }}
                onClick={handlePrintPdf}
              >
                <Download size={16} />
                <span>Print / Save PDF</span>
              </button>

              <button
                id="btn-download-md-report"
                className="btn-primary"
                style={{
                  padding: '10px 20px',
                  borderRadius: '9px',
                  fontWeight: 600,
                  background: '#0f172a'
                }}
                onClick={handleDownloadMarkdown}
              >
                <FileText size={16} />
                <span>Download Paper Draft (.md)</span>
              </button>
            </div>

            {downloadSuccess && (
              <div style={{ marginBottom: '14px', fontSize: '12.5px', color: '#059669', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <CheckCircle size={15} />
                <span>{downloadSuccess}</span>
              </div>
            )}

            <div style={{ fontSize: '12px', color: '#94a3b8', borderTop: '1px solid #f1f5f9', paddingTop: '14px' }}>
              Last evaluated: {report?.timestamp || 'Live Benchmark Ready'} • Gold Set: {report?.total_gold_pairs || 120} pairs
            </div>
          </div>
        </div>

        {/* Right Column: Report Sections List */}
        <div>
          <div className="card-panel">
            <h3 className="card-heading" style={{ marginBottom: '16px' }}>
              Report & Paper Structure
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {sections.map((sec, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '12px',
                    padding: '10px 12px',
                    background: '#f8fafc',
                    borderRadius: '8px',
                    border: '1px solid #e2e8f0'
                  }}
                >
                  <div
                    style={{
                      width: '22px',
                      height: '22px',
                      borderRadius: '50%',
                      background: '#dbeafe',
                      color: '#1d4ed8',
                      fontSize: '11px',
                      fontWeight: 700,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                      marginTop: '1px'
                    }}
                  >
                    {idx + 1}
                  </div>
                  <div>
                    <h5 style={{ fontSize: '13px', fontWeight: 600, color: '#0f172a' }}>
                      {sec.title}
                    </h5>
                    <p style={{ fontSize: '11.5px', color: '#64748b', marginTop: '2px' }}>
                      {sec.desc}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

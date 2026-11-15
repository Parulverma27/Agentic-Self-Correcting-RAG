import React, { useState } from 'react';
import { Send, CheckCircle2, Loader2, Sparkles, Box, Target } from 'lucide-react';
import { demoSampleQueries, demoPresetResponses } from '../data/mockData';
import { runCragLiveCompare } from '../services/api';

const defaultQuery = demoSampleQueries[0];

export default function DemoView() {
  const [query, setQuery] = useState(defaultQuery);
  const [domain, setDomain] = useState('HotpotQA');
  const [isLoading, setIsLoading] = useState(false);
  const [comparison, setComparison] = useState(
    demoPresetResponses[defaultQuery] || {
      llm: { relevant: '1/4', latency: '2.84s', retries: 0, llmCalls: 5, result: 'Select or enter a query to compare all 3 grading strategies.' },
      cross_encoder: { relevant: '1/4', latency: '0.06s', retries: 0, llmCalls: 1, result: 'Select or enter a query to compare all 3 grading strategies.' },
      similarity_threshold: { relevant: '2/4', latency: '0.01s', retries: 0, llmCalls: 1, result: 'Select or enter a query to compare all 3 grading strategies.' },
      finalAnswer: 'The Roman Colosseum (Flavian Amphitheatre) was commissioned by Emperor Vespasian in AD 72 and completed under Titus in AD 80.',
      evidenceBadge: 'Grounded in retrieved domain corpus'
    }
  );

  const handleExecuteQuery = async (queryText, domainOverride) => {
    const q = queryText || query;
    const dom = domainOverride || domain;
    if (!q.trim()) return;

    setIsLoading(true);
    try {
      const res = await runCragLiveCompare(q, dom);
      setComparison(res);
    } catch {
      // fallback
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="demo-view">
      {/* Title */}
      <div className="section-header">
        <h2 className="section-title">Interactive Demo</h2>
        <p className="section-subtitle">
          Ask a question on HotpotQA or Legal text and inspect how each grading strategy filters retrieved chunks in real time.
        </p>
      </div>

      {/* Query Search / Input Bar */}
      <div className="card-panel" style={{ marginBottom: '22px' }}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleExecuteQuery(query, domain);
          }}
          style={{ display: 'flex', gap: '10px' }}
        >
          <select
            id="demo-domain-select"
            className="form-control"
            style={{ width: '160px', fontWeight: 600 }}
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
          >
            <option value="HotpotQA">HotpotQA</option>
            <option value="Legal">Legal Contracts</option>
          </select>
          <input
            id="demo-query-input"
            type="text"
            className="form-control"
            style={{ flex: 1, padding: '12px 18px', fontSize: '14px' }}
            placeholder="Ask a question..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button
            id="btn-send-demo-query"
            type="submit"
            className="btn-primary"
            style={{ padding: '0 22px', borderRadius: '10px' }}
            disabled={isLoading}
          >
            {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
          </button>
        </form>

        {/* Quick query chips */}
        <div style={{ display: 'flex', gap: '8px', marginTop: '12px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '12px', color: '#64748b', alignSelf: 'center' }}>
            Try asking:
          </span>
          {demoSampleQueries.map((item, idx) => {
            const inferredDomain = item.includes('Section') || item.includes('Agreement') ? 'Legal' : 'HotpotQA';
            return (
              <button
                key={idx}
                type="button"
                style={{
                  background: '#f1f5f9',
                  border: '1px solid #e2e8f0',
                  borderRadius: '9999px',
                  padding: '4px 12px',
                  fontSize: '12px',
                  color: '#334155',
                  cursor: 'pointer'
                }}
                onClick={() => {
                  setQuery(item);
                  setDomain(inferredDomain);
                  handleExecuteQuery(item, inferredDomain);
                }}
              >
                [{inferredDomain}] {item.length > 68 ? `${item.slice(0, 68)}…` : item}
              </button>
            );
          })}
        </div>
      </div>

      {/* Strategy Comparison Heading */}
      <div style={{ marginBottom: '14px' }}>
        <h3 className="card-heading" style={{ fontSize: '15px' }}>
          Side-by-Side Grading Strategy Comparison ({domain})
        </h3>
      </div>

      {/* 3 Side-by-side Strategy Columns */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '18px', marginBottom: '22px' }}>
        {/* Strategy 1: LLM-prompt Judge */}
        <div
          className="card-panel"
          style={{
            borderTop: '3px solid #10b981',
            background: '#ffffff',
            opacity: isLoading ? 0.6 : 1
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <div style={{ width: '28px', height: '28px', borderRadius: '7px', background: '#ecfdf5', color: '#059669', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Sparkles size={16} />
            </div>
            <h4 style={{ fontSize: '13.5px', fontWeight: 700, color: '#0f172a' }}>
              Strategy A: LLM Judge (qwen2.5:3b)
            </h4>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '12.5px', color: '#475569', marginBottom: '14px' }}>
            <div>
              <span>Relevant Chunks Kept: </span>
              <strong className="mono-num" style={{ color: '#0f172a' }}>
                {comparison.llm.relevant}
              </strong>
            </div>
            <div>
              <span>End-to-End Latency: </span>
              <strong className="mono-num" style={{ color: '#2563eb' }}>
                {comparison.llm.latency}
              </strong>
            </div>
            {comparison.llm.llmCalls !== undefined && (
              <div>
                <span>LLM Calls / Retries: </span>
                <strong className="mono-num" style={{ color: '#059669' }}>
                  {comparison.llm.llmCalls} calls ({comparison.llm.retries ?? 0} retries)
                </strong>
              </div>
            )}
          </div>

          <div style={{ background: '#f8fafc', padding: '10px 12px', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12.5px', color: '#1e293b', minHeight: '52px' }}>
            {comparison.llm.result}
          </div>
        </div>

        {/* Strategy 2: Cross-encoder / NLI */}
        <div
          className="card-panel"
          style={{
            borderTop: '3px solid #8b5cf6',
            background: '#ffffff',
            opacity: isLoading ? 0.6 : 1
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <div style={{ width: '28px', height: '28px', borderRadius: '7px', background: '#f3e8ff', color: '#7c3aed', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Box size={16} />
            </div>
            <h4 style={{ fontSize: '13.5px', fontWeight: 700, color: '#0f172a' }}>
              Strategy B: Cross-Encoder (MiniLM)
            </h4>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '12.5px', color: '#475569', marginBottom: '14px' }}>
            <div>
              <span>Relevant Chunks Kept: </span>
              <strong className="mono-num" style={{ color: '#0f172a' }}>
                {comparison.cross_encoder.relevant}
              </strong>
            </div>
            <div>
              <span>End-to-End Latency: </span>
              <strong className="mono-num" style={{ color: '#2563eb' }}>
                {comparison.cross_encoder.latency}
              </strong>
            </div>
            {comparison.cross_encoder.llmCalls !== undefined && (
              <div>
                <span>LLM Calls / Retries: </span>
                <strong className="mono-num" style={{ color: '#7c3aed' }}>
                  {comparison.cross_encoder.llmCalls} call ({comparison.cross_encoder.retries ?? 0} retries)
                </strong>
              </div>
            )}
          </div>

          <div style={{ background: '#f8fafc', padding: '10px 12px', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12.5px', color: '#1e293b', minHeight: '52px' }}>
            {comparison.cross_encoder.result}
          </div>
        </div>

        {/* Strategy 3: Similarity Threshold */}
        <div
          className="card-panel"
          style={{
            borderTop: '3px solid #3b82f6',
            background: '#ffffff',
            opacity: isLoading ? 0.6 : 1
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <div style={{ width: '28px', height: '28px', borderRadius: '7px', background: '#eff6ff', color: '#2563eb', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Target size={16} />
            </div>
            <h4 style={{ fontSize: '13.5px', fontWeight: 700, color: '#0f172a' }}>
              Strategy C: Similarity Threshold
            </h4>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '12.5px', color: '#475569', marginBottom: '14px' }}>
            <div>
              <span>Relevant Chunks Kept: </span>
              <strong className="mono-num" style={{ color: '#0f172a' }}>
                {comparison.similarity_threshold.relevant}
              </strong>
            </div>
            <div>
              <span>End-to-End Latency: </span>
              <strong className="mono-num" style={{ color: '#2563eb' }}>
                {comparison.similarity_threshold.latency}
              </strong>
            </div>
            {comparison.similarity_threshold.llmCalls !== undefined && (
              <div>
                <span>LLM Calls / Retries: </span>
                <strong className="mono-num" style={{ color: '#2563eb' }}>
                  {comparison.similarity_threshold.llmCalls} call ({comparison.similarity_threshold.retries ?? 0} retries)
                </strong>
              </div>
            )}
          </div>

          <div style={{ background: '#f8fafc', padding: '10px 12px', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12.5px', color: '#1e293b', minHeight: '52px' }}>
            {comparison.similarity_threshold.result}
          </div>
        </div>
      </div>

      {/* Final Answer (Corrected RAG) Box */}
      <div
        className="card-panel"
        style={{
          border: '1px solid #86efac',
          background: '#f0fdf4',
          padding: '20px 24px'
        }}
        id="final-answer-crag-panel"
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
          <div style={{ color: '#15803d' }}>
            <CheckCircle2 size={20} />
          </div>
          <h4 style={{ fontSize: '15px', fontWeight: 700, color: '#166534' }}>
            Final Answer (Corrective RAG Output)
          </h4>
        </div>

        <p style={{ fontSize: '14px', fontWeight: 600, color: '#0f172a', marginBottom: '12px' }}>
          {comparison.finalAnswer}
        </p>

        <span
          className="badge-pill badge-relevant"
          style={{ fontSize: '11px', padding: '4px 10px', fontWeight: 500 }}
        >
          {comparison.evidenceBadge}
        </span>
      </div>
    </div>
  );
}

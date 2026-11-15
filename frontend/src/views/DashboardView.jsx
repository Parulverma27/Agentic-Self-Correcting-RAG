import React, { useState, useEffect } from 'react';
import {
  Layers,
  Cpu,
  HelpCircle,
  CheckCircle2,
  ArrowRight,
  Play,
  Database,
  BarChart2,
  FileDown
} from 'lucide-react';
import { initialStats, recentResultsData } from '../data/mockData';
import { fetchLatestEvaluation } from '../services/api';

const STRATEGY_NAMES = {
  llm: 'LLM-Prompt Judge',
  cross_encoder: 'Cross-Encoder / NLI',
  similarity_threshold: 'Similarity Threshold'
};

export default function DashboardView({ onNavigate }) {
  const [recentRows, setRecentRows] = useState(recentResultsData);
  const [stats, setStats] = useState(initialStats);

  useEffect(() => {
    fetchLatestEvaluation().then((report) => {
      if (report && report.matrix && report.matrix.length > 0) {
        const mapped = report.matrix.map((m) => ({
          strategy: STRATEGY_NAMES[m.strategy] || m.strategy,
          domain: m.domain === 'hotpotqa' ? 'HotpotQA' : m.domain === 'legal' ? 'Legal' : m.domain,
          em: (m.exact_match ?? m.answer_quality?.exact_match ?? 0) * 100,
          f1: (m.f1_score ?? m.grading_accuracy?.f1_score ?? 0) * 100,
          latency: `${(m.avg_grading_latency_ms ?? 0).toFixed(2)} ms`
        }));
        setRecentRows(mapped);
        setStats((prev) => ({
          ...prev,
          queries: report.total_gold_pairs || prev.queries,
          completedText: `Paired t-test & 2,000-iter bootstrap (${report.statistical_significance?.length || 12} tests)`
        }));
      }
    });
  }, []);
  return (
    <div className="dashboard-view">
      {/* Hero Banner */}
      <div className="hero-banner">
        <div className="hero-left">
          <h1 className="hero-title">
            Comparative Evaluation of Relevance-Grading Strategies in Corrective RAG Systems
          </h1>
          <p className="hero-desc">
            Analyzing and comparing LLM-based, cross-encoder and similarity-based grading approaches
            for better, faster and more accurate RAG.
          </p>
          <button
            id="hero-start-eval-btn"
            className="hero-btn"
            onClick={() => onNavigate('evaluation')}
          >
            <span>Start Evaluation</span>
            <ArrowRight size={16} />
          </button>
        </div>

        <div className="hero-right">
          <img
            src="/assets/rag-hero.jpg"
            alt="AI RAG Evaluation"
            className="hero-artwork"
          />
        </div>
      </div>

      {/* 4 Stat Cards */}
      <div className="stats-grid-4">
        {/* Card 1: Domains */}
        <div className="stat-card" id="stat-card-domains">
          <div className="stat-icon-wrapper" style={{ backgroundColor: '#f3e8ff', color: '#8b5cf6' }}>
            <Layers size={22} strokeWidth={2.2} />
          </div>
          <div className="stat-info">
            <span className="stat-label">Domains</span>
            <span className="stat-value">{stats.domains}</span>
            <span className="stat-subtext">{stats.domainsText}</span>
          </div>
        </div>

        {/* Card 2: Grading Strategies */}
        <div className="stat-card" id="stat-card-strategies">
          <div className="stat-icon-wrapper" style={{ backgroundColor: '#eff6ff', color: '#3b82f6' }}>
            <Cpu size={22} strokeWidth={2.2} />
          </div>
          <div className="stat-info">
            <span className="stat-label">Grading Strategies</span>
            <span className="stat-value">{stats.strategies}</span>
            <span className="stat-subtext">{stats.strategiesText}</span>
          </div>
        </div>

        {/* Card 3: Total Queries */}
        <div className="stat-card" id="stat-card-queries">
          <div className="stat-icon-wrapper" style={{ backgroundColor: '#ecfdf5', color: '#10b981' }}>
            <HelpCircle size={22} strokeWidth={2.2} />
          </div>
          <div className="stat-info">
            <span className="stat-label">Total Gold Pairs</span>
            <span className="stat-value">{stats.queries}</span>
            <span className="stat-subtext">{stats.queriesText}</span>
          </div>
        </div>

        {/* Card 4: Evaluation Completed */}
        <div className="stat-card" id="stat-card-completed">
          <div className="stat-icon-wrapper" style={{ backgroundColor: '#ecfeff', color: '#06b6d4' }}>
            <CheckCircle2 size={22} strokeWidth={2.2} />
          </div>
          <div className="stat-info">
            <span className="stat-label">Evaluation Completed</span>
            <span className="stat-value">{stats.completed}</span>
            <span className="stat-subtext">{stats.completedText}</span>
          </div>
        </div>
      </div>

      {/* Dashboard 2-Column Split */}
      <div className="dashboard-grid">
        {/* Recent Results Table */}
        <div className="card-panel" id="recent-results-panel">
          <div className="card-header-row">
            <h3 className="card-heading">Empirical Comparison Matrix (Live Results)</h3>
          </div>

          <table className="custom-table" id="recent-results-table">
            <thead>
              <tr>
                <th>Strategy</th>
                <th>Domain</th>
                <th>Ans EM ↑</th>
                <th>Grade F1 ↑</th>
                <th>Latency ↓</th>
              </tr>
            </thead>
            <tbody>
              {recentRows.map((row, index) => (
                <tr key={index}>
                  <td style={{ fontWeight: 500 }}>{row.strategy}</td>
                  <td>
                    <span className="badge-pill badge-domain">{row.domain}</span>
                  </td>
                  <td className="mono-num">{row.em.toFixed(1)}</td>
                  <td className="mono-num">{row.f1.toFixed(1)}</td>
                  <td className="mono-num" style={{ color: '#2563eb' }}>{row.latency}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div style={{ marginTop: '16px' }}>
            <button
              id="view-all-results-link"
              className="card-link"
              style={{ background: 'none', border: 'none' }}
              onClick={() => onNavigate('results')}
            >
              <span>View All Results</span>
              <ArrowRight size={14} />
            </button>
          </div>
        </div>

        {/* Quick Actions Card */}
        <div className="card-panel" id="quick-actions-panel">
          <div className="card-header-row">
            <h3 className="card-heading">Quick Actions</h3>
          </div>

          <div className="quick-actions-list">
            {/* Action 1 */}
            <div
              className="quick-action-item"
              id="action-run-eval"
              onClick={() => onNavigate('evaluation')}
            >
              <div className="quick-action-left">
                <div className="quick-action-icon" style={{ backgroundColor: '#eff6ff', color: '#2563eb' }}>
                  <Play size={18} fill="#2563eb" />
                </div>
                <div>
                  <div className="quick-action-title">Run Evaluation</div>
                  <div className="quick-action-desc">Start new experiment</div>
                </div>
              </div>
              <ArrowRight size={16} color="#94a3b8" />
            </div>

            {/* Action 2 */}
            <div
              className="quick-action-item"
              id="action-manage-datasets"
              onClick={() => onNavigate('documents')}
            >
              <div className="quick-action-left">
                <div className="quick-action-icon" style={{ backgroundColor: '#f3e8ff', color: '#7c3aed' }}>
                  <Database size={18} />
                </div>
                <div>
                  <div className="quick-action-title">Manage Datasets</div>
                  <div className="quick-action-desc">Add / View datasets</div>
                </div>
              </div>
              <ArrowRight size={16} color="#94a3b8" />
            </div>

            {/* Action 3 */}
            <div
              className="quick-action-item"
              id="action-view-results"
              onClick={() => onNavigate('results')}
            >
              <div className="quick-action-left">
                <div className="quick-action-icon" style={{ backgroundColor: '#ecfdf5', color: '#059669' }}>
                  <BarChart2 size={18} />
                </div>
                <div>
                  <div className="quick-action-title">View Results</div>
                  <div className="quick-action-desc">Check detailed metrics</div>
                </div>
              </div>
              <ArrowRight size={16} color="#94a3b8" />
            </div>

            {/* Action 4 */}
            <div
              className="quick-action-item"
              id="action-generate-report"
              onClick={() => onNavigate('reports')}
            >
              <div className="quick-action-left">
                <div className="quick-action-icon" style={{ backgroundColor: '#fff7ed', color: '#ea580c' }}>
                  <FileDown size={18} />
                </div>
                <div>
                  <div className="quick-action-title">Generate Report</div>
                  <div className="quick-action-desc">Download PDF</div>
                </div>
              </div>
              <ArrowRight size={16} color="#94a3b8" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

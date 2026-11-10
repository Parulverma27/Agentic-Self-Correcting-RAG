import React, { useState } from 'react';
import {
  Award,
  Zap,
  TrendingUp,
  DollarSign,
  ChevronDown,
  Info
} from 'lucide-react';
import {
  comparisonMetrics,
  emComparisonData,
  latencyComparisonData
} from '../data/mockData';

export default function ResultsView() {
  const [activeSubTab, setActiveSubTab] = useState('Overview');
  const [domainFilter, setDomainFilter] = useState('All Domains');
  const [hoveredBar, setHoveredBar] = useState(null);

  const tabs = [
    'Overview',
    'Grading Accuracy',
    'Answer Quality',
    'Latency',
    'Retry Rate',
    'Cost'
  ];

  return (
    <div className="results-view">
      {/* Title Header */}
      <div className="section-header">
        <h2 className="section-title">Results & Comparison</h2>
        <p className="section-subtitle">
          Compare the performance of all three strategies across domains.
        </p>
      </div>

      {/* Tabs and Domain Dropdown Filter */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '22px',
          flexWrap: 'wrap',
          gap: '12px'
        }}
      >
        <div style={{ display: 'flex', gap: '8px', overflowX: 'auto' }}>
          {tabs.map((tab) => (
            <button
              key={tab}
              className="btn-primary"
              style={{
                background: activeSubTab === tab ? '#2563eb' : '#ffffff',
                color: activeSubTab === tab ? '#ffffff' : '#64748b',
                border: activeSubTab === tab ? 'none' : '1fr solid #e2e8f0',
                padding: '7px 16px',
                borderRadius: '8px',
                fontSize: '12.5px',
                boxShadow: activeSubTab === tab ? '0 2px 8px rgba(37,99,235,0.25)' : 'none'
              }}
              onClick={() => setActiveSubTab(tab)}
            >
              {tab}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '12.5px', color: '#64748b', fontWeight: 500 }}>Domain:</span>
          <select
            className="form-control"
            style={{ width: '160px', padding: '7px 12px', fontSize: '12.5px' }}
            value={domainFilter}
            onChange={(e) => setDomainFilter(e.target.value)}
          >
            <option value="All Domains">All Domains</option>
            <option value="HotpotQA">HotpotQA</option>
            <option value="BioASQ">BioASQ</option>
          </select>
        </div>
      </div>

      {/* 4 Highlight Stat Cards */}
      <div className="stats-grid-4" style={{ marginBottom: '24px' }}>
        {/* Card 1: Best Accuracy */}
        <div className="stat-card" style={{ borderLeft: '4px solid #10b981' }}>
          <div className="stat-icon-wrapper" style={{ backgroundColor: '#ecfdf5', color: '#059669' }}>
            <Award size={22} />
          </div>
          <div className="stat-info">
            <span className="stat-label">Best Accuracy</span>
            <span className="stat-value">{comparisonMetrics.bestAccuracy.value}</span>
            <span className="stat-subtext" style={{ color: '#059669', fontWeight: 600 }}>
              {comparisonMetrics.bestAccuracy.strategy}
            </span>
          </div>
        </div>

        {/* Card 2: Lowest Latency */}
        <div className="stat-card" style={{ borderLeft: '4px solid #8b5cf6' }}>
          <div className="stat-icon-wrapper" style={{ backgroundColor: '#f3e8ff', color: '#7c3aed' }}>
            <Zap size={22} />
          </div>
          <div className="stat-info">
            <span className="stat-label">Lowest Latency</span>
            <span className="stat-value">{comparisonMetrics.lowestLatency.value}</span>
            <span className="stat-subtext" style={{ color: '#7c3aed', fontWeight: 600 }}>
              {comparisonMetrics.lowestLatency.strategy}
            </span>
          </div>
        </div>

        {/* Card 3: Highest F1 */}
        <div className="stat-card" style={{ borderLeft: '4px solid #3b82f6' }}>
          <div className="stat-icon-wrapper" style={{ backgroundColor: '#eff6ff', color: '#2563eb' }}>
            <TrendingUp size={22} />
          </div>
          <div className="stat-info">
            <span className="stat-label">Highest F1</span>
            <span className="stat-value">{comparisonMetrics.highestF1.value}</span>
            <span className="stat-subtext" style={{ color: '#2563eb', fontWeight: 600 }}>
              {comparisonMetrics.highestF1.strategy}
            </span>
          </div>
        </div>

        {/* Card 4: Lowest Cost */}
        <div className="stat-card" style={{ borderLeft: '4px solid #f59e0b' }}>
          <div className="stat-icon-wrapper" style={{ backgroundColor: '#fffbeb', color: '#d97706' }}>
            <DollarSign size={22} />
          </div>
          <div className="stat-info">
            <span className="stat-label">Lowest Cost</span>
            <span className="stat-value">{comparisonMetrics.lowestCost.value}</span>
            <span className="stat-subtext" style={{ color: '#d97706', fontWeight: 600 }}>
              {comparisonMetrics.lowestCost.strategy}
            </span>
          </div>
        </div>
      </div>

      {/* 2 Charts Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '22px' }}>
        {/* Exact Match (EM) Comparison Bar Chart */}
        <div className="card-panel" id="chart-panel-em">
          <div className="card-header-row" style={{ marginBottom: '12px' }}>
            <h3 className="card-heading">Exact Match (EM) Comparison</h3>
            <div style={{ display: 'flex', gap: '14px', fontSize: '11.5px', color: '#64748b' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '10px', height: '10px', backgroundColor: '#38bdf8', borderRadius: '2px' }} />
                <span>HotpotQA</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '10px', height: '10px', backgroundColor: '#34d399', borderRadius: '2px' }} />
                <span>BioASQ</span>
              </div>
            </div>
          </div>

          <div style={{ height: '260px', width: '100%', position: 'relative', marginTop: '14px' }}>
            <svg viewBox="0 0 500 240" style={{ width: '100%', height: '100%' }}>
              {/* Grid lines */}
              <line x1="40" y1="20" x2="480" y2="20" stroke="#f1f5f9" strokeWidth="1" />
              <line x1="40" y1="65" x2="480" y2="65" stroke="#f1f5f9" strokeWidth="1" />
              <line x1="40" y1="110" x2="480" y2="110" stroke="#f1f5f9" strokeWidth="1" />
              <line x1="40" y1="155" x2="480" y2="155" stroke="#f1f5f9" strokeWidth="1" />
              <line x1="40" y1="200" x2="480" y2="200" stroke="#e2e8f0" strokeWidth="1" />

              {/* Y Axis labels */}
              <text x="32" y="24" fill="#94a3b8" fontSize="10" textAnchor="end">100%</text>
              <text x="32" y="69" fill="#94a3b8" fontSize="10" textAnchor="end">75%</text>
              <text x="32" y="114" fill="#94a3b8" fontSize="10" textAnchor="end">50%</text>
              <text x="32" y="159" fill="#94a3b8" fontSize="10" textAnchor="end">25%</text>
              <text x="32" y="204" fill="#94a3b8" fontSize="10" textAnchor="end">0%</text>

              {/* Group 1: LLM (72.4%, 68.7%) */}
              {/* Bar 1 */}
              <rect
                x="85"
                y={200 - (72.4 * 1.8)}
                width="28"
                height={72.4 * 1.8}
                rx="4"
                fill="#38bdf8"
                onMouseEnter={() => setHoveredBar('LLM HotpotQA: 72.4%')}
                onMouseLeave={() => setHoveredBar(null)}
              />
              {/* Bar 2 */}
              <rect
                x="117"
                y={200 - (68.7 * 1.8)}
                width="28"
                height={68.7 * 1.8}
                rx="4"
                fill="#34d399"
                onMouseEnter={() => setHoveredBar('LLM BioASQ: 68.7%')}
                onMouseLeave={() => setHoveredBar(null)}
              />
              <text x="115" y="218" fill="#475569" fontSize="10" fontWeight="600" textAnchor="middle">
                LLM-prompt Judge
              </text>

              {/* Group 2: Cross-Encoder (70.1%, 66.8%) */}
              <rect
                x="225"
                y={200 - (70.1 * 1.8)}
                width="28"
                height={70.1 * 1.8}
                rx="4"
                fill="#38bdf8"
                onMouseEnter={() => setHoveredBar('Cross-Encoder HotpotQA: 70.1%')}
                onMouseLeave={() => setHoveredBar(null)}
              />
              <rect
                x="257"
                y={200 - (66.8 * 1.8)}
                width="28"
                height={66.8 * 1.8}
                rx="4"
                fill="#34d399"
                onMouseEnter={() => setHoveredBar('Cross-Encoder BioASQ: 66.8%')}
                onMouseLeave={() => setHoveredBar(null)}
              />
              <text x="255" y="218" fill="#475569" fontSize="10" fontWeight="600" textAnchor="middle">
                Cross-encoder / NLI
              </text>

              {/* Group 3: Similarity (65.3%, 60.2%) */}
              <rect
                x="365"
                y={200 - (65.3 * 1.8)}
                width="28"
                height={65.3 * 1.8}
                rx="4"
                fill="#38bdf8"
                onMouseEnter={() => setHoveredBar('Similarity HotpotQA: 65.3%')}
                onMouseLeave={() => setHoveredBar(null)}
              />
              <rect
                x="397"
                y={200 - (60.2 * 1.8)}
                width="28"
                height={60.2 * 1.8}
                rx="4"
                fill="#34d399"
                onMouseEnter={() => setHoveredBar('Similarity BioASQ: 60.2%')}
                onMouseLeave={() => setHoveredBar(null)}
              />
              <text x="395" y="218" fill="#475569" fontSize="10" fontWeight="600" textAnchor="middle">
                Similarity Threshold
              </text>
            </svg>

            {hoveredBar && (
              <div
                style={{
                  position: 'absolute',
                  top: '10px',
                  right: '10px',
                  background: '#0f172a',
                  color: '#ffffff',
                  padding: '4px 8px',
                  borderRadius: '6px',
                  fontSize: '11px',
                  fontFamily: 'var(--font-mono)'
                }}
              >
                {hoveredBar}
              </div>
            )}
          </div>
        </div>

        {/* Latency Comparison Curved Line Chart */}
        <div className="card-panel" id="chart-panel-latency">
          <div className="card-header-row" style={{ marginBottom: '12px' }}>
            <h3 className="card-heading">Latency Comparison</h3>
            <div style={{ display: 'flex', gap: '14px', fontSize: '11.5px', color: '#64748b' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '10px', height: '3px', backgroundColor: '#06b6d4' }} />
                <span>HotpotQA</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '10px', height: '3px', backgroundColor: '#a855f7' }} />
                <span>BioASQ</span>
              </div>
            </div>
          </div>

          <div style={{ height: '260px', width: '100%', position: 'relative', marginTop: '14px' }}>
            <svg viewBox="0 0 500 240" style={{ width: '100%', height: '100%' }}>
              {/* Grid lines */}
              <line x1="40" y1="20" x2="480" y2="20" stroke="#f1f5f9" strokeWidth="1" />
              <line x1="40" y1="65" x2="480" y2="65" stroke="#f1f5f9" strokeWidth="1" />
              <line x1="40" y1="110" x2="480" y2="110" stroke="#f1f5f9" strokeWidth="1" />
              <line x1="40" y1="155" x2="480" y2="155" stroke="#f1f5f9" strokeWidth="1" />
              <line x1="40" y1="200" x2="480" y2="200" stroke="#e2e8f0" strokeWidth="1" />

              {/* Y Axis labels */}
              <text x="32" y="24" fill="#94a3b8" fontSize="10" textAnchor="end">4s</text>
              <text x="32" y="69" fill="#94a3b8" fontSize="10" textAnchor="end">3s</text>
              <text x="32" y="114" fill="#94a3b8" fontSize="10" textAnchor="end">2s</text>
              <text x="32" y="159" fill="#94a3b8" fontSize="10" textAnchor="end">1s</text>
              <text x="32" y="204" fill="#94a3b8" fontSize="10" textAnchor="end">0s</text>

              {/* Line 1: HotpotQA (3.42s -> 0.84s -> 0.42s) */}
              {/* Y coordinates: 200 - (seconds * 45) -> 3.42*45=153.9 => y=46.1; 0.84*45=37.8 => y=162.2; 0.42*45=18.9 => y=181.1 */}
              <path
                d="M 115 46 Q 255 160 395 181"
                fill="none"
                stroke="#06b6d4"
                strokeWidth="3"
                strokeLinecap="round"
              />
              <circle cx="115" cy="46" r="4.5" fill="#06b6d4" />
              <circle cx="255" cy="162" r="4.5" fill="#06b6d4" />
              <circle cx="395" cy="181" r="4.5" fill="#06b6d4" />

              {/* Line 2: BioASQ (3.21s -> 0.76s -> 0.38s) */}
              {/* Y: 3.21*45=144.45 => y=55.5; 0.76*45=34.2 => y=165.8; 0.38*45=17.1 => y=182.9 */}
              <path
                d="M 115 56 Q 255 165 395 183"
                fill="none"
                stroke="#a855f7"
                strokeWidth="3"
                strokeLinecap="round"
              />
              <circle cx="115" cy="56" r="4.5" fill="#a855f7" />
              <circle cx="255" cy="166" r="4.5" fill="#a855f7" />
              <circle cx="395" cy="183" r="4.5" fill="#a855f7" />

              {/* X Axis labels */}
              <text x="115" y="218" fill="#475569" fontSize="10" fontWeight="600" textAnchor="middle">
                LLM-prompt Judge
              </text>
              <text x="255" y="218" fill="#475569" fontSize="10" fontWeight="600" textAnchor="middle">
                Cross-encoder / NLI
              </text>
              <text x="395" y="218" fill="#475569" fontSize="10" fontWeight="600" textAnchor="middle">
                Similarity Threshold
              </text>
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

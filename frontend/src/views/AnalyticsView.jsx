import React, { useState } from 'react';
import { Award, Zap, DollarSign, CheckCircle2 } from 'lucide-react';
import { keyFindings } from '../data/mockData';

export default function AnalyticsView() {
  const [activeTab, setActiveTab] = useState('Performance Summary');

  return (
    <div className="analytics-view">
      {/* Header */}
      <div className="section-header">
        <h2 className="section-title">Analytics & Insights</h2>
        <p className="section-subtitle">
          Key insights from the comparative evaluation.
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '22px' }}>
        {['Performance Summary', 'Domain Analysis', 'Strategy Insights'].map((tab) => (
          <button
            key={tab}
            className="btn-primary"
            style={{
              background: activeTab === tab ? '#2563eb' : '#ffffff',
              color: activeTab === tab ? '#ffffff' : '#64748b',
              border: activeTab === tab ? 'none' : '1px solid #e2e8f0',
              padding: '7px 16px',
              borderRadius: '8px',
              fontSize: '12.5px'
            }}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* 3 Top Highlight Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '18px', marginBottom: '24px' }}>
        {/* Card 1: Accuracy Leader */}
        <div className="card-panel" style={{ borderTop: '3px solid #10b981' }}>
          <div style={{ fontSize: '12px', fontWeight: 600, color: '#059669', marginBottom: '4px' }}>
            Accuracy Leader
          </div>
          <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '8px' }}>
            LLM-prompt Judge
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: '#0f172a', letterSpacing: '-0.03em', marginBottom: '4px' }}>
            86.7%
          </div>
          <div style={{ fontSize: '11.5px', color: '#94a3b8' }}>
            Best overall accuracy
          </div>
        </div>

        {/* Card 2: Fastest Strategy */}
        <div className="card-panel" style={{ borderTop: '3px solid #8b5cf6' }}>
          <div style={{ fontSize: '12px', fontWeight: 600, color: '#7c3aed', marginBottom: '4px' }}>
            Fastest Strategy
          </div>
          <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '8px' }}>
            Similarity Threshold
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: '#0f172a', letterSpacing: '-0.03em', marginBottom: '4px' }}>
            0.42s
          </div>
          <div style={{ fontSize: '11.5px', color: '#94a3b8' }}>
            Lowest latency
          </div>
        </div>

        {/* Card 3: Most Cost Efficient */}
        <div className="card-panel" style={{ borderTop: '3px solid #2563eb' }}>
          <div style={{ fontSize: '12px', fontWeight: 600, color: '#2563eb', marginBottom: '4px' }}>
            Most Cost Efficient
          </div>
          <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '8px' }}>
            Similarity Threshold
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: '#0f172a', letterSpacing: '-0.03em', marginBottom: '4px' }}>
            1 call/query
          </div>
          <div style={{ fontSize: '11.5px', color: '#94a3b8' }}>
            Minimal LLM usage
          </div>
        </div>
      </div>

      {/* Key Findings Card */}
      <div className="card-panel" id="key-findings-panel">
        <h3 className="card-heading" style={{ marginBottom: '18px' }}>
          Key Findings
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {keyFindings.map((finding, idx) => (
            <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
              <div style={{ color: '#2563eb', marginTop: '2px', flexShrink: 0 }}>
                <CheckCircle2 size={18} fill="#dbeafe" color="#2563eb" />
              </div>
              <p style={{ fontSize: '13.5px', color: '#334155', lineHeight: 1.5 }}>
                {finding}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

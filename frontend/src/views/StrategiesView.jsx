import React, { useState } from 'react';
import {
  Sparkles,
  Box,
  Target,
  Check,
  X,
  Sliders,
  Settings2,
  Info
} from 'lucide-react';
import { gradingStrategies } from '../data/mockData';

export default function StrategiesView() {
  const [strategies, setStrategies] = useState(gradingStrategies);
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [configThreshold, setConfigThreshold] = useState(0.7);

  const openConfig = (strat) => {
    setSelectedStrategy(strat);
    setConfigThreshold(strat.threshold);
  };

  const saveConfig = () => {
    setStrategies(
      strategies.map((s) =>
        s.id === selectedStrategy.id ? { ...s, threshold: configThreshold } : s
      )
    );
    setSelectedStrategy(null);
  };

  const getStrategyIcon = (id) => {
    if (id === 'llm') return Sparkles;
    if (id === 'cross_encoder') return Box;
    return Target;
  };

  return (
    <div className="strategies-view">
      {/* Header */}
      <div className="section-header">
        <h2 className="section-title">Grading Strategies</h2>
        <p className="section-subtitle">
          Configure and understand the three strategies used for relevance grading.
        </p>
      </div>

      {/* 3 Strategy Cards */}
      <div className="strategies-grid-3">
        {strategies.map((strat) => {
          const Icon = getStrategyIcon(strat.id);

          return (
            <div key={strat.id} className={`strategy-card ${strat.theme}`} id={`strategy-card-${strat.id}`}>
              <div>
                {/* Badge Icon */}
                <div
                  className="strategy-badge-icon"
                  style={{
                    backgroundColor: strat.badgeBg,
                    border: `1px solid ${strat.badgeBorder}`,
                    color: strat.badgeColor
                  }}
                >
                  <Icon size={22} strokeWidth={2.2} />
                </div>

                {/* Subtitle & Title */}
                <div className="strategy-subtitle" style={{ color: strat.badgeColor }}>
                  {strat.code}
                </div>
                <h3 className="strategy-name">{strat.name}</h3>

                {/* Features List */}
                <ul className="strategy-feature-list">
                  {strat.features.map((feature, idx) => (
                    <li key={idx} className="strategy-feature-item">
                      {feature.positive ? (
                        <div
                          style={{
                            color: '#10b981',
                            marginTop: '2px',
                            display: 'flex',
                            alignItems: 'center'
                          }}
                        >
                          <Check size={16} strokeWidth={2.5} />
                        </div>
                      ) : (
                        <div
                          style={{
                            color: '#ef4444',
                            marginTop: '2px',
                            display: 'flex',
                            alignItems: 'center'
                          }}
                        >
                          <X size={16} strokeWidth={2.5} />
                        </div>
                      )}
                      <span>{feature.text}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Threshold & Configure Button */}
              <div>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '12px',
                    color: '#64748b',
                    padding: '8px 12px',
                    background: '#f8fafc',
                    borderRadius: '8px',
                    marginBottom: '16px',
                    border: '1px solid #e2e8f0'
                  }}
                >
                  <span>Decision Threshold</span>
                  <strong className="mono-num" style={{ color: '#0f172a' }}>
                    {strat.threshold.toFixed(2)}
                  </strong>
                </div>

                <button
                  id={`btn-configure-${strat.id}`}
                  className="strategy-btn"
                  style={{
                    backgroundColor: strat.btnColor,
                    color: '#ffffff'
                  }}
                  onClick={() => openConfig(strat)}
                >
                  Configure
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Strategy Configuration Modal */}
      {selectedStrategy && (
        <div className="modal-overlay" onClick={() => setSelectedStrategy(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ padding: '28px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <div
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '10px',
                  backgroundColor: selectedStrategy.badgeBg,
                  color: selectedStrategy.badgeColor,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <Sliders size={20} />
              </div>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a' }}>
                  Configure {selectedStrategy.name}
                </h3>
                <span style={{ fontSize: '12px', color: '#64748b' }}>{selectedStrategy.code}</span>
              </div>
            </div>

            <div className="form-group" style={{ marginBottom: '16px' }}>
              <label className="form-label">Underlying Model / Technique</label>
              <input
                type="text"
                className="form-control"
                value={selectedStrategy.model}
                disabled
                style={{ backgroundColor: '#f8fafc' }}
              />
            </div>

            <div className="form-group" style={{ marginBottom: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <label className="form-label">Confidence Acceptance Threshold</label>
                <span className="mono-num" style={{ color: '#2563eb' }}>
                  {configThreshold.toFixed(2)}
                </span>
              </div>
              <input
                type="range"
                min="0.4"
                max="0.95"
                step="0.01"
                value={configThreshold}
                onChange={(e) => setConfigThreshold(parseFloat(e.target.value))}
                style={{ width: '100%', accentColor: '#2563eb' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#94a3b8', marginTop: '4px' }}>
                <span>0.40 (High Recall)</span>
                <span>0.95 (High Precision)</span>
              </div>
            </div>

            <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '10px', padding: '12px', marginBottom: '22px', display: 'flex', gap: '10px', fontSize: '12px', color: '#1e40af' }}>
              <Info size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
              <div>
                <strong>Performance Profile: </strong>
                {selectedStrategy.latencyDesc}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                className="btn-primary"
                style={{ background: '#f1f5f9', color: '#475569' }}
                onClick={() => setSelectedStrategy(null)}
              >
                Cancel
              </button>
              <button
                className="btn-primary"
                style={{ background: selectedStrategy.btnColor }}
                onClick={saveConfig}
              >
                Save Configuration
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

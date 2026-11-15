import React, { useState, useEffect } from 'react';
import { Plus, ArrowRight, Search } from 'lucide-react';
import { initialGoldLabels } from '../data/mockData';
import { fetchGoldLabels, saveGoldLabelApi } from '../services/api';

export default function GoldLabelsView() {
  const [labels, setLabels] = useState(initialGoldLabels);
  const [search, setSearch] = useState('');
  const [domainFilter, setDomainFilter] = useState('ALL');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [visibleCount, setVisibleCount] = useState(15);

  // New label modal form
  const [newQuery, setNewQuery] = useState('');
  const [newChunkId, setNewChunkId] = useState('');
  const [newRelevance, setNewRelevance] = useState(true);
  const [newDomain, setNewDomain] = useState('HotpotQA');
  const [newPassageText, setNewPassageText] = useState('');
  const [newExpectedAnswer, setNewExpectedAnswer] = useState('');

  useEffect(() => {
    fetchGoldLabels().then((data) => {
      if (data && data.length) setLabels(data);
    });
  }, []);

  const filteredLabels = labels.filter((item) => {
    const matchesSearch =
      item.query.toLowerCase().includes(search.toLowerCase()) ||
      item.chunk.toLowerCase().includes(search.toLowerCase());
    const matchesDomain =
      domainFilter === 'ALL' || item.domain.toLowerCase() === domainFilter.toLowerCase();
    return matchesSearch && matchesDomain;
  });

  const handleAddLabel = async (e) => {
    e.preventDefault();
    if (!newQuery.trim() || !newChunkId.trim()) return;

    const newItem = {
      id: `item-${Date.now()}`,
      query: newQuery,
      chunk: newChunkId,
      relevance: newRelevance,
      domain: newDomain,
      text: newPassageText || 'Custom annotated passage content.',
      expected_answer: newExpectedAnswer
    };

    await saveGoldLabelApi(newItem);
    setLabels([newItem, ...labels]);
    setNewQuery('');
    setNewChunkId('');
    setNewPassageText('');
    setNewExpectedAnswer('');
    setIsModalOpen(false);
  };

  return (
    <div className="gold-labels-view">
      {/* Header */}
      <div className="section-header">
        <h2 className="section-title">Gold Standard Labels ({labels.length} Pairs)</h2>
        <p className="section-subtitle">
          Hand-labelled query-chunk relevance judgements across HotpotQA and Legal domains used to measure grading precision, recall, and F1 directly.
        </p>
      </div>

      <div className="card-panel">
        {/* Filter & Search Bar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px', gap: '16px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flex: 1 }}>
            <div className="search-container" style={{ width: '280px' }}>
              <Search size={16} color="#94a3b8" />
              <input
                type="text"
                className="search-input"
                placeholder="Filter queries or chunk IDs..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            <select
              className="form-control"
              style={{ width: '160px', padding: '8px 12px', fontSize: '13px' }}
              value={domainFilter}
              onChange={(e) => setDomainFilter(e.target.value)}
            >
              <option value="ALL">All Domains ({labels.length})</option>
              <option value="HotpotQA">HotpotQA</option>
              <option value="Legal">Legal</option>
            </select>
          </div>

          <button
            id="btn-add-label-modal"
            className="btn-primary"
            style={{ padding: '8px 16px', fontSize: '13px' }}
            onClick={() => setIsModalOpen(true)}
          >
            <Plus size={16} />
            <span>Add Annotation</span>
          </button>
        </div>

        {/* Labels Table */}
        <table className="custom-table" id="gold-labels-table">
          <thead>
            <tr>
              <th style={{ width: '42%' }}>Query</th>
              <th style={{ width: '18%' }}>Chunk ID</th>
              <th style={{ width: '20%' }}>Gold Relevance</th>
              <th style={{ width: '20%' }}>Domain</th>
            </tr>
          </thead>
          <tbody>
            {filteredLabels.slice(0, visibleCount).map((row) => (
              <tr key={row.id}>
                <td style={{ fontWeight: 600, color: '#0f172a' }}>
                  <div>{row.query}</div>
                  {row.text && (
                    <div style={{ fontSize: '11.5px', color: '#64748b', fontWeight: 400, marginTop: '4px' }}>
                      {row.text.length > 140 ? `${row.text.slice(0, 140)}...` : row.text}
                    </div>
                  )}
                </td>
                <td className="mono-num" style={{ color: '#64748b' }}>{row.chunk}</td>
                <td>
                  {row.relevance ? (
                    <span className="badge-pill badge-relevant">
                      <span style={{ fontSize: '8px' }}>●</span> Relevant
                    </span>
                  ) : (
                    <span className="badge-pill badge-not-relevant">
                      <span style={{ fontSize: '8px' }}>●</span> Not Relevant
                    </span>
                  )}
                </td>
                <td>
                  <span className="badge-pill badge-domain" style={{ textTransform: 'uppercase' }}>{row.domain}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Footer with Legend and Load More / Manage Labels */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginTop: '20px',
            paddingTop: '16px',
            borderTop: '1px solid #e2e8f0',
            flexWrap: 'wrap',
            gap: '12px'
          }}
        >
          {/* Legend */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '12px', color: '#64748b' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#10b981' }} />
              <span>Relevant</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#ef4444' }} />
              <span>Not Relevant (Hard-Negative Distractor)</span>
            </div>
            <span style={{ color: '#94a3b8' }}>
              • Showing 1–{Math.min(visibleCount, filteredLabels.length)} of {filteredLabels.length} labels
            </span>
          </div>

          <div style={{ display: 'flex', gap: '14px', alignItems: 'center' }}>
            {visibleCount < filteredLabels.length && (
              <button
                className="card-link"
                style={{ background: 'none', border: 'none', fontSize: '13px', cursor: 'pointer' }}
                onClick={() => setVisibleCount((prev) => prev + 30)}
              >
                <span>Show More (+30)</span>
              </button>
            )}
            <button
              id="btn-manage-labels"
              className="card-link"
              style={{ background: 'none', border: 'none', fontSize: '13px' }}
              onClick={() => setIsModalOpen(true)}
            >
              <span>Add Gold Pair</span>
              <ArrowRight size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* Add / Manage Annotation Modal */}
      {isModalOpen && (
        <div className="modal-overlay" onClick={() => setIsModalOpen(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ padding: '26px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '6px', color: '#0f172a' }}>
              Add Benchmark Gold Label
            </h3>
            <p style={{ fontSize: '12.5px', color: '#64748b', marginBottom: '18px' }}>
              Register a curated human-annotated query-chunk relevance judgment (persisted to gold_benchmark.json).
            </p>

            <form onSubmit={handleAddLabel}>
              <div className="form-group">
                <label className="form-label">Query Text</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. What is the maximum aggregate cumulative liability cap under Section 8.1?"
                  value={newQuery}
                  onChange={(e) => setNewQuery(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '14px' }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Chunk ID</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="leg_chunk_016"
                    value={newChunkId}
                    onChange={(e) => setNewChunkId(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Domain</label>
                  <select
                    className="form-control"
                    value={newDomain}
                    onChange={(e) => setNewDomain(e.target.value)}
                  >
                    <option value="HotpotQA">HotpotQA</option>
                    <option value="Legal">Legal</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Ground Truth Relevance</label>
                <div style={{ display: 'flex', gap: '14px' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', cursor: 'pointer' }}>
                    <input
                      type="radio"
                      name="relevance"
                      checked={newRelevance === true}
                      onChange={() => setNewRelevance(true)}
                    />
                    <span className="badge-pill badge-relevant">Relevant</span>
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', cursor: 'pointer' }}>
                    <input
                      type="radio"
                      name="relevance"
                      checked={newRelevance === false}
                      onChange={() => setNewRelevance(false)}
                    />
                    <span className="badge-pill badge-not-relevant">Not Relevant</span>
                  </label>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Passage Content</label>
                <textarea
                  className="form-control"
                  rows={3}
                  placeholder="Document chunk text snippet..."
                  value={newPassageText}
                  onChange={(e) => setNewPassageText(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Expected Ground-Truth Answer (Optional)</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. Twelve (12) months of fees paid or $2,500,000"
                  value={newExpectedAnswer}
                  onChange={(e) => setNewExpectedAnswer(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }}>
                <button
                  type="button"
                  className="btn-primary"
                  style={{ background: '#f1f5f9', color: '#475569' }}
                  onClick={() => setIsModalOpen(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Save Annotation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

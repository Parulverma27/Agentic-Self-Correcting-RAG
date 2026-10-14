import React, { useState } from 'react';
import { FileText, Download, CheckCircle, ExternalLink, Printer } from 'lucide-react';

export default function ReportsView() {
  const [downloadSuccess, setDownloadSuccess] = useState(false);

  const sections = [
    { title: 'Introduction', desc: 'Background on RAG hallucination and corrective mechanisms.' },
    { title: 'Motivation & Research Gap', desc: 'Lack of systematic comparison across grading modalities.' },
    { title: 'Methodology', desc: 'Pipeline architecture, dataset curation, and scoring formulas.' },
    { title: 'Results & Analysis', desc: 'Quantitative F1, EM, latency trade-offs, and paired t-tests.' },
    { title: 'Discussion', desc: 'Cost-performance Pareto frontier for real-world deployments.' },
    { title: 'Conclusion & Future Work', desc: 'Hybrid cascade grading proposals and summary.' }
  ];

  const handleDownload = () => {
    window.print();
    setDownloadSuccess(true);
    setTimeout(() => setDownloadSuccess(false), 4000);
  };

  return (
    <div className="reports-view">
      {/* Title */}
      <div className="section-header">
        <h2 className="section-title">Research Report</h2>
        <p className="section-subtitle">
          Generate and download the complete research report in PDF format.
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
                  Project Report (PDF)
                </h3>
                <p style={{ fontSize: '13px', color: '#64748b' }}>
                  Detailed analysis, methodology, results and conclusions.
                </p>
              </div>
            </div>

            <div style={{ marginBottom: '22px' }}>
              <button
                id="btn-download-pdf-report"
                className="btn-primary"
                style={{ padding: '10px 20px', borderRadius: '9px', fontWeight: 600 }}
                onClick={handleDownload}
              >
                <Download size={16} />
                <span>Download PDF</span>
              </button>
              {downloadSuccess && (
                <div style={{ marginTop: '10px', fontSize: '12.5px', color: '#059669', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <CheckCircle size={15} />
                  <span>Report print preview loaded!</span>
                </div>
              )}
            </div>

            <div style={{ fontSize: '12px', color: '#94a3b8', borderTop: '1px solid #f1f5f9', paddingTop: '14px' }}>
              Last updated: 12 Aug 2025
            </div>
          </div>
        </div>

        {/* Right Column: Report Sections List */}
        <div>
          <div className="card-panel">
            <h3 className="card-heading" style={{ marginBottom: '16px' }}>
              Report Sections
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

import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  FileText,
  Eye,
  Trash2,
  Database,
  ArrowRight,
  CheckCircle,
  ExternalLink
} from 'lucide-react';
import { uploadedDocuments, datasetInfoList } from '../data/mockData';

export default function DocumentsView({ onNavigateToDataset }) {
  const [activeTab, setActiveTab] = useState('documents');
  const [documents, setDocuments] = useState(uploadedDocuments);
  const [selectedDataset, setSelectedDataset] = useState(null);
  const [previewDoc, setPreviewDoc] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileUpload = (e) => {
    const files = e.target.files;
    if (files && files[0]) {
      const file = files[0];
      const newDoc = {
        id: Date.now(),
        name: file.name,
        size: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
        domain: 'Custom',
        date: 'Today'
      };
      setDocuments([newDoc, ...documents]);
    }
  };

  const handleDelete = (id) => {
    setDocuments(documents.filter((doc) => doc.id !== id));
  };

  return (
    <div className="documents-view">
      {/* Title Header */}
      <div className="section-header">
        <h2 className="section-title">Documents & Datasets</h2>
      </div>

      {/* Tabs Row */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '22px' }}>
        <button
          id="tab-documents"
          className="btn-primary"
          style={{
            background: activeTab === 'documents' ? '#2563eb' : '#f1f5f9',
            color: activeTab === 'documents' ? '#ffffff' : '#64748b',
            padding: '8px 18px',
            borderRadius: '9999px',
            fontSize: '13px'
          }}
          onClick={() => setActiveTab('documents')}
        >
          Documents
        </button>
        <button
          id="tab-datasets"
          className="btn-primary"
          style={{
            background: activeTab === 'datasets' ? '#2563eb' : '#f1f5f9',
            color: activeTab === 'datasets' ? '#ffffff' : '#64748b',
            padding: '8px 18px',
            borderRadius: '9999px',
            fontSize: '13px'
          }}
          onClick={() => setActiveTab('datasets')}
        >
          Datasets
        </button>
      </div>

      {/* Main Grid: Left Upload & Table, Right Dataset Info */}
      <div style={{ display: 'grid', gridTemplateColumns: '66% 34%', gap: '22px' }}>
        {/* Left Column */}
        <div>
          {/* Upload Dropzone */}
          <div
            className="upload-dropzone"
            id="doc-upload-dropzone"
            onClick={() => fileInputRef.current && fileInputRef.current.click()}
          >
            <input
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              onChange={handleFileUpload}
              accept=".pdf,.txt,.docx"
            />
            <div className="upload-icon-circle">
              <UploadCloud size={26} strokeWidth={2.2} />
            </div>
            <h4 style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a', marginBottom: '4px' }}>
              Upload Documents
            </h4>
            <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '6px' }}>
              Drag & drop files here or click to browse
            </p>
            <span style={{ fontSize: '11.5px', color: '#94a3b8' }}>
              Supports PDF, TXT, DOCX (Max 50MB)
            </span>
          </div>

          {/* Uploaded Documents Table */}
          <div className="card-panel">
            <div className="card-header-row">
              <h3 className="card-heading">Uploaded Documents</h3>
            </div>

            <table className="custom-table" id="uploaded-docs-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Size</th>
                  <th>Domain</th>
                  <th>Uploaded</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.id}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <FileText size={16} color="#64748b" />
                        <span style={{ fontWeight: 600, color: '#1e293b' }}>{doc.name}</span>
                      </div>
                    </td>
                    <td className="mono-num" style={{ color: '#64748b' }}>{doc.size}</td>
                    <td>
                      <span className="badge-pill badge-domain">{doc.domain}</span>
                    </td>
                    <td style={{ color: '#64748b', fontSize: '12.5px' }}>{doc.date}</td>
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '6px' }}>
                        <button
                          title="Preview document"
                          style={{
                            background: '#f1f5f9',
                            border: 'none',
                            borderRadius: '6px',
                            padding: '6px',
                            cursor: 'pointer',
                            color: '#475569'
                          }}
                          onClick={() => setPreviewDoc(doc)}
                        >
                          <Eye size={14} />
                        </button>
                        <button
                          title="Delete"
                          style={{
                            background: '#fee2e2',
                            border: 'none',
                            borderRadius: '6px',
                            padding: '6px',
                            cursor: 'pointer',
                            color: '#b91c1c'
                          }}
                          onClick={() => handleDelete(doc.id)}
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div style={{ marginTop: '16px', fontSize: '12px', color: '#94a3b8' }}>
              Showing 1-{documents.length} of {documents.length} documents
            </div>
          </div>
        </div>

        {/* Right Column: Dataset Info Sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          <div className="card-panel">
            <h3 className="card-heading" style={{ marginBottom: '16px' }}>
              Dataset Info
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {datasetInfoList.map((dataset) => (
                <div
                  key={dataset.id}
                  style={{
                    border: '1px solid #e2e8f0',
                    borderRadius: '12px',
                    padding: '16px',
                    background: '#f8fafc'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                    <div
                      style={{
                        width: '32px',
                        height: '32px',
                        borderRadius: '8px',
                        backgroundColor: `${dataset.color}18`,
                        color: dataset.color,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                    >
                      <Database size={17} />
                    </div>
                    <div>
                      <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a' }}>
                        {dataset.name}
                      </h4>
                      <span style={{ fontSize: '11px', color: '#64748b' }}>{dataset.category}</span>
                    </div>
                  </div>

                  <p style={{ fontSize: '12px', color: '#475569', lineHeight: 1.5, marginBottom: '14px' }}>
                    {dataset.description}
                  </p>

                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#64748b', marginBottom: '12px', borderTop: '1px solid #e2e8f0', paddingTop: '10px' }}>
                    <div>
                      <span style={{ color: '#94a3b8' }}>Documents: </span>
                      <strong style={{ color: '#0f172a' }}>{dataset.docs}</strong>
                    </div>
                    <div>
                      <span style={{ color: '#94a3b8' }}>Questions: </span>
                      <strong style={{ color: '#0f172a' }}>{dataset.questions}</strong>
                    </div>
                    <div>
                      <span style={{ color: '#94a3b8' }}>Domain: </span>
                      <strong style={{ color: '#0f172a' }}>{dataset.domain}</strong>
                    </div>
                  </div>

                  <button
                    className="btn-primary"
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      fontSize: '12.5px',
                      background: '#ffffff',
                      color: dataset.color,
                      border: `1px solid ${dataset.color}50`
                    }}
                    onClick={() => {
                      if (onNavigateToDataset) onNavigateToDataset();
                    }}
                  >
                    View Details
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Preview Modal if doc clicked */}
      {previewDoc && (
        <div className="modal-overlay" onClick={() => setPreviewDoc(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '17px', fontWeight: 700, marginBottom: '8px' }}>
              Document Preview: {previewDoc.name}
            </h3>
            <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '16px' }}>
              Domain: {previewDoc.domain} | Size: {previewDoc.size}
            </p>
            <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '10px', fontSize: '13px', color: '#334155', maxHeight: '250px', overflowY: 'auto' }}>
              <p>Sample indexed corpus passage for {previewDoc.name}:</p>
              <br />
              <p>
                "Corrective Retrieval-Augmented Generation (CRAG) is designed to evaluate candidate
                document chunks prior to generation. The evaluator scores the semantic relevance
                of retrieved passages against the user inquiry. If passages pass the threshold,
                evidence is synthesized; otherwise, query reformulation and web fallback search are
                triggered."
              </p>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px' }}>
              <button className="btn-primary" onClick={() => setPreviewDoc(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

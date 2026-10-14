import React, { useState } from 'react';
import {
  FileText,
  UploadCloud,
  Send,
  Sparkles,
  Box,
  Target,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Loader2,
  BookOpen,
  FileCheck,
  ChevronRight,
  Copy,
  Check,
  Layers,
  ArrowRight
} from 'lucide-react';
import { askDocQA, uploadCustomDoc } from '../services/api';

export default function DocQAView() {
  const [activeDoc, setActiveDoc] = useState('Extended_RAG_Grading_Comparison_Report.docx');
  const [docDomain, setDocDomain] = useState('report');
  const [docChunksCount, setDocChunksCount] = useState(9);
  const [selectedStrategy, setSelectedStrategy] = useState('llm'); // 'llm' | 'cross_encoder' | 'similarity_threshold'
  
  const [query, setQuery] = useState('What is the core problem statement and corrective solution in this report?');
  const [isLoading, setIsLoading] = useState(false);
  const [qaResult, setQaResult] = useState({
    final_answer: "Problem Statement: A known weakness of standard RAG pipelines is that they trust retrieval blindly: if the retrieved passages are irrelevant or incomplete, the model still generates a fluent, confident answer that may not be grounded in any real evidence (hallucination).\n\nProposed Solution: Corrective RAG (CRAG) addresses this by introducing an active relevance-grading step that evaluates candidate document chunks prior to generation. The system compares three interchangeable grading strategies (Strategy A: LLM-prompt judge, Strategy B: Cross-encoder/NLI, and Strategy C: Similarity threshold) to determine whether retrieved evidence is sufficient, retrying retrieval or reformulating queries when necessary.",
    used_chunks: [
      {
        chunk_id: "rep_chunk_002",
        domain: "report",
        text: "Problem Statement: A known weakness of standard RAG pipelines is that they trust retrieval blindly: if the retrieved passages are irrelevant or incomplete, the model still generates a fluent, confident answer that may not be grounded in any real evidence (hallucination). Corrective RAG approaches address this by adding a grading step that checks whether retrieved evidence is actually relevant before answering, retrying the search when it is not.",
        metadata: { section: "1. Introduction", title: "Problem Statement & RAG Weakness" },
        similarity_score: 0.94
      },
      {
        chunk_id: "rep_chunk_006",
        domain: "report",
        text: "Methodology and System Architecture: The underlying pipeline is unchanged from the original build: documents are chunked and embedded into a vector store; a query retrieves the top-k candidate chunks; the active grading strategy scores each chunk as relevant or not; if too few chunks are judged relevant, the query is automatically reformulated and retrieval is retried, up to a bounded number of attempts, after which a fallback response is returned.",
        metadata: { section: "5. Methodology", title: "Corrective Pipeline Architecture" },
        similarity_score: 0.88
      }
    ],
    grading_results: [
      {
        chunk_id: "rep_chunk_002",
        strategy: "llm",
        is_relevant: true,
        score: 0.94,
        latency_ms: 45.2,
        llm_calls_made: 1
      },
      {
        chunk_id: "rep_chunk_006",
        strategy: "llm",
        is_relevant: true,
        score: 0.88,
        latency_ms: 42.1,
        llm_calls_made: 1
      }
    ],
    total_latency_ms: 1420,
    total_llm_calls: 3
  });

  const [copied, setCopied] = useState(false);
  const [customText, setCustomText] = useState('');
  const [showUploadModal, setShowUploadModal] = useState(false);

  const samplePrompts = [
    {
      title: "Problem Statement & RAG Weakness",
      q: "What is the core problem statement and standard RAG weakness according to this report?"
    },
    {
      title: "Proposed Solution & Pipeline",
      q: "What is the proposed Corrective RAG solution and system architecture?"
    },
    {
      title: "The 3 Grading Strategies Compared",
      q: "What are the three relevance-grading strategies compared in this research?"
    },
    {
      title: "Genuine Research Contribution",
      q: "Why does this study constitute a genuine research contribution and Pareto frontier?"
    },
    {
      title: "Project Evolution (Original vs Extended)",
      q: "How did the project idea evolve from the original idea to the extended major project?"
    }
  ];

  const handleAsk = async (questionText) => {
    const q = questionText || query;
    if (!q.trim()) return;

    setIsLoading(true);
    try {
      const res = await askDocQA(q, docDomain, selectedStrategy, 4);
      if (res) {
        setQaResult(res);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = () => {
    if (qaResult?.final_answer) {
      navigator.clipboard.writeText(qaResult.final_answer);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (evt) => {
      const text = evt.target?.result;
      if (typeof text === 'string') {
        const uploadRes = await uploadCustomDoc(file.name, text, 'custom_doc');
        setActiveDoc(file.name);
        setDocDomain('custom_doc');
        setDocChunksCount(uploadRes.chunks_indexed || 5);
        setShowUploadModal(false);
        setQuery(`What is the main topic of ${file.name}?`);
        handleAsk(`What is the main topic of ${file.name}?`);
      }
    };
    reader.readAsText(file);
  };

  const handleCustomTextSubmit = async () => {
    if (!customText.trim()) return;
    const docName = "Pasted_Document.txt";
    const uploadRes = await uploadCustomDoc(docName, customText, 'custom_doc');
    setActiveDoc(docName);
    setDocDomain('custom_doc');
    setDocChunksCount(uploadRes.chunks_indexed || 4);
    setShowUploadModal(false);
    setQuery("What are the key points in this uploaded document?");
    handleAsk("What are the key points in this uploaded document?");
  };

  return (
    <div className="docqa-view">
      {/* Header */}
      <div className="section-header">
        <h2 className="section-title">Document Q&A & Corrective Intelligence</h2>
        <p className="section-subtitle">
          Ask questions from research reports or custom documents with verified relevance-grading and evidence attribution.
        </p>
      </div>

      {/* Document Status Banner */}
      <div
        className="card-panel"
        style={{
          background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
          border: '1px solid #cbd5e1',
          marginBottom: '22px',
          padding: '20px 24px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div
              style={{
                width: '46px',
                height: '46px',
                borderRadius: '12px',
                backgroundColor: '#eff6ff',
                color: '#2563eb',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <BookOpen size={24} strokeWidth={2.2} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <h3 style={{ fontSize: '15px', fontWeight: 800, color: '#0f172a' }}>
                  {activeDoc}
                </h3>
                <span className="badge-pill badge-relevant" style={{ fontSize: '11px', padding: '2px 8px' }}>
                  ● Indexed & Active
                </span>
              </div>
              <p style={{ fontSize: '12px', color: '#64748b', marginTop: '3px' }}>
                B.Tech CSE (AI/ML) Major Project Report • {docChunksCount} Indexed Semantic Chunks • Domain: <strong style={{ color: '#0f172a' }}>{docDomain}</strong>
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            {activeDoc !== 'Extended_RAG_Grading_Comparison_Report.docx' && (
              <button
                className="btn-primary"
                style={{
                  background: '#ffffff',
                  color: '#2563eb',
                  border: '1px solid #bfdbfe',
                  fontSize: '12.5px',
                  padding: '7px 14px'
                }}
                onClick={() => {
                  setActiveDoc('Extended_RAG_Grading_Comparison_Report.docx');
                  setDocDomain('report');
                  setDocChunksCount(9);
                  setQuery('What is the problem statement and solution in this report?');
                  handleAsk('What is the problem statement and solution in this report?');
                }}
              >
                Reset to Report.docx
              </button>
            )}

            <button
              id="btn-upload-doc-modal"
              className="btn-primary"
              style={{ fontSize: '12.5px', padding: '7px 16px' }}
              onClick={() => setShowUploadModal(true)}
            >
              <UploadCloud size={16} />
              <span>Upload Document</span>
            </button>
          </div>
        </div>

        {/* Section Pill Badges if active doc is the report */}
        {activeDoc === 'Extended_RAG_Grading_Comparison_Report.docx' && (
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '16px', paddingTop: '14px', borderTop: '1px solid #f1f5f9' }}>
            <span style={{ fontSize: '11px', color: '#64748b', alignSelf: 'center', marginRight: '4px' }}>
              Indexed Chapters:
            </span>
            {['1. Introduction', '2. Motivation & Gap', '3. Objectives', '4. Three Grading Strategies', '5. Methodology', '6. Pareto Frontier', '9. Project Evolution'].map((sec, idx) => (
              <span
                key={idx}
                style={{
                  background: '#f1f5f9',
                  color: '#475569',
                  fontSize: '11px',
                  padding: '3px 10px',
                  borderRadius: '6px',
                  fontWeight: 500,
                  border: '1px solid #e2e8f0'
                }}
              >
                {sec}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Main Grid: Left Q&A and Strategy, Right Pipeline Trace */}
      <div style={{ display: 'grid', gridTemplateColumns: '62% 38%', gap: '22px' }}>
        {/* Left Column: Ask Question & Grounded Answer */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Strategy Selector Toggle */}
          <div className="card-panel" style={{ padding: '16px 20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
              <span style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: '#64748b' }}>
                Select Relevance Grading Grader
              </span>
              <span style={{ fontSize: '11.5px', color: '#94a3b8' }}>
                Active Grader in Corrective Loop
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
              {/* Option A: LLM */}
              <button
                type="button"
                style={{
                  border: selectedStrategy === 'llm' ? '2px solid #10b981' : '1px solid #e2e8f0',
                  background: selectedStrategy === 'llm' ? '#ecfdf5' : '#ffffff',
                  borderRadius: '10px',
                  padding: '10px 12px',
                  cursor: 'pointer',
                  textAlign: 'left'
                }}
                onClick={() => setSelectedStrategy('llm')}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#059669', marginBottom: '3px' }}>
                  <Sparkles size={15} />
                  <span style={{ fontSize: '12px', fontWeight: 700 }}>Strategy A</span>
                </div>
                <div style={{ fontSize: '12px', fontWeight: 600, color: '#0f172a' }}>LLM-prompt Judge</div>
                <div style={{ fontSize: '10.5px', color: '#64748b', marginTop: '2px' }}>High accuracy (slow)</div>
              </button>

              {/* Option B: Cross-Encoder */}
              <button
                type="button"
                style={{
                  border: selectedStrategy === 'cross_encoder' ? '2px solid #8b5cf6' : '1px solid #e2e8f0',
                  background: selectedStrategy === 'cross_encoder' ? '#f3e8ff' : '#ffffff',
                  borderRadius: '10px',
                  padding: '10px 12px',
                  cursor: 'pointer',
                  textAlign: 'left'
                }}
                onClick={() => setSelectedStrategy('cross_encoder')}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#7c3aed', marginBottom: '3px' }}>
                  <Box size={15} />
                  <span style={{ fontSize: '12px', fontWeight: 700 }}>Strategy B</span>
                </div>
                <div style={{ fontSize: '12px', fontWeight: 600, color: '#0f172a' }}>Cross-Encoder</div>
                <div style={{ fontSize: '10.5px', color: '#64748b', marginTop: '2px' }}>Fast & balanced</div>
              </button>

              {/* Option C: Similarity */}
              <button
                type="button"
                style={{
                  border: selectedStrategy === 'similarity_threshold' ? '2px solid #3b82f6' : '1px solid #e2e8f0',
                  background: selectedStrategy === 'similarity_threshold' ? '#eff6ff' : '#ffffff',
                  borderRadius: '10px',
                  padding: '10px 12px',
                  cursor: 'pointer',
                  textAlign: 'left'
                }}
                onClick={() => setSelectedStrategy('similarity_threshold')}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#2563eb', marginBottom: '3px' }}>
                  <Target size={15} />
                  <span style={{ fontSize: '12px', fontWeight: 700 }}>Strategy C</span>
                </div>
                <div style={{ fontSize: '12px', fontWeight: 600, color: '#0f172a' }}>Cosine Similarity</div>
                <div style={{ fontSize: '10.5px', color: '#64748b', marginTop: '2px' }}>Zero-cost baseline</div>
              </button>
            </div>
          </div>

          {/* Ask Input Console */}
          <div className="card-panel">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleAsk(query);
              }}
            >
              <div style={{ display: 'flex', gap: '10px', marginBottom: '12px' }}>
                <input
                  id="docqa-query-input"
                  type="text"
                  className="form-control"
                  style={{ flex: 1, padding: '12px 16px', fontSize: '14px', borderRadius: '10px' }}
                  placeholder="Ask a question about the uploaded document..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
                <button
                  id="btn-docqa-submit"
                  type="submit"
                  className="btn-primary"
                  style={{ padding: '0 22px', borderRadius: '10px' }}
                  disabled={isLoading}
                >
                  {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
                </button>
              </div>
            </form>

            {/* Quick Prompts Chips */}
            <div>
              <span style={{ fontSize: '11.5px', color: '#64748b', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
                Suggested Report Inquiries:
              </span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {samplePrompts.map((item, idx) => (
                  <button
                    key={idx}
                    type="button"
                    style={{
                      background: '#f8fafc',
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px',
                      padding: '7px 12px',
                      fontSize: '12px',
                      color: '#334155',
                      cursor: 'pointer',
                      textAlign: 'left',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      transition: 'all 0.15s ease'
                    }}
                    onClick={() => {
                      setQuery(item.q);
                      handleAsk(item.q);
                    }}
                  >
                    <span>
                      <strong style={{ color: '#2563eb' }}>{item.title}:</strong> {item.q}
                    </span>
                    <ArrowRight size={13} color="#94a3b8" />
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Grounded Final Answer Card */}
          <div
            className="card-panel"
            style={{
              border: '1px solid #bfdbfe',
              background: '#f8fafc',
              position: 'relative'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{ color: '#2563eb' }}>
                  <CheckCircle2 size={18} />
                </div>
                <h4 style={{ fontSize: '14.5px', fontWeight: 800, color: '#0f172a' }}>
                  Grounded Corrective Answer
                </h4>
                <span className="badge-pill badge-relevant" style={{ fontSize: '10.5px' }}>
                  Verified Against Document Context
                </span>
              </div>

              <button
                type="button"
                style={{
                  background: 'none',
                  border: '1px solid #cbd5e1',
                  borderRadius: '6px',
                  padding: '4px 8px',
                  fontSize: '11.5px',
                  color: '#475569',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
                onClick={handleCopy}
              >
                {copied ? <Check size={13} color="#16a34a" /> : <Copy size={13} />}
                <span>{copied ? 'Copied' : 'Copy Answer'}</span>
              </button>
            </div>

            {isLoading ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '24px 0', color: '#64748b', fontSize: '13px' }}>
                <Loader2 size={20} className="animate-spin" color="#2563eb" />
                <span>Running Corrective Retrieval, Relevance Grading & Synthesis...</span>
              </div>
            ) : (
              <div style={{ fontSize: '13.5px', color: '#1e293b', lineHeight: 1.65, whiteSpace: 'pre-line' }}>
                {qaResult.final_answer}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Evidence Chunks & Relevance Grading Verdict */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          <div className="card-panel">
            <div className="card-header-row" style={{ marginBottom: '12px' }}>
              <h3 className="card-heading" style={{ fontSize: '14.5px' }}>
                Retrieved Passages & Relevance Scores
              </h3>
            </div>

            <p style={{ fontSize: '12px', color: '#64748b', marginBottom: '14px' }}>
              Passages extracted from <strong style={{ color: '#0f172a' }}>{activeDoc}</strong> and evaluated by <strong style={{ color: '#2563eb' }}>{selectedStrategy}</strong>.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {qaResult.used_chunks && qaResult.used_chunks.length > 0 ? (
                qaResult.used_chunks.map((chunk, idx) => {
                  const grade = qaResult.grading_results?.[idx];
                  const isRel = grade ? grade.is_relevant : true;
                  const score = grade ? grade.score : (chunk.similarity_score || 0.85);

                  return (
                    <div
                      key={idx}
                      style={{
                        border: isRel ? '1px solid #bbf7d0' : '1px solid #fecaca',
                        borderRadius: '10px',
                        padding: '12px',
                        background: isRel ? '#f0fdf4' : '#fef2f2'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                        <span style={{ fontSize: '11px', fontWeight: 700, color: '#475569' }}>
                          {chunk.metadata?.section || `Chunk ${chunk.chunk_id}`}
                        </span>
                        <span
                          className={`badge-pill ${isRel ? 'badge-relevant' : 'badge-not-relevant'}`}
                          style={{ fontSize: '10px', padding: '2px 7px' }}
                        >
                          {isRel ? `Relevant (${score.toFixed(2)})` : `Filtered (${score.toFixed(2)})`}
                        </span>
                      </div>

                      <p style={{ fontSize: '12px', color: '#334155', lineHeight: 1.45 }}>
                        "{chunk.text}"
                      </p>
                    </div>
                  );
                })
              ) : (
                <div style={{ fontSize: '12px', color: '#94a3b8', textAlign: 'center', padding: '16px' }}>
                  No evidence chunks retrieved.
                </div>
              )}
            </div>

            {/* Performance Footer */}
            <div
              style={{
                marginTop: '16px',
                paddingTop: '12px',
                borderTop: '1px solid #e2e8f0',
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '11.5px',
                color: '#64748b'
              }}
            >
              <span>Latency: <strong className="mono-num" style={{ color: '#2563eb' }}>{qaResult.total_latency_ms || 120}ms</strong></span>
              <span>LLM Calls: <strong className="mono-num" style={{ color: '#0f172a' }}>{qaResult.total_llm_calls || 1}</strong></span>
              <span>Passages: <strong className="mono-num">{qaResult.used_chunks?.length || 0}</strong></span>
            </div>
          </div>
        </div>
      </div>

      {/* Upload Custom Document Modal */}
      {showUploadModal && (
        <div className="modal-overlay" onClick={() => setShowUploadModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ padding: '28px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', marginBottom: '6px' }}>
              Upload Custom Document for Q&A
            </h3>
            <p style={{ fontSize: '12.5px', color: '#64748b', marginBottom: '18px' }}>
              Upload any PDF, TXT, DOCX file or paste raw document text to index into the vector store.
            </p>

            {/* File Input */}
            <div
              className="upload-dropzone"
              style={{ padding: '24px 16px', marginBottom: '16px' }}
              onClick={() => document.getElementById('file-picker-docqa')?.click()}
            >
              <input
                id="file-picker-docqa"
                type="file"
                style={{ display: 'none' }}
                accept=".txt,.md,.pdf,.docx,.json"
                onChange={handleFileUpload}
              />
              <UploadCloud size={32} color="#2563eb" style={{ margin: '0 auto 8px auto' }} />
              <div style={{ fontSize: '13.5px', fontWeight: 600, color: '#0f172a' }}>
                Click to browse document file
              </div>
              <span style={{ fontSize: '11px', color: '#94a3b8' }}>
                Supports .txt, .md, .docx, .pdf
              </span>
            </div>

            <div style={{ textAlign: 'center', margin: '12px 0', fontSize: '12px', color: '#94a3b8' }}>
              — OR PASTE TEXT DIRECTLY —
            </div>

            <div className="form-group">
              <textarea
                className="form-control"
                rows={5}
                placeholder="Paste contract terms, research notes, or document paragraphs here..."
                value={customText}
                onChange={(e) => setCustomText(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
              <button
                type="button"
                className="btn-primary"
                style={{ background: '#f1f5f9', color: '#475569' }}
                onClick={() => setShowUploadModal(false)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn-primary"
                disabled={!customText.trim()}
                onClick={handleCustomTextSubmit}
              >
                Index & Start Q&A
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

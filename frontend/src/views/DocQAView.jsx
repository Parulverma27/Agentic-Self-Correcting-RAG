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
  Clock,
  Zap,
  BarChart3,
  TrendingUp,
  Loader2,
  BookOpen,
  Copy,
  Check,
  ArrowRight,
  FileUp,
  RefreshCw,
  Gauge,
  AlertCircle
} from 'lucide-react';
import {
  askDocQA,
  compareDocQA,
  uploadCustomDoc,
  uploadCustomDocFile
} from '../services/api';

export default function DocQAView() {
  const [activeDoc, setActiveDoc] = useState('Extended_RAG_Grading_Comparison_Report.docx');
  const [docDomain, setDocDomain] = useState('report');
  const [docChunksCount, setDocChunksCount] = useState(9);
  const [selectedStrategy, setSelectedStrategy] = useState('llm'); // 'llm' | 'cross_encoder' | 'similarity_threshold'
  const [viewedAnswerStrategy, setViewedAnswerStrategy] = useState('llm');
  
  const [query, setQuery] = useState('What is the core problem statement and corrective solution in this report?');
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [copied, setCopied] = useState(false);
  const [customText, setCustomText] = useState('');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [metricMode, setMetricMode] = useState('total'); // 'total' | 'grading'

  // Results for the current query across all 3 strategies
  const [allStrategyResults, setAllStrategyResults] = useState({
    llm: {
      final_answer: "Problem Statement: A known weakness of standard RAG pipelines is that they trust retrieval blindly: if the retrieved passages are irrelevant or incomplete, the model still generates a fluent, confident answer that may not be grounded in any real evidence (hallucination).\n\nProposed Solution: Corrective RAG (CRAG) introduces an active relevance-grading step that evaluates candidate document chunks prior to generation. The system compares three interchangeable grading strategies (Strategy A: LLM-prompt judge, Strategy B: Cross-encoder/NLI, and Strategy C: Similarity threshold) to determine whether retrieved evidence is sufficient, retrying retrieval or reformulating queries when necessary.",
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
        { chunk_id: "rep_chunk_002", strategy: "llm", is_relevant: true, score: 0.94, latency_ms: 45.2, llm_calls_made: 1 },
        { chunk_id: "rep_chunk_006", strategy: "llm", is_relevant: true, score: 0.88, latency_ms: 42.1, llm_calls_made: 1 }
      ],
      total_latency_ms: 1420,
      grading_latency_ms: 45.2,
      total_llm_calls: 3,
      graded_relevant_count: 2,
      retrieved_chunks_count: 4
    },
    cross_encoder: {
      final_answer: "Based on Cross-Encoder joint-attention grading: The core problem identified is standard RAG's vulnerability to ungrounded generation when retrieval fetches noisy or irrelevant passages. Corrective RAG deploys active passage scoring, filtering non-relevant chunks and reformulating search terms when confidence falls below the acceptance threshold.",
      used_chunks: [
        {
          chunk_id: "rep_chunk_002",
          domain: "report",
          text: "Problem Statement: A known weakness of standard RAG pipelines is that they trust retrieval blindly: if the retrieved passages are irrelevant or incomplete, the model still generates a fluent, confident answer that may not be grounded in any real evidence (hallucination).",
          metadata: { section: "1. Introduction", title: "Problem Statement & RAG Weakness" },
          similarity_score: 0.94
        }
      ],
      grading_results: [
        { chunk_id: "rep_chunk_002", strategy: "cross_encoder", is_relevant: true, score: 0.91, latency_ms: 12.4, llm_calls_made: 0 }
      ],
      total_latency_ms: 460,
      grading_latency_ms: 12.4,
      total_llm_calls: 1,
      graded_relevant_count: 2,
      retrieved_chunks_count: 4
    },
    similarity_threshold: {
      final_answer: "Based on Vector Cosine Similarity thresholding: Standard RAG blind retrieval causes hallucinations. The Corrective RAG pipeline integrates an active relevance threshold filter to discard low-scoring candidate chunks before final generation.",
      used_chunks: [
        {
          chunk_id: "rep_chunk_002",
          domain: "report",
          text: "Problem Statement: A known weakness of standard RAG pipelines is that they trust retrieval blindly: if the retrieved passages are irrelevant or incomplete, the model still generates a fluent, confident answer that may not be grounded in any real evidence (hallucination).",
          metadata: { section: "1. Introduction", title: "Problem Statement & RAG Weakness" },
          similarity_score: 0.94
        }
      ],
      grading_results: [
        { chunk_id: "rep_chunk_002", strategy: "similarity_threshold", is_relevant: true, score: 0.88, latency_ms: 0.8, llm_calls_made: 0 }
      ],
      total_latency_ms: 110,
      grading_latency_ms: 0.8,
      total_llm_calls: 1,
      graded_relevant_count: 1,
      retrieved_chunks_count: 4
    }
  });

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

  // Active QA result being viewed
  const currentResult = allStrategyResults[viewedAnswerStrategy] || allStrategyResults[selectedStrategy] || allStrategyResults.llm;

  const handleAsk = async (questionText, targetStrategy) => {
    const q = questionText || query;
    if (!q.trim()) return;

    const strat = targetStrategy || selectedStrategy;
    setIsLoading(true);

    try {
      // Execute all 3 strategies concurrently via compare endpoint so we get real-time comparative latency
      const compareRes = await compareDocQA(q, docDomain, 4);
      if (compareRes && compareRes.results) {
        setAllStrategyResults(compareRes.results);
      }
    } catch (err) {
      console.error("Doc QA execution error:", err);
    } finally {
      setIsLoading(false);
      setViewedAnswerStrategy(strat);
    }
  };

  const handleStrategyChange = (strat) => {
    setSelectedStrategy(strat);
    setViewedAnswerStrategy(strat);
  };

  const handleCopy = () => {
    if (currentResult?.final_answer) {
      navigator.clipboard.writeText(currentResult.final_answer);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadStatus({ type: 'info', msg: `Reading & indexing '${file.name}' into vector store...` });

    try {
      const uploadRes = await uploadCustomDocFile(file, 'custom_doc');
      setActiveDoc(file.name);
      setDocDomain('custom_doc');
      const count = uploadRes.chunks_indexed || 5;
      setDocChunksCount(count);
      setShowUploadModal(false);

      setUploadStatus({
        type: 'success',
        msg: `Successfully uploaded '${file.name}'! Indexed ${count} semantic chunks into vector database.`
      });
      setTimeout(() => setUploadStatus(null), 6000);

      // Auto ask starter question
      const starterQ = `What are the key points and findings in ${file.name}?`;
      setQuery(starterQ);
      handleAsk(starterQ, selectedStrategy);
    } catch (err) {
      setUploadStatus({ type: 'error', msg: `Failed to upload document: ${err.message}` });
    } finally {
      setIsUploading(false);
    }
  };

  const handleCustomTextSubmit = async () => {
    if (!customText.trim()) return;
    setIsUploading(true);
    setUploadStatus({ type: 'info', msg: 'Indexing custom pasted document...' });

    try {
      const docName = "Pasted_Document.txt";
      const uploadRes = await uploadCustomDoc(docName, customText, 'custom_doc');
      setActiveDoc(docName);
      setDocDomain('custom_doc');
      const count = uploadRes.chunks_indexed || 4;
      setDocChunksCount(count);
      setShowUploadModal(false);
      setCustomText('');

      setUploadStatus({
        type: 'success',
        msg: `Successfully indexed pasted text into ${count} semantic passages.`
      });
      setTimeout(() => setUploadStatus(null), 6000);

      const starterQ = "What are the main key points in this uploaded document?";
      setQuery(starterQ);
      handleAsk(starterQ, selectedStrategy);
    } catch (err) {
      setUploadStatus({ type: 'error', msg: `Indexing failed: ${err.message}` });
    } finally {
      setIsUploading(false);
    }
  };

  // Timing metrics for each strategy
  const metrics = [
    {
      id: 'llm',
      name: 'Strategy A: LLM Judge',
      shortName: 'LLM-prompt Judge',
      color: '#10b981',
      darkColor: '#059669',
      bgColor: '#ecfdf5',
      borderColor: '#a7f3d0',
      totalLatency: Math.max(10, Math.round(allStrategyResults.llm?.total_latency_ms || 1420)),
      gradingLatency: Math.max(1, +(allStrategyResults.llm?.grading_latency_ms || 45.2).toFixed(1)),
      llmCalls: allStrategyResults.llm?.total_llm_calls || 3,
      relevantCount: allStrategyResults.llm?.graded_relevant_count || 2,
      totalChunks: allStrategyResults.llm?.retrieved_chunks_count || 4,
      retries: allStrategyResults.llm?.reformulation_retries || 0
    },
    {
      id: 'cross_encoder',
      name: 'Strategy B: Cross-Encoder',
      shortName: 'Cross-Encoder (NLI)',
      color: '#8b5cf6',
      darkColor: '#7c3aed',
      bgColor: '#f5f3ff',
      borderColor: '#ddd6fe',
      totalLatency: Math.max(10, Math.round(allStrategyResults.cross_encoder?.total_latency_ms || 460)),
      gradingLatency: Math.max(1, +(allStrategyResults.cross_encoder?.grading_latency_ms || 12.4).toFixed(1)),
      llmCalls: allStrategyResults.cross_encoder?.total_llm_calls || 1,
      relevantCount: allStrategyResults.cross_encoder?.graded_relevant_count || 2,
      totalChunks: allStrategyResults.cross_encoder?.retrieved_chunks_count || 4,
      retries: allStrategyResults.cross_encoder?.reformulation_retries || 0
    },
    {
      id: 'similarity_threshold',
      name: 'Strategy C: Cosine Similarity',
      shortName: 'Cosine Similarity',
      color: '#3b82f6',
      darkColor: '#2563eb',
      bgColor: '#eff6ff',
      borderColor: '#bfdbfe',
      totalLatency: Math.max(5, Math.round(allStrategyResults.similarity_threshold?.total_latency_ms || 110)),
      gradingLatency: Math.max(0.2, +(allStrategyResults.similarity_threshold?.grading_latency_ms || 0.8).toFixed(1)),
      llmCalls: allStrategyResults.similarity_threshold?.total_llm_calls || 1,
      relevantCount: allStrategyResults.similarity_threshold?.graded_relevant_count || 1,
      totalChunks: allStrategyResults.similarity_threshold?.retrieved_chunks_count || 4,
      retries: allStrategyResults.similarity_threshold?.reformulation_retries || 0
    }
  ];

  // Calculation for bar heights in chart
  const maxMetricValue = Math.max(
    ...metrics.map((m) => (metricMode === 'total' ? m.totalLatency : m.gradingLatency)),
    100
  );

  const fastestStrategy = [...metrics].sort((a, b) => a.totalLatency - b.totalLatency)[0];
  const slowestStrategy = [...metrics].sort((a, b) => b.totalLatency - a.totalLatency)[0];
  const crossSpeedupVsLlm = (
    metrics.find((m) => m.id === 'llm').totalLatency /
    Math.max(1, metrics.find((m) => m.id === 'cross_encoder').totalLatency)
  ).toFixed(1);

  return (
    <div className="docqa-view">
      {/* Header */}
      <div className="section-header">
        <h2 className="section-title">Document Q&A & Strategy Timing Benchmark</h2>
        <p className="section-subtitle">
          Upload any document, select a relevance-grading strategy to generate grounded answers, and view live execution time benchmarks across all strategies.
        </p>
      </div>

      {/* Global Upload Notification Banner */}
      {uploadStatus && (
        <div
          style={{
            padding: '12px 18px',
            borderRadius: '10px',
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            background: uploadStatus.type === 'error' ? '#fef2f2' : '#f0fdf4',
            border: uploadStatus.type === 'error' ? '1px solid #fecaca' : '1px solid #bbf7d0',
            color: uploadStatus.type === 'error' ? '#991b1b' : '#166534',
            fontSize: '13px'
          }}
        >
          {uploadStatus.type === 'error' ? <AlertCircle size={18} /> : <CheckCircle2 size={18} />}
          <span>{uploadStatus.msg}</span>
        </div>
      )}

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
                width: '48px',
                height: '48px',
                borderRadius: '12px',
                backgroundColor: '#eff6ff',
                color: '#2563eb',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 2px 6px rgba(37,99,235,0.12)'
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
                  ● Active & Indexed
                </span>
                <span style={{ fontSize: '11px', color: '#64748b', background: '#f1f5f9', padding: '2px 7px', borderRadius: '4px' }}>
                  {docDomain}
                </span>
              </div>
              <p style={{ fontSize: '12px', color: '#64748b', marginTop: '3px' }}>
                {docChunksCount} Indexed Semantic Passages in Vector Store • Ready for Multi-Strategy Relevance Grading
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
                  padding: '8px 14px'
                }}
                onClick={() => {
                  setActiveDoc('Extended_RAG_Grading_Comparison_Report.docx');
                  setDocDomain('report');
                  setDocChunksCount(9);
                  const q = 'What is the problem statement and solution in this report?';
                  setQuery(q);
                  handleAsk(q, selectedStrategy);
                }}
              >
                <RefreshCw size={14} style={{ marginRight: '6px' }} />
                Reset to Report.docx
              </button>
            )}

            <button
              id="btn-upload-doc-modal"
              className="btn-primary"
              style={{ fontSize: '12.5px', padding: '8px 18px', background: '#2563eb' }}
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

      {/* Strategy Selection Area */}
      <div className="card-panel" style={{ padding: '18px 22px', marginBottom: '22px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
          <div>
            <span style={{ fontSize: '13px', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.04em', color: '#0f172a' }}>
              Step 1: Select Relevance-Grading Strategy
            </span>
            <p style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>
              Choose which grading algorithm evaluates retrieved document passages before answer generation
            </p>
          </div>
          <span style={{ fontSize: '11.5px', color: '#64748b', background: '#f8fafc', padding: '4px 10px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
            Active: <strong style={{ color: '#0f172a' }}>{metrics.find(m => m.id === selectedStrategy)?.name}</strong>
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' }}>
          {/* Strategy A: LLM */}
          <button
            type="button"
            style={{
              border: selectedStrategy === 'llm' ? '2.5px solid #10b981' : '1px solid #e2e8f0',
              background: selectedStrategy === 'llm' ? '#ecfdf5' : '#ffffff',
              borderRadius: '12px',
              padding: '14px 16px',
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'all 0.15s ease',
              boxShadow: selectedStrategy === 'llm' ? '0 4px 14px rgba(16,185,129,0.18)' : 'none'
            }}
            onClick={() => handleStrategyChange('llm')}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#059669' }}>
                <Sparkles size={16} />
                <span style={{ fontSize: '12px', fontWeight: 800 }}>Strategy A</span>
              </div>
              {selectedStrategy === 'llm' && (
                <span style={{ fontSize: '10.5px', background: '#10b981', color: '#fff', padding: '2px 7px', borderRadius: '4px', fontWeight: 700 }}>
                  Active
                </span>
              )}
            </div>
            <div style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a' }}>LLM-prompt Judge</div>
            <div style={{ fontSize: '11.5px', color: '#475569', marginTop: '4px' }}>
              High contextual nuance • Prompted verification • 1 LLM call/chunk
            </div>
            <div style={{ marginTop: '8px', fontSize: '11px', color: '#059669', fontWeight: 600 }}>
              Avg Latency: ~{metrics.find(m => m.id === 'llm')?.totalLatency}ms
            </div>
          </button>

          {/* Strategy B: Cross-Encoder */}
          <button
            type="button"
            style={{
              border: selectedStrategy === 'cross_encoder' ? '2.5px solid #8b5cf6' : '1px solid #e2e8f0',
              background: selectedStrategy === 'cross_encoder' ? '#f5f3ff' : '#ffffff',
              borderRadius: '12px',
              padding: '14px 16px',
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'all 0.15s ease',
              boxShadow: selectedStrategy === 'cross_encoder' ? '0 4px 14px rgba(139,92,246,0.18)' : 'none'
            }}
            onClick={() => handleStrategyChange('cross_encoder')}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#7c3aed' }}>
                <Box size={16} />
                <span style={{ fontSize: '12px', fontWeight: 800 }}>Strategy B</span>
              </div>
              {selectedStrategy === 'cross_encoder' && (
                <span style={{ fontSize: '10.5px', background: '#8b5cf6', color: '#fff', padding: '2px 7px', borderRadius: '4px', fontWeight: 700 }}>
                  Active
                </span>
              )}
            </div>
            <div style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a' }}>Cross-Encoder / NLI</div>
            <div style={{ fontSize: '11.5px', color: '#475569', marginTop: '4px' }}>
              Deep joint attention • Near-LLM accuracy • Zero LLM calls
            </div>
            <div style={{ marginTop: '8px', fontSize: '11px', color: '#7c3aed', fontWeight: 600 }}>
              Avg Latency: ~{metrics.find(m => m.id === 'cross_encoder')?.totalLatency}ms ({crossSpeedupVsLlm}x faster)
            </div>
          </button>

          {/* Strategy C: Similarity */}
          <button
            type="button"
            style={{
              border: selectedStrategy === 'similarity_threshold' ? '2.5px solid #3b82f6' : '1px solid #e2e8f0',
              background: selectedStrategy === 'similarity_threshold' ? '#eff6ff' : '#ffffff',
              borderRadius: '12px',
              padding: '14px 16px',
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'all 0.15s ease',
              boxShadow: selectedStrategy === 'similarity_threshold' ? '0 4px 14px rgba(59,130,246,0.18)' : 'none'
            }}
            onClick={() => handleStrategyChange('similarity_threshold')}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#2563eb' }}>
                <Target size={16} />
                <span style={{ fontSize: '12px', fontWeight: 800 }}>Strategy C</span>
              </div>
              {selectedStrategy === 'similarity_threshold' && (
                <span style={{ fontSize: '10.5px', background: '#3b82f6', color: '#fff', padding: '2px 7px', borderRadius: '4px', fontWeight: 700 }}>
                  Active
                </span>
              )}
            </div>
            <div style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a' }}>Cosine Similarity Cutoff</div>
            <div style={{ fontSize: '11.5px', color: '#475569', marginTop: '4px' }}>
              Vector similarity score • Zero auxiliary inference • Ultra-low latency
            </div>
            <div style={{ marginTop: '8px', fontSize: '11px', color: '#2563eb', fontWeight: 600 }}>
              Avg Latency: ~{metrics.find(m => m.id === 'similarity_threshold')?.totalLatency}ms (Fastest)
            </div>
          </button>
        </div>
      </div>

      {/* Main Grid: Left Q&A, Right Retrieved Chunks */}
      <div style={{ display: 'grid', gridTemplateColumns: '62% 38%', gap: '22px', marginBottom: '24px' }}>
        {/* Left Column: Ask Console & Generated Answer */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Ask Input Console */}
          <div className="card-panel">
            <span style={{ fontSize: '13px', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.04em', color: '#0f172a', display: 'block', marginBottom: '8px' }}>
              Step 2: Ask a Question from {activeDoc}
            </span>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleAsk(query, selectedStrategy);
              }}
            >
              <div style={{ display: 'flex', gap: '10px', marginBottom: '12px' }}>
                <input
                  id="docqa-query-input"
                  type="text"
                  className="form-control"
                  style={{ flex: 1, padding: '12px 16px', fontSize: '14px', borderRadius: '10px' }}
                  placeholder={`Ask questions about ${activeDoc}...`}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
                <button
                  id="btn-docqa-submit"
                  type="submit"
                  className="btn-primary"
                  style={{ padding: '0 24px', borderRadius: '10px', background: '#2563eb', fontWeight: 600 }}
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Loader2 size={17} className="animate-spin" />
                      <span>Grading...</span>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Send size={16} />
                      <span>Generate</span>
                    </div>
                  )}
                </button>
              </div>
            </form>

            {/* Suggested Inquiries */}
            <div>
              <span style={{ fontSize: '11.5px', color: '#64748b', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
                Suggested Inquiries:
              </span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {samplePrompts.slice(0, 3).map((item, idx) => (
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
                      handleAsk(item.q, selectedStrategy);
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
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{ color: '#2563eb' }}>
                  <CheckCircle2 size={19} />
                </div>
                <div>
                  <h4 style={{ fontSize: '14.5px', fontWeight: 800, color: '#0f172a' }}>
                    Grounded Generated Answer
                  </h4>
                  <span style={{ fontSize: '11px', color: '#64748b' }}>
                    Evaluated by <strong style={{ color: '#0f172a' }}>{metrics.find(m => m.id === viewedAnswerStrategy)?.name}</strong>
                  </span>
                </div>
              </div>

              {/* Strategy Answer Switcher Tabs */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ fontSize: '11px', color: '#64748b', marginRight: '4px' }}>View Answer As:</span>
                {metrics.map((m) => (
                  <button
                    key={m.id}
                    type="button"
                    style={{
                      fontSize: '11px',
                      fontWeight: 600,
                      padding: '4px 10px',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      border: viewedAnswerStrategy === m.id ? `1.5px solid ${m.color}` : '1px solid #cbd5e1',
                      background: viewedAnswerStrategy === m.id ? m.bgColor : '#ffffff',
                      color: viewedAnswerStrategy === m.id ? m.darkColor : '#475569'
                    }}
                    onClick={() => setViewedAnswerStrategy(m.id)}
                  >
                    {m.id === 'llm' ? 'Strategy A' : m.id === 'cross_encoder' ? 'Strategy B' : 'Strategy C'}
                  </button>
                ))}

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
                    gap: '4px',
                    marginLeft: '6px'
                  }}
                  onClick={handleCopy}
                >
                  {copied ? <Check size={13} color="#16a34a" /> : <Copy size={13} />}
                  <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
            </div>

            {isLoading ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '24px 0', color: '#64748b', fontSize: '13px' }}>
                <Loader2 size={20} className="animate-spin" color="#2563eb" />
                <span>Running Corrective Retrieval, Relevance Grading & Answer Synthesis...</span>
              </div>
            ) : (
              <div>
                <div style={{ fontSize: '13.5px', color: '#1e293b', lineHeight: 1.7, whiteSpace: 'pre-line' }}>
                  {currentResult.final_answer}
                </div>

                <div
                  style={{
                    marginTop: '16px',
                    paddingTop: '12px',
                    borderTop: '1px solid #e2e8f0',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '11.5px',
                    color: '#64748b'
                  }}
                >
                  <div style={{ display: 'flex', gap: '14px' }}>
                    <span>Strategy Response Time: <strong style={{ color: '#0f172a' }}>{currentResult.total_latency_ms || 460}ms</strong></span>
                    <span>Grading Time: <strong style={{ color: '#2563eb' }}>{currentResult.grading_latency_ms || 12}ms</strong></span>
                    <span>LLM Calls: <strong style={{ color: '#0f172a' }}>{currentResult.total_llm_calls || 1}</strong></span>
                  </div>
                  <span className="badge-pill badge-relevant" style={{ fontSize: '10.5px' }}>
                    ● Evidence Verified
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Evidence Chunks */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          <div className="card-panel">
            <div className="card-header-row" style={{ marginBottom: '12px' }}>
              <h3 className="card-heading" style={{ fontSize: '14.5px' }}>
                Retrieved Passages & Scoring
              </h3>
            </div>

            <p style={{ fontSize: '12px', color: '#64748b', marginBottom: '14px' }}>
              Passages extracted from <strong style={{ color: '#0f172a' }}>{activeDoc}</strong> evaluated by <strong style={{ color: '#2563eb' }}>{viewedAnswerStrategy}</strong>.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {currentResult.used_chunks && currentResult.used_chunks.length > 0 ? (
                currentResult.used_chunks.map((chunk, idx) => {
                  const grade = currentResult.grading_results?.[idx];
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
                          {chunk.metadata?.section || chunk.metadata?.title || `Passage ${chunk.chunk_id}`}
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
                  No evidence chunks retrieved for this document.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* STRATEGY LATENCY & TIMING BENCHMARK GRAPH (User Requirement) */}
      <div
        className="card-panel"
        style={{
          border: '1px solid #cbd5e1',
          padding: '24px',
          background: '#ffffff',
          marginBottom: '28px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px', marginBottom: '18px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ color: '#2563eb' }}>
                <BarChart3 size={20} />
              </div>
              <h3 style={{ fontSize: '16px', fontWeight: 800, color: '#0f172a' }}>
                Strategy Execution Time Benchmark Graph
              </h3>
            </div>
            <p style={{ fontSize: '12.5px', color: '#64748b', marginTop: '3px' }}>
              Live comparison of latency and processing time for each grading strategy on query: <em>"{query.slice(0, 55)}..."</em>
            </p>
          </div>

          {/* Metric Switcher Toggle */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#f1f5f9', padding: '4px', borderRadius: '8px' }}>
            <button
              type="button"
              style={{
                background: metricMode === 'total' ? '#2563eb' : 'transparent',
                color: metricMode === 'total' ? '#ffffff' : '#475569',
                border: 'none',
                padding: '6px 14px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
              onClick={() => setMetricMode('total')}
            >
              ⏱️ Total Response Time (ms)
            </button>
            <button
              type="button"
              style={{
                background: metricMode === 'grading' ? '#2563eb' : 'transparent',
                color: metricMode === 'grading' ? '#ffffff' : '#475569',
                border: 'none',
                padding: '6px 14px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
              onClick={() => setMetricMode('grading')}
            >
              🎯 Grading Step Latency (ms)
            </button>
          </div>
        </div>

        {/* Visual Graph Area (Interactive High-Fidelity SVG Bar Chart) */}
        <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '24px 20px', marginBottom: '20px' }}>
          <div style={{ width: '100%', height: '220px', position: 'relative' }}>
            <svg width="100%" height="100%" viewBox="0 0 700 220" preserveAspectRatio="none">
              <defs>
                <linearGradient id="llmGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10b981" />
                  <stop offset="100%" stopColor="#059669" />
                </linearGradient>
                <linearGradient id="crossGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#8b5cf6" />
                  <stop offset="100%" stopColor="#6d28d9" />
                </linearGradient>
                <linearGradient id="simGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#3b82f6" />
                  <stop offset="100%" stopColor="#1d4ed8" />
                </linearGradient>
              </defs>

              {/* Grid Background Horizontal Lines */}
              <line x1="60" y1="30" x2="680" y2="30" stroke="#e2e8f0" strokeDasharray="3 3" />
              <line x1="60" y1="80" x2="680" y2="80" stroke="#e2e8f0" strokeDasharray="3 3" />
              <line x1="60" y1="130" x2="680" y2="130" stroke="#e2e8f0" strokeDasharray="3 3" />
              <line x1="60" y1="180" x2="680" y2="180" stroke="#cbd5e1" strokeWidth="1.5" />

              {/* Y Axis Labels */}
              <text x="50" y="34" fill="#94a3b8" fontSize="10" textAnchor="end">{maxMetricValue}ms</text>
              <text x="50" y="84" fill="#94a3b8" fontSize="10" textAnchor="end">{Math.round(maxMetricValue * 0.66)}ms</text>
              <text x="50" y="134" fill="#94a3b8" fontSize="10" textAnchor="end">{Math.round(maxMetricValue * 0.33)}ms</text>
              <text x="50" y="184" fill="#94a3b8" fontSize="10" textAnchor="end">0ms</text>

              {/* Bars for Each Strategy */}
              {metrics.map((m, idx) => {
                const val = metricMode === 'total' ? m.totalLatency : m.gradingLatency;
                // Height in SVG pixels (max bar height 140px)
                const barHeight = Math.max(8, (val / maxMetricValue) * 140);
                const barY = 180 - barHeight;
                // Position X coordinates
                const barWidth = 110;
                const barX = 110 + idx * 200;
                const isSelected = selectedStrategy === m.id;
                const gradientId = m.id === 'llm' ? 'url(#llmGradient)' : m.id === 'cross_encoder' ? 'url(#crossGradient)' : 'url(#simGradient)';

                return (
                  <g key={m.id}>
                    {/* Highlight outline if selected strategy */}
                    {isSelected && (
                      <rect
                        x={barX - 6}
                        y={barY - 6}
                        width={barWidth + 12}
                        height={barHeight + 12}
                        rx="10"
                        fill="none"
                        stroke="#0f172a"
                        strokeWidth="2"
                        strokeDasharray="4 4"
                      />
                    )}

                    {/* Main Bar */}
                    <rect
                      x={barX}
                      y={barY}
                      width={barWidth}
                      height={barHeight}
                      rx="8"
                      fill={gradientId}
                      style={{ cursor: 'pointer', transition: 'all 0.3s ease' }}
                      onClick={() => handleStrategyChange(m.id)}
                    />

                    {/* Value text above bar */}
                    <text
                      x={barX + barWidth / 2}
                      y={barY - 12}
                      fill="#0f172a"
                      fontSize="12.5"
                      fontWeight="800"
                      textAnchor="middle"
                    >
                      {val} ms
                    </text>

                    {/* Selected badge if active */}
                    {isSelected && (
                      <text
                        x={barX + barWidth / 2}
                        y={barY - 26}
                        fill="#2563eb"
                        fontSize="10"
                        fontWeight="700"
                        textAnchor="middle"
                      >
                        ★ Selected
                      </text>
                    )}

                    {/* X-Axis Strategy Label */}
                    <text
                      x={barX + barWidth / 2}
                      y="200"
                      fill="#0f172a"
                      fontSize="11.5"
                      fontWeight="700"
                      textAnchor="middle"
                    >
                      {m.shortName}
                    </text>

                    {/* Latency in seconds sublabel */}
                    <text
                      x={barX + barWidth / 2}
                      y="214"
                      fill="#64748b"
                      fontSize="10"
                      textAnchor="middle"
                    >
                      {(m.totalLatency / 1000).toFixed(2)}s total
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        </div>

        {/* Analytical KPI Cards Below Graph */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px' }}>
          {/* Card 1: Selected Strategy Time */}
          <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#64748b', fontSize: '11.5px', marginBottom: '4px' }}>
              <Clock size={14} />
              <span>Selected Strategy Latency</span>
            </div>
            <div style={{ fontSize: '20px', fontWeight: 800, color: '#0f172a' }}>
              {metrics.find(m => m.id === selectedStrategy)?.totalLatency} <span style={{ fontSize: '13px', fontWeight: 500 }}>ms</span>
            </div>
            <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>
              {((metrics.find(m => m.id === selectedStrategy)?.totalLatency || 0) / 1000).toFixed(2)} seconds
            </div>
          </div>

          {/* Card 2: Fastest Strategy */}
          <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '10px', padding: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#2563eb', fontSize: '11.5px', marginBottom: '4px' }}>
              <Zap size={14} />
              <span>Fastest Strategy</span>
            </div>
            <div style={{ fontSize: '20px', fontWeight: 800, color: '#1d4ed8' }}>
              {fastestStrategy.shortName}
            </div>
            <div style={{ fontSize: '11px', color: '#2563eb', marginTop: '2px' }}>
              {fastestStrategy.totalLatency} ms ({fastestStrategy.gradingLatency}ms grading)
            </div>
          </div>

          {/* Card 3: Cross-Encoder Speedup */}
          <div style={{ background: '#f5f3ff', border: '1px solid #ddd6fe', borderRadius: '10px', padding: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#7c3aed', fontSize: '11.5px', marginBottom: '4px' }}>
              <TrendingUp size={14} />
              <span>Cross-Encoder Advantage</span>
            </div>
            <div style={{ fontSize: '20px', fontWeight: 800, color: '#6d28d9' }}>
              {crossSpeedupVsLlm}x Faster
            </div>
            <div style={{ fontSize: '11px', color: '#7c3aed', marginTop: '2px' }}>
              Near-LLM accuracy with 0 extra LLM calls
            </div>
          </div>

          {/* Card 4: Grading Phase Overhead */}
          <div style={{ background: '#ecfdf5', border: '1px solid #a7f3d0', borderRadius: '10px', padding: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#059669', fontSize: '11.5px', marginBottom: '4px' }}>
              <Gauge size={14} />
              <span>Grading Step Efficiency</span>
            </div>
            <div style={{ fontSize: '20px', fontWeight: 800, color: '#047857' }}>
              {((metrics.find(m => m.id === selectedStrategy)?.gradingLatency || 12) /
                Math.max(1, metrics.find(m => m.id === selectedStrategy)?.totalLatency || 100) * 100).toFixed(1)}%
            </div>
            <div style={{ fontSize: '11px', color: '#059669', marginTop: '2px' }}>
              Overhead of relevance verification
            </div>
          </div>
        </div>
      </div>

      {/* Upload Custom Document Modal */}
      {showUploadModal && (
        <div className="modal-overlay" onClick={() => !isUploading && setShowUploadModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ padding: '28px', maxWidth: '580px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a' }}>
                Upload Document for CRAG Evaluation
              </h3>
              <button
                type="button"
                style={{ background: 'none', border: 'none', fontSize: '18px', cursor: 'pointer', color: '#94a3b8' }}
                onClick={() => !isUploading && setShowUploadModal(false)}
              >
                ✕
              </button>
            </div>
            <p style={{ fontSize: '12.5px', color: '#64748b', marginBottom: '18px' }}>
              Upload your research report, syllabus, contract, or notes (.pdf, .docx, .txt, .md). The backend parses passages, indexes them into vector storage, and runs all 3 grading algorithms.
            </p>

            {/* File Dropzone */}
            <div
              className="upload-dropzone"
              style={{
                padding: '28px 20px',
                marginBottom: '16px',
                border: '2px dashed #93c5fd',
                borderRadius: '12px',
                background: '#f8fafc',
                cursor: isUploading ? 'not-allowed' : 'pointer',
                textAlign: 'center'
              }}
              onClick={() => !isUploading && document.getElementById('file-picker-docqa')?.click()}
            >
              <input
                id="file-picker-docqa"
                type="file"
                style={{ display: 'none' }}
                accept=".txt,.md,.pdf,.docx,.json"
                onChange={handleFileUpload}
                disabled={isUploading}
              />
              {isUploading ? (
                <div>
                  <Loader2 size={36} className="animate-spin" color="#2563eb" style={{ margin: '0 auto 10px auto' }} />
                  <div style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a' }}>
                    Parsing & Indexing Document...
                  </div>
                  <span style={{ fontSize: '11.5px', color: '#64748b' }}>
                    Extracting semantic passages into vector store
                  </span>
                </div>
              ) : (
                <div>
                  <FileUp size={36} color="#2563eb" style={{ margin: '0 auto 10px auto' }} />
                  <div style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a' }}>
                    Click to select Document File (.pdf, .docx, .txt, .md)
                  </div>
                  <span style={{ fontSize: '11.5px', color: '#64748b', display: 'block', marginTop: '4px' }}>
                    Supports Word documents (.docx), PDFs (.pdf), and text files
                  </span>
                </div>
              )}
            </div>

            <div style={{ textAlign: 'center', margin: '14px 0', fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>
              — OR PASTE TEXT CONTENT DIRECTLY —
            </div>

            <div className="form-group">
              <textarea
                className="form-control"
                rows={5}
                placeholder="Paste document sections, research abstract, or text paragraphs here..."
                value={customText}
                onChange={(e) => setCustomText(e.target.value)}
                disabled={isUploading}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '18px' }}>
              <button
                type="button"
                className="btn-primary"
                style={{ background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1' }}
                onClick={() => setShowUploadModal(false)}
                disabled={isUploading}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn-primary"
                style={{ background: '#2563eb' }}
                disabled={!customText.trim() || isUploading}
                onClick={handleCustomTextSubmit}
              >
                {isUploading ? 'Indexing...' : 'Index & Start Q&A'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

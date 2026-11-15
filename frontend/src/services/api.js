// Client API connector for RAGLab Comparative Evaluation Backend
import { demoPresetResponses, initialGoldLabels } from '../data/mockData';

const BASE_URL = '';

export async function checkBackendHealth() {
  try {
    const res = await fetch(`${BASE_URL}/api/health`, { method: 'GET' });
    if (!res.ok) throw new Error('Backend offline');
    return await res.json();
  } catch (err) {
    return { status: 'offline', error: err.message };
  }
}

export async function fetchGraders() {
  try {
    const res = await fetch(`${BASE_URL}/api/graders`);
    if (res.ok) return await res.json();
  } catch {
    // fallback
  }
  return null;
}

export async function fetchDomains() {
  try {
    const res = await fetch(`${BASE_URL}/api/domains`);
    if (res.ok) return await res.json();
  } catch {
    // fallback
  }
  return null;
}

export async function fetchGoldLabels(domain) {
  try {
    const normDomain = domain && domain !== 'All' ? domain.toLowerCase() : '';
    const url = normDomain ? `${BASE_URL}/api/dataset/gold?domain=${normDomain}` : `${BASE_URL}/api/dataset/gold`;
    const res = await fetch(url);
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        return data.map((item, idx) => ({
          id: item.pair_id || `item-${idx + 1}`,
          queryId: item.query_id || `q_${idx + 1}`,
          query: item.query,
          chunk: item.chunk_id,
          relevance: item.ground_truth_relevance,
          domain: item.domain === 'hotpotqa' ? 'HotpotQA' : 'Legal',
          text: item.chunk_text,
          groundTruthAnswer: item.ground_truth_answer || ''
        }));
      }
    }
  } catch {
    // fallback
  }
  return initialGoldLabels;
}

export async function saveGoldLabelApi(item) {
  try {
    const res = await fetch(`${BASE_URL}/api/dataset/gold`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(item)
    });
    if (res.ok) return await res.json();
  } catch {
    // fallback
  }
  return null;
}

export async function runCragLiveCompare(query, domain = 'hotpotqa', topK = 4) {
  try {
    const normDomain = domain.toLowerCase() === 'legal' ? 'legal' : 'hotpotqa';
    const res = await fetch(`${BASE_URL}/api/crag/compare-live`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, domain: normDomain, top_k: topK })
    });
    if (res.ok) {
      const data = await res.json();
      const results = data.results || {};

      const llmResult = results.llm || {};
      const crossResult = results.cross_encoder || {};
      const simResult = results.similarity_threshold || {};

      return {
        llm: {
          relevant: `${llmResult.graded_relevant_count ?? 0}/${llmResult.retrieved_chunks_count ?? topK}`,
          latency: `${((llmResult.total_latency_ms ?? 0) / 1000).toFixed(2)}s`,
          gradingLatency: `${(llmResult.grading_latency_ms ?? 0).toFixed(1)} ms`,
          retries: llmResult.reformulation_retries ?? 0,
          llmCalls: llmResult.total_llm_calls ?? 0,
          result: llmResult.final_answer || 'No response generated.'
        },
        cross_encoder: {
          relevant: `${crossResult.graded_relevant_count ?? 0}/${crossResult.retrieved_chunks_count ?? topK}`,
          latency: `${((crossResult.total_latency_ms ?? 0) / 1000).toFixed(2)}s`,
          gradingLatency: `${(crossResult.grading_latency_ms ?? 0).toFixed(1)} ms`,
          retries: crossResult.reformulation_retries ?? 0,
          llmCalls: crossResult.total_llm_calls ?? 0,
          result: crossResult.final_answer || 'No response generated.'
        },
        similarity_threshold: {
          relevant: `${simResult.graded_relevant_count ?? 0}/${simResult.retrieved_chunks_count ?? topK}`,
          latency: `${((simResult.total_latency_ms ?? 0) / 1000).toFixed(2)}s`,
          gradingLatency: `${(simResult.grading_latency_ms ?? 0).toFixed(1)} ms`,
          retries: simResult.reformulation_retries ?? 0,
          llmCalls: simResult.total_llm_calls ?? 0,
          result: simResult.final_answer || 'No response generated.'
        },
        finalAnswer: crossResult.final_answer || llmResult.final_answer || simResult.final_answer || 'No response generated.',
        evidenceBadge: 'Grounded in retrieved domain corpus'
      };
    }
  } catch {
    // Offline fallback only when backend server is unreachable
  }

  if (demoPresetResponses[query]) {
    return demoPresetResponses[query];
  }

  return {
    llm: {
      relevant: '0/4',
      latency: '0.00s',
      result: 'Backend server unreachable. Start FastAPI backend on port 8000.'
    },
    cross_encoder: {
      relevant: '0/4',
      latency: '0.00s',
      result: 'Backend server unreachable. Start FastAPI backend on port 8000.'
    },
    similarity_threshold: {
      relevant: '0/4',
      latency: '0.00s',
      result: 'Backend server unreachable. Start FastAPI backend on port 8000.'
    },
    finalAnswer: 'Backend API is offline. Please ensure the FastAPI server is running on http://127.0.0.1:8000.',
    evidenceBadge: 'Backend Offline'
  };
}

export async function fetchLatestEvaluation() {
  try {
    const res = await fetch(`${BASE_URL}/api/eval/latest`);
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // fallback
  }
  return null;
}

export async function runEvaluationApi(domain = 'All Domains', strategies = ['llm', 'cross_encoder', 'similarity_threshold']) {
  try {
    const domLower = (domain || '').toLowerCase();
    const domainsList = domLower.includes('all')
      ? ['hotpotqa', 'legal']
      : [domLower === 'legal' || domLower === 'bioasq' ? 'legal' : 'hotpotqa'];
    const res = await fetch(`${BASE_URL}/api/eval/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        domains: domainsList,
        strategies
      })
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // fallback
  }
  return null;
}

export async function askDocQA(query, domain = 'report', strategy = 'llm', topK = 4) {
  try {
    const res = await fetch(`${BASE_URL}/api/doc-qa/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        domain,
        strategy,
        top_k: topK
      })
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // fallback
  }

  return {
    query,
    domain,
    strategy,
    final_answer: 'Backend server is offline. Please start the FastAPI server on port 8000 to run live Document QA.',
    used_chunks: [],
    grading_results: [],
    total_latency_ms: 0,
    total_llm_calls: 0
  };
}

export async function uploadCustomDoc(docName, docText, domain = 'custom_doc') {
  try {
    const res = await fetch(`${BASE_URL}/api/doc-qa/upload`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        doc_name: docName,
        doc_text: docText,
        domain
      })
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // fallback
  }

  const paragraphs = docText.split('\n\n').filter((p) => p.trim().length > 20);
  return {
    status: 'offline',
    domain,
    doc_name: docName,
    chunks_indexed: Math.max(1, paragraphs.length),
    message: `Backend offline: could not index '${docName}'.`
  };
}

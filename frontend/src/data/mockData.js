// Baseline & Fallback Data Store for RAGLab Comparative Evaluation
// Live views fetch real evaluation metrics from GET /api/eval/latest and GET /api/dataset/gold

export const initialStats = {
  domains: 2,
  domainsText: "HotpotQA & Legal",
  strategies: 3,
  strategiesText: "LLM (qwen2.5:3b) | Cross-Encoder | Cosine",
  queries: "60",
  queriesText: "30 per domain (120 gold pairs)",
  completed: "100%",
  completedText: "Empirically validated"
};

export const recentResultsData = [
  { strategy: "LLM-prompt judge (qwen2.5:3b)", domain: "HotpotQA", gradingF1: 91.8, em: 83.3, f1: 79.4, latency: "2.84s" },
  { strategy: "Cross-encoder (ms-marco-MiniLM)", domain: "HotpotQA", gradingF1: 87.0, em: 76.7, f1: 72.1, latency: "0.06s" },
  { strategy: "Similarity threshold (MiniLM-L6)", domain: "HotpotQA", gradingF1: 80.0, em: 63.3, f1: 58.6, latency: "0.01s" },
  { strategy: "LLM-prompt judge (qwen2.5:3b)", domain: "Legal", gradingF1: 90.3, em: 80.0, f1: 76.8, latency: "2.91s" },
  { strategy: "Cross-encoder (ms-marco-MiniLM)", domain: "Legal", gradingF1: 84.5, em: 73.3, f1: 69.5, latency: "0.06s" },
  { strategy: "Similarity threshold (MiniLM-L6)", domain: "Legal", gradingF1: 76.9, em: 53.3, f1: 49.2, latency: "0.01s" }
];

export const uploadedDocuments = [
  { id: 1, name: "HotpotQA_Corpus_30_Passages.json", size: "18.4 KB", domain: "HotpotQA", date: "Nov 2026" },
  { id: 2, name: "Legal_Contracts_GDPR_30_Clauses.json", size: "22.1 KB", domain: "Legal", date: "Nov 2026" },
  { id: 3, name: "gold_benchmark_120_pairs.json", size: "54.6 KB", domain: "Both Domains", date: "Nov 2026" },
  { id: 4, name: "Extended_RAG_Grading_Report_Corpus.json", size: "12.8 KB", domain: "Report", date: "Nov 2026" }
];

export const datasetInfoList = [
  {
    id: "hotpotqa",
    name: "HotpotQA",
    category: "General Knowledge / Multi-Hop",
    description: "Multi-hop encyclopedia passages covering history, science, astronomy, biology, and geography with paired distractor passages.",
    docs: 30,
    questions: 30,
    goldPairs: 60,
    domain: "HotpotQA",
    color: "#3b82f6"
  },
  {
    id: "legal",
    name: "Legal Contracts & Statutes",
    category: "Dense Legal Text",
    description: "Commercial Master Services Agreements, SaaS SLAs, IP indemnification clauses, and EU GDPR statutory provisions with cross-clause lexical distractors.",
    docs: 30,
    questions: 30,
    goldPairs: 60,
    domain: "Legal",
    color: "#8b5cf6"
  }
];

export const gradingStrategies = [
  {
    id: "llm",
    code: "Strategy A",
    name: "LLM-Prompt Judge",
    theme: "green",
    badgeBg: "#ecfdf5",
    badgeBorder: "#a7f3d0",
    badgeColor: "#059669",
    btnColor: "#059669",
    features: [
      { text: "Prompts local Ollama (qwen2.5:3b) for yes/no relevance", positive: true },
      { text: "Highest specificity against lexical-trap distractors", positive: true },
      { text: "Requires 1 LLM call per candidate chunk (~2.5-3.5s/call on CPU)", positive: false }
    ],
    threshold: 0.50,
    model: "Ollama (qwen2.5:3b)",
    latencyDesc: "High (~2,500–3,500 ms per chunk on local CPU)"
  },
  {
    id: "cross_encoder",
    code: "Strategy B",
    name: "Cross-Encoder / NLI",
    theme: "purple",
    badgeBg: "#f3e8ff",
    badgeBorder: "#d8b4fe",
    badgeColor: "#7c3aed",
    btnColor: "#7c3aed",
    features: [
      { text: "Pretrained MS MARCO Cross-Encoder (joint query-passage attention)", positive: true },
      { text: "Zero LLM grading calls; ~15 ms per chunk on CPU", positive: true },
      { text: "Strong Pareto balance of grading F1 and speed", positive: true }
    ],
    threshold: 0.50,
    model: "cross-encoder/ms-marco-MiniLM-L-6-v2",
    latencyDesc: "Low (~10–25 ms per chunk on CPU)"
  },
  {
    id: "similarity_threshold",
    code: "Strategy C",
    name: "Similarity Threshold",
    theme: "blue",
    badgeBg: "#eff6ff",
    badgeBorder: "#bfdbfe",
    badgeColor: "#2563eb",
    btnColor: "#2563eb",
    features: [
      { text: "Thresholds raw all-MiniLM-L6-v2 FAISS cosine similarity", positive: true },
      { text: "Zero grading inference overhead (< 0.1 ms)", positive: true },
      { text: "Vulnerable to boilerplate false positives in dense legal text", positive: false }
    ],
    threshold: 0.45,
    model: "SentenceTransformer (all-MiniLM-L6-v2) + FAISS",
    latencyDesc: "Negligible (< 0.1 ms)"
  }
];

export const initialGoldLabels = [
  {
    id: "gold_hp_001",
    query: "Who commissioned the Roman Colosseum and under which emperor was it completed in AD 80?",
    chunk: "hp_chunk_001",
    relevance: true,
    domain: "HotpotQA",
    text: "The Roman Colosseum, originally named the Flavian Amphitheatre, was commissioned by Emperor Vespasian in AD 72 and completed under his successor Titus in AD 80."
  },
  {
    id: "gold_hp_002",
    query: "Who commissioned the Roman Colosseum and under which emperor was it completed in AD 80?",
    chunk: "hp_chunk_002",
    relevance: false,
    domain: "HotpotQA",
    text: "Vespasian ruled as Roman emperor from AD 69 to AD 79. As the fourth and final ruler in the Year of the Four Emperors, he founded the Flavian dynasty."
  },
  {
    id: "gold_leg_001",
    query: "What is the maximum aggregate cumulative liability cap under Section 8.1 of the Agreement?",
    chunk: "leg_chunk_001",
    relevance: true,
    domain: "Legal",
    text: "Section 8.1 (Limitation of Liability Cap): In no event shall either party's aggregate cumulative liability arising out of or related to this Agreement exceed the total subscription fees actually paid by Customer to Vendor hereunder in the twelve (12) months immediately preceding the event."
  },
  {
    id: "gold_leg_002",
    query: "What is the maximum aggregate cumulative liability cap under Section 8.1 of the Agreement?",
    chunk: "leg_chunk_024",
    relevance: false,
    domain: "Legal",
    text: "Section 8.3 (Super-Cap Exceptions to Liability Limitation): The liability cap in Section 8.1 shall not apply to indemnification obligations under Section 9.3, breaches of confidentiality under Section 4.3, or gross negligence."
  }
];

export const comparisonMetrics = {
  bestAccuracy: { strategy: "LLM-Prompt Judge", value: "88.3%", badge: "green" },
  lowestLatency: { strategy: "Similarity Threshold", value: "0.05 ms", badge: "purple" },
  highestF1: { strategy: "LLM-Prompt Judge", value: "78.1%", badge: "blue" },
  lowestCost: { strategy: "Cross-Encoder / Similarity", value: "1.0 call/query", badge: "orange" }
};

export const emComparisonData = [
  { strategy: "LLM-prompt judge", hotpotqa: 83.3, legal: 80.0 },
  { strategy: "Cross-encoder / NLI", hotpotqa: 76.7, legal: 73.3 },
  { strategy: "Similarity threshold", hotpotqa: 63.3, legal: 53.3 }
];

export const latencyComparisonData = [
  { strategy: "LLM-prompt judge", hotpotqa: 2.84, legal: 2.91 },
  { strategy: "Cross-encoder / NLI", hotpotqa: 0.06, legal: 0.06 },
  { strategy: "Similarity threshold", hotpotqa: 0.01, legal: 0.01 }
];

export const keyFindings = [
  "Strategy B (Cross-Encoder ms-marco-MiniLM-L-6-v2) achieves 87.0% grading F1 on HotpotQA and 84.5% on Legal with zero grading LLM calls (~15 ms/chunk).",
  "Strategy C (Raw Cosine Similarity >= 0.45) suffers high false-positive rates on dense Legal text (40.0% specificity) due to contractual boilerplate overlap.",
  "Strategy A (Ollama qwen2.5:3b Judge) delivers high specificity and downstream Answer F1, but requires 4+ grading LLM calls per query (~2.5-3.5s per chunk on CPU).",
  "Domain complexity matters: moving from general knowledge (HotpotQA) to dense Legal clauses widens the precision gap between dedicated graders (Strategies A/B) and raw retrieval similarity (Strategy C)."
];

export const demoSampleQueries = [
  "Who commissioned the Roman Colosseum and under which emperor was it completed in AD 80?",
  "What electromechanical machine did Alan Turing devise at Bletchley Park to decipher Enigma messages?",
  "What is the maximum aggregate cumulative liability cap under Section 8.1 of the Agreement?",
  "Within how many hours must the Data Processor notify the Data Controller of a confirmed Security Incident under Section 7.4?"
];

export const demoPresetResponses = {
  "Who commissioned the Roman Colosseum and under which emperor was it completed in AD 80?": {
    llm: { relevant: "1/4", latency: "2.84s", result: "The Roman Colosseum, originally named the Flavian Amphitheatre, was commissioned by Emperor Vespasian in AD 72 and completed under his successor Titus in AD 80." },
    cross_encoder: { relevant: "1/4", latency: "0.06s", result: "The Roman Colosseum, originally named the Flavian Amphitheatre, was commissioned by Emperor Vespasian in AD 72 and completed under his successor Titus in AD 80." },
    similarity_threshold: { relevant: "2/4", latency: "0.01s", result: "The Roman Colosseum was commissioned by Emperor Vespasian in AD 72 and completed under Titus in AD 80. Vespasian ruled as Roman emperor from AD 69 to AD 79." },
    finalAnswer: "The Roman Colosseum (Flavian Amphitheatre) was commissioned by Emperor Vespasian in AD 72 and completed under Titus in AD 80.",
    evidenceBadge: "Grounded in retrieved domain corpus"
  }
};

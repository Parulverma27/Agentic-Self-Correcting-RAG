// Data store and API connector for RAGLab Comparative Analysis

export const initialStats = {
  domains: 2,
  domainsText: "HotpotQA & BioASQ",
  strategies: 3,
  strategiesText: "LLM | Cross-Encoder | Similarity",
  queries: "100+",
  queriesText: "Per domain",
  completed: "100%",
  completedText: "All experiments finished"
};

export const recentResultsData = [
  { strategy: "LLM-prompt judge", domain: "HotpotQA", em: 72.4, f1: 78.9, latency: "3.42s" },
  { strategy: "Cross-encoder / NLI", domain: "HotpotQA", em: 70.1, f1: 76.2, latency: "0.84s" },
  { strategy: "Similarity threshold", domain: "HotpotQA", em: 65.3, f1: 71.8, latency: "0.42s" },
  { strategy: "LLM-prompt judge", domain: "BioASQ", em: 68.7, f1: 74.6, latency: "3.21s" },
  { strategy: "Cross-encoder / NLI", domain: "BioASQ", em: 66.8, f1: 72.9, latency: "0.76s" },
  { strategy: "Similarity threshold", domain: "BioASQ", em: 60.2, f1: 66.4, latency: "0.38s" }
];

export const uploadedDocuments = [
  { id: 1, name: "HotpotQA_dataset.pdf", size: "2.4 MB", domain: "General", date: "12 Aug 2025" },
  { id: 2, name: "BioASQ_corpus.pdf", size: "5.1 MB", domain: "Medical", date: "11 Aug 2025" },
  { id: 3, name: "research_papers.txt", size: "1.2 MB", domain: "General", date: "10 Aug 2025" },
  { id: 4, name: "knowledge_base.docx", size: "3.8 MB", domain: "General", date: "08 Aug 2025" }
];

export const datasetInfoList = [
  {
    id: "hotpotqa",
    name: "HotpotQA",
    category: "General Knowledge",
    description: "Multi-hop question answering dataset with complex reasoning requirements.",
    docs: 50,
    questions: 50,
    domain: "General",
    color: "#3b82f6"
  },
  {
    id: "bioasq",
    name: "BioASQ",
    category: "Medical",
    description: "Biomedical question answering dataset with expert domain knowledge.",
    docs: 50,
    questions: 50,
    domain: "Medical",
    color: "#8b5cf6"
  }
];

export const gradingStrategies = [
  {
    id: "llm",
    code: "Strategy A",
    name: "LLM-prompt Judge",
    theme: "green",
    badgeBg: "#ecfdf5",
    badgeBorder: "#a7f3d0",
    badgeColor: "#059669",
    btnColor: "#059669",
    features: [
      { text: "Uses LLM to judge relevance", positive: true },
      { text: "Flexible and accurate", positive: true },
      { text: "Slower and more expensive", positive: false }
    ],
    threshold: 0.70,
    model: "Llama-3 / GPT-4o-mini",
    latencyDesc: "Medium-High (~30-65ms simulated or local Ollama)"
  },
  {
    id: "cross_encoder",
    code: "Strategy B",
    name: "Cross-encoder / NLI",
    theme: "purple",
    badgeBg: "#f3e8ff",
    badgeBorder: "#d8b4fe",
    badgeColor: "#7c3aed",
    btnColor: "#7c3aed",
    features: [
      { text: "Uses pretrained cross-encoder", positive: true },
      { text: "Fast and cost-effective", positive: true },
      { text: "Runs locally", positive: true }
    ],
    threshold: 0.65,
    model: "ms-marco-MiniLM-L-6-v2",
    latencyDesc: "Low (~8-15ms)"
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
      { text: "Uses cosine similarity score", positive: true },
      { text: "Cheapest baseline", positive: true },
      { text: "No extra model needed", positive: true }
    ],
    threshold: 0.75,
    model: "Cosine Cosine Distance (Vector Index)",
    latencyDesc: "Negligible (<1ms)"
  }
];

export const initialGoldLabels = [
  {
    id: "item-1",
    query: "What is the capital of France?",
    chunk: "chunk_001",
    relevance: true,
    domain: "HotpotQA",
    text: "Paris is the capital and most populous city of France, situated on the Seine River."
  },
  {
    id: "item-2",
    query: "Who wrote Hamlet?",
    chunk: "chunk_023",
    relevance: true,
    domain: "HotpotQA",
    text: "The Tragedy of Hamlet, Prince of Denmark, often shortened to Hamlet, is a tragedy written by William Shakespeare."
  },
  {
    id: "item-3",
    query: "Symptoms of diabetes",
    chunk: "chunk_045",
    relevance: false,
    domain: "BioASQ",
    text: "Hypertension (high blood pressure) is when the pressure in your blood vessels is too high (140/90 mmHg or higher)."
  },
  {
    id: "item-4",
    query: "Treatment for hypertension",
    chunk: "chunk_067",
    relevance: true,
    domain: "BioASQ",
    text: "Standard first-line medical therapy for essential hypertension includes ACE inhibitors, ARBs, CCBs, and thiazide diuretics."
  },
  {
    id: "item-5",
    query: "When was Google founded?",
    chunk: "chunk_089",
    relevance: false,
    domain: "HotpotQA",
    text: "Microsoft Corporation is an American multinational corporation and technology company headquartered in Redmond, Washington."
  },
  {
    id: "item-6",
    query: "Causes of type 2 diabetes",
    chunk: "chunk_102",
    relevance: true,
    domain: "BioASQ",
    text: "Type 2 diabetes results primarily from insulin resistance combined with insufficient compensatory insulin secretion."
  },
  {
    id: "item-7",
    query: "Where was Nikola Tesla born?",
    chunk: "chunk_115",
    relevance: true,
    domain: "HotpotQA",
    text: "Nikola Tesla was born an ethnic Serb in the village of Smiljan, in the Austrian Empire (present-day Croatia)."
  }
];

export const comparisonMetrics = {
  bestAccuracy: { strategy: "LLM-prompt Judge", value: "86.7%", badge: "green" },
  lowestLatency: { strategy: "Similarity Threshold", value: "0.42s", badge: "purple" },
  highestF1: { strategy: "LLM-prompt Judge", value: "82.3%", badge: "blue" },
  lowestCost: { strategy: "Similarity Threshold", value: "1 call/query", badge: "orange" }
};

export const emComparisonData = [
  { strategy: "LLM-prompt judge", hotpotqa: 72.4, bioasq: 68.7 },
  { strategy: "Cross-encoder / NLI", hotpotqa: 70.1, bioasq: 66.8 },
  { strategy: "Similarity threshold", hotpotqa: 65.3, bioasq: 60.2 }
];

export const latencyComparisonData = [
  { strategy: "LLM-prompt judge", hotpotqa: 3.42, bioasq: 3.21 },
  { strategy: "Cross-encoder / NLI", hotpotqa: 0.84, bioasq: 0.76 },
  { strategy: "Similarity threshold", hotpotqa: 0.42, bioasq: 0.38 }
];

export const keyFindings = [
  "LLM-prompt judge achieves the highest accuracy but at the cost of higher latency.",
  "Cross-encoder offers a good balance of accuracy and speed.",
  "Similarity threshold is the cheapest but slightly lower in performance.",
  "Performance varies by domain, with HotpotQA being more challenging."
];

export const demoSampleQueries = [
  "What is the capital of France?",
  "Who wrote Hamlet?",
  "Treatment for hypertension",
  "When was Google founded?"
];

export const demoPresetResponses = {
  "What is the capital of France?": {
    llm: { relevant: "3/5", latency: "3.12s", result: "Paris is the capital of France." },
    cross_encoder: { relevant: "2/5", latency: "0.78s", result: "Paris is the capital of France." },
    similarity_threshold: { relevant: "1/5", latency: "0.35s", result: "Paris is the capital of France." },
    finalAnswer: "The capital of France is Paris.",
    evidenceBadge: "Generated from relevant evidence"
  },
  "Who wrote Hamlet?": {
    llm: { relevant: "4/5", latency: "2.95s", result: "William Shakespeare wrote Hamlet." },
    cross_encoder: { relevant: "3/5", latency: "0.81s", result: "William Shakespeare wrote Hamlet." },
    similarity_threshold: { relevant: "2/5", latency: "0.32s", result: "William Shakespeare wrote Hamlet." },
    finalAnswer: "William Shakespeare is the author of the tragedy Hamlet.",
    evidenceBadge: "Generated from relevant evidence"
  },
  "Treatment for hypertension": {
    llm: { relevant: "3/5", latency: "3.40s", result: "First-line antihypertensive drugs include ACE inhibitors, ARBs, and CCBs." },
    cross_encoder: { relevant: "3/5", latency: "0.79s", result: "First-line antihypertensive drugs include ACE inhibitors and ARBs." },
    similarity_threshold: { relevant: "2/5", latency: "0.36s", result: "Treatment involves lifestyle modifications and medications." },
    finalAnswer: "Treatment for hypertension includes lifestyle changes and medications such as ACE inhibitors, ARBs, CCBs, and thiazide diuretics.",
    evidenceBadge: "Generated from relevant evidence"
  },
  "When was Google founded?": {
    llm: { relevant: "3/5", latency: "3.05s", result: "Google was founded on September 4, 1998 by Larry Page and Sergey Brin." },
    cross_encoder: { relevant: "2/5", latency: "0.72s", result: "Google was founded in September 1998." },
    similarity_threshold: { relevant: "1/5", latency: "0.30s", result: "Google was founded in 1998." },
    finalAnswer: "Google was founded on September 4, 1998, by Larry Page and Sergey Brin.",
    evidenceBadge: "Generated from relevant evidence"
  }
};

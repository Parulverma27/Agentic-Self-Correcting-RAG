# Comparative Evaluation of Relevance-Grading Strategies in Corrective Retrieval-Augmented Generation Systems

**Extended Major Project Report & Research Paper Draft — B.Tech CSE (AI/ML), Final Year**

---

## Abstract

Retrieval-Augmented Generation (RAG) systems frequently hallucinate when vector retrieval returns topically adjacent but factually irrelevant passages. Corrective RAG (CRAG) pipelines address this vulnerability by inserting a relevance-grading module between retrieval and generation, triggering query reformulation and retry loops when retrieved evidence is insufficient. However, seminal works such as Self-RAG and CRAG each adopt a single grading paradigm without comparing alternative grading architectures across cost, latency, grading accuracy, and domain complexity. In this study, we conduct a controlled empirical comparison of three interchangeable relevance-grading strategies integrated behind a unified interface inside an identical Corrective RAG pipeline: **Strategy A** (zero-shot LLM-prompt judge using local Ollama `qwen2.5:3b`), **Strategy B** (a pretrained neural cross-encoder `cross-encoder/ms-marco-MiniLM-L-6-v2`), and **Strategy C** (direct thresholding of dense bi-encoder cosine similarity from `all-MiniLM-L6-v2` + FAISS). We evaluate all three strategies across two distinct domains—multi-hop encyclopedic questions (**HotpotQA**) and dense corporate contractual clauses (**Legal**)—against a hand-labelled gold benchmark of $N = 120$ query-chunk pairs ($60$ per domain: $30$ positive and $30$ hard-negative distractor pairs). Statistical significance is validated using paired Student's $t$-tests, Holm-Bonferroni step-down multiple-testing correction, and $2{,}000$-iteration paired bootstrap resampling. Our results show that Strategy B (Cross-Encoder) occupies the Pareto frontier: it achieves the highest gold-set grading $F_1$ ($87.0\%$ on HotpotQA, $84.5\%$ on Legal) and significantly outperforms raw similarity thresholding on downstream Answer Token $F_1$ ($+4.98\%$ on HotpotQA, $p = 0.0118$, bootstrap $p = 0.0010$; $+8.43\%$ on Legal, $p = 0.0029$, Holm-adjusted $p = 0.0172$, bootstrap $p = 0.0010$, Cohen's $d_z = 0.595$) while operating $59\times$ faster than the LLM judge ($31.5\text{ ms}$ vs. $1{,}873.5\text{ ms}$ per chunk) and requiring zero grading LLM calls. Furthermore, we demonstrate a strong domain interaction effect: moving from general knowledge to dense Legal text degrades raw similarity specificity from $50.0\%$ to $40.0\%$ due to contractual boilerplate overlap, nearly doubling the downstream accuracy advantage of dedicated cross-encoder grading.

---

## 1. Introduction

Retrieval-Augmented Generation (RAG) grounds large language model (LLM) responses in external document collections by retrieving top-$k$ passages via dense vector similarity and conditioning generation on the retrieved context. A well-documented failure mode of standard RAG architectures is their *blind trust in retrieval*: when the vector index returns irrelevant, partially relevant, or distractor passages, the generator still synthesizes a fluent, confident response that may be unfaithful or polluted by distractor facts.

Corrective Retrieval-Augmented Generation (CRAG) mitigates this vulnerability by introducing an explicit **relevance-grading step** prior to generation. Each retrieved candidate passage is evaluated against the user query; if the count of relevant passages falls below a sufficiency threshold, the pipeline automatically reformulates the query and retries retrieval up to a bounded number of attempts before falling back to a safe abstention message.

Rather than assuming a single grading paradigm is optimal, this work extends an existing Corrective RAG system into a controlled comparative study of how the relevance-grading step itself should be constructed, evaluated across multiple document domains with rigorous statistical validation.

---

## 2. Motivation and Research Gap

Published architectures such as Self-RAG (Asai et al., 2023) and Corrective RAG (Yan et al., 2024) each introduce a specific grading mechanism—fine-tuned reflection tokens or an evaluator model—and evaluate their end-to-end system against standard ungraded RAG. However, neither work isolates the **grading module itself** to compare realistic engineering alternatives under identical retrieval, reformulation, and generation conditions.

In practical deployments, system architects face an immediate design trade-off among three natural choices:
1. Prompting a general-purpose LLM to judge passage relevance (`yes`/`no`).
2. Deploying a lightweight, purpose-built neural cross-encoder / NLI scorer locally.
3. Skipping a separate grading model altogether and thresholding the raw cosine similarity score already produced by dense vector retrieval.

This leaves two open, practically relevant research questions:
- **RQ1 (Cost-Latency-Accuracy Trade-off):** Does invoking an LLM as a relevance judge outperform cheaper neural cross-encoder or cosine-threshold alternatives by enough to justify its latency and compute cost?
- **RQ2 (Domain Sensitivity):** Does the relative effectiveness of these three grading strategies hold across domains, or do dense, boilerplate-heavy domains (such as corporate Legal contracts) penalize raw cosine similarity thresholding more severely than general-knowledge domains (HotpotQA)?

---

## 3. The Three Grading Strategies Under Comparison

All three strategies implement a single shared asynchronous interface (`BaseGrader.grade(query, chunk) -> GradingResult` and `grade_batch(query, chunks) -> List[GradingResult]`), allowing any grader to be swapped into the Corrective RAG loop without modifying retrieval, query reformulation, or answer generation.

| Strategy ID | Strategy Name | Underlying Model / Mechanism | Decision Rule | LLM Calls / Chunk |
| :--- | :--- | :--- | :--- | :---: |
| **Strategy A (`llm`)** | LLM-Prompt Judge | Local Ollama `qwen2.5:3b` (`temperature=0.0`) | Prompts LLM for binary `yes`/`no` relevance judgement | $1$ |
| **Strategy B (`cross_encoder`)** | Cross-Encoder / NLI | Hugging Face `cross-encoder/ms-marco-MiniLM-L-6-v2` (6-layer MiniLM) | Jointly encodes $(q, d)$ with full cross-attention; $\sigma(\text{logit}) \ge 0.50$ | $0$ |
| **Strategy C (`similarity_threshold`)** | Similarity Threshold Baseline | Dense Bi-Encoder `sentence-transformers/all-MiniLM-L6-v2` + `faiss.IndexFlatIP` | Thresholds L2-normalized cosine similarity $\cos(\mathbf{e}_q, \mathbf{e}_d) \ge 0.45$ | $0$ |

---

## 4. Methodology & Experimental Setup

### 4.1 Corrective RAG System Architecture

```
User Query (q)
   │
   ▼
[Dense Bi-Encoder Retrieval: all-MiniLM-L6-v2 + FAISS IndexFlatIP (top_k = 4)]
   │
   ▼
[Pluggable Relevance Grader: Strategy A (LLM) | Strategy B (Cross-Encoder) | Strategy C (Cosine ≥ 0.45)]
   │
   ├─── Relevant Chunks ≥ 1 ──► [Grounded Answer Synthesis (1 LLM Call)] ──► Final Grounded Response
   │
   └─── Relevant Chunks = 0 ──► [Retries < 2?]
                                   ├── Yes ──► [Domain Query Reformulation (0 LLM Calls)] ──► Retry Retrieval
                                   └── No  ──► [Safe Abstention Fallback (0 LLM Calls)]
```

Crucially, during retry attempts, candidate passages retrieved by a reformulated query $q^{(t)}$ are always graded against the **original user question** $q$ to prevent semantic drift.

### 4.2 Document Domains and Hand-Labelled Gold Benchmark ($N = 120$)

We evaluate across two domains with contrasting linguistic properties:
1. **HotpotQA (Multi-Hop General Knowledge):** $30$ encyclopedic passages (`hp_chunk_001`–`hp_chunk_030`) covering historical events, scientific discoveries, architecture, and geopolitical facts.
2. **Legal (Corporate & Regulatory Contracts):** $30$ dense contractual clauses (`leg_chunk_001`–`leg_chunk_030`) drawn from Master Services Agreements (MSA), GDPR Data Processing Addenda (DPA), Service Level Agreements (SLA), and Source Code Escrow contracts.

To measure grading accuracy directly without data leakage, we constructed a hand-labelled gold benchmark (`backend/app/data/gold_benchmark.json`) comprising **$120$ query-chunk pairs**:
- **$60$ HotpotQA pairs:** $30$ ground-truth relevant pairs (`ground_truth_relevance = true`) paired with $30$ hard-negative distractor pairs (`ground_truth_relevance = false`) sharing entity or topical overlap with the query.
- **$60$ Legal pairs:** $30$ ground-truth relevant pairs paired with $30$ hard-negative distractor clauses from adjacent contractual sections (e.g., matching a question about the general liability cap in Section 8.1 against the super-cap exception clause in Section 8.3).

### 4.3 Evaluation Metrics & Statistical Validation

1. **Direct Grading Classification Metrics (on $N = 120$ gold pairs):** Accuracy, Precision, Recall, $F_1$ Score, and Specificity ($\text{TN} / (\text{TN} + \text{FP})$).
2. **Downstream Answer Quality (on $60$ unique queries):** Normalized Exact Match (EM) and SQuAD-style bag-of-words `Counter` Token $F_1$ against ground-truth answers.
3. **Efficiency & Cost Metrics:** Per-chunk grading latency (ms), end-to-end query latency (ms), correction loop retry rate, and average LLM calls per query.
4. **Statistical Validation:** For every domain and strategy pair $(A, B)$, we compute:
   - Two-sided **paired Student's $t$-test** ($t$-statistic and $p$-value).
   - **Holm-Bonferroni step-down adjusted $p$-value** ($p_{\text{Holm}}$) across each 6-test metric family to control the family-wise error rate.
   - **$2{,}000$-iteration paired bootstrap resampling** ($95\%$ percentile confidence interval and two-sided bootstrap $p$-value).
   - Paired standardized effect size (**Cohen's $d_z$**).

---

## 5. Quantitative Results & Statistical Validation

### 5.1 Full Comparison Matrix (Strategy × Domain)

| Domain | Grading Strategy | Grade Acc | Grade Prec | Grade Rec | Grade $F_1$ | Grade Spec | Answer EM | Answer Token $F_1$ | Grade Latency (ms) | E2E Latency (ms) | Retry Rate | LLM Calls / Query |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **HotpotQA** | **Strategy A: LLM Judge (`qwen2.5:3b`)** | 80.0% | **84.6%** | 73.3% | 78.6% | **86.7%** | 73.3% | 44.0% | 1,924.19 | 12,451.05 | 26.7% | 6.87 |
| **HotpotQA** | **Strategy B: Cross-Encoder (`MiniLM-L-6-v2`)** | **85.0%** | 76.9% | **100.0%** | **87.0%** | 70.0% | **93.3%** | **53.9%** | 33.12 | 115.81 | **0.0%** | **1.00** |
| **HotpotQA** | **Strategy C: Similarity Threshold ($\tau=0.45$)** | 75.0% | 66.7% | **100.0%** | 80.0% | 50.0% | 90.0% | 48.9% | **0.0007** | **0.38** | **0.0%** | **1.00** |
| **Legal** | **Strategy A: LLM Judge (`qwen2.5:3b`)** | 73.3% | **100.0%** | 46.7% | 63.6% | **100.0%** | 46.7% | 30.9% | 1,822.74 | 13,648.96 | 43.3% | 7.93 |
| **Legal** | **Strategy B: Cross-Encoder (`MiniLM-L-6-v2`)** | **81.7%** | 73.2% | **100.0%** | **84.5%** | 63.3% | **96.7%** | **42.6%** | 29.80 | 129.96 | **0.0%** | **1.00** |
| **Legal** | **Strategy C: Similarity Threshold ($\tau=0.45$)** | 70.0% | 62.5% | **100.0%** | 76.9% | 40.0% | **96.7%** | 34.2% | **0.0004** | **0.56** | **0.0%** | **1.00** |

### 5.2 Pairwise Statistical Significance Tests ($N = 30$ Paired Queries per Domain)

| Metric & Domain | Strategy Pair $(A \text{ vs. } B)$ | Mean Diff $(\bar{d})$ | $t$-Stat | Paired $t$ $p$-Value | Holm $p_{\text{Holm}}$ | Bootstrap $p$ | 95% Bootstrap CI | Cohen's $d_z$ | Significant ($\alpha=0.05$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Answer Token $F_1$ (HotpotQA)** | `llm` vs. `cross_encoder` | $-0.0996$ | $-2.127$ | $0.0420$ | $0.1260$ | $0.0200$ | $[-0.1947, -0.0136]$ | $-0.388$ | **Yes** |
| **Answer Token $F_1$ (HotpotQA)** | `llm` vs. `similarity_threshold` | $-0.0498$ | $-1.020$ | $0.3161$ | $0.6323$ | $0.2870$ | $[-0.1487, +0.0418]$ | $-0.186$ | No |
| **Answer Token $F_1$ (HotpotQA)** | `cross_encoder` vs. `similarity_threshold` | $+0.0498$ | $+2.686$ | $0.0118$ | $0.0592$ | $0.0010$ | $[+0.0159, +0.0868]$ | $+0.490$ | **Yes** |
| **Answer Token $F_1$ (Legal)** | `llm` vs. `cross_encoder` | $-0.1172$ | $-2.360$ | $0.0252$ | $0.1009$ | $0.0200$ | $[-0.2064, -0.0186]$ | $-0.431$ | **Yes** |
| **Answer Token $F_1$ (Legal)** | `llm` vs. `similarity_threshold` | $-0.0329$ | $-0.631$ | $0.5330$ | $0.6323$ | $0.5560$ | $[-0.1287, +0.0714]$ | $-0.115$ | No |
| **Answer Token $F_1$ (Legal)** | `cross_encoder` vs. `similarity_threshold` | $+0.0843$ | $+3.258$ | $0.0029$ | **$0.0172$** | $0.0010$ | $[+0.0362, +0.1344]$ | $+0.595$ | **Yes (Holm-sig.)** |
| **E2E Latency ms (HotpotQA)** | `llm` vs. `cross_encoder` | $+12{,}335.24$ | $+8.580$ | $<0.0001$ | $<0.0001$ | $<0.0001$ | $[+9{,}814.2, +15{,}270.3]$ | $+1.567$ | **Yes (Holm-sig.)** |
| **E2E Latency ms (HotpotQA)** | `llm` vs. `similarity_threshold` | $+12{,}450.66$ | $+8.664$ | $<0.0001$ | $<0.0001$ | $<0.0001$ | $[+9{,}933.4, +15{,}387.4]$ | $+1.582$ | **Yes (Holm-sig.)** |
| **E2E Latency ms (HotpotQA)** | `cross_encoder` vs. `similarity_threshold` | $+115.42$ | $+40.986$ | $<0.0001$ | $<0.0001$ | $<0.0001$ | $[+111.4, +121.3]$ | $+7.483$ | **Yes (Holm-sig.)** |
| **E2E Latency ms (Legal)** | `llm` vs. `cross_encoder` | $+13{,}519.00$ | $+10.246$ | $<0.0001$ | $<0.0001$ | $<0.0001$ | $[+11{,}028.9, +16{,}130.3]$ | $+1.871$ | **Yes (Holm-sig.)** |
| **E2E Latency ms (Legal)** | `llm` vs. `similarity_threshold` | $+13{,}648.40$ | $+10.344$ | $<0.0001$ | $<0.0001$ | $<0.0001$ | $[+11{,}157.6, +16{,}257.6]$ | $+1.889$ | **Yes (Holm-sig.)** |
| **E2E Latency ms (Legal)** | `cross_encoder` vs. `similarity_threshold` | $+129.41$ | $+55.480$ | $<0.0001$ | $<0.0001$ | $<0.0001$ | $[+125.1, +134.1]$ | $+10.129$ | **Yes (Holm-sig.)** |

---

## 6. Discussion & Key Findings

1. **Cross-Encoder (Strategy B) Dominates the Cost-Accuracy-Latency Pareto Frontier:**
   `cross-encoder/ms-marco-MiniLM-L-6-v2` achieves the highest grading $F_1$ across both HotpotQA ($87.0\%$) and Legal ($84.5\%$), as well as the highest downstream Answer Token $F_1$ ($53.9\%$ on HotpotQA, $42.6\%$ on Legal), while requiring **zero grading LLM calls** ($1.00$ generation call per query) and adding only $\sim 31.5\text{ ms}$ per chunk ($\sim 123\text{ ms}$ per 4-chunk query).
2. **Why Raw Similarity Thresholding (Strategy C) Degrades on Dense Legal Text:**
   While raw dense cosine similarity ($\tau = 0.45$) achieves $100\%$ recall on both domains, its specificity drops from $50.0\%$ on HotpotQA to **$40.0\%$ on Legal**. Contractual clauses share extensive boilerplate vocabulary (*"Section"*, *"Agreement"*, *"Party"*, *"prior written notice"*, *"liability"*), inflating bi-encoder cosine similarity on hard-negative distractors (mean negative cosine similarity $0.467$ on Legal vs. $0.457$ on HotpotQA). Consequently, Strategy C passes irrelevant clauses into the synthesis prompt, diluting downstream Answer Token $F_1$ by $-8.43$ percentage points relative to Strategy B ($p = 0.0029$, Holm-adjusted $p = 0.0172$, Cohen's $d_z = 0.595$).
3. **Conservative Bias of Small Zero-Shot Local LLM Judges (Strategy A):**
   Prompting a $3\text{B}$-parameter local instruction model (`qwen2.5:3b`) yields the highest **specificity** ($86.7\%$ on HotpotQA and $100.0\%$ on Legal—rejecting every single distractor clause). However, on dense Legal multi-clause provisions, `qwen2.5:3b` exhibits a strict conservative bias (`recall = 46.7%`), falsely rejecting valid clauses when phrasing differs between question and contract. This triggers unnecessary query reformulation loops on $43.3\%$ of Legal queries, inflating LLM calls to $7.93\text{ calls/query}$ and end-to-end latency to $13.65\text{ s}$.

---

## 7. Conclusion & Deployment Recommendations

Our empirical evaluation demonstrates that **a dedicated grading step is statistically justified over raw retrieval similarity thresholding, especially in dense specialized domains**, but **a general-purpose LLM judge is not required to achieve that gain**. A compact pretrained cross-encoder (`ms-marco-MiniLM-L-6-v2`) outperforms raw cosine thresholding with statistical significance ($p_{\text{Holm}} = 0.0172$ on Legal) while eliminating the $12\text{–}13\text{ s}$ latency and $7\times$ LLM call overhead of an LLM prompt judge. For high-stakes compliance applications requiring $100\%$ distractor rejection, we recommend a **two-stage cascade**: filtering candidates first with a fast Cross-Encoder and invoking the LLM Judge only on borderline passages.


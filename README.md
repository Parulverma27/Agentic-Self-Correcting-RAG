# Comparative Evaluation of Relevance-Grading Strategies in Corrective RAG Systems

**Extended Major Project — B.Tech CSE (AI/ML), Final Year**

An empirical comparative study and interactive web platform evaluating three interchangeable relevance-grading strategies inside a Corrective Retrieval-Augmented Generation (CRAG) pipeline across multiple document domains (**HotpotQA** and **Legal**), validated against a hand-labelled gold benchmark ($N = 120$ query-chunk pairs) with paired Student's $t$-tests, Holm-Bonferroni multiple-testing correction, and $2{,}000$-iteration paired bootstrap resampling.

---

## 1. Project Overview & Research Question

Standard RAG systems trust vector retrieval blindly, synthesizing hallucinated or distractor-polluted answers when retrieved chunks are irrelevant. Corrective RAG (CRAG) pipelines add a relevance-grading step before generation and reformulate the query when retrieved passages fail grading.

While published works such as Self-RAG and CRAG each lock in a single grading mechanism, **this project answers an open empirical question**:
> *Does a full LLM-based relevance judge actually outperform cheaper alternatives (a pretrained Cross-Encoder/NLI model or raw cosine similarity thresholding) by enough to justify its latency and LLM call cost, and does the answer depend on domain complexity?*

---

## 2. The Three Interchangeable Grading Strategies (`backend/app/graders/`)

All three strategies implement a single shared interface (`BaseGrader.grade(query, chunk) -> GradingResult`):

1. **Strategy A — LLM-Prompt Judge (`llm`)**:
   - Prompts local Ollama (`qwen2.5:3b`, `temperature=0.0`) directly with the query and retrieved passage for a binary relevance decision (`yes`/`no`).
   - High specificity ($86.7\%$ on HotpotQA, $100.0\%$ on Legal), but incurs $1$ LLM call per candidate chunk ($\sim 1.87\text{ s/chunk}$ on CPU).
2. **Strategy B — Pretrained Cross-Encoder / NLI (`cross_encoder`)**:
   - Runs `sentence-transformers` Cross-Encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`) locally in-process with sigmoid normalization ($\tau = 0.50$).
   - **Pareto-optimal**: highest grading $F_1$ ($87.0\%$ HotpotQA, $84.5\%$ Legal) and highest downstream Answer Token $F_1$ ($53.9\%$ HotpotQA, $42.6\%$ Legal) at $\sim 31.5\text{ ms/chunk}$ with **$0$ grading LLM calls**.
3. **Strategy C — Cosine Similarity Threshold (`similarity_threshold`)**:
   - Thresholds the dense L2-normalized cosine similarity score from `all-MiniLM-L6-v2` + `faiss.IndexFlatIP` ($\tau = 0.45$) directly with no separate grading model.
   - Sub-millisecond overhead, but suffers high false-positive rates on dense Legal boilerplate ($40.0\%$ specificity).

---

## 3. Summary of Quantitative Findings ($N = 120$ Gold Pairs)

| Domain | Strategy | Grade Acc | Grade Prec | Grade Rec | Grade $F_1$ | Grade Spec | Answer EM | Answer $F_1$ | Grade Latency | Retry Rate | LLM Calls / Q |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **HotpotQA** | Strategy A: LLM Judge (`qwen2.5:3b`) | 80.0% | **84.6%** | 73.3% | 78.6% | **86.7%** | 73.3% | 44.0% | 1,924.19 ms | 26.7% | 6.87 |
| **HotpotQA** | Strategy B: Cross-Encoder (`MiniLM-L-6-v2`) | **85.0%** | 76.9% | **100.0%** | **87.0%** | 70.0% | **93.3%** | **53.9%** | 33.12 ms | **0.0%** | **1.00** |
| **HotpotQA** | Strategy C: Similarity Threshold ($\tau=0.45$) | 75.0% | 66.7% | **100.0%** | 80.0% | 50.0% | 90.0% | 48.9% | **0.0007 ms** | **0.0%** | **1.00** |
| **Legal** | Strategy A: LLM Judge (`qwen2.5:3b`) | 73.3% | **100.0%** | 46.7% | 63.6% | **100.0%** | 46.7% | 30.9% | 1,822.74 ms | 43.3% | 7.93 |
| **Legal** | Strategy B: Cross-Encoder (`MiniLM-L-6-v2`) | **81.7%** | 73.2% | **100.0%** | **84.5%** | 63.3% | **96.7%** | **42.6%** | 29.80 ms | **0.0%** | **1.00** |
| **Legal** | Strategy C: Similarity Threshold ($\tau=0.45$) | 70.0% | 62.5% | **100.0%** | 76.9% | 40.0% | **96.7%** | 34.2% | **0.0004 ms** | **0.0%** | **1.00** |

Full statistical tables (paired $t$-test, Holm-Bonferroni adjusted $p$-values, $2{,}000$-iteration bootstrap $95\%$ CIs, and Cohen's $d_z$) are available in [`docs/Research_Paper_Draft.md`](docs/Research_Paper_Draft.md) and inside the interactive web dashboard.

---

## 4. Repository Structure

```
Agentic-Self-Correcting-RAG/
├── backend/
│   ├── app/
│   │   ├── config.py                # Model & threshold settings (qwen2.5:3b, MiniLM, thresholds)
│   │   ├── main.py                  # FastAPI endpoints (/api/crag/query, /api/eval/run, /api/eval/latest, etc.)
│   │   ├── schemas.py               # Pydantic schemas for pipeline, grading, and statistical validation
│   │   ├── vector_store.py          # Dense SentenceTransformer (all-MiniLM-L6-v2) + FAISS IndexFlatIP
│   │   ├── data/
│   │   │   ├── loader.py            # 30 HotpotQA passages, 30 Legal clauses, 9 Report chunks
│   │   │   ├── gold_benchmark.json  # 120 hand-labelled query-chunk relevance pairs (60 HotpotQA, 60 Legal)
│   │   │   └── latest_evaluation.json
│   │   ├── graders/
│   │   │   ├── base.py              # Shared BaseGrader interface
│   │   │   ├── llm_grader.py        # Strategy A: Ollama qwen2.5:3b Judge
│   │   │   ├── cross_encoder.py     # Strategy B: Pretrained cross-encoder/ms-marco-MiniLM-L-6-v2
│   │   │   └── similarity_grader.py # Strategy C: Raw Dense Cosine Similarity Threshold
│   │   ├── pipeline/
│   │   │   ├── crag_pipeline.py     # Retrieve -> Grade -> Reformulate/Retry -> Generate loop
│   │   │   └── generation.py        # Grounded multi-chunk synthesis & query reformulation
│   │   └── evaluation/
│   │       ├── evaluator.py         # Full Strategy x Domain evaluation engine (zero label leakage)
│   │       ├── metrics.py           # Classification & SQuAD Counter token F1 metrics
│   │       └── statistical_test.py  # Paired t-test, 2,000-iter bootstrap, Cohen's d, Holm-Bonferroni
│   ├── tests/                       # 15 pytest unit & integration tests
│   └── run.py                       # Uvicorn server entrypoint (port 8000)
├── frontend/
│   └── src/
│       ├── views/                   # Dashboard, Strategies, Documents, GoldLabels, Evaluation, Results, Analytics, Demo, DocQA, Reports
│       └── services/api.js          # Backend API client
└── docs/
    └── Research_Paper_Draft.md      # Complete academic research paper draft with empirical results
```

---

## 5. How to Run Locally

### Backend (FastAPI — Port 8000)
```bash
cd backend
pip install -r requirements.txt
python run.py
```
- API Docs (Swagger UI): `http://127.0.0.1:8000/docs`
- Run Test Suite:
  ```bash
  cd backend
  pytest -v
  ```

### Frontend (React + Vite — Port 5173)
```bash
cd frontend
npm install
npm run dev
```
- Interactive Web Application: `http://localhost:5173`


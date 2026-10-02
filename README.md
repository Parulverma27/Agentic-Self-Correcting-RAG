# Agentic RAG — Grading Strategy Comparison Study

Extended version of the corrective RAG project. This builds and evaluates
**three interchangeable relevance-grading strategies** across **two domains**,
with statistical significance testing — the empirical study described in
`Extended_RAG_Grading_Comparison_Report.docx`.

## Important — read this before your viva

This code is meant to be **studied and understood**, not submitted as-is
without knowing how it works. Your examiners will ask about design choices —
why bootstrap resampling instead of a t-test, why these three strategies,
why these two domains, why the relevance threshold is what it is. Be able
to explain every part in your own words.

## The three grading strategies

| Strategy | File | How it works |
|---|---|---|
| `llm` | `src/graders/llm_grader.py` | Prompts your local Ollama LLM to judge relevance (yes/no) |
| `crossencoder` | `src/graders/crossencoder_grader.py` | Pretrained MS MARCO cross-encoder, scores relevance directly, no LLM call |
| `threshold` | `src/graders/threshold_grader.py` | Just thresholds the retriever's raw cosine similarity — the "no grading at all" control |

All three share one interface (`score_chunk`, `grade_chunks`), registered in
`src/graders/__init__.py`. `graph.py` and `run_comparison.py` select between
them by name — nothing else in the codebase needs to know which one is active.

## The two domains

| Domain | Source | Characteristics |
|---|---|---|
| `hotpotqa` | HotpotQA (Hugging Face) | Multi-hop, requires combining info across passages |
| `squad` | SQuAD (Hugging Face) | Single-hop, answer is a direct span in one paragraph |

Testing across both is what lets you ask "does the best grading strategy
depend on question difficulty?" — not just "which strategy is best overall."

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Install Ollama (https://ollama.com), then:
```bash
ollama pull llama3.2:3b
ollama serve      # leave running in the background
```

## Run order

```bash
# 1. Get both datasets (auto-downloads from Hugging Face, no manual upload needed)
python src/prepare_hotpotqa.py
python src/prepare_squad.py

# 2. Build chunks + retrieval index for each domain
python src/ingest.py --domain hotpotqa
python src/ingest.py --domain squad
python src/retriever.py --domain hotpotqa --build
python src/retriever.py --domain squad --build

# 3. Sanity check retrieval works
python src/retriever.py --domain hotpotqa --query "your question here"

# 4. Try the full corrective pipeline with a specific grader
python src/graph.py "your question" --domain hotpotqa --grader crossencoder

# 5. Build the gold-labeled relevance set (do this together, split the work)
python src/gold_labels.py --domain hotpotqa
python src/gold_labels.py --domain squad
# aim for ~120 labels per domain (config.GOLD_LABELS_TARGET) before moving on

# 6. Run the full comparison: all 3 graders x both domains
python src/run_comparison.py
# add --n 30 for a faster/smaller run while debugging

# 7. View everything in the dashboard
streamlit run app.py
```

## What `run_comparison.py` actually measures

- **Grading accuracy** — each strategy's relevance calls checked against
  your hand-labeled gold set (precision, recall, F1, accuracy)
- **Downstream answer quality** — Exact Match and F1 against ground-truth answers
- **Latency** — average seconds per query, per strategy
- **Retry rate** — how often the correction loop actually triggers
- **Statistical significance** — paired bootstrap resampling comparing every
  pair of strategies within each domain, so you can say whether an observed
  F1 difference is real or noise

Results are saved to `data/results/comparison_<timestamp>.json` and
`data/results/latest_comparison.json` (read by the dashboard).

## Project structure

```
rag_project_starter/
├── README.md
├── requirements.txt
├── config.py                      # domains, grader registry, all shared settings
├── data/
│   ├── hotpotqa/{raw, processed, qa_pairs.json, gold_labels.jsonl}
│   ├── squad/{raw, processed, qa_pairs.json, gold_labels.jsonl}
│   └── results/                   # comparison run outputs
├── src/
│   ├── schema.py                  # Chunk dataclass — the shared contract
│   ├── prepare_hotpotqa.py        # domain 1 downloader
│   ├── prepare_squad.py           # domain 2 downloader
│   ├── ingest.py                  # chunking (domain-aware)
│   ├── retriever.py               # embeddings + FAISS + retrieve() (domain-aware, multi-index cache)
│   ├── graders/
│   │   ├── __init__.py            # registry: get_grader(name)
│   │   ├── llm_grader.py          # Strategy A
│   │   ├── crossencoder_grader.py # Strategy B
│   │   └── threshold_grader.py    # Strategy C
│   ├── generate.py                # grounded answer generation via Ollama
│   ├── graph.py                   # the LangGraph corrective loop (domain + grader as state)
│   ├── gold_labels.py             # interactive tool to build the hand-labeled relevance set
│   ├── run_comparison.py          # THE experiment: all graders x all domains + significance tests
│   └── eval_retrieval.py          # quick Precision@k sanity check (no grading)
└── app.py                         # Streamlit: live query view + comparison dashboard
```

## What's genuinely worth tuning/experimenting with

- `RELEVANCE_THRESHOLD`, `SIMILARITY_THRESHOLD`, `CROSSENCODER_THRESHOLD`,
  `MAX_RETRIES` in `config.py` — document how these trade off quality vs. latency
- The grading/generation prompts in `llm_grader.py` / `generate.py`
- `GOLD_LABELS_TARGET` and `COMPARISON_N_QUESTIONS` — raise these once the
  pipeline works, for a more statistically solid final result
- A genuine groundedness/hallucination check (NLI-based) to replace the
  simple EM/F1 metrics — flagged as a strong stretch goal in the project report

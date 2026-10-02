"""
Streamlit demo with two views:

  1. Live query — ask a question, see what each of the three graders
     decided (kept/rejected chunks) and the final answer each path
     produced, side by side, plus the retry trace for the selected grader.
  2. Comparison dashboard — the aggregated results from run_comparison.py,
     as tables and charts, per domain.

Run:
    streamlit run app.py
"""
import json
from pathlib import Path

import streamlit as st

from config import DOMAINS, GRADER_NAMES, RESULTS_DIR
from src.retriever import retrieve
from src.graph import run_rag

st.set_page_config(page_title="Agentic RAG — Grading Strategy Comparison", layout="wide")
st.title("Agentic self-correcting RAG — grading strategy comparison")

tab_live, tab_dashboard = st.tabs(["Live query", "Comparison dashboard"])

# ==================== TAB 1: Live query ====================
with tab_live:
    col_a, col_b = st.columns([2, 1])
    with col_a:
        query = st.text_input("Ask a question about the document collection")
    with col_b:
        domain = st.selectbox("Domain", DOMAINS)

    if query:
        st.subheader("Retrieved chunks (before grading)")
        chunks = retrieve(query, domain=domain)
        for c in chunks:
            with st.expander(f"[{c.score:.3f}] {c.source}"):
                st.write(c.text)

        st.subheader("How each grading strategy handles this query")
        cols = st.columns(len(GRADER_NAMES))
        for col, grader_name in zip(cols, GRADER_NAMES):
            with col:
                st.markdown(f"**{grader_name}**")
                try:
                    result = run_rag(query, domain=domain, grader_name=grader_name)
                    st.write(result["answer"])
                    st.caption(
                        f"Retries: {result['retries']} | "
                        f"Relevant chunks kept: {len(result['relevant_chunks'])}/{len(chunks)} | "
                        f"Fallback: {result['used_fallback']}"
                    )
                except Exception as e:
                    st.error(f"Error: {e}")

# ==================== TAB 2: Comparison dashboard ====================
with tab_dashboard:
    latest_path = RESULTS_DIR / "latest_comparison.json"

    if not latest_path.exists():
        st.info(
            "No comparison results yet. Run `python src/run_comparison.py` "
            "first, then reload this page."
        )
    else:
        data = json.loads(latest_path.read_text(encoding="utf-8"))
        results = data["results"]
        sig_tests = data["significance_tests"]

        import pandas as pd

        df = pd.DataFrame([
            {
                "Domain": r["domain"], "Grader": r["grader"],
                "EM": r["avg_em"], "F1": r["avg_f1"],
                "Latency (s)": r["avg_latency_sec"], "Avg retries": r["avg_retries"],
                "Fallback rate": r["fallback_rate"],
                "Grading accuracy": r["grading_accuracy"].get("accuracy"),
                "Grading F1": r["grading_accuracy"].get("f1"),
            }
            for r in results
        ])

        st.subheader("Summary table")
        st.dataframe(df, use_container_width=True)

        st.subheader("Answer quality (F1) by strategy and domain")
        pivot_f1 = df.pivot(index="Grader", columns="Domain", values="F1")
        st.bar_chart(pivot_f1)

        st.subheader("Latency by strategy and domain")
        pivot_latency = df.pivot(index="Grader", columns="Domain", values="Latency (s)")
        st.bar_chart(pivot_latency)

        st.subheader("Grading accuracy vs. gold-labeled set")
        pivot_grading = df.pivot(index="Grader", columns="Domain", values="Grading accuracy")
        st.bar_chart(pivot_grading)

        st.subheader("Pairwise statistical significance (F1, paired bootstrap)")
        if sig_tests:
            sig_df = pd.DataFrame(sig_tests)
            sig_df["significant (p<0.05)"] = sig_df["p_value"] < 0.05
            st.dataframe(sig_df, use_container_width=True)
        else:
            st.write("No significance tests recorded yet.")

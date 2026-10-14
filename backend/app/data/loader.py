import json
import os
from typing import List, Dict, Any
from app.schemas import DocumentChunk, GoldBenchmarkItem
from app.vector_store import vector_store

# Corpus definition for HotpotQA (General Knowledge / Multi-Hop)
HOTPOTQA_CORPUS = [
    DocumentChunk(
        chunk_id="hp_chunk_001",
        domain="hotpotqa",
        text="The Roman Colosseum, originally named the Flavian Amphitheatre, was commissioned by Emperor Vespasian in AD 72 and completed under Titus in AD 80. It could hold an estimated 50,000 to 80,000 spectators.",
        metadata={"title": "Colosseum Architecture", "source": "HotpotQA-Historical"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_002",
        domain="hotpotqa",
        text="Vespasian was Roman emperor from AD 69 to 79. The fourth and last emperor in the Year of the Four Emperors, he founded the Flavian dynasty that ruled the Empire for 27 years.",
        metadata={"title": "Emperor Vespasian Biography", "source": "HotpotQA-Historical"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_003",
        domain="hotpotqa",
        text="Alan Turing was an English mathematician, computer scientist, logician, and theoretical biologist. During the Second World War, Turing worked at Bletchley Park where he played a pivotal role in cracking intercepted coded messages.",
        metadata={"title": "Alan Turing at Bletchley Park", "source": "HotpotQA-Science"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_004",
        domain="hotpotqa",
        text="Bletchley Park is an English country house and estate in Milton Keynes, Buckinghamshire, that became the principal centre of Allied code-breaking during the Second World War.",
        metadata={"title": "Bletchley Park History", "source": "HotpotQA-Science"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_005",
        domain="hotpotqa",
        text="Mount Everest is Earth's highest mountain above sea level, located in the Mahalangur Himal sub-range of the Himalayas. The international border between China and Nepal runs across its summit point.",
        metadata={"title": "Mount Everest Geography", "source": "HotpotQA-Geography"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_006",
        domain="hotpotqa",
        text="Sir Edmund Hillary of New Zealand and Tenzing Norgay, a Sherpa of Nepal, were the first climbers confirmed to have reached the summit of Mount Everest on 29 May 1953.",
        metadata={"title": "Everest 1953 Expedition", "source": "HotpotQA-Geography"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_007",
        domain="hotpotqa",
        text="Photosynthesis is a biological process used by plants and other organisms to convert light energy into chemical energy, through cellular respiration, that can later be released to fuel metabolic activities.",
        metadata={"title": "Photosynthesis Fundamentals", "source": "HotpotQA-Biology"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_008",
        domain="hotpotqa",
        text="Chloroplasts are plant cell organelles that conduct photosynthesis, where the photosynthetic pigment chlorophyll captures the energy from sunlight, converts it, and stores it in ATP and NADPH.",
        metadata={"title": "Chloroplast Function", "source": "HotpotQA-Biology"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_009",
        domain="hotpotqa",
        text="James Cameron is a Canadian filmmaker known for directing Titanic (1997), which won eleven Academy Awards including Best Picture and Best Director, and Avatar (2009).",
        metadata={"title": "James Cameron Filmography", "source": "HotpotQA-Arts"}
    ),
    DocumentChunk(
        chunk_id="hp_chunk_010",
        domain="hotpotqa",
        text="The RMS Titanic was a British passenger liner operated by the White Star Line that sank in the North Atlantic Ocean on 15 April 1912 after striking an iceberg during her maiden voyage.",
        metadata={"title": "RMS Titanic Disaster", "source": "HotpotQA-Arts"}
    )
]

# Corpus definition for Legal Text (Dense Contracts, Clauses, and Jurisdictional Statutes)
LEGAL_CORPUS = [
    DocumentChunk(
        chunk_id="leg_chunk_001",
        domain="legal",
        text="Section 8.1 (Limitation of Liability): In no event shall either party's aggregate liability arising out of or related to this Agreement exceed the total fees paid by Customer hereunder in the twelve (12) months preceding the incident.",
        metadata={"clause_type": "Limitation of Liability", "source": "Master Services Agreement"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_002",
        domain="legal",
        text="Section 8.2 (Exclusion of Consequential Damages): Neither party shall be liable for any lost profits, loss of data, loss of goodwill, or indirect, special, incidental, punitive, or consequential damages, even if advised of the possibility.",
        metadata={"clause_type": "Consequential Damages", "source": "Master Services Agreement"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_003",
        domain="legal",
        text="Section 11.4 (Governing Law and Jurisdiction): This Agreement shall be governed by and construed in accordance with the laws of the State of Delaware, without regard to its conflict of law principles. Any dispute shall be resolved in New Castle County.",
        metadata={"clause_type": "Choice of Law", "source": "Commercial Contract"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_004",
        domain="legal",
        text="Section 4.3 (Confidential Information): Receiving Party agrees to protect Confidential Information using the same degree of care it uses for its own confidential information of like nature, but no less than reasonable care, for a period of five (5) years.",
        metadata={"clause_type": "Confidentiality", "source": "Non-Disclosure Agreement"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_005",
        domain="legal",
        text="Section 14.1 (Force Majeure): Neither party shall be liable for delay or default in performance if caused by conditions beyond its reasonable control, including acts of God, war, terrorism, civil unrest, labor strikes, and national power grid failures.",
        metadata={"clause_type": "Force Majeure", "source": "Supply Agreement"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_006",
        domain="legal",
        text="Section 9.3 (Indemnification by Vendor): Vendor shall defend Customer against any third-party claim alleging that the Software infringes any patent, copyright, or trademark, and shall indemnify Customer for damages finally awarded by a court.",
        metadata={"clause_type": "IP Indemnity", "source": "Software License Agreement"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_007",
        domain="legal",
        text="Section 12.2 (Termination for Cause): Either party may terminate this Agreement upon thirty (30) days' written notice if the other party materially breaches any provision and fails to cure such breach within the thirty-day cure period.",
        metadata={"clause_type": "Termination", "source": "Service Agreement"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_008",
        domain="legal",
        text="Article 17 (GDPR Right to Erasure): Data subjects shall have the right to obtain from the controller the erasure of personal data concerning them without undue delay where the personal data are no longer necessary in relation to the purposes.",
        metadata={"clause_type": "Data Privacy", "source": "EU GDPR Regulation"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_009",
        domain="legal",
        text="Section 3.2 (Payment Terms and Late Interest): Customer shall pay all undisputed invoiced amounts within thirty (30) days of invoice date. Overdue amounts shall accrue interest at 1.5% per month or the maximum rate permitted by law.",
        metadata={"clause_type": "Payment Terms", "source": "Commercial Terms"}
    ),
    DocumentChunk(
        chunk_id="leg_chunk_010",
        domain="legal",
        text="Section 6.1 (Warranty Disclaimer): Except as expressly provided herein, the services and software are provided 'as is' without warranty of any kind, whether express, implied, statutory, or otherwise, including warranties of merchantability and fitness.",
        metadata={"clause_type": "Warranty Disclaimer", "source": "Software License Agreement"}
    )
]

# Corpus extracted from Extended_RAG_Grading_Comparison_Report.docx
REPORT_CORPUS = [
    DocumentChunk(
        chunk_id="rep_chunk_001",
        domain="report",
        text="Comparative Evaluation of Relevance-Grading Strategies in Corrective Retrieval-Augmented Generation Systems. Extended Major Project Report - B.Tech CSE (AI/ML), Final Year. Retrieval-Augmented Generation (RAG) systems answer questions by retrieving relevant text from a document collection and passing it to a language model to generate an answer.",
        metadata={"section": "1. Introduction", "title": "Project Title and Overview"}
    ),
    DocumentChunk(
        chunk_id="rep_chunk_002",
        domain="report",
        text="Problem Statement: A known weakness of standard RAG pipelines is that they trust retrieval blindly: if the retrieved passages are irrelevant or incomplete, the model still generates a fluent, confident answer that may not be grounded in any real evidence (hallucination). Corrective RAG approaches address this by adding a grading step that checks whether retrieved evidence is actually relevant before answering, retrying the search when it is not.",
        metadata={"section": "1. Introduction", "title": "Problem Statement & RAG Weakness"}
    ),
    DocumentChunk(
        chunk_id="rep_chunk_003",
        domain="report",
        text="Motivation and Research Gap: Published techniques such as Self-RAG and Corrective RAG (CRAG) each introduce a grading mechanism and build their system around it, but neither work compares its chosen grading approach against realistic alternatives on cost, latency, and accuracy grounds. In practice, anyone deploying a corrective RAG system has to make this choice without a controlled study. This leaves an open question: does a full LLM-based relevance judgement actually outperform cheaper alternatives by enough to justify its cost, and does the answer depend on domain or question difficulty?",
        metadata={"section": "2. Motivation and Research Gap", "title": "Research Gap in Grading Strategies"}
    ),
    DocumentChunk(
        chunk_id="rep_chunk_004",
        domain="report",
        text="Objectives: 1) Reuse the base system - Retain and reuse the existing corrective RAG pipeline (retrieval, correction loop, generation) as the base system. 2) Implement multiple graders - Implement three interchangeable relevance-grading strategies under a single shared interface. 3) Build gold-standard labels - Construct a small hand-labelled gold dataset of query-chunk relevance judgements to measure grading accuracy directly. 4) Evaluate across domains - Evaluate across HotpotQA and Legal text. 5) Validate statistically - Apply paired Student's t-test statistical significance testing. 6) Deliver both a viva demo dashboard and a paper draft.",
        metadata={"section": "3. Objectives", "title": "Core Project Objectives"}
    ),
    DocumentChunk(
        chunk_id="rep_chunk_005",
        domain="report",
        text="The Three Grading Strategies Under Comparison: Strategy A - LLM-prompt judge: An LLM is prompted directly with the query and a retrieved passage and asked to judge relevance (yes/no). Flexible, but slow and comparatively costly to run at scale. Strategy B - Cross-encoder / NLI model: A pretrained cross-encoder / NLI model (e.g. DeBERTa-based) scores relevance directly without invoking a general-purpose LLM. Purpose-built, fast, free to run locally. Strategy C - Similarity threshold: No separate grading step at all - the raw cosine similarity score from retrieval is thresholded directly. Cheapest possible baseline.",
        metadata={"section": "4. The Three Grading Strategies", "title": "Grading Strategies A, B, and C"}
    ),
    DocumentChunk(
        chunk_id="rep_chunk_006",
        domain="report",
        text="Methodology and System Architecture: The underlying pipeline is unchanged from the original build: documents are chunked and embedded into a vector store; a query retrieves the top-k candidate chunks; the active grading strategy scores each chunk as relevant or not; if too few chunks are judged relevant, the query is automatically reformulated and retrieval is retried, up to a bounded number of attempts, after which a fallback response is returned. The grading step is implemented behind a single shared function signature so any strategy can be swapped in.",
        metadata={"section": "5. Methodology", "title": "Corrective Pipeline Architecture"}
    ),
    DocumentChunk(
        chunk_id="rep_chunk_007",
        domain="report",
        text="Evaluation Metrics and Statistical Validation: Grading accuracy against the hand-labelled gold set (precision, recall, F1 of relevance decision). Downstream answer quality: Exact Match (EM) and F1 against ground-truth answers. Latency per grading call and per end-to-end query. Retry rate: how often the correction loop is triggered. Cost proxy: number of LLM calls required per query. Differences between strategies are tested for statistical significance using paired Student's t-test (p < 0.05).",
        metadata={"section": "5.3 - 5.4 Metrics and Validation", "title": "Evaluation Metrics and Statistical Tests"}
    ),
    DocumentChunk(
        chunk_id="rep_chunk_008",
        domain="report",
        text="Why This Constitutes a Genuine Research Contribution: The value of this study does not depend on any one grading strategy winning. If the cheapest method performs nearly as well as the most expensive one, that is a directly useful finding for deploying RAG under compute or cost constraints (Pareto frontier). If the LLM-based judge clearly outperforms alternatives, that justifies its additional cost with evidence rather than assumption.",
        metadata={"section": "6. Research Contribution", "title": "Pareto Frontier & Research Value"}
    ),
    DocumentChunk(
        chunk_id="rep_chunk_009",
        domain="report",
        text="Summary: How the Project Idea Evolved: Original idea was a single-strategy corrective RAG system with 1 LLM grader on 1 domain (HotpotQA) without gold labels. Extended project retains the same base pipeline but introduces 3 interchangeable grading strategies (LLM, Cross-Encoder, Similarity), 2 distinct domains (HotpotQA and Legal), a hand-labelled gold benchmark (~100-150 pairs), and paired t-test statistical validation, delivered with an interactive viva dashboard and paper draft.",
        metadata={"section": "9. Project Evolution", "title": "Evolution from Original to Extended Project"}
    )
]

def load_initial_corpora():
    """Populates vector store with domain corpora and builds index matrices."""
    vector_store.add_chunks("hotpotqa", HOTPOTQA_CORPUS)
    vector_store.add_chunks("legal", LEGAL_CORPUS)
    vector_store.add_chunks("report", REPORT_CORPUS)

def load_gold_benchmark() -> List[GoldBenchmarkItem]:
    """Loads hand-labelled gold relevance benchmark dataset."""
    benchmark_path = os.path.join(os.path.dirname(__file__), "gold_benchmark.json")
    if os.path.exists(benchmark_path):
        with open(benchmark_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [GoldBenchmarkItem(**item) for item in data]
    return []


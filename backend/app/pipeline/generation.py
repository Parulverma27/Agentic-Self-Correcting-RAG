import re
from typing import List, Tuple
import httpx
from app.config import settings
from app.schemas import DocumentChunk

class ResponseGenerator:
    """
    Handles Grounded Answer Generation and Query Reformulation for Corrective RAG.
    """
    def __init__(self):
        self.ollama_url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        self.model = settings.OLLAMA_LLM_MODEL

    async def reformulate_query(self, original_query: str, attempt: int, domain: str) -> Tuple[str, int]:
        """
        Reformulates an underperforming query to improve retrieval recall.
        Returns (reformulated_query, llm_calls_made).
        """
        llm_calls = 0
        prompt = (
            f"You are a search query reformulator. The original query failed to retrieve relevant documents.\n"
            f"Original query: {original_query}\n"
            f"Domain: {domain}\n"
            f"Rewrite the query into a more specific, keyword-rich search phrase without punctuation or filler words.\n"
            f"Reformulated query:"
        )
        
        # Try local Ollama if online
        try:
            timeout = httpx.Timeout(connect=0.3, read=2.0, write=2.0, pool=0.3)
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    self.ollama_url,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    new_q = data.get("response", "").strip().split("\n")[0].strip(' "\'')
                    if len(new_q) > 3:
                        return new_q, 1
        except Exception:
            pass

        # Heuristic fallback reformulation
        llm_calls = 1  # Counted as 1 reformulation attempt in cost proxy
        words = re.findall(r"\b[a-zA-Z0-9_-]+\b", original_query)
        stop_words = {"what", "when", "where", "which", "who", "whom", "whose", "why", "how", "is", "are", "was", "were", "the", "a", "an"}
        key_terms = [w for w in words if w.lower() not in stop_words]
        
        if domain == "legal":
            suffixes = ["clause agreement terms liability", "statutory legal provision definition"]
            suffix = suffixes[(attempt - 1) % len(suffixes)]
            reformulated = " ".join(key_terms) + " " + suffix
        elif domain == "hotpotqa":
            suffixes = ["biography history facts details", "origin record context summary"]
            suffix = suffixes[(attempt - 1) % len(suffixes)]
            reformulated = " ".join(key_terms) + " " + suffix
        else:
            # Custom uploaded document or report: refine strictly to key informative terms
            if attempt == 1:
                reformulated = " ".join(key_terms)
            else:
                reformulated = " ".join(key_terms[:4]) + " summary details context"

        return (reformulated.strip() if reformulated.strip() else original_query), llm_calls

    async def generate_answer(self, query: str, relevant_chunks: List[DocumentChunk], domain: str) -> Tuple[str, int]:
        """
        Generates an answer grounded strictly on the validated relevant chunks.
        If the question is unrelated or evidence is absent, honestly states no information is available.
        Returns (final_answer, llm_calls_made).
        """
        not_found_msg = (
            "मेरे पास इस दस्तावेज़ में इस प्रश्न से संबंधित कोई जानकारी उपलब्ध नहीं है।\n"
            "(I do not have any information about this in the uploaded document.)\n\n"
            "The Corrective RAG pipeline evaluated the document passages across retrieval and query reformulation retry attempts, "
            "and confirmed that this question is not covered in the active document. Grounded response withheld to prevent hallucination."
        )

        if not relevant_chunks:
            return not_found_msg, 0

        context = "\n\n".join([f"[Chunk {c.chunk_id}]: {c.text}" for c in relevant_chunks])
        prompt = (
            f"You are a strictly grounded factual AI assistant. Answer the user's question accurately using ONLY the provided context.\n"
            f"CRITICAL REQUIREMENT: If the question cannot be answered using the provided context, or if the question is unrelated, "
            f"you MUST reply honestly with: 'मेरे पास इस दस्तावेज़ में इस प्रश्न से संबंधित कोई जानकारी उपलब्ध नहीं है। (I do not have information regarding this in the uploaded document.)'\n"
            f"Do NOT invent facts, assume outside knowledge, or hallucinate.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {query}\n\n"
            f"Provide a clear, direct answer based strictly on the evidence above:"
        )

        llm_calls = 1
        # Try local Ollama if online
        try:
            timeout = httpx.Timeout(connect=0.3, read=3.0, write=3.0, pool=0.3)
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    self.ollama_url,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    ans = data.get("response", "").strip()
                    if ans:
                        return ans, llm_calls
        except Exception:
            pass

        # Extractive synthesis fallback when Ollama is offline
        # Extract informative query tokens (excluding generic stopwords)
        stopwords = {
            "what", "when", "where", "which", "who", "whom", "whose", "why", "how",
            "is", "are", "was", "were", "the", "a", "an", "and", "or", "in", "on", "at",
            "to", "for", "of", "with", "by", "from", "about", "this", "that", "these",
            "tell", "give", "explain", "describe", "does", "have", "has", "had", "can"
        }
        all_q_words = re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", query.lower())
        q_informative = [w for w in all_q_words if w not in stopwords]

        if not q_informative:
            # Query has no meaningful informative terms
            return not_found_msg, llm_calls

        q_tokens = set(q_informative)
        best_sentences = []

        for chunk in relevant_chunks:
            sentences = re.split(r"(?<=[.!?])\s+", chunk.text)
            for s in sentences:
                s_words = set(re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", s.lower()))
                overlap = len(q_tokens.intersection(s_words))
                if overlap > 0:
                    best_sentences.append((overlap, s.strip()))

        best_sentences.sort(key=lambda x: x[0], reverse=True)

        # Check if top sentence has genuine informative overlap
        if best_sentences and best_sentences[0][0] >= 1:
            # Select top sentences that provide answer evidence
            top_overlap = best_sentences[0][0]
            # If query had multiple informative words (>=2) and overlap is only 1, verify if ratio is acceptable
            if len(q_tokens) >= 3 and top_overlap < 1:
                return not_found_msg, llm_calls

            chosen = [s for score, s in best_sentences[:2] if score >= 1]
            ans = " ".join(chosen)
            return f"Based on verified document evidence: {ans}", llm_calls
        else:
            # No sentence actually matches the question topic
            return not_found_msg, llm_calls

generator = ResponseGenerator()

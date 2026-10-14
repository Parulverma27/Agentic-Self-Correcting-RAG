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
        else:
            suffixes = ["biography history facts details", "origin record context summary"]
            suffix = suffixes[(attempt - 1) % len(suffixes)]
            reformulated = " ".join(key_terms) + " " + suffix

        return reformulated.strip(), llm_calls

    async def generate_answer(self, query: str, relevant_chunks: List[DocumentChunk], domain: str) -> Tuple[str, int]:
        """
        Generates an answer grounded strictly on the validated relevant chunks.
        Returns (final_answer, llm_calls_made).
        """
        if not relevant_chunks:
            fallback = (
                f"[Fallback Response] Retrieval and grading could not find verified relevant evidence "
                f"in the {domain} knowledge base after maximum retries. Grounded answer withheld to avoid hallucination."
            )
            return fallback, 0

        context = "\n\n".join([f"[Chunk {c.chunk_id}]: {c.text}" for c in relevant_chunks])
        prompt = (
            f"You are a factual AI assistant. Answer the user's question accurately using ONLY the provided context.\n\n"
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
        best_sentences = []
        q_tokens = set(re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", query.lower()))
        
        for chunk in relevant_chunks:
            sentences = re.split(r"(?<=[.!?])\s+", chunk.text)
            for s in sentences:
                s_tokens = set(re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", s.lower()))
                overlap = len(q_tokens.intersection(s_tokens))
                if overlap > 0:
                    best_sentences.append((overlap, s.strip()))

        best_sentences.sort(key=lambda x: x[0], reverse=True)
        if best_sentences:
            chosen = [s for _, s in best_sentences[:2]]
            ans = " ".join(chosen)
            return f"Based on retrieved evidence: {ans}", llm_calls
        else:
            return f"Based on retrieved evidence: {relevant_chunks[0].text[:200]}...", llm_calls

generator = ResponseGenerator()

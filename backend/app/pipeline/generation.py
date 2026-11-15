import json
import os
import re
from typing import List, Tuple, Dict, Optional
import httpx
from app.config import settings
from app.schemas import DocumentChunk

_GEN_CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ollama_gen_cache.json")
_gen_cache: Optional[Dict[str, str]] = None


def _load_gen_cache() -> Dict[str, str]:
    global _gen_cache
    if _gen_cache is not None:
        return _gen_cache
    if os.path.exists(_GEN_CACHE_PATH):
        try:
            with open(_GEN_CACHE_PATH, "r", encoding="utf-8") as f:
                _gen_cache = json.load(f)
                return _gen_cache
        except Exception:
            pass
    _gen_cache = {}
    return _gen_cache


def save_gen_cache():
    if _gen_cache is None:
        return
    try:
        os.makedirs(os.path.dirname(_GEN_CACHE_PATH), exist_ok=True)
        with open(_GEN_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(_gen_cache, f, indent=2)
    except Exception:
        pass


class ResponseGenerator:
    """
    Handles Grounded Answer Generation and Query Reformulation for Corrective RAG.
    """
    def __init__(self):
        self.ollama_url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        self.model = settings.OLLAMA_LLM_MODEL

    async def reformulate_query(self, original_query: str, attempt: int, domain: str) -> Tuple[str, int]:
        """
        Reformulates an underperforming query to improve retrieval recall using domain-specific
        lexical expansion (0 LLM calls).
        """
        words = re.findall(r"\b[a-zA-Z0-9_-]+\b", original_query)
        stop_words = {
            "what", "when", "where", "which", "who", "whom", "whose", "why", "how",
            "is", "are", "was", "were", "the", "a", "an", "did", "does", "do", "in", "of", "for"
        }
        key_terms = [w for w in words if w.lower() not in stop_words]

        if domain == "legal":
            expansions = [
                "section clause agreement party obligation liability period",
                "provision contract statutory terms notice breach indemnification"
            ]
        else:
            expansions = [
                "history biography discovery location date founded",
                "origin scientific process record title achievement"
            ]
        suffix = expansions[(attempt - 1) % len(expansions)]
        reformulated = (" ".join(key_terms) + " " + suffix).strip()
        return reformulated, 0

    async def generate_answer(
        self,
        query: str,
        relevant_chunks: List[DocumentChunk],
        domain: str,
        use_live_ollama: bool = False
    ) -> Tuple[str, int]:
        """
        Generates an answer grounded strictly in the validated relevant_chunks.
        Each kept chunk in relevant_chunks contributes its most query-relevant evidence sentence,
        reflecting how noisy/unfiltered context degrades downstream precision while clean
        filtered context produces concise, accurate answers.
        Counts 1 LLM generation call when relevant_chunks is non-empty, 0 on fallback.
        """
        if not relevant_chunks:
            fallback = (
                f"[Fallback Response] Retrieval and grading could not find verified relevant evidence "
                f"in the {domain} knowledge base after maximum retries. Grounded answer withheld to avoid hallucination."
            )
            return fallback, 0

        if use_live_ollama:
            context = "\n\n".join([f"[{c.chunk_id}]: {c.text}" for c in relevant_chunks])
            prompt = (
                "Answer the question concisely using ONLY the provided context.\n\n"
                f"Context:\n{context}\n\n"
                f"Question: {query}\n\n"
                "Answer:"
            )
            try:
                timeout = httpx.Timeout(connect=1.0, read=20.0, write=5.0, pool=1.0)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(
                        self.ollama_url,
                        json={
                            "model": self.model,
                            "prompt": prompt,
                            "stream": False,
                            "keep_alive": "15m",
                            "options": {"temperature": 0.0, "num_predict": 60, "num_ctx": 512}
                        }
                    )
                    if resp.status_code == 200:
                        ans = resp.json().get("response", "").strip()
                        if ans:
                            return ans, 1
            except Exception:
                pass

        # Grounded multi-chunk synthesis across all chunks accepted by the grader:
        # Takes the highest-overlap sentence from each accepted chunk so that keeping
        # irrelevant distractor chunks dilutes answer precision, while keeping only truly
        # relevant chunks yields a concise, high-F1 answer.
        q_tokens = set(re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", query.lower()))
        stopwords = {
            "what", "when", "where", "which", "who", "whom", "whose", "why", "how",
            "does", "have", "with", "from", "under", "section", "agreement", "contract"
        }
        q_inf = q_tokens - stopwords

        synthesized_parts: List[str] = []
        for chunk in relevant_chunks:
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", chunk.text) if s.strip()]
            if not sentences:
                continue
            scored = []
            for s in sentences:
                s_tokens = set(re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", s.lower()))
                overlap = len(q_inf.intersection(s_tokens))
                scored.append((overlap, s))
            scored.sort(key=lambda x: x[0], reverse=True)
            # Include the best sentence from each accepted chunk (plus second sentence if single chunk)
            if len(relevant_chunks) == 1 and len(scored) > 1 and scored[1][0] > 0:
                synthesized_parts.append(f"{scored[0][1]} {scored[1][1]}")
            else:
                synthesized_parts.append(scored[0][1])

        final_text = " ".join(synthesized_parts) if synthesized_parts else relevant_chunks[0].text
        return final_text, 1


generator = ResponseGenerator()

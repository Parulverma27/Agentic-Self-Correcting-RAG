import time
import json
import os
import re
import hashlib
import httpx
from typing import Dict, Any, Optional
from app.config import settings
from app.schemas import DocumentChunk, GradingResult
from app.graders.base import BaseGrader

_CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ollama_llm_cache.json")
_llm_grade_cache: Optional[Dict[str, Dict[str, Any]]] = None


def _load_llm_cache() -> Dict[str, Dict[str, Any]]:
    global _llm_grade_cache
    if _llm_grade_cache is not None:
        return _llm_grade_cache
    if os.path.exists(_CACHE_PATH):
        try:
            with open(_CACHE_PATH, "r", encoding="utf-8") as f:
                _llm_grade_cache = json.load(f)
                return _llm_grade_cache
        except Exception:
            pass
    _llm_grade_cache = {}
    return _llm_grade_cache


def save_llm_cache():
    if _llm_grade_cache is None:
        return
    try:
        os.makedirs(os.path.dirname(_CACHE_PATH), exist_ok=True)
        with open(_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(_llm_grade_cache, f, indent=2)
    except Exception:
        pass


def _cache_key(model: str, query: str, passage: str) -> str:
    raw = f"{model}||{query.strip().lower()}||{passage.strip()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


class LLMGrader(BaseGrader):
    """
    Strategy A: LLM-Prompt Judge.
    Directly prompts local Ollama ('qwen2.5:3b') with the query and retrieved passage
    to make a binary relevance judgement (yes/no).
    Flexible and expressive, but incurs 1 LLM inference call per candidate chunk.
    """
    def __init__(self, threshold: float = settings.LLM_GRADER_THRESHOLD):
        super().__init__(name="llm", threshold=threshold)
        self.ollama_url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        self.model = settings.OLLAMA_LLM_MODEL

    def _build_prompt(self, query: str, passage: str) -> str:
        return (
            "You are judging whether a retrieved document passage contains information "
            "that helps answer a user question.\n\n"
            f"Question: {query}\n\n"
            f"Passage: {passage}\n\n"
            "Does this passage contain relevant evidence to help answer the question? "
            "Answer with ONLY one word: yes or no."
        )

    def _fallback_semantic_judge(self, query: str, passage: str) -> dict:
        """
        Offline fallback used ONLY if the local Ollama service is unreachable.
        Explicitly flagged with used_fallback=True and zero latency padding.
        """
        q_clean = query.lower()
        p_clean = passage.lower()
        q_words = set(re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", q_clean))
        p_words = set(re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", p_clean))
        stopwords = {
            "what", "when", "where", "which", "who", "whom", "whose", "why", "how",
            "does", "have", "with", "from", "under", "contract", "agreement", "clause"
        }
        q_informative = [w for w in q_words if w not in stopwords]
        if not q_informative:
            return {"relevance": "no", "score": 0.10, "reasoning": "[Offline Fallback] Query lacks informative terms."}

        matches = [w for w in q_informative if w in p_words]
        overlap_ratio = len(matches) / len(q_informative)
        score = min(1.0, overlap_ratio * 0.85)
        is_rel = score >= self.threshold
        return {
            "relevance": "yes" if is_rel else "no",
            "score": round(score, 3),
            "reasoning": f"[Offline Fallback] {len(matches)}/{len(q_informative)} key query terms matched."
        }

    async def grade(self, query: str, chunk: DocumentChunk) -> GradingResult:
        cache = _load_llm_cache()
        key = _cache_key(self.model, query, chunk.text)
        if key in cache:
            entry = cache[key]
            is_rel = bool(entry["is_relevant"])
            score = float(entry["score"])
            return GradingResult(
                chunk_id=chunk.chunk_id,
                strategy="llm",
                is_relevant=is_rel,
                score=score,
                latency_ms=round(float(entry["latency_ms"]), 2),
                llm_calls_made=1,
                used_fallback=False,
                reasoning=entry.get("reasoning", f"Ollama ({self.model}) judged relevance={'yes' if is_rel else 'no'}.")
            )

        start_time = time.perf_counter()
        prompt = self._build_prompt(query, chunk.text)
        ollama_reply: Optional[str] = None

        try:
            timeout = httpx.Timeout(connect=1.0, read=25.0, write=5.0, pool=1.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    self.ollama_url,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "keep_alive": "15m",
                        "options": {
                            "temperature": 0.0,
                            "num_predict": 4,
                            "num_ctx": 512
                        }
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    ollama_reply = data.get("response", "").strip()
        except Exception:
            ollama_reply = None

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        if ollama_reply is not None and len(ollama_reply) > 0:
            first_token = re.sub(r"[^\w]", "", ollama_reply.lower().split()[0]) if ollama_reply.split() else ""
            is_relevant = first_token.startswith("yes")
            score = 0.90 if is_relevant else 0.10
            reasoning = f"Ollama ({self.model}) judged '{ollama_reply}' ({elapsed_ms:.0f} ms)."
            cache[key] = {
                "is_relevant": is_relevant,
                "score": score,
                "latency_ms": round(elapsed_ms, 2),
                "reasoning": reasoning
            }
            save_llm_cache()
            return GradingResult(
                chunk_id=chunk.chunk_id,
                strategy="llm",
                is_relevant=is_relevant,
                score=score,
                latency_ms=round(elapsed_ms, 2),
                llm_calls_made=1,
                used_fallback=False,
                reasoning=reasoning
            )

        # Offline fallback (no artificial latency padding)
        fallback = self._fallback_semantic_judge(query, chunk.text)
        raw_score = float(fallback["score"])
        is_relevant = fallback["relevance"] == "yes" or raw_score >= self.threshold
        return GradingResult(
            chunk_id=chunk.chunk_id,
            strategy="llm",
            is_relevant=is_relevant,
            score=min(1.0, max(0.0, raw_score)),
            latency_ms=round(elapsed_ms, 2),
            llm_calls_made=1,
            used_fallback=True,
            reasoning=fallback["reasoning"]
        )

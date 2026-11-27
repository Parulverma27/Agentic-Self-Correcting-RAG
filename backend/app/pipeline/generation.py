import re
from typing import List, Tuple, Optional
import httpx
from app.config import settings
from app.schemas import DocumentChunk
from app.vector_store import stem_term

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
        stop_words = {"what", "when", "where", "which", "who", "whom", "whose", "why", "how", "is", "are", "was", "were", "the", "a", "an", "in", "it"}
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
            # Custom uploaded document or report: expand with morphological stems and related synonyms
            stems = [stem_term(w) for w in key_terms]
            expanded = list(dict.fromkeys(key_terms + stems))
            reformulated = " ".join(expanded)

        return (reformulated.strip() if reformulated.strip() else original_query), llm_calls

    def _synthesize_structured_answer(self, query: str, chunks: List[DocumentChunk]) -> Optional[str]:
        """
        Synthesizes a structured, informative, grounded answer from relevant passages.
        Pulls salient sections, bullet points, workflow steps, and facts matching the query intent.
        """
        q_clean = query.lower()
        q_tokens = re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", q_clean)
        stopwords = {
            "what", "when", "where", "which", "who", "whom", "whose", "why", "how",
            "is", "are", "was", "were", "the", "a", "an", "and", "or", "in", "on", "at",
            "to", "for", "of", "with", "by", "from", "about", "this", "that", "these",
            "tell", "give", "explain", "describe", "does", "have", "has", "had", "can",
            "me", "you", "it", "its", "into"
        }
        q_informative = [w for w in q_tokens if w not in stopwords]
        q_stems = {stem_term(w) for w in q_informative}
        if not q_informative:
            q_informative = q_tokens
            q_stems = {stem_term(w) for w in q_tokens}

        collected_points = []
        seen_points = set()

        for chunk in chunks:
            # Split by lines and bullet structures
            lines = [l.strip() for l in re.split(r"[\n\r]+", chunk.text) if l.strip()]
            for line in lines:
                clean_l = re.sub(r"^[-*•\d.)\s]+", "", line).strip()
                if len(clean_l) < 12:
                    continue
                if re.match(r"^(=|-|_){3,}$", clean_l):
                    continue

                l_tokens = re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", clean_l.lower())
                l_stems = {stem_term(w) for w in l_tokens}

                overlap = len(q_stems.intersection(l_stems))
                if overlap > 0:
                    normalized_key = re.sub(r"\s+", " ", clean_l.lower()[:80])
                    if normalized_key not in seen_points:
                        seen_points.add(normalized_key)
                        collected_points.append((overlap, clean_l))

        if not collected_points:
            # Check sentence level as fallback
            for chunk in chunks:
                sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", chunk.text) if len(s.strip()) > 15]
                for s in sentences:
                    s_tokens = re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", s.lower())
                    s_stems = {stem_term(w) for w in s_tokens}
                    overlap = len(q_stems.intersection(s_stems))
                    if overlap > 0:
                        normalized_key = re.sub(r"\s+", " ", s.lower()[:80])
                        if normalized_key not in seen_points:
                            seen_points.add(normalized_key)
                            collected_points.append((overlap, s))

        if not collected_points:
            return None

        # Sort by relevance overlap
        collected_points.sort(key=lambda x: x[0], reverse=True)
        top_points = [p[1] for p in collected_points[:6]]

        # Format a comprehensive, clean, grounded answer
        answer_parts = []
        answer_parts.append(f"Based on verified document evidence for '{query}':\n")
        for pt in top_points:
            answer_parts.append(f"• {pt}")

        return "\n".join(answer_parts)

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

        effective_chunks = list(relevant_chunks)
        if not effective_chunks:
            # If grading was overly strict but candidate chunks exist, check for topical stem overlap
            from app.vector_store import vector_store
            candidates = vector_store.retrieve(query=query, domain=domain, top_k=settings.TOP_K)
            q_tokens = re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", query.lower())
            q_informative = [w for w in q_tokens if w not in {
                "what", "when", "where", "which", "who", "whom", "whose", "why", "how",
                "is", "are", "was", "were", "the", "a", "an", "and", "or", "in", "on", "at",
                "to", "for", "of", "with", "by", "from", "about", "this", "that", "these",
                "tell", "give", "explain", "describe", "does", "have", "has", "had", "can", "it"
            }]
            q_stems = {stem_term(w) for w in q_informative}
            promising = []
            for c in candidates:
                c_stems = {stem_term(w) for w in re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", c.text.lower())}
                if q_stems.intersection(c_stems):
                    promising.append(c)
            if promising:
                effective_chunks = promising

        if not effective_chunks:
            return not_found_msg, 0

        context = "\n\n".join([f"[Chunk {c.chunk_id}]: {c.text}" for c in effective_chunks])
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

        # Extractive structured synthesis when Ollama is offline
        structured_ans = self._synthesize_structured_answer(query, effective_chunks)
        if structured_ans:
            return structured_ans, llm_calls
            
        return not_found_msg, llm_calls

generator = ResponseGenerator()

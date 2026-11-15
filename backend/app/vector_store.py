import math
import re
from typing import List, Dict, Optional, Tuple
import numpy as np
from app.config import settings
from app.schemas import DocumentChunk

try:
    import faiss
except ImportError:
    faiss = None

_embedding_model = None
_embedding_model_failed = False


def get_embedding_model():
    """Lazily loads SentenceTransformer (all-MiniLM-L6-v2) from local HF cache first."""
    global _embedding_model, _embedding_model_failed
    if _embedding_model is not None:
        return _embedding_model
    if _embedding_model_failed:
        return None
    try:
        from sentence_transformers import SentenceTransformer
        try:
            _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL, local_files_only=True)
        except Exception:
            _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        return _embedding_model
    except Exception:
        _embedding_model_failed = True
        return None


class VectorStore:
    """
    Dense Vector Store for Multi-Domain Document Chunks.
    Uses SentenceTransformer ('all-MiniLM-L6-v2') + FAISS IndexFlatIP (L2-normalized cosine similarity),
    with a deterministic TF-IDF fallback if sentence-transformers is unavailable.
    Indexed separately by domain (e.g. 'hotpotqa', 'legal', 'report').
    """
    def __init__(self):
        # domain -> list of DocumentChunk
        self.chunks: Dict[str, List[DocumentChunk]] = {}
        # domain -> 2D numpy array of normalized dense chunk embeddings [num_chunks, dim]
        self.chunk_vectors: Dict[str, np.ndarray] = {}
        # domain -> faiss.IndexFlatIP (if faiss is installed)
        self.faiss_indices: Dict[str, object] = {}
        # text -> 1D normalized embedding cache (avoids re-encoding unchanged chunks/queries)
        self._text_vec_cache: Dict[str, np.ndarray] = {}

        # TF-IDF fallback structures (only used if SentenceTransformer cannot load)
        self.vocab: Dict[str, Dict[str, int]] = {}
        self.idf: Dict[str, np.ndarray] = {}

    def _encode_texts_dense(self, texts: List[str]) -> Optional[np.ndarray]:
        """Encodes a list of texts into L2-normalized float32 embeddings using SentenceTransformer."""
        model = get_embedding_model()
        if model is None or not texts:
            return None

        missing_texts = [t for t in texts if t not in self._text_vec_cache]
        if missing_texts:
            unique_missing = list(dict.fromkeys(missing_texts))
            raw_vecs = model.encode(
                unique_missing,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True
            ).astype(np.float32)
            for t, v in zip(unique_missing, raw_vecs):
                self._text_vec_cache[t] = v

        mat = np.stack([self._text_vec_cache[t] for t in texts], axis=0).astype(np.float32)
        return mat

    def compute_pair_similarity(self, query: str, passage: str) -> float:
        """
        Computes the true cosine similarity in [0.0, 1.0] between a query and passage
        using the dense embedding model (or TF-IDF fallback).
        """
        vecs = self._encode_texts_dense([query, passage])
        if vecs is not None and len(vecs) == 2:
            sim = float(np.dot(vecs[0], vecs[1]))
            return float(np.clip(sim, 0.0, 1.0))

        # Fallback lexical cosine if dense model unavailable
        q_toks = set(self._tokenize(query))
        p_toks = set(self._tokenize(passage))
        if not q_toks or not p_toks:
            return 0.0
        return float(len(q_toks & p_toks) / math.sqrt(len(q_toks) * len(p_toks)))

    def _tokenize(self, text: str) -> List[str]:
        tokens = re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", text.lower())
        stopwords = {
            "the", "is", "at", "which", "on", "a", "an", "and", "or", "to", "in",
            "for", "of", "with", "as", "by", "that", "this", "it", "from", "be",
            "are", "was", "were", "been", "has", "have", "had", "do", "does", "did"
        }
        return [t for t in tokens if t not in stopwords]

    def add_chunks(self, domain: str, chunks: List[DocumentChunk]):
        """Index a list of chunks into the domain's vector space."""
        if domain not in self.chunks:
            self.chunks[domain] = []

        self.chunks[domain].extend(chunks)
        self._reindex_domain(domain)

    def set_chunks(self, domain: str, chunks: List[DocumentChunk]):
        """Replace a domain's chunks and rebuild its index."""
        self.chunks[domain] = list(chunks)
        self._reindex_domain(domain)

    def _reindex_domain(self, domain: str):
        """Build dense FAISS / normalized embedding matrix for the specified domain."""
        doc_chunks = self.chunks.get(domain, [])
        if not doc_chunks:
            return

        texts = [c.text for c in doc_chunks]
        dense_mat = self._encode_texts_dense(texts)
        if dense_mat is not None:
            self.chunk_vectors[domain] = dense_mat
            if faiss is not None:
                dim = dense_mat.shape[1]
                idx = faiss.IndexFlatIP(dim)
                idx.add(dense_mat)
                self.faiss_indices[domain] = idx
            return

        # Fallback: TF-IDF matrix
        vocab: Dict[str, int] = {}
        doc_tokens_list: List[List[str]] = []
        doc_freq: Dict[str, int] = {}

        for chunk in doc_chunks:
            tokens = self._tokenize(chunk.text)
            doc_tokens_list.append(tokens)
            for t in set(tokens):
                doc_freq[t] = doc_freq.get(t, 0) + 1
                if t not in vocab:
                    vocab[t] = len(vocab)

        num_docs = len(doc_chunks)
        vocab_size = len(vocab)
        self.vocab[domain] = vocab

        idf = np.zeros(vocab_size, dtype=np.float32)
        for token, idx in vocab.items():
            df = doc_freq.get(token, 1)
            idf[idx] = math.log((num_docs + 1) / (df + 1)) + 1.0
        self.idf[domain] = idf

        vectors = np.zeros((num_docs, vocab_size), dtype=np.float32)
        for i, tokens in enumerate(doc_tokens_list):
            if not tokens:
                continue
            tf: Dict[int, float] = {}
            for t in tokens:
                idx = vocab[t]
                tf[idx] = tf.get(idx, 0.0) + 1.0
            for idx, count in tf.items():
                vectors[i, idx] = (1.0 + math.log(count)) * idf[idx]
            norm = np.linalg.norm(vectors[i])
            if norm > 0:
                vectors[i] /= norm

        self.chunk_vectors[domain] = vectors

    def _embed_query_tfidf(self, query: str, domain: str) -> Optional[np.ndarray]:
        vocab = self.vocab.get(domain)
        idf = self.idf.get(domain)
        if not vocab or idf is None:
            return None
        tokens = self._tokenize(query)
        if not tokens:
            return None
        q_vec = np.zeros(len(vocab), dtype=np.float32)
        tf: Dict[int, float] = {}
        for t in tokens:
            if t in vocab:
                idx = vocab[t]
                tf[idx] = tf.get(idx, 0.0) + 1.0
        if not tf:
            return None
        for idx, count in tf.items():
            q_vec[idx] = (1.0 + math.log(count)) * idf[idx]
        norm = np.linalg.norm(q_vec)
        if norm > 0:
            q_vec /= norm
        return q_vec

    def retrieve(self, query: str, domain: str, top_k: int = 4) -> List[DocumentChunk]:
        """
        Cosine similarity top-k retrieval using dense SentenceTransformer embeddings + FAISS.
        Returns DocumentChunk objects with .similarity_score populated from real cosine similarity.
        """
        domain_chunks = self.chunks.get(domain, [])
        if not domain_chunks or domain not in self.chunk_vectors:
            return []

        num_chunks = len(domain_chunks)
        k = min(top_k, num_chunks)

        q_dense = self._encode_texts_dense([query])
        if q_dense is not None:
            if domain in self.faiss_indices and faiss is not None:
                scores, indices = self.faiss_indices[domain].search(q_dense, k)
                results: List[DocumentChunk] = []
                for score, idx in zip(scores[0], indices[0]):
                    if idx < 0 or idx >= num_chunks:
                        continue
                    c = domain_chunks[int(idx)]
                    results.append(
                        DocumentChunk(
                            chunk_id=c.chunk_id,
                            text=c.text,
                            domain=c.domain,
                            metadata=c.metadata,
                            similarity_score=float(np.clip(score, 0.0, 1.0))
                        )
                    )
                return results

            sim_scores = np.clip(np.dot(self.chunk_vectors[domain], q_dense[0]), 0.0, 1.0)
            top_indices = np.argsort(sim_scores)[::-1][:k]
            return [
                DocumentChunk(
                    chunk_id=domain_chunks[idx].chunk_id,
                    text=domain_chunks[idx].text,
                    domain=domain_chunks[idx].domain,
                    metadata=domain_chunks[idx].metadata,
                    similarity_score=float(sim_scores[idx])
                )
                for idx in top_indices
            ]

        # TF-IDF fallback
        q_vec = self._embed_query_tfidf(query, domain)
        if q_vec is None:
            return [
                DocumentChunk(
                    chunk_id=c.chunk_id,
                    text=c.text,
                    domain=c.domain,
                    metadata=c.metadata,
                    similarity_score=0.0
                )
                for c in domain_chunks[:k]
            ]

        sim_scores = np.clip(np.dot(self.chunk_vectors[domain], q_vec), 0.0, 1.0)
        top_indices = np.argsort(sim_scores)[::-1][:k]
        return [
            DocumentChunk(
                chunk_id=domain_chunks[idx].chunk_id,
                text=domain_chunks[idx].text,
                domain=domain_chunks[idx].domain,
                metadata=domain_chunks[idx].metadata,
                similarity_score=float(sim_scores[idx])
            )
            for idx in top_indices
        ]

    def get_chunk_by_id(self, domain: str, chunk_id: str) -> Optional[DocumentChunk]:
        for c in self.chunks.get(domain, []):
            if c.chunk_id == chunk_id:
                return c
        return None


# Global singleton
vector_store = VectorStore()

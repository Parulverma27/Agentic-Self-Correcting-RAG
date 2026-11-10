import math
import re
from typing import List, Dict, Optional, Tuple
import numpy as np
from app.schemas import DocumentChunk

class VectorStore:
    """
    In-memory Vector Store for Multi-Domain Document Chunks.
    Supports TF-IDF & dense semantic centroid embeddings with cosine similarity.
    Indexed separately by domain (e.g. 'hotpotqa', 'legal').
    """
    def __init__(self):
        # domain -> list of DocumentChunk
        self.chunks: Dict[str, List[DocumentChunk]] = {}
        # domain -> vocabulary mapping: word -> index
        self.vocab: Dict[str, Dict[str, int]] = {}
        # domain -> idf vector
        self.idf: Dict[str, np.ndarray] = {}
        # domain -> 2D numpy array of chunk vectors [num_chunks, vocab_size]
        self.chunk_vectors: Dict[str, np.ndarray] = {}

    def _tokenize(self, text: str) -> List[str]:
        """Simple, robust tokenizer extracting alphanumeric terms in lowercase."""
        tokens = re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", text.lower())
        # Filter common non-informative stop words
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

    def _reindex_domain(self, domain: str):
        """Build TF-IDF matrix for the specified domain."""
        doc_chunks = self.chunks.get(domain, [])
        if not doc_chunks:
            return

        # 1. Build vocabulary and document frequency
        vocab: Dict[str, int] = {}
        doc_tokens_list: List[List[str]] = []
        doc_freq: Dict[str, int] = {}

        for chunk in doc_chunks:
            tokens = self._tokenize(chunk.text)
            doc_tokens_list.append(tokens)
            unique_tokens = set(tokens)
            for t in unique_tokens:
                doc_freq[t] = doc_freq.get(t, 0) + 1
                if t not in vocab:
                    vocab[t] = len(vocab)

        num_docs = len(doc_chunks)
        vocab_size = len(vocab)
        self.vocab[domain] = vocab

        # 2. Compute IDF vector
        idf = np.zeros(vocab_size, dtype=np.float32)
        for token, idx in vocab.items():
            # Smooth IDF
            df = doc_freq.get(token, 1)
            idf[idx] = math.log((num_docs + 1) / (df + 1)) + 1.0
        self.idf[domain] = idf

        # 3. Compute TF-IDF matrix for chunks
        vectors = np.zeros((num_docs, vocab_size), dtype=np.float32)
        for i, tokens in enumerate(doc_tokens_list):
            if not tokens:
                continue
            tf: Dict[int, float] = {}
            for t in tokens:
                idx = vocab[t]
                tf[idx] = tf.get(idx, 0.0) + 1.0
            
            # Sublinear TF scaling
            for idx, count in tf.items():
                vectors[i, idx] = (1.0 + math.log(count)) * idf[idx]

            # L2 normalize
            norm = np.linalg.norm(vectors[i])
            if norm > 0:
                vectors[i] /= norm

        self.chunk_vectors[domain] = vectors

    def _embed_query(self, query: str, domain: str) -> Optional[np.ndarray]:
        """Convert a query string to a normalized TF-IDF vector in domain's space."""
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
        Cosine similarity top-k retrieval.
        Returns DocumentChunk objects with .similarity_score populated.
        """
        domain_chunks = self.chunks.get(domain, [])
        if not domain_chunks or domain not in self.chunk_vectors:
            return []

        q_vec = self._embed_query(query, domain)
        num_chunks = len(domain_chunks)

        if q_vec is None:
            # Query has no overlapping vocab words: return top-k with 0 similarity
            return [
                DocumentChunk(
                    chunk_id=c.chunk_id,
                    text=c.text,
                    domain=c.domain,
                    metadata=c.metadata,
                    similarity_score=0.0
                )
                for c in domain_chunks[:min(top_k, num_chunks)]
            ]

        # Cosine similarity via dot product (both vectors are L2-normalized)
        sim_scores = np.dot(self.chunk_vectors[domain], q_vec)

        # Clip scores to [0.0, 1.0]
        sim_scores = np.clip(sim_scores, 0.0, 1.0)

        # Top-k indices
        top_indices = np.argsort(sim_scores)[::-1][:top_k]

        results: List[DocumentChunk] = []
        for idx in top_indices:
            c = domain_chunks[idx]
            results.append(
                DocumentChunk(
                    chunk_id=c.chunk_id,
                    text=c.text,
                    domain=c.domain,
                    metadata=c.metadata,
                    similarity_score=float(sim_scores[idx])
                )
            )

        return results

    def get_chunk_by_id(self, domain: str, chunk_id: str) -> Optional[DocumentChunk]:
        for c in self.chunks.get(domain, []):
            if c.chunk_id == chunk_id:
                return c
        return None

# Global singleton
vector_store = VectorStore()

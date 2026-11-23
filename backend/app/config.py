import os
from pydantic import BaseModel

class Settings(BaseModel):
    # App Settings
    PROJECT_NAME: str = "Comparative Evaluation of Relevance-Grading Strategies in CRAG"
    VERSION: str = "2.0.0"
    API_PREFIX: str = "/api"

    # Grading & Pipeline Hyperparameters
    TOP_K: int = 4
    SIMILARITY_THRESHOLD: float = 0.45
    CROSS_ENCODER_THRESHOLD: float = 0.50
    LLM_GRADER_THRESHOLD: float = 0.50
    CASCADE_COSINE_MIN: float = 0.30
    CASCADE_CE_LOW: float = 0.35
    CASCADE_CE_HIGH: float = 0.65
    MIN_RELEVANT_CHUNKS: int = 1
    MAX_REFORMULATION_RETRIES: int = 2
    BOOTSTRAP_ITERATIONS: int = 2000

    # Local Models (Ollama + SentenceTransformers / CrossEncoder)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_LLM_MODEL: str = os.getenv("OLLAMA_LLM_MODEL", "qwen2.5:3b")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    CROSS_ENCODER_MODEL: str = os.getenv("CROSS_ENCODER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

    # Benchmark Domains
    DOMAINS: list[str] = ["hotpotqa", "legal"]

settings = Settings()

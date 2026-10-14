import os
from pydantic import BaseModel

class Settings(BaseModel):
    # App Settings
    PROJECT_NAME: str = "Comparative Evaluation of Relevance-Grading Strategies in CRAG"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Grading & Pipeline Hyperparameters
    TOP_K: int = 4
    SIMILARITY_THRESHOLD: float = 0.55
    CROSS_ENCODER_THRESHOLD: float = 0.50
    LLM_GRADER_THRESHOLD: float = 0.50
    MIN_RELEVANT_CHUNKS: int = 1
    MAX_REFORMULATION_RETRIES: int = 2
    
    # Model Endpoints (Local Ollama / HuggingFace)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_LLM_MODEL: str = os.getenv("OLLAMA_LLM_MODEL", "llama3.2")
    HUGGINGFACE_ENDPOINT: str = os.getenv("HUGGINGFACE_ENDPOINT", "http://localhost:8000/score")
    
    # Benchmark Domains
    DOMAINS: list[str] = ["hotpotqa", "legal"]

settings = Settings()

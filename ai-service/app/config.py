"""Runtime configuration for the NyayaSetu AI service (12-factor, env driven)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- service -----------------------------------------------------------
    internal_token: str = "change-me-internal-token"
    log_level: str = "INFO"

    # --- database (pgvector knowledge base) ---------------------------------
    database_url: str = "postgresql://nyayasetu:nyayasetu@localhost:5432/nyayasetu"
    # "memory" keeps the knowledge base in RAM (tests / quick demos without Postgres)
    vector_store: Literal["pgvector", "memory"] = "pgvector"

    # --- LLM ----------------------------------------------------------------
    # "mock" is a deterministic extractive fallback for demos/tests; it does NOT
    # translate or truly simplify. Use a real provider for real output.
    llm_provider: Literal["anthropic", "openai", "ollama", "mock"] = "mock"
    llm_model: str = "claude-sonnet-5-5"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096
    llm_timeout_s: int = 120
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    ollama_base_url: str = "http://localhost:11434"

    # --- embeddings / retrieval --------------------------------------------
    # "hash" is an offline, dependency-free embedder (weaker); use "fastembed" in production.
    embedding_provider: Literal["fastembed", "hash"] = "fastembed"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dim: int = 384
    reranker: Literal["cross-encoder", "lexical", "none"] = "cross-encoder"
    reranker_model: str = "jinaai/jina-reranker-v2-base-multilingual"
    retrieval_candidates: int = 20  # per retriever (vector / keyword) before fusion
    rerank_candidates: int = 16  # fused candidates passed to the reranker
    retrieval_top_k: int = 6  # sources given to the LLM
    kb_dir: Path = BASE_DIR / "knowledge_base"
    auto_ingest_kb: bool = True

    # --- extraction / OCR -----------------------------------------------------
    ocr_engine: Literal["tesseract", "paddle"] = "tesseract"
    ocr_langs: str = "mar+hin+eng"  # tesseract language codes
    ocr_dpi: int = 200
    min_chars_per_page: int = 40  # below this a digital-PDF page is treated as scanned
    max_pages: int = 60
    max_upload_mb: int = 25

    # --- chunking / long documents ----------------------------------------------
    chunk_size: int = 1800
    chunk_overlap: int = 200
    max_direct_chars: int = 14000  # longer documents go through map-reduce
    max_map_chunks: int = 24


    @field_validator("anthropic_api_key", "openai_api_key", "openai_base_url", mode="before")
    @classmethod
    def _clean_secret(cls, v):
        """Keys pasted into .env often carry quotes, spaces or a 'Bearer ' prefix; none of them belong to the value."""
        if v is None:
            return None
        v = str(v).strip().strip("\"'").strip()
        if v.lower().startswith("bearer "):
            v = v[7:].strip()
        return v or None


@lru_cache
def get_settings() -> Settings:
    return Settings()

"""Application configuration.

Aurora is *local-first*: every default points at on-device, API-free engines.
You can opt into an OpenAI-compatible endpoint (Ollama, LM Studio, Groq free
tier, OpenAI, ...) purely through environment variables — nothing in the code
hard-codes a paid provider.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo layout: <repo>/backend/app/config.py  ->  data dir at <repo>/backend/data
BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = BACKEND_DIR / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AURORA_",
        env_file=(BACKEND_DIR.parent / ".env", BACKEND_DIR / ".env"),
        extra="ignore",
    )

    # ── Storage ────────────────────────────────────────────────────────────
    data_dir: Path = DEFAULT_DATA_DIR
    db_path: Path | None = None  # defaults to <data_dir>/aurora.db

    # ── CORS / server ──────────────────────────────────────────────────────
    cors_origins: str = "*"

    # ── LLM provider ───────────────────────────────────────────────────────
    # provider: "ollama" (default, local) | "openai" (any OpenAI-compatible
    # base_url, incl. LM Studio / Groq / OpenRouter) | "heuristic" (no model).
    llm_provider: str = "ollama"
    llm_base_url: str = "http://localhost:11434"
    llm_model: str = "llama3.1:8b"
    llm_api_key: str = ""  # only needed for hosted OpenAI-compatible endpoints
    llm_temperature: float = 0.4
    llm_timeout: float = 120.0

    # ── Embedding provider ─────────────────────────────────────────────────
    # "ollama" | "sentence-transformers" | "hashing" (pure-python fallback).
    # "auto" probes ollama, then sentence-transformers, then hashing.
    embedding_provider: str = "auto"
    embedding_model: str = "nomic-embed-text"  # ollama model name
    st_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim_fallback: int = 384  # dim of the hashing fallback

    # ── Text-to-speech (podcast) ───────────────────────────────────────────
    # "auto" | "piper" | "pyttsx3" | "none"
    tts_provider: str = "auto"
    piper_model_path: str = ""  # path to a .onnx piper voice, if installed

    # ── Speech-to-text (audio/video sources) ───────────────────────────────
    stt_model: str = "base"  # faster-whisper model size

    # ── Retrieval ──────────────────────────────────────────────────────────
    chunk_size: int = 1100        # characters per chunk
    chunk_overlap: int = 150
    retrieval_top_k: int = 8

    # ── Ingestion safety ───────────────────────────────────────────────────
    max_upload_mb: int = 50       # reject uploads larger than this
    # By default, refuse to fetch URLs that resolve to private/loopback/link-local
    # addresses (SSRF guard). Set true if you self-host internal docs you want to
    # add as sources.
    allow_private_urls: bool = False

    @property
    def database_path(self) -> Path:
        return self.db_path or (self.data_dir / "aurora.db")

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def media_dir(self) -> Path:
        return self.data_dir / "media"

    def ensure_dirs(self) -> None:
        for p in (self.data_dir, self.uploads_dir, self.media_dir):
            p.mkdir(parents=True, exist_ok=True)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings

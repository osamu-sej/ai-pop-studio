from __future__ import annotations

from fastapi import APIRouter

from ..ai.embeddings import get_embedder
from ..ai.engine import llm_mode
from ..ai.llm import get_llm
from ..ai.tts import get_tts
from ..config import get_settings
from ..schemas import ProviderStatus

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/status", response_model=ProviderStatus)
def status():
    settings = get_settings()
    llm = get_llm(refresh=True)
    try:
        llm_available = llm.available()
    except Exception:
        llm_available = False
    embedder = get_embedder(refresh=True)
    tts = get_tts()

    notes: list[str] = []
    if not llm_available:
        notes.append(
            "No LLM reachable — running in heuristic mode (extractive). Install Ollama "
            "and pull a model (e.g. `ollama pull llama3.1:8b`) for full-quality answers."
        )
    if embedder.name == "hashing":
        notes.append(
            "Using the built-in hashing embeddings. Install Ollama's `nomic-embed-text` "
            "or `sentence-transformers` for stronger semantic search."
        )
    if not tts.available():
        notes.append(
            "No local TTS engine — podcasts produce a transcript only. Install `pyttsx3` "
            "or `piper` for audio."
        )

    return ProviderStatus(
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model,
        llm_available=llm_available,
        llm_mode=llm_mode(),
        embedding_provider=embedder.name,
        embedding_available=True,
        tts_provider=tts.name,
        tts_available=tts.available(),
        notes=notes,
    )

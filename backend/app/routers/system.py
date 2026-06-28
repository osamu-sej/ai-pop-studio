from __future__ import annotations

from fastapi import APIRouter

from ..ai import runtime
from ..ai.embeddings import get_embedder
from ..ai.engine import llm_mode
from ..ai.llm import get_llm
from ..ai.tts import get_tts
from ..schemas import (
    GlobalSearchHit,
    GlobalSearchRequest,
    ProviderStatus,
    SettingsUpdate,
    SettingsView,
)
from ..services import search as search_service

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/search", response_model=list[GlobalSearchHit], tags=["search"])
def global_search(body: GlobalSearchRequest):
    return search_service.global_search(body.query, top_k=body.top_k)


def _settings_view() -> SettingsView:
    return SettingsView(
        llm_provider=str(runtime.value("llm_provider")),
        llm_base_url=str(runtime.value("llm_base_url")),
        llm_model=str(runtime.value("llm_model")),
        llm_api_key_set=bool(runtime.value("llm_api_key")),
        embedding_provider=str(runtime.value("embedding_provider")),
        embedding_model=str(runtime.value("embedding_model")),
        tts_provider=str(runtime.value("tts_provider")),
    )


@router.get("/settings", response_model=SettingsView)
def get_settings_view():
    return _settings_view()


@router.put("/settings", response_model=ProviderStatus)
def update_settings(body: SettingsUpdate):
    runtime.save(body.model_dump(exclude_none=True))
    get_llm(refresh=True)
    get_embedder(refresh=True)
    return status()


@router.get("/status", response_model=ProviderStatus)
def status():
    llm = get_llm(refresh=True)
    try:
        llm_available = llm.available()
    except Exception:
        llm_available = False
    embedder = get_embedder(refresh=True)
    tts = get_tts()
    llm_provider = str(runtime.value("llm_provider"))
    llm_model = str(runtime.value("llm_model"))

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
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_available=llm_available,
        llm_mode=llm_mode(),
        embedding_provider=embedder.name,
        embedding_available=True,
        tts_provider=tts.name,
        tts_available=tts.available(),
        notes=notes,
    )

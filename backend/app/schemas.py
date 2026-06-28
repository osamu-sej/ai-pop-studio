"""Pydantic request/response models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ── Notebooks ──────────────────────────────────────────────────────────────
class NotebookCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    emoji: str = "📓"


class NotebookUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    emoji: str | None = None


class Notebook(BaseModel):
    id: str
    name: str
    description: str
    emoji: str
    created_at: str
    updated_at: str
    source_count: int = 0
    note_count: int = 0


# ── Sources ────────────────────────────────────────────────────────────────
class SourceCreateText(BaseModel):
    title: str = "Pasted text"
    content: str = Field(min_length=1)


class SourceCreateUrl(BaseModel):
    url: str = Field(min_length=4)
    title: str | None = None


class Source(BaseModel):
    id: str
    notebook_id: str
    title: str
    source_type: str
    origin: str
    summary: str
    status: str
    token_count: int
    metadata: dict[str, Any] = {}
    created_at: str


class SourceDetail(Source):
    content: str


# ── Notes ──────────────────────────────────────────────────────────────────
class NoteCreate(BaseModel):
    title: str = "Untitled note"
    content: str = ""


class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


class Note(BaseModel):
    id: str
    notebook_id: str
    title: str
    content: str
    note_type: str
    kind: str
    created_at: str
    updated_at: str


# ── Chat ───────────────────────────────────────────────────────────────────
class Citation(BaseModel):
    source_id: str
    source_title: str
    chunk_idx: int
    snippet: str
    score: float


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    source_ids: list[str] | None = None  # restrict context to these sources


class ChatMessage(BaseModel):
    id: str
    notebook_id: str
    role: str
    content: str
    citations: list[Citation] = []
    created_at: str


# ── Search ─────────────────────────────────────────────────────────────────
class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    source_ids: list[str] | None = None
    top_k: int = 10


class SearchHit(BaseModel):
    source_id: str
    source_title: str
    chunk_idx: int
    text: str
    score: float


class GlobalSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = 20


class GlobalSearchHit(BaseModel):
    notebook_id: str
    notebook_name: str
    notebook_emoji: str
    source_id: str
    source_title: str
    chunk_idx: int
    text: str
    score: float


# ── Studio / transformations ───────────────────────────────────────────────
class TransformRequest(BaseModel):
    kind: str  # summary | study_guide | faq | timeline | briefing | mindmap | key_topics
    source_ids: list[str] | None = None
    save_as_note: bool = True


class TransformResult(BaseModel):
    kind: str
    title: str
    content: str
    note_id: str | None = None


class PodcastRequest(BaseModel):
    title: str | None = None
    source_ids: list[str] | None = None
    style: str = "conversational"  # conversational | deep_dive | debate | solo
    speaker_a: str = "Alex"
    speaker_b: str = "Sam"
    length: str = "medium"  # short | medium | long


class NotebookGuide(BaseModel):
    overview: str
    topics: list[str]
    suggestions: list[str]
    source_count: int


class Podcast(BaseModel):
    id: str
    notebook_id: str
    title: str
    transcript: str
    audio_path: str
    audio_url: str | None = None
    status: str
    created_at: str


# ── System / providers ─────────────────────────────────────────────────────
class SettingsUpdate(BaseModel):
    llm_provider: str | None = None
    llm_base_url: str | None = None
    llm_model: str | None = None
    llm_api_key: str | None = None
    embedding_provider: str | None = None
    embedding_model: str | None = None
    tts_provider: str | None = None


class SettingsView(BaseModel):
    llm_provider: str
    llm_base_url: str
    llm_model: str
    llm_api_key_set: bool
    embedding_provider: str
    embedding_model: str
    tts_provider: str


class ProviderStatus(BaseModel):
    llm_provider: str
    llm_model: str
    llm_available: bool
    llm_mode: str  # "model" | "heuristic"
    embedding_provider: str
    embedding_available: bool
    tts_provider: str
    tts_available: bool
    notes: list[str] = []

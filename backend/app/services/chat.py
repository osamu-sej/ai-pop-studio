"""Grounded chat: retrieve from sources, answer with citations, persist."""

from __future__ import annotations

from collections.abc import Iterator

from .. import repositories as repo
from ..ai import engine
from ..config import get_settings
from . import search


def _snippet(text: str, limit: int = 240) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"


def _retrieve(notebook_id: str, message: str, source_ids: list[str] | None):
    """Run retrieval and build (context_blocks, citations) once for reuse."""
    settings = get_settings()
    hits = search.hybrid_search(
        notebook_id, message, top_k=settings.retrieval_top_k, source_ids=source_ids
    )
    context_blocks = [h["text"] for h in hits]
    citations: list[dict] = []
    seen = set()
    for h in hits:
        key = (h["source_id"], h["chunk_idx"])
        if key in seen:
            continue
        seen.add(key)
        citations.append({
            "source_id": h["source_id"],
            "source_title": h["source_title"],
            "chunk_idx": h["chunk_idx"],
            "snippet": _snippet(h["text"]),
            "score": h["score"],
        })
        if len(citations) >= 5:
            break
    return context_blocks, citations


def ask(notebook_id: str, message: str, source_ids: list[str] | None = None) -> dict:
    repo.add_chat_message(notebook_id, "user", message)
    context_blocks, citations = _retrieve(notebook_id, message, source_ids)
    answer = engine.answer_question(message, context_blocks)
    return repo.add_chat_message(notebook_id, "assistant", answer, citations)


def ask_stream(notebook_id: str, message: str,
               source_ids: list[str] | None = None) -> Iterator[dict]:
    """Generator of SSE-ready events: {'type': 'token'|'done', ...}.

    Persists the user message up front and the full assistant message at the end.
    """
    repo.add_chat_message(notebook_id, "user", message)
    context_blocks, citations = _retrieve(notebook_id, message, source_ids)

    parts: list[str] = []
    for delta in engine.answer_question_stream(message, context_blocks):
        parts.append(delta)
        yield {"type": "token", "text": delta}

    full = "".join(parts).strip()
    saved = repo.add_chat_message(notebook_id, "assistant", full, citations)
    yield {"type": "done", "message": saved}


def history(notebook_id: str) -> list[dict]:
    return repo.list_chat_messages(notebook_id)


def reset(notebook_id: str) -> None:
    repo.clear_chat(notebook_id)

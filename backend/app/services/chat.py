"""Grounded chat: retrieve from sources, answer with citations, persist."""

from __future__ import annotations

from .. import repositories as repo
from ..ai import engine
from ..config import get_settings
from . import search


def _snippet(text: str, limit: int = 240) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"


def ask(notebook_id: str, message: str, source_ids: list[str] | None = None) -> dict:
    settings = get_settings()
    repo.add_chat_message(notebook_id, "user", message)

    hits = search.hybrid_search(
        notebook_id, message, top_k=settings.retrieval_top_k, source_ids=source_ids
    )
    context_blocks = [h["text"] for h in hits]
    answer = engine.answer_question(message, context_blocks)

    # Cite the chunks we actually retrieved (deduped by source, best first).
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

    return repo.add_chat_message(notebook_id, "assistant", answer, citations)


def history(notebook_id: str) -> list[dict]:
    return repo.list_chat_messages(notebook_id)


def reset(notebook_id: str) -> None:
    repo.clear_chat(notebook_id)

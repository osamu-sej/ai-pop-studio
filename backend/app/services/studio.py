"""Studio: source transformations and podcast (audio overview) generation."""

from __future__ import annotations

import hashlib

from .. import repositories as repo
from ..ai import engine, heuristics
from ..ai.tts import get_tts
from ..config import get_settings
from ..database import transaction

TRANSFORM_TITLES = {
    "summary": "Summary",
    "key_topics": "Key Topics",
    "study_guide": "Study Guide",
    "faq": "FAQ",
    "timeline": "Timeline",
    "briefing": "Briefing Document",
    "mindmap": "Mind Map",
}


def _gather_text(notebook_id: str, source_ids: list[str] | None) -> tuple[str, list[dict]]:
    sources = repo.list_sources(notebook_id)
    if source_ids:
        sources = [s for s in sources if s["id"] in set(source_ids)]
    blocks = []
    for s in sources:
        if s.get("content"):
            blocks.append(f"# {s['title']}\n{s['content']}")
    return "\n\n".join(blocks), sources


def run_transformation(notebook_id: str, kind: str, source_ids: list[str] | None,
                       save_as_note: bool = True) -> dict:
    text, sources = _gather_text(notebook_id, source_ids)
    title = TRANSFORM_TITLES.get(kind, kind.replace("_", " ").title())
    if not text.strip():
        content = "_No source content available to transform. Add a source first._"
    else:
        content = engine.transform(kind, text)

    note_id = None
    if save_as_note:
        note = repo.create_note(notebook_id, title, content, note_type="generated", kind=kind)
        note_id = note["id"]
    return {"kind": kind, "title": title, "content": content, "note_id": note_id}


def export_markdown(notebook_id: str) -> tuple[str, str]:
    """Build a single Markdown document of the whole notebook. Returns (filename, text)."""
    nb = repo.get_notebook(notebook_id)
    name = nb["name"] if nb else "notebook"
    sources = repo.list_sources(notebook_id)
    notes = repo.list_notes(notebook_id)
    chat = repo.list_chat_messages(notebook_id)

    lines = [f"# {nb['emoji'] if nb else '📓'} {name}", ""]
    if nb and nb.get("description"):
        lines += [nb["description"], ""]

    lines += [f"## Sources ({len(sources)})", ""]
    for s in sources:
        lines.append(f"### {s['title']}  \n*{s['source_type']}{' · ' + s['origin'] if s['origin'] else ''}*")
        if s.get("summary"):
            lines += ["", s["summary"]]
        lines.append("")

    if notes:
        lines += [f"## Notes ({len(notes)})", ""]
        for n in notes:
            tag = "✨ " if n["note_type"] == "generated" else ""
            lines += [f"### {tag}{n['title']}", "", n["content"], ""]

    if chat:
        lines += ["## Conversation", ""]
        for m in chat:
            who = "**You**" if m["role"] == "user" else "**Aurora**"
            lines += [f"{who}: {m['content']}", ""]

    filename = "".join(c if c.isalnum() or c in " -_" else "_" for c in name).strip() or "notebook"
    return f"{filename}.md", "\n".join(lines)


def suggested_questions(notebook_id: str, source_ids: list[str] | None = None) -> list[str]:
    text, _ = _gather_text(notebook_id, source_ids)
    if not text.strip():
        return []
    return engine.suggest_questions(text, n=4)


def notebook_guide(notebook_id: str, force: bool = False) -> dict:
    """An at-a-glance overview of the whole notebook (NotebookLM-style guide).

    Cached and keyed by a fingerprint of the notebook's sources so it isn't
    re-generated (2 LLM calls) on every open — only when the sources change or
    the caller asks to refresh.
    """
    text, sources = _gather_text(notebook_id, None)
    if not text.strip():
        return {"overview": "", "topics": [], "suggestions": [], "source_count": 0}

    fingerprint = hashlib.md5(
        ";".join(sorted(s["id"] for s in sources)).encode("utf-8")
    ).hexdigest()
    if not force:
        cached = repo.get_guide_cache(notebook_id)
        if cached and cached["fingerprint"] == fingerprint:
            return {
                "overview": cached["overview"],
                "topics": cached["topics"],
                "suggestions": cached["suggestions"],
                "source_count": cached["source_count"],
            }

    # topics from raw content only (exclude the injected "# title" lines)
    raw = " ".join(s.get("content", "") for s in sources)
    guide = {
        "overview": engine.transform("summary", text),
        "topics": heuristics.top_keywords(raw, 12),
        "suggestions": engine.suggest_questions(text, n=4),
        "source_count": len(sources),
    }
    repo.set_guide_cache(
        notebook_id, fingerprint, guide["overview"], guide["topics"],
        guide["suggestions"], guide["source_count"],
    )
    return guide


def transcript_to_markdown(script: list[dict], title: str) -> str:
    lines = [f"# 🎙️ {title}", ""]
    for turn in script:
        lines.append(f"**{turn['speaker']}:** {turn['text']}")
        lines.append("")
    return "\n".join(lines)


def generate_podcast(notebook_id: str, req) -> dict:
    settings = get_settings()
    text, sources = _gather_text(notebook_id, req.source_ids)
    title = req.title or "Audio Overview"

    if not text.strip():
        return repo.create_podcast(
            notebook_id, title,
            transcript="_No source content available. Add a source first._",
            status="empty",
        )

    if req.style == "solo":
        speaker_b = req.speaker_a
    else:
        speaker_b = req.speaker_b

    script = engine.podcast_script(text, req.style, req.speaker_a, speaker_b, req.length)
    transcript_md = transcript_to_markdown(script, title)

    # Persist the record first so the UI can show the transcript immediately.
    podcast = repo.create_podcast(notebook_id, title, transcript=transcript_md, status="ready")

    # Best-effort local audio synthesis (no-op if no TTS engine installed).
    audio_path = ""
    try:
        tts = get_tts()
        if tts.available():
            out = settings.media_dir / f"podcast_{podcast['id']}.wav"
            if tts.synthesize(script, out):
                audio_path = str(out)
    except Exception:
        audio_path = ""

    if audio_path:
        with transaction() as conn:
            conn.execute(
                "UPDATE podcasts SET audio_path = ? WHERE id = ?", (audio_path, podcast["id"])
            )
        podcast = repo.get_podcast(podcast["id"])
    return podcast

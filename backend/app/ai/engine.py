"""High-level cognition.

Each function tries the configured LLM and transparently falls back to the
heuristic engine if no model is reachable. The rest of the app calls these and
never has to care which path was taken.
"""

from __future__ import annotations

import json

from . import heuristics, prompts
from .llm import get_llm


def llm_mode() -> str:
    """'model' if a real LLM is reachable, else 'heuristic'."""
    try:
        return "model" if get_llm().available() else "heuristic"
    except Exception:
        return "heuristic"


def _truncate(text: str, max_chars: int) -> str:
    return text if len(text) <= max_chars else text[:max_chars] + "\n…[truncated]…"


def answer_question(question: str, context_blocks: list[str]) -> str:
    llm = get_llm()
    if context_blocks and llm.available():
        try:
            messages = [
                {"role": "system", "content": prompts.RAG_SYSTEM},
                {"role": "user", "content": prompts.rag_user_prompt(question, context_blocks)},
            ]
            return llm.chat(messages, max_tokens=900)
        except Exception:
            pass
    return heuristics.answer(question, context_blocks)


def transform(kind: str, text: str) -> str:
    text = _truncate(text, 24000)
    llm = get_llm()
    if llm.available():
        try:
            return llm.chat(prompts.transform_messages(kind, text), max_tokens=1400)
        except Exception:
            pass
    fn = {
        "summary": lambda t: "## Summary\n\n" + heuristics.summarize(t, 6),
        "key_topics": heuristics.key_topics,
        "study_guide": heuristics.study_guide,
        "faq": heuristics.faq,
        "timeline": heuristics.timeline,
        "briefing": heuristics.briefing,
        "mindmap": heuristics.mindmap,
    }.get(kind, lambda t: "## Summary\n\n" + heuristics.summarize(t, 6))
    return fn(text)


def summarize_source(text: str) -> str:
    """Short summary shown under each source card."""
    text = _truncate(text, 16000)
    llm = get_llm()
    if llm.available():
        try:
            msgs = [
                {"role": "system", "content": "Summarize the document in 2-3 sentences. Plain text."},
                {"role": "user", "content": text},
            ]
            return llm.chat(msgs, max_tokens=220, temperature=0.2)
        except Exception:
            pass
    return heuristics.summarize(text, 3)


def podcast_script(text: str, style: str, speaker_a: str, speaker_b: str,
                   length: str) -> list[dict]:
    text = _truncate(text, 22000)
    llm = get_llm()
    if llm.available():
        try:
            messages = [
                {"role": "system", "content": prompts.podcast_system(style, speaker_a, speaker_b)},
                {"role": "user", "content": prompts.podcast_user(text, length)},
            ]
            raw = llm.chat(messages, max_tokens=2200, temperature=0.7)
            parsed = _parse_script_json(raw)
            if parsed:
                return parsed
        except Exception:
            pass
    turns = {"short": 8, "medium": 16, "long": 28}.get(length, 16)
    return heuristics.podcast_script(text, speaker_a, speaker_b, turns)


def _parse_script_json(raw: str) -> list[dict] | None:
    raw = raw.strip()
    # Strip markdown code fences if the model wrapped its JSON.
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1] if raw.count("```") >= 2 else raw
        raw = raw.removeprefix("json").strip()
    start, end = raw.find("["), raw.rfind("]")
    if start == -1 or end == -1:
        return None
    try:
        data = json.loads(raw[start:end + 1])
    except Exception:
        return None
    out = []
    for item in data:
        if isinstance(item, dict) and "text" in item:
            out.append({"speaker": str(item.get("speaker", "Host")), "text": str(item["text"])})
    return out or None

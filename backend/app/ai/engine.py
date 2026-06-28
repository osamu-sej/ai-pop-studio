"""High-level cognition.

Each function tries the configured LLM and transparently falls back to the
heuristic engine if no model is reachable. The rest of the app calls these and
never has to care which path was taken.
"""

from __future__ import annotations

import json
from collections.abc import Iterator

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


def answer_question_stream(question: str, context_blocks: list[str]) -> Iterator[str]:
    """Yield the answer incrementally (real streaming if a model is available)."""
    llm = get_llm()
    if context_blocks and llm.available():
        produced = False
        try:
            messages = [
                {"role": "system", "content": prompts.RAG_SYSTEM},
                {"role": "user", "content": prompts.rag_user_prompt(question, context_blocks)},
            ]
            for delta in llm.stream(messages, max_tokens=900):
                produced = True
                yield delta
        except Exception:
            pass
        # If the model emitted anything, never append the heuristic answer on top
        # (that would garble a partial reply). Only fall back when nothing came out.
        if produced:
            return
    # Heuristic path: compute then emit in word groups so the UI still "types".
    text = heuristics.answer(question, context_blocks)
    yield from _chunk_words(text)


def _chunk_words(text: str, group: int = 4) -> Iterator[str]:
    words = text.split(" ")
    for i in range(0, len(words), group):
        chunk = " ".join(words[i:i + group])
        yield chunk if i == 0 else " " + chunk


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


def suggest_questions(text: str, n: int = 4) -> list[str]:
    text = _truncate(text, 12000)
    llm = get_llm()
    if llm.available():
        try:
            msgs = [
                {"role": "system", "content": "Propose insightful questions a reader would ask "
                                              "about the material. Return ONLY the questions, one "
                                              "per line, no numbering."},
                {"role": "user", "content": text},
            ]
            raw = llm.chat(msgs, max_tokens=240, temperature=0.5)
            lines = [
                ln.strip(" -•0123456789.").strip()
                for ln in raw.splitlines()
                if "?" in ln
            ]
            lines = [ln for ln in lines if ln]
            if lines:
                return lines[:n]
        except Exception:
            pass
    return heuristics.suggested_questions(text, n)


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

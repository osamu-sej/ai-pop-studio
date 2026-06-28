"""Prompt templates used when a real LLM is available."""

from __future__ import annotations

RAG_SYSTEM = (
    "You are Aurora, a meticulous research assistant. Answer the user's question "
    "using ONLY the provided source excerpts. Be accurate and concise.\n"
    "- Cite excerpts inline using their bracket numbers, e.g. [1], [2].\n"
    "- If the answer is not contained in the sources, say so plainly instead of "
    "guessing.\n"
    "- Prefer specific facts and quotes from the sources over generalities."
)


def rag_user_prompt(question: str, context_blocks: list[str]) -> str:
    context = "\n\n".join(f"[{i + 1}] {b}" for i, b in enumerate(context_blocks))
    return (
        f"Source excerpts:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer (cite excerpts with [n]):"
    )


TRANSFORM_INSTRUCTIONS = {
    "summary": (
        "Write a clear, well-structured summary of the material in markdown. "
        "Open with a one-sentence TL;DR, then 3-6 concise bullet points of the key ideas."
    ),
    "key_topics": (
        "Extract the key topics and entities from the material as a markdown bulleted "
        "list. Group related items and keep each item short."
    ),
    "study_guide": (
        "Create a study guide in markdown with: a short overview, a 'Key terms' section "
        "with definitions, a 'Key concepts' section, and 6-10 review questions."
    ),
    "faq": (
        "Write a markdown FAQ of 6-10 question/answer pairs that a reader of this material "
        "would most want answered. Base every answer strictly on the material."
    ),
    "timeline": (
        "Produce a chronological timeline in markdown of the events, dates, or milestones "
        "mentioned in the material. Use a bulleted list ordered by time."
    ),
    "briefing": (
        "Write a professional briefing document in markdown with an executive summary, "
        "main themes, important facts/quotes, and key takeaways."
    ),
    "mindmap": (
        "Produce a hierarchical mind map in markdown nested-bullet form. Start from one "
        "central idea and branch into themes and sub-points."
    ),
}


def transform_messages(kind: str, text: str) -> list[dict]:
    instruction = TRANSFORM_INSTRUCTIONS.get(kind, TRANSFORM_INSTRUCTIONS["summary"])
    return [
        {"role": "system", "content": "You are Aurora, an expert research analyst. "
                                      "Use only the material provided. Output clean markdown."},
        {"role": "user", "content": f"{instruction}\n\n--- MATERIAL ---\n{text}"},
    ]


def podcast_system(style: str, speaker_a: str, speaker_b: str) -> str:
    styles = {
        "conversational": "warm, curious, and accessible — like a friendly explainer podcast",
        "deep_dive": "analytical and thorough, exploring nuance and implications",
        "debate": "two hosts who respectfully challenge each other's interpretations",
        "solo": "a single host narrating an engaging monologue",
    }
    tone = styles.get(style, styles["conversational"])
    return (
        f"You are a podcast script writer. Write a {tone} episode based ONLY on the "
        f"provided material. Two hosts: {speaker_a} and {speaker_b}. "
        "Make it natural and engaging with back-and-forth, but keep every claim grounded "
        "in the material. Return STRICT JSON: a list of objects with keys 'speaker' and "
        "'text'. No commentary outside the JSON."
    )


def podcast_user(text: str, length: str) -> str:
    target = {"short": "about 8 exchanges", "medium": "about 16 exchanges",
              "long": "about 28 exchanges"}.get(length, "about 16 exchanges")
    return f"Write {target}. Material:\n\n{text}"

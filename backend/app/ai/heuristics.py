"""Zero-model algorithmic fallbacks.

These run when no LLM is installed. They are intentionally simple, deterministic
and fast — classic extractive/statistical NLP — so Aurora is genuinely usable
out of the box with *nothing* installed, then upgrades seamlessly when an Ollama
model is present.
"""

from __future__ import annotations

import re
from collections import Counter

from ..utils import split_sentences

# A compact English/Japanese-friendly stopword set for keyword scoring.
STOPWORDS = set(
    """a an the and or but if then else for to of in on at by with without from into
    is are was were be been being it its this that these those as not no nor so than
    too very can could should would may might will just about over under again further
    here there all any both each few more most other some such only own same we you they
    he she i me my our your their them us he's she's it's we're you're i'm about which who
    whom what when where why how do does did doing have has had having
    includes include including also using used use based upon onto within via etc
    into out off down up many much per among across""".split()
)

_WORD = re.compile(r"[A-Za-z0-9_]+|[぀-ヿ一-鿿]+")


def tokenize(text: str) -> list[str]:
    return [w.lower() for w in _WORD.findall(text)]


def keyword_scores(text: str) -> Counter:
    counts: Counter = Counter()
    for w in tokenize(text):
        if len(w) <= 2 or w in STOPWORDS:
            continue
        counts[w] += 1
    return counts


def top_keywords(text: str, n: int = 12) -> list[str]:
    return [w for w, _ in keyword_scores(text).most_common(n)]


def summarize(text: str, max_sentences: int = 6) -> str:
    """Frequency-based extractive summary (a TextRank-lite)."""
    sentences = split_sentences(text)
    if len(sentences) <= max_sentences:
        return " ".join(sentences)
    freqs = keyword_scores(text)
    if not freqs:
        return " ".join(sentences[:max_sentences])
    peak = max(freqs.values())
    norm = {w: c / peak for w, c in freqs.items()}
    scored = []
    for i, s in enumerate(sentences):
        words = [w for w in tokenize(s) if w in norm]
        if not words:
            continue
        score = sum(norm[w] for w in words) / (len(words) ** 0.5)
        # mild lead bias — early sentences often carry the thesis
        score *= 1.0 + max(0.0, (8 - i)) * 0.02
        scored.append((score, i, s))
    scored.sort(reverse=True)
    chosen = sorted(scored[:max_sentences], key=lambda t: t[1])
    return " ".join(s for _, _, s in chosen)


def answer(question: str, context_blocks: list[str], max_sentences: int = 6) -> str:
    """Pick the sentences from context most relevant to the question."""
    q_terms = {w for w in tokenize(question) if w not in STOPWORDS and len(w) > 2}
    pool: list[tuple[float, int, str]] = []
    for bi, block in enumerate(context_blocks):
        for s in split_sentences(block):
            terms = [w for w in tokenize(s) if len(w) > 2]
            if not terms:
                continue
            overlap = sum(1 for w in terms if w in q_terms)
            if overlap == 0:
                continue
            score = overlap / (len(terms) ** 0.4)
            pool.append((score, bi, s))
    if not pool:
        # No lexical overlap — fall back to a short extractive digest.
        joined = "\n".join(context_blocks)
        digest = summarize(joined, max_sentences=4)
        return (
            "I couldn't find a direct match in your sources for that question, "
            "but here is the most relevant material I have:\n\n" + digest
        )
    pool.sort(reverse=True)
    picked = [s for _, _, s in pool[:max_sentences]]
    return " ".join(picked)


def study_guide(text: str) -> str:
    kws = top_keywords(text, 10)
    summary = summarize(text, 5)
    sentences = split_sentences(text)
    questions = []
    for kw in kws[:6]:
        for s in sentences:
            if kw in tokenize(s):
                questions.append(f"- What does the material say about **{kw}**?")
                break
    lines = ["## Study Guide", "", "### Overview", summary, "", "### Key terms",
             ", ".join(kws) or "—", "", "### Review questions", *questions]
    return "\n".join(lines)


def faq(text: str) -> str:
    sentences = split_sentences(text)
    kws = top_keywords(text, 8)
    out = ["## Frequently Asked Questions", ""]
    for kw in kws[:6]:
        ans = next((s for s in sentences if kw in tokenize(s)), "")
        if ans:
            out.append(f"**Q: What about {kw}?**")
            out.append(f"A: {ans}")
            out.append("")
    return "\n".join(out)


def timeline(text: str) -> str:
    # Pull sentences that mention a year or an explicit date.
    date_re = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b|\b\d{1,2}/\d{1,2}\b")
    events = [s for s in split_sentences(text) if date_re.search(s)]
    out = ["## Timeline", ""]
    if not events:
        out.append("_No explicit dates were found in the sources._")
    else:
        for s in events[:25]:
            out.append(f"- {s}")
    return "\n".join(out)


def briefing(text: str) -> str:
    summary = summarize(text, 6)
    kws = top_keywords(text, 8)
    return "\n".join([
        "## Briefing Document", "",
        "### Executive summary", summary, "",
        "### Main themes", *[f"- {k}" for k in kws], "",
    ])


def mindmap(text: str) -> str:
    kws = top_keywords(text, 9)
    out = ["## Mind Map", "", "- **Central idea**"]
    for k in kws:
        out.append(f"  - {k}")
    return "\n".join(out)


def key_topics(text: str) -> str:
    kws = top_keywords(text, 15)
    return "## Key Topics\n\n" + "\n".join(f"- {k}" for k in kws)


def suggested_questions(text: str, n: int = 4) -> list[str]:
    kws = top_keywords(text, n + 2)
    questions = [f"What do the sources say about {kw}?" for kw in kws[:n]]
    if questions:
        questions[0] = "Give me a concise summary of these sources."
    while len(questions) < n:
        questions.append("What are the most important takeaways?")
    return questions[:n]


def podcast_script(text: str, speaker_a: str, speaker_b: str, turns: int = 12) -> list[dict]:
    """Build a two-host dialogue from the most salient sentences."""
    summary_sentences = split_sentences(summarize(text, max_sentences=turns))
    if not summary_sentences:
        summary_sentences = ["There wasn't much content in the sources to discuss."]
    script = [{
        "speaker": speaker_a,
        "text": f"Welcome to the show! Today {speaker_b} and I are unpacking your sources. Let's get into it.",
    }]
    hosts = [speaker_b, speaker_a]
    connectors = [
        "Right, so here's something that stood out:",
        "That's a great point. Building on that —",
        "Interesting. And there's more to it:",
        "Exactly. Which brings us to:",
        "I was curious about this part too:",
        "Let me add to that:",
    ]
    for i, sentence in enumerate(summary_sentences):
        speaker = hosts[i % 2]
        lead = connectors[i % len(connectors)]
        script.append({"speaker": speaker, "text": f"{lead} {sentence}"})
    script.append({
        "speaker": speaker_a,
        "text": "That's a wrap for today. Thanks for listening, and we'll see you next time!",
    })
    return script

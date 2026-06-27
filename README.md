# 🌌 Aurora Notebook

**A local-first, API-free alternative to Google NotebookLM.**
Bring your own sources — PDFs, web pages, YouTube videos, documents, pasted text —
then chat with them (grounded, with citations), generate study guides, briefings,
timelines and mind maps, and produce two-host **audio overviews**. All of it runs
on **your machine**, with **no API keys and no per-token costs** by default.

> Inspired by [`lfnovo/open-notebook`](https://github.com/lfnovo/open-notebook) and
> Google NotebookLM — rebuilt around a strict goal: **maximum capability at zero
> running cost**, with privacy and offline operation as first-class features.

---

## ✨ Why Aurora

| | Google NotebookLM | Aurora Notebook |
|---|---|---|
| Cost | Free tier w/ limits | **$0 — runs on your hardware** |
| Privacy | Cloud | **100% local, your data never leaves** |
| Offline | No | **Yes** |
| Model choice | Locked to Google | **Any local model (Ollama) or any OpenAI-compatible endpoint** |
| Source types | PDF, web, YouTube, text | PDF, **DOCX**, web, YouTube, text, **audio** |
| Studio outputs | Summary, audio, study guide… | Summary, study guide, FAQ, **timeline**, **briefing**, **mind map**, key topics, **podcast** |
| Works with zero AI installed | — | **Yes (built-in heuristic engine)** |
| Self-hostable / hackable | No | **Yes, MIT-style, single SQLite file** |

---

## 🧱 Architecture at a glance

```
┌──────────────── React + Vite (3-pane NotebookLM UI) ────────────────┐
│   Sources         │            Chat (cited)          │    Studio     │
└─────────────────────────────── /api ────────────────────────────────┘
                                   │
┌────────────────────────── FastAPI backend ──────────────────────────┐
│  ingestion → chunking → embeddings → hybrid search → RAG/transform   │
│                         │                                             │
│   AI layer (swappable):  Ollama  ·  OpenAI-compatible  ·  heuristic   │
│   Storage:  single SQLite file (metadata + vectors inline)           │
└──────────────────────────────────────────────────────────────────────┘
```

- **Backend** — Python 3.12 · FastAPI
- **Frontend** — React 19 · Vite · TypeScript (no UI framework lock-in)
- **Database** — embedded **SQLite** (no server), vectors stored inline, cosine search in numpy
- **AI** — pluggable: **Ollama** (default), any **OpenAI-compatible** endpoint, or a **zero-model heuristic engine**

The whole AI layer hides behind small interfaces in `backend/app/ai/`. Nothing
in the code hard-requires a paid provider — see [`DESIGN.md`](DESIGN.md) for the
full **"can this be done without APIs?"** analysis (short answer: **yes**).

---

## 🚀 Quick start

### 1. Install (no API key needed)

```bash
make install          # backend (pip) + frontend (npm)
```

### 2. Run

```bash
make dev              # backend :8000  +  frontend :5173 (Vite proxies /api)
```

Open **http://localhost:5173**. That's it — Aurora already works in **offline /
heuristic mode** (extractive summaries, keyword-grounded chat, podcast scripts).

### 3. Unlock full AI quality — still 100% free & local

Install [Ollama](https://ollama.com) and pull a couple of models:

```bash
ollama pull llama3.1:8b        # the reasoning model (chat, summaries, podcasts)
ollama pull nomic-embed-text   # semantic embeddings for better retrieval
# or simply:  make ollama-setup
```

Aurora auto-detects Ollama on `localhost:11434` and switches to full quality —
LLM-written answers with inline citations, rich transformations, and natural
multi-host podcast scripts. The status pill in the top-right shows live engine state.

### Production (single process)

```bash
make serve            # builds the frontend and serves the whole app on :8000
```

### Run with Docker (fully self-hosted, API-free)

One command brings up Aurora **and** a local Ollama for the models:

```bash
docker compose up -d --build
docker compose exec ollama ollama pull llama3.1:8b
docker compose exec ollama ollama pull nomic-embed-text
# open http://localhost:8000
```

Everything runs on your box — no API keys, nothing leaves the machine. Aurora
still works if you skip the model pulls (heuristic fallback), just at lower quality.

---

## 🎛️ Choosing your AI engine

Everything is configured by env vars (`.env`, prefix `AURORA_`). Defaults are local.

| Goal | Setting |
|---|---|
| **Local & free (recommended)** | `AURORA_LLM_PROVIDER=ollama` (default) |
| **No model at all** | `AURORA_LLM_PROVIDER=heuristic` — built-in extractive engine |
| **LM Studio / llama.cpp** | `AURORA_LLM_PROVIDER=openai`, `AURORA_LLM_BASE_URL=http://localhost:1234/v1` |
| **Free-tier cloud (e.g. Groq)** | `AURORA_LLM_PROVIDER=openai`, set base URL + `AURORA_LLM_API_KEY` |

See [`.env.example`](.env.example) for every option.

> **On free-tier cloud APIs:** they can be faster than a laptop, but you trade
> away privacy and hit rate/quota limits, and quality varies. Aurora treats them
> as an *optional accelerator*, never a requirement. The recommended path —
> **local Ollama** — has no quotas, no data leaving your machine, and excellent
> quality on an 8B model.

---

## 🧩 Features

**Sources** — drag-and-drop **PDF / DOCX / TXT / Markdown / CSV**, paste text, add a
**web URL** (readable-content extraction) or a **YouTube link** (transcript import).
Optional local **Whisper** transcribes **audio/video**. Select which sources are
"in context" for chat and studio.

**Chat** — hybrid **semantic + keyword** retrieval grounds every answer in your
sources, **streamed token-by-token** (SSE), with **clickable inline `[n]` citations**
that jump to the exact supporting snippet (and a relevance score). Open any citation
to read the **full source with the cited passage highlighted**, save any answer to
**notes** in one click, and start from **source-grounded suggested questions**.

**Switch AI engines from the UI** — a settings panel (⚙️) lets you change provider
(Ollama / OpenAI-compatible / heuristic), model, base URL and API key live, with a
"Save & test" that reports whether the model is reachable — no env editing, no restart.

**Notebook guide** — open a notebook and Aurora auto-generates an at-a-glance
**overview**, **topic chips** (click to ask about a topic), and starter questions.

**Studio** — one-click generation, each saved as an editable note:
Summary · Study Guide · FAQ · Timeline · Key Topics · Briefing Document · Mind Map.

**Audio Overview** — generate a **two-host podcast** (conversational / deep-dive /
debate / solo) from your sources. Script is always produced; audio is synthesized
locally if `pyttsx3` or `piper` is installed.

**Notes** — keep your own markdown notes alongside generated ones.

**Export** — download an entire notebook (source summaries, notes, conversation)
as a single **Markdown** file.

---

## 🗂️ Project layout

```
backend/
  app/
    main.py            FastAPI app (also serves the built SPA)
    config.py          env-driven settings, local-first defaults
    database.py        SQLite schema + connection
    repositories.py    data access (notebooks/sources/chunks/notes/chat/podcasts)
    ai/                ← the swappable brain
      llm.py           Ollama + OpenAI-compatible providers
      embeddings.py    Ollama / sentence-transformers / hashing fallback
      tts.py           piper / pyttsx3 / none
      heuristics.py    zero-model extractive NLP
      engine.py        routes model ↔ heuristic transparently
    services/          ingestion, chunking, vectorstore, search, chat, studio
    routers/           REST API
  tests/               pytest suite (runs fully offline)
frontend/
  src/
    components/        Home, NotebookView (3-pane), Sources/Chat/Studio panels
    lib/markdown.tsx   dependency-free markdown renderer
    api.ts, types.ts
```

---

## ✅ Tests

```bash
make test       # 32 tests, fully offline (heuristic + hashing), no network
make lint       # eslint (frontend)
```

---

## 📜 License

MIT. Use it, fork it, self-host it.

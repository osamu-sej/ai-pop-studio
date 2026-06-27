"""Aurora AI layer.

Everything cognitive lives here behind small, swappable interfaces:

    llm.py         local/optional LLM providers (Ollama default)
    embeddings.py  local/optional embedding providers (+ pure-python fallback)
    tts.py         local text-to-speech for podcasts
    heuristics.py  zero-model algorithmic fallbacks (runs with NO AI installed)
    engine.py      high-level cognition used by the app (routes model<->heuristic)

Design rule: the app NEVER hard-requires a paid API. The default path is
fully on-device, and if no model is installed at all the heuristic engine keeps
every feature working (at reduced quality).
"""

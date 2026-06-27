"""LLM providers.

Default: **Ollama** running on the user's own machine — free, private, offline.
Also supports any **OpenAI-compatible** endpoint (LM Studio, llama.cpp server,
Groq's free tier, OpenRouter, OpenAI, ...) purely via env vars.

If no model is reachable, callers fall back to the heuristic engine, so the
provider layer never raises during normal app use — `available()` tells the
caller which path to take.
"""

from __future__ import annotations

import httpx

from ..config import get_settings


class BaseLLM:
    kind = "none"

    def available(self) -> bool:  # pragma: no cover - interface
        return False

    def chat(self, messages: list[dict], temperature: float | None = None,
             max_tokens: int = 1024) -> str:  # pragma: no cover - interface
        raise NotImplementedError


class OllamaLLM(BaseLLM):
    kind = "ollama"

    def __init__(self, base_url: str, model: str, timeout: float):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def available(self) -> bool:
        try:
            r = httpx.get(f"{self.base_url}/api/tags", timeout=2.0)
            return r.status_code == 200
        except Exception:
            return False

    def chat(self, messages: list[dict], temperature: float | None = None,
             max_tokens: int = 1024) -> str:
        settings = get_settings()
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": settings.llm_temperature if temperature is None else temperature,
                "num_predict": max_tokens,
            },
        }
        r = httpx.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        return (data.get("message") or {}).get("content", "").strip()


class OpenAICompatibleLLM(BaseLLM):
    kind = "openai"

    def __init__(self, base_url: str, model: str, api_key: str, timeout: float):
        # Accept either ".../v1" or a bare host; normalise to a /v1 base.
        base = base_url.rstrip("/")
        if not base.endswith("/v1"):
            base = base + "/v1"
        self.base_url = base
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def available(self) -> bool:
        try:
            r = httpx.get(f"{self.base_url}/models", headers=self._headers(), timeout=3.0)
            return r.status_code < 500
        except Exception:
            return False

    def chat(self, messages: list[dict], temperature: float | None = None,
             max_tokens: int = 1024) -> str:
        settings = get_settings()
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": settings.llm_temperature if temperature is None else temperature,
            "max_tokens": max_tokens,
        }
        r = httpx.post(f"{self.base_url}/chat/completions", headers=self._headers(),
                       json=payload, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()


def build_llm() -> BaseLLM:
    s = get_settings()
    provider = (s.llm_provider or "ollama").lower()
    if provider == "ollama":
        return OllamaLLM(s.llm_base_url, s.llm_model, s.llm_timeout)
    if provider in {"openai", "openai-compatible", "lmstudio", "groq", "openrouter"}:
        return OpenAICompatibleLLM(s.llm_base_url, s.llm_model, s.llm_api_key, s.llm_timeout)
    return BaseLLM()  # "heuristic" / unknown -> not available -> heuristic path


_cached: BaseLLM | None = None


def get_llm(refresh: bool = False) -> BaseLLM:
    global _cached
    if _cached is None or refresh:
        _cached = build_llm()
    return _cached

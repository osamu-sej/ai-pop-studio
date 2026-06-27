"""LLM providers.

Default: **Ollama** running on the user's own machine — free, private, offline.
Also supports any **OpenAI-compatible** endpoint (LM Studio, llama.cpp server,
Groq's free tier, OpenRouter, OpenAI, ...) purely via env vars.

If no model is reachable, callers fall back to the heuristic engine, so the
provider layer never raises during normal app use — `available()` tells the
caller which path to take.
"""

from __future__ import annotations

import json
from collections.abc import Iterator

import httpx

from ..config import get_settings


class BaseLLM:
    kind = "none"

    def available(self) -> bool:  # pragma: no cover - interface
        return False

    def chat(self, messages: list[dict], temperature: float | None = None,
             max_tokens: int = 1024) -> str:  # pragma: no cover - interface
        raise NotImplementedError

    def stream(self, messages: list[dict], temperature: float | None = None,
               max_tokens: int = 1024) -> Iterator[str]:
        """Yield response deltas. Default: a single chunk from chat()."""
        yield self.chat(messages, temperature, max_tokens)


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

    def stream(self, messages: list[dict], temperature: float | None = None,
               max_tokens: int = 1024) -> Iterator[str]:
        settings = get_settings()
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": settings.llm_temperature if temperature is None else temperature,
                "num_predict": max_tokens,
            },
        }
        with httpx.stream("POST", f"{self.base_url}/api/chat", json=payload,
                          timeout=self.timeout) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                delta = (obj.get("message") or {}).get("content", "")
                if delta:
                    yield delta
                if obj.get("done"):
                    break


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

    def stream(self, messages: list[dict], temperature: float | None = None,
               max_tokens: int = 1024) -> Iterator[str]:
        settings = get_settings()
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": settings.llm_temperature if temperature is None else temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        with httpx.stream("POST", f"{self.base_url}/chat/completions",
                          headers=self._headers(), json=payload, timeout=self.timeout) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line[len("data:"):].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                    delta = obj["choices"][0]["delta"].get("content", "")
                except Exception:
                    continue
                if delta:
                    yield delta


def build_llm() -> BaseLLM:
    from . import runtime

    s = get_settings()
    provider = str(runtime.value("llm_provider") or "ollama").lower()
    base_url = runtime.value("llm_base_url")
    model = runtime.value("llm_model")
    api_key = runtime.value("llm_api_key")
    if provider == "ollama":
        return OllamaLLM(base_url, model, s.llm_timeout)
    if provider in {"openai", "openai-compatible", "lmstudio", "groq", "openrouter"}:
        return OpenAICompatibleLLM(base_url, model, api_key, s.llm_timeout)
    return BaseLLM()  # "heuristic" / unknown -> not available -> heuristic path


_cached: BaseLLM | None = None


def get_llm(refresh: bool = False) -> BaseLLM:
    global _cached
    if _cached is None or refresh:
        _cached = build_llm()
    return _cached

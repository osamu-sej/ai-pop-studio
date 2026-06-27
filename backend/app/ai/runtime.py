"""Effective AI configuration = env defaults overlaid with UI-set DB overrides.

This lets users switch provider/model from the app (no env editing, no restart)
while keeping env vars as the baseline. Only a safe allowlist of keys is
overridable.
"""

from __future__ import annotations

from .. import repositories as repo
from ..config import get_settings

OVERRIDABLE = {
    "llm_provider",
    "llm_base_url",
    "llm_model",
    "llm_api_key",
    "embedding_provider",
    "embedding_model",
    "tts_provider",
}


def _overrides() -> dict[str, str]:
    try:
        return {k: v for k, v in repo.get_app_settings().items() if k in OVERRIDABLE}
    except Exception:
        return {}


def value(key: str):
    """Effective value for a key: DB override if present, else env default."""
    ov = _overrides()
    if key in ov and ov[key] != "":
        return ov[key]
    return getattr(get_settings(), key)


def save(values: dict) -> None:
    clean = {k: str(v) for k, v in values.items() if k in OVERRIDABLE and v is not None}
    if clean:
        repo.set_app_settings(clean)

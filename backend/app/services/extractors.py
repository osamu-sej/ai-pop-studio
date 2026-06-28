"""Content extractors — turn any source into clean text + metadata.

Every extractor is local. Web/YouTube obviously need network to *fetch*, but no
third-party AI API is ever involved: PDFs use PyMuPDF, web pages use
BeautifulSoup, YouTube uses the public transcript endpoint, audio uses local
Whisper (optional).

Each returns: (title, text, source_type, metadata).
"""

from __future__ import annotations

import importlib.util
import ipaddress
import re
import socket
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx

from ..config import get_settings
from ..utils import clean_text

UA = "Mozilla/5.0 (compatible; AuroraNotebook/1.0; +local)"


def _assert_safe_url(url: str) -> None:
    """Reject non-http(s) schemes and (by default) private/loopback targets.

    This is an SSRF guard: without it, anyone who can add a URL source could make
    the server fetch internal addresses (cloud metadata, localhost services, …).
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only http(s) URLs are supported")
    host = parsed.hostname
    if not host:
        raise ValueError("Invalid URL host")
    if get_settings().allow_private_urls:
        return
    try:
        infos = socket.getaddrinfo(host, None)
    except Exception as exc:
        raise ValueError(f"Could not resolve host: {host}") from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
            raise ValueError(
                "Refusing to fetch a private/loopback address. "
                "Set AURORA_ALLOW_PRIVATE_URLS=true to allow internal URLs."
            )


# ── PDF ────────────────────────────────────────────────────────────────────
def extract_pdf(data: bytes, filename: str) -> tuple[str, str, str, dict]:
    import fitz  # PyMuPDF

    doc = fitz.open(stream=data, filetype="pdf")
    pages = [page.get_text("text") for page in doc]
    text = clean_text("\n\n".join(pages))
    title = filename
    meta = doc.metadata or {}
    if meta.get("title"):
        title = meta["title"]
    info = {"pages": doc.page_count, "filename": filename}
    doc.close()
    return title, text, "pdf", info


# ── DOCX ───────────────────────────────────────────────────────────────────
def extract_docx(data: bytes, filename: str) -> tuple[str, str, str, dict]:
    import io

    from docx import Document

    doc = Document(io.BytesIO(data))
    paras = [p.text for p in doc.paragraphs if p.text.strip()]
    text = clean_text("\n".join(paras))
    return filename, text, "docx", {"filename": filename, "paragraphs": len(paras)}


# ── Plain text / markdown ──────────────────────────────────────────────────
def extract_text_bytes(data: bytes, filename: str) -> tuple[str, str, str, dict]:
    text = clean_text(data.decode("utf-8", errors="replace"))
    return filename, text, "text", {"filename": filename}


def extract_text(title: str, content: str) -> tuple[str, str, str, dict]:
    return title or "Pasted text", clean_text(content), "text", {}


# ── Web pages ──────────────────────────────────────────────────────────────
def _fetch_validated(url: str, max_redirects: int = 5) -> httpx.Response:
    """Fetch a URL, validating every hop so a redirect can't bypass the SSRF guard."""
    current = url
    with httpx.Client(headers={"User-Agent": UA}, timeout=30.0, follow_redirects=False) as client:
        for _ in range(max_redirects + 1):
            _assert_safe_url(current)
            resp = client.get(current)
            if resp.is_redirect and resp.headers.get("location"):
                current = str(httpx.URL(current).join(resp.headers["location"]))
                continue
            resp.raise_for_status()
            return resp
    raise ValueError("Too many redirects")


def extract_web(url: str, title: str | None = None) -> tuple[str, str, str, dict]:
    from bs4 import BeautifulSoup

    resp = _fetch_validated(url)
    soup = BeautifulSoup(resp.text, "lxml")

    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside", "form"]):
        tag.decompose()

    page_title = title
    if not page_title and soup.title and soup.title.string:
        page_title = soup.title.string.strip()
    page_title = page_title or url

    # Prefer the main/article region if present.
    main = soup.find("article") or soup.find("main") or soup.body or soup
    parts = []
    for el in main.find_all(["h1", "h2", "h3", "h4", "p", "li", "blockquote", "pre"]):
        txt = el.get_text(" ", strip=True)
        if txt:
            prefix = "# " if el.name in {"h1", "h2", "h3", "h4"} else ""
            parts.append(prefix + txt)
    text = clean_text("\n\n".join(parts)) or clean_text(main.get_text("\n", strip=True))
    return page_title, text, "web", {"url": url}


# ── YouTube ────────────────────────────────────────────────────────────────
_YT_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}


def is_youtube(url: str) -> bool:
    try:
        return urlparse(url).hostname in _YT_HOSTS
    except Exception:
        return False


def _youtube_id(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.hostname == "youtu.be":
        return parsed.path.lstrip("/") or None
    if parsed.path == "/watch":
        return parse_qs(parsed.query).get("v", [None])[0]
    m = re.search(r"/(embed|shorts|v)/([A-Za-z0-9_-]{6,})", parsed.path)
    return m.group(2) if m else None


def extract_youtube(url: str) -> tuple[str, str, str, dict]:
    from youtube_transcript_api import YouTubeTranscriptApi

    vid = _youtube_id(url)
    if not vid:
        raise ValueError("Could not parse a YouTube video id from the URL")
    transcript = YouTubeTranscriptApi.get_transcript(vid, languages=["en", "ja", "es", "fr", "de"])
    text = clean_text(" ".join(seg["text"] for seg in transcript))
    title = f"YouTube · {vid}"
    return title, text, "youtube", {"url": url, "video_id": vid}


# ── Audio / video (optional local Whisper) ─────────────────────────────────
def whisper_available() -> bool:
    return importlib.util.find_spec("faster_whisper") is not None


def extract_audio(path: Path, filename: str, model_size: str = "base") -> tuple[str, str, str, dict]:
    from faster_whisper import WhisperModel  # optional

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(str(path))
    text = clean_text(" ".join(seg.text for seg in segments))
    return filename, text, "audio", {"filename": filename, "language": getattr(info, "language", "")}


# ── Dispatcher for URLs ────────────────────────────────────────────────────
def extract_url(url: str, title: str | None = None) -> tuple[str, str, str, dict]:
    if is_youtube(url):
        return extract_youtube(url)
    return extract_web(url, title)

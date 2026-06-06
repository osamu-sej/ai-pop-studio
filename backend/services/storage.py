"""生成画像と弁当レイアウトの永続化（ファイルベース）。

- 画像本体: storage/images/<id>.png
- 画像メタ:  storage/images.json
- 弁当配置:  storage/bento.json

軽量なファイルストレージ。単一プロセス前提のシンプルな実装。
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# backend/storage/
STORAGE_DIR = Path(__file__).resolve().parent.parent / "storage"
IMAGES_DIR = STORAGE_DIR / "images"
IMAGES_META = STORAGE_DIR / "images.json"
BENTO_FILE = STORAGE_DIR / "bento.json"

_lock = threading.Lock()


def _ensure_dirs() -> None:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_meta() -> list[dict[str, Any]]:
    if not IMAGES_META.exists():
        return []
    try:
        return json.loads(IMAGES_META.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _write_meta(items: list[dict[str, Any]]) -> None:
    IMAGES_META.write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def save_image(png_bytes: bytes, prompt: str, style: str | None) -> dict[str, Any]:
    """画像を保存しメタデータを返す。"""
    with _lock:
        _ensure_dirs()
        image_id = uuid.uuid4().hex
        (IMAGES_DIR / f"{image_id}.png").write_bytes(png_bytes)
        record = {
            "id": image_id,
            "prompt": prompt,
            "style": style,
            "url": f"/media/images/{image_id}.png",
            "created_at": _now_iso(),
        }
        items = _read_meta()
        items.insert(0, record)  # 新しい順
        _write_meta(items)
        return record


def list_images() -> list[dict[str, Any]]:
    with _lock:
        return _read_meta()


def delete_image(image_id: str) -> bool:
    """画像を削除。存在すれば True。"""
    with _lock:
        items = _read_meta()
        remaining = [it for it in items if it["id"] != image_id]
        if len(remaining) == len(items):
            return False
        _write_meta(remaining)
        png = IMAGES_DIR / f"{image_id}.png"
        if png.exists():
            png.unlink()
        # この画像を使っている弁当配置からも除去
        _remove_image_from_bento(image_id)
        return True


def get_bento() -> dict[str, Any]:
    """弁当レイアウト（仕切りID -> 画像ID のマップ）を返す。"""
    with _lock:
        if not BENTO_FILE.exists():
            return {"compartments": {}, "updated_at": None}
        try:
            return json.loads(BENTO_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"compartments": {}, "updated_at": None}


def save_bento(compartments: dict[str, str | None]) -> dict[str, Any]:
    """弁当レイアウトを保存する。値が None の仕切りは除外。"""
    with _lock:
        _ensure_dirs()
        cleaned = {k: v for k, v in compartments.items() if v}
        data = {"compartments": cleaned, "updated_at": _now_iso()}
        BENTO_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return data


def _remove_image_from_bento(image_id: str) -> None:
    """（_lock 保持中に呼ぶ）削除画像を弁当配置から外す。"""
    if not BENTO_FILE.exists():
        return
    try:
        data = json.loads(BENTO_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return
    compartments = data.get("compartments", {})
    changed = False
    for slot, img in list(compartments.items()):
        if img == image_id:
            del compartments[slot]
            changed = True
    if changed:
        data["compartments"] = compartments
        data["updated_at"] = _now_iso()
        BENTO_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

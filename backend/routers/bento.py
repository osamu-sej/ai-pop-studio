"""幕の内弁当のレイアウト（仕切りへの画像配置）API。"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from services import storage

router = APIRouter()


class BentoLayout(BaseModel):
    # 使用中の弁当箱プリセットID
    preset: str | None = None
    # 仕切りID -> 画像ID（未配置は null）
    compartments: dict[str, str | None]


@router.get("")
def get_bento():
    """現在の弁当レイアウトを返す。"""
    return storage.get_bento()


@router.put("")
def save_bento(layout: BentoLayout):
    """弁当レイアウトを保存する。"""
    return storage.save_bento(layout.preset, layout.compartments)

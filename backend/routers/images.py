"""画像の生成・保管・一覧・削除API。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services import image_generator, storage

router = APIRouter()


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=500)
    style: str | None = Field(default=None, max_length=50)


@router.post("/generate")
def generate(req: GenerateRequest):
    """プロンプトから画像を生成し、保管して返す。"""
    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="プロンプトを入力してください")
    png = image_generator.generate_image(prompt, style=req.style)
    record = storage.save_image(png, prompt=prompt, style=req.style)
    return record


@router.get("")
def list_images():
    """保管済み画像の一覧（新しい順）。"""
    return {"images": storage.list_images()}


@router.delete("/{image_id}")
def delete_image(image_id: str):
    if not storage.delete_image(image_id):
        raise HTTPException(status_code=404, detail="画像が見つかりません")
    return {"deleted": image_id}

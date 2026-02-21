import json
import os

from fastapi import APIRouter

router = APIRouter()

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")


@router.get("")
async def list_templates():
    """利用可能なテンプレート一覧を返す（テンプレートディレクトリから動的に読み込み）"""
    templates = []

    if not os.path.isdir(TEMPLATES_DIR):
        return {"templates": templates}

    for entry in os.listdir(TEMPLATES_DIR):
        meta_path = os.path.join(TEMPLATES_DIR, entry, "meta.json")
        if not os.path.isfile(meta_path):
            continue
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        total_sheets = len(meta.get("sheets", []))
        products_per_sheet = (
            meta["sheets"][0]["products_per_sheet"] if meta.get("sheets") else 0
        )

        templates.append(
            {
                "template_id": meta["template_id"],
                "name": meta["name"],
                "products_per_sheet": products_per_sheet,
                "total_sheets": total_sheets,
            }
        )

    return {"templates": templates}

from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_templates():
    """利用可能なテンプレート一覧を返す"""
    # TODO: テンプレートディレクトリからメタデータを読み込み
    return {
        "templates": [
            {
                "template_id": "new_pop_np",
                "name": "新規POP",
                "products_per_sheet": 2,
                "total_sheets": 6,
            }
        ]
    }

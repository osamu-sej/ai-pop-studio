import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from services.excel_writer import generate_pop_excel

logger = logging.getLogger(__name__)
router = APIRouter()


class ProductInput(BaseModel):
    product_name: str
    selling_price: int
    tax_rate: float = 1.08
    recommendation: str = ""
    photo_base64: str = ""


class PopGenerateRequest(BaseModel):
    template_id: str
    products: list[ProductInput]


@router.post("/generate")
async def generate_pop(request: PopGenerateRequest):
    """商品情報からPOPを生成し、Excelファイルを返す"""
    if not request.products:
        raise HTTPException(status_code=400, detail="商品が選択されていません")

    try:
        products = [p.model_dump() for p in request.products]
        excel_bytes = generate_pop_excel(request.template_id, products)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"テンプレート '{request.template_id}' が見つかりません",
        )
    except Exception:
        logger.exception("POP生成中にエラーが発生しました")
        raise HTTPException(status_code=500, detail="POP生成に失敗しました")

    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=pop_output.xlsx"},
    )

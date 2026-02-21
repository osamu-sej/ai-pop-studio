from fastapi import APIRouter
from pydantic import BaseModel

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
    # TODO: Excel差し替え処理
    return {"message": "Not implemented yet"}

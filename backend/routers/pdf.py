from fastapi import APIRouter, UploadFile, File

from services.pdf_parser import parse_pdf as _parse_pdf
from services.image_extractor import extract_product_images

router = APIRouter()


@router.post("/parse")
async def parse_pdf(file: UploadFile = File(...)):
    """商品案内PDFを解析し、商品情報を抽出する"""
    pdf_bytes = await file.read()

    # Claude Vision APIでテキスト情報 + 写真座標を抽出
    result = await _parse_pdf(pdf_bytes)

    # 座標情報を使って商品写真をクロップ
    result["products"] = await extract_product_images(pdf_bytes, result["products"])

    return result

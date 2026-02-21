import logging

from fastapi import APIRouter, HTTPException, UploadFile, File

from services.pdf_parser import parse_pdf as _parse_pdf
from services.image_extractor import extract_product_images

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/parse")
async def parse_pdf(file: UploadFile = File(...)):
    """商品案内PDFを解析し、商品情報を抽出する"""
    if file.content_type and file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="PDFファイルのみアップロード可能です")

    pdf_bytes = await file.read()

    if len(pdf_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="ファイルサイズが50MBを超えています")

    if len(pdf_bytes) == 0:
        raise HTTPException(status_code=400, detail="空のファイルです")

    try:
        result = await _parse_pdf(pdf_bytes)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception:
        logger.exception("PDF解析中にエラーが発生しました")
        raise HTTPException(status_code=500, detail="PDF解析に失敗しました")

    try:
        result["products"] = await extract_product_images(pdf_bytes, result["products"])
    except Exception:
        logger.exception("商品写真抽出中にエラーが発生しました")
        # 写真抽出に失敗しても、テキスト情報は返す
        for p in result["products"]:
            p.setdefault("photo_base64", "")

    return result

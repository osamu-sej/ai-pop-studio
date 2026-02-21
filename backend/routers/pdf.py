from fastapi import APIRouter, UploadFile, File

router = APIRouter()


@router.post("/parse")
async def parse_pdf(file: UploadFile = File(...)):
    """商品案内PDFを解析し、商品情報を抽出する"""
    # TODO: Claude Vision APIで解析
    return {
        "products": [],
        "total_pages": 0,
        "total_products": 0,
    }

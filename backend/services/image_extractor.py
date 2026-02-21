"""商品写真抽出サービス - PDFから商品写真をクロップ"""

import base64
import io

import fitz  # PyMuPDF
from PIL import Image


def _render_page_to_image(pdf_bytes: bytes, page_num: int, dpi: int = 300) -> Image.Image:
    """PDFの指定ページをPIL Imageとしてレンダリングする"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[page_num]
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    doc.close()
    return img


def crop_product_photo(
    pdf_bytes: bytes, page_num: int, bbox: dict
) -> str:
    """PDFページから商品写真をクロップし、base64 data URIで返す

    Args:
        pdf_bytes: PDFバイナリ
        page_num: ページ番号（0始まり）
        bbox: 正規化座標 {"x": 0-1, "y": 0-1, "w": 0-1, "h": 0-1}

    Returns:
        "data:image/png;base64,..." 形式の文字列
    """
    img = _render_page_to_image(pdf_bytes, page_num)
    w, h = img.size

    left = int(bbox["x"] * w)
    top = int(bbox["y"] * h)
    right = int((bbox["x"] + bbox["w"]) * w)
    bottom = int((bbox["y"] + bbox["h"]) * h)

    # 境界チェック
    left = max(0, left)
    top = max(0, top)
    right = min(w, right)
    bottom = min(h, bottom)

    cropped = img.crop((left, top, right, bottom))

    buf = io.BytesIO()
    cropped.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


async def extract_product_images(
    pdf_bytes: bytes, products: list[dict]
) -> list[dict]:
    """全商品のphoto_bboxから写真をクロップし、photo_base64を付与して返す"""
    for product in products:
        bbox = product.get("photo_bbox")
        if bbox:
            page_num = product.get("page_number", 1) - 1  # 1始まり→0始まり
            product["photo_base64"] = crop_product_photo(pdf_bytes, page_num, bbox)
        else:
            product["photo_base64"] = ""
    return products

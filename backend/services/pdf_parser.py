"""PDF解析サービス - Claude Vision APIを使用して商品情報を抽出"""

import base64
import json
import os

import anthropic
import fitz  # PyMuPDF

EXTRACTION_PROMPT = """\
この画像はセブンイレブンの商品案内PDFの1ページです。
各商品について以下の情報をJSON配列で抽出してください。

各商品のオブジェクト:
- product_name: 商品名（文字列）
- product_code: 商品コード（文字列、なければ空文字）
- category: カテゴリ（おにぎり、弁当、飲料など。不明なら空文字）
- selling_price: 税抜売価（整数）
- description: 説明文（○で始まる箇条書きをまとめた文字列。なければ空文字）
- delivery_start: 納品開始日（文字列、なければ空文字）
- photo_bbox: 商品写真のバウンディングボックス。画像全体を基準とした正規化座標で、
  {"x": 左端0-1, "y": 上端0-1, "w": 幅0-1, "h": 高さ0-1} 形式。
  写真が見つからない場合はnull。

商品が見つからないページの場合は空配列 [] を返してください。
JSONのみを返し、他のテキストは含めないでください。
"""


def _render_page_to_png(pdf_bytes: bytes, page_num: int, dpi: int = 300) -> bytes:
    """PDFの指定ページをPNG画像としてレンダリングする"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[page_num]
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    png_bytes = pix.tobytes("png")
    doc.close()
    return png_bytes


async def parse_pdf(pdf_bytes: bytes) -> dict:
    """PDFバイナリから商品情報を抽出する

    Returns:
        {
            "products": [...],
            "total_pages": int,
            "total_products": int
        }
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

    client = anthropic.Anthropic(api_key=api_key)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = len(doc)
    doc.close()

    all_products = []

    for page_num in range(total_pages):
        png_bytes = _render_page_to_png(pdf_bytes, page_num)
        b64_image = base64.b64encode(png_bytes).decode("utf-8")

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": b64_image,
                            },
                        },
                        {
                            "type": "text",
                            "text": EXTRACTION_PROMPT,
                        },
                    ],
                }
            ],
        )

        response_text = message.content[0].text.strip()
        # JSON部分を抽出（コードブロックで囲まれている場合に対応）
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])

        try:
            products = json.loads(response_text)
        except json.JSONDecodeError:
            products = []

        for product in products:
            product["page_number"] = page_num + 1
            all_products.append(product)

    return {
        "products": all_products,
        "total_pages": total_pages,
        "total_products": len(all_products),
    }

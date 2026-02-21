"""PDF解析サービス - EasyOCRを使用して商品情報を抽出（API不要）"""

import re
from io import BytesIO

import easyocr
import fitz  # PyMuPDF
import numpy as np
from PIL import Image

# EasyOCR readerはモデルロードが重いのでモジュールレベルで1回だけ初期化
_reader: easyocr.Reader | None = None


def _get_reader() -> easyocr.Reader:
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["ja", "en"], gpu=False)
    return _reader


def _render_page_to_image(pdf_bytes: bytes, page_num: int, dpi: int = 200) -> Image.Image:
    """PDFの指定ページをPIL Imageとしてレンダリングする"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[page_num]
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    doc.close()
    return img


def _ocr_page(img: Image.Image) -> list[tuple]:
    """ページ画像をOCRし、(bbox, text, confidence) のリストを返す

    bboxは [[x1,y1],[x2,y2],[x3,y3],[x4,y4]] 形式（4点座標）
    """
    reader = _get_reader()
    img_array = np.array(img)
    results = reader.readtext(img_array)
    return results


# --- テキストから商品情報を抽出するパターン ---

# 売価パターン: "220円" "¥220" "税抜220" "売価220" など
PRICE_PATTERN = re.compile(
    r"(?:売価|税抜[き]?|本体)?[:\s]*[¥￥]?\s*(\d{2,5})\s*円?", re.UNICODE
)

# 商品コードパターン: 6桁数字
CODE_PATTERN = re.compile(r"\b(\d{6})\b")

# 日付パターン: 2026/02/10 や 2/10 など
DATE_PATTERN = re.compile(r"(\d{1,4}[/年]\d{1,2}[/月]\d{1,2}日?)")

# 説明文パターン: ○で始まる行
DESC_PATTERN = re.compile(r"[○◯〇●・]\s*(.+)")


def _group_texts_into_products(
    ocr_results: list[tuple], img_width: int, img_height: int
) -> list[dict]:
    """OCR結果を位置情報でグルーピングし、商品情報を構造化する

    戦略:
    1. ページを縦方向に走査し、大きな空白（ギャップ）で領域を分割
    2. 横方向にも分割して、2×2などのグリッドレイアウトに対応
    3. 各領域内のテキストから商品名・売価・説明文を抽出
    """
    if not ocr_results:
        return []

    # OCR結果をバウンディングボックスの中心Y座標でソート
    items = []
    for bbox, text, conf in ocr_results:
        # bbox: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        center_x = sum(xs) / 4
        center_y = sum(ys) / 4
        min_x = min(xs)
        max_x = max(xs)
        min_y = min(ys)
        max_y = max(ys)
        items.append({
            "text": text.strip(),
            "conf": conf,
            "center_x": center_x,
            "center_y": center_y,
            "min_x": min_x,
            "max_x": max_x,
            "min_y": min_y,
            "max_y": max_y,
        })

    # Y座標でソート
    items.sort(key=lambda it: it["center_y"])

    # --- 領域分割: Y方向のギャップで水平バンドに分割 ---
    y_gap_threshold = img_height * 0.08  # 画像高さの8%以上のギャップ
    bands = []
    current_band = [items[0]]

    for i in range(1, len(items)):
        gap = items[i]["min_y"] - items[i - 1]["max_y"]
        if gap > y_gap_threshold:
            bands.append(current_band)
            current_band = [items[i]]
        else:
            current_band.append(items[i])
    bands.append(current_band)

    # --- 各バンドを左右に分割（2列レイアウト対応） ---
    mid_x = img_width / 2
    regions = []

    for band in bands:
        left = [it for it in band if it["center_x"] < mid_x]
        right = [it for it in band if it["center_x"] >= mid_x]

        # 左右両方にそれなりの量のテキストがあれば2列として扱う
        if len(left) >= 3 and len(right) >= 3:
            regions.append(left)
            regions.append(right)
        else:
            regions.append(band)

    # --- 各領域から商品情報を抽出 ---
    products = []
    for region in regions:
        product = _extract_product_from_region(region, img_width, img_height)
        if product:
            products.append(product)

    return products


def _extract_product_from_region(
    region: list[dict], img_width: int, img_height: int
) -> dict | None:
    """テキスト領域から商品情報を抽出する"""
    all_text = " ".join(it["text"] for it in region)

    # 売価を探す
    price_match = PRICE_PATTERN.search(all_text)
    selling_price = int(price_match.group(1)) if price_match else 0

    # 商品コードを探す
    code_match = CODE_PATTERN.search(all_text)
    product_code = code_match.group(1) if code_match else ""

    # 日付を探す
    date_match = DATE_PATTERN.search(all_text)
    delivery_start = date_match.group(1) if date_match else ""

    # 説明文（○で始まるテキスト）
    descriptions = []
    for it in region:
        desc_match = DESC_PATTERN.match(it["text"])
        if desc_match:
            descriptions.append(desc_match.group(1))
    description = " ".join(descriptions)

    # 商品名の推定: 最もフォントが大きい（高さが大きい）テキストで、
    # 売価や日付やコードでないもの
    name_candidates = []
    for it in region:
        text = it["text"]
        # 数字のみ、短すぎ、売価パターン、日付パターンは除外
        if len(text) < 2:
            continue
        if re.match(r"^[\d¥￥円%/.,\s]+$", text):
            continue
        if PRICE_PATTERN.match(text):
            continue
        if DATE_PATTERN.match(text):
            continue
        if CODE_PATTERN.match(text) and len(text) <= 7:
            continue
        if DESC_PATTERN.match(text):
            continue
        # 除外キーワード
        skip_keywords = [
            "売価", "原価", "税抜", "税込", "発注", "納品", "グループ",
            "カテゴリ", "商品コード", "入数", "配送", "温度",
        ]
        if any(kw in text for kw in skip_keywords):
            continue
        height = it["max_y"] - it["min_y"]
        name_candidates.append((text, height))

    if not name_candidates and selling_price == 0:
        return None

    # 高さが大きい順にソートして最初のものを商品名とする
    name_candidates.sort(key=lambda x: x[1], reverse=True)
    product_name = name_candidates[0][0] if name_candidates else ""

    if not product_name and selling_price == 0:
        return None

    # 商品写真の領域を推定（テキストが存在しない大きな空白領域）
    # テキスト領域のバウンディングボックスを算出
    text_min_x = min(it["min_x"] for it in region)
    text_max_x = max(it["max_x"] for it in region)
    text_min_y = min(it["min_y"] for it in region)
    text_max_y = max(it["max_y"] for it in region)

    # 領域の右側または上側に写真がある可能性（正規化座標）
    photo_bbox = {
        "x": text_min_x / img_width,
        "y": text_min_y / img_height,
        "w": (text_max_x - text_min_x) / img_width,
        "h": (text_max_y - text_min_y) / img_height,
    }

    return {
        "product_name": product_name,
        "product_code": product_code,
        "selling_price": selling_price,
        "description": description,
        "delivery_start": delivery_start,
        "photo_bbox": photo_bbox,
    }


async def parse_pdf(pdf_bytes: bytes) -> dict:
    """PDFバイナリから商品情報を抽出する（EasyOCR使用、API不要）

    Returns:
        {
            "products": [...],
            "total_pages": int,
            "total_products": int
        }
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = len(doc)
    doc.close()

    all_products = []

    for page_num in range(total_pages):
        img = _render_page_to_image(pdf_bytes, page_num)
        ocr_results = _ocr_page(img)
        products = _group_texts_into_products(ocr_results, img.width, img.height)

        for product in products:
            product["page_number"] = page_num + 1
            all_products.append(product)

    return {
        "products": all_products,
        "total_pages": total_pages,
        "total_products": len(all_products),
    }

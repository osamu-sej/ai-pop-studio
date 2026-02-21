"""Excel差し替えサービス - 正規表現によるDrawingML文字列操作

重要な知見（DESIGN.md 3.3参照）:
- Python xml.etree.ElementTree は書き出し時に名前空間プレフィックスを変更する
  (xdr: → ns0:, a: → ns1: など)
- Excelはこの変更されたプレフィックスを認識できず、描画が全て消える
- 対策: XMLをテキスト（文字列）として扱い、正規表現で差し替える
"""

import base64
import io
import json
import os
import re
import shutil
import tempfile
import zipfile

from PIL import Image

from services.tax_calculator import calc_tax_included

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")


def _load_template_meta(template_id: str) -> dict:
    """テンプレートメタデータJSONを読み込む"""
    meta_path = os.path.join(TEMPLATES_DIR, template_id, "meta.json")
    with open(meta_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _replace_shape_text(drawing_xml: str, shape_name: str, new_text: str) -> str:
    """Shape名でテキスト要素を特定し、テキスト内容を差し替える

    DrawingML内のShape定義は以下のような構造:
    <xdr:sp>
      <xdr:nvSpPr><xdr:cNvPr name="正方形/長方形 8"/></xdr:nvSpPr>
      ...
      <a:t>元のテキスト</a:t>
      ...
    </xdr:sp>
    """
    # Shape名を含むsp要素全体を見つける
    escaped_name = re.escape(shape_name)
    # nvCNvPr（コネクタ）やcNvPr のname属性でShape名を探す
    sp_pattern = re.compile(
        r'(<xdr:sp\b[^>]*>.*?name="' + escaped_name + r'".*?</xdr:sp>)',
        re.DOTALL,
    )
    match = sp_pattern.search(drawing_xml)
    if not match:
        return drawing_xml

    sp_block = match.group(1)
    # sp_block内の全ての <a:t>...</a:t> を見つけて、最初のものを差し替え
    # （複数のa:tがある場合、最初のみ差し替え、残りは空にする）
    t_pattern = re.compile(r"(<a:t>)(.*?)(</a:t>)", re.DOTALL)
    t_matches = list(t_pattern.finditer(sp_block))
    if not t_matches:
        return drawing_xml

    new_sp_block = sp_block
    for i, t_match in enumerate(reversed(t_matches)):
        if i == len(t_matches) - 1:
            # 最初のa:t（逆順なので最後にprocessされる）に新テキストを設定
            replacement = t_match.group(1) + new_text + t_match.group(3)
        else:
            replacement = t_match.group(1) + t_match.group(3)
        new_sp_block = (
            new_sp_block[: t_match.start()]
            + replacement
            + new_sp_block[t_match.end() :]
        )

    return drawing_xml.replace(sp_block, new_sp_block)


def _replace_anchor_text(drawing_xml: str, anchor_index: int, new_text: str) -> str:
    """Anchor番号（0始まり）でテキストを差し替える

    twoCellAnchorの出現順でインデックスを特定する。
    """
    anchor_pattern = re.compile(
        r"(<xdr:twoCellAnchor\b[^>]*>.*?</xdr:twoCellAnchor>)", re.DOTALL
    )
    anchors = list(anchor_pattern.finditer(drawing_xml))
    if anchor_index >= len(anchors):
        return drawing_xml

    anchor_block = anchors[anchor_index].group(1)
    t_pattern = re.compile(r"(<a:t>)(.*?)(</a:t>)", re.DOTALL)
    t_matches = list(t_pattern.finditer(anchor_block))
    if not t_matches:
        return drawing_xml

    new_anchor = anchor_block
    for i, t_match in enumerate(reversed(t_matches)):
        if i == len(t_matches) - 1:
            replacement = t_match.group(1) + new_text + t_match.group(3)
        else:
            replacement = t_match.group(1) + t_match.group(3)
        new_anchor = (
            new_anchor[: t_match.start()]
            + replacement
            + new_anchor[t_match.end() :]
        )

    return drawing_xml.replace(anchor_block, new_anchor)


def _replace_cell_value(sheet_xml: str, cell_ref: str, value: str) -> str:
    """シートXML内の指定セルの値を差し替える

    セル構造例:
    <c r="S36" s="..." t="n"><v>220</v></c>
    """
    escaped_ref = re.escape(cell_ref)
    cell_pattern = re.compile(
        r'(<c\s[^>]*r="' + escaped_ref + r'"[^>]*>.*?<v>)(.*?)(</v>)',
        re.DOTALL,
    )
    return cell_pattern.sub(r"\g<1>" + value + r"\3", sheet_xml)


def _resize_image_to_fit(image_bytes: bytes, target_w: int, target_h: int) -> bytes:
    """画像をターゲットサイズに合わせてリサイズ（レターボックス方式）"""
    img = Image.open(io.BytesIO(image_bytes))
    img = img.convert("RGB")

    # アスペクト比を保持してフィット
    img_ratio = img.width / img.height
    target_ratio = target_w / target_h

    if img_ratio > target_ratio:
        new_w = target_w
        new_h = int(target_w / img_ratio)
    else:
        new_h = target_h
        new_w = int(target_h * img_ratio)

    img = img.resize((new_w, new_h), Image.LANCZOS)

    # 白背景のキャンバスに中央配置
    canvas = Image.new("RGB", (target_w, target_h), (255, 255, 255))
    offset_x = (target_w - new_w) // 2
    offset_y = (target_h - new_h) // 2
    canvas.paste(img, (offset_x, offset_y))

    buf = io.BytesIO()
    canvas.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def generate_pop_excel(template_id: str, products: list[dict]) -> bytes:
    """テンプレートExcelに商品情報を差し替えてPOPを生成する

    Args:
        template_id: テンプレートID
        products: 商品情報のリスト。各商品は以下のキーを持つ:
            - product_name: 商品名
            - selling_price: 税抜売価（整数）
            - tax_rate: 税率（1.08 or 1.10）
            - recommendation: おすすめ文言
            - photo_base64: "data:image/png;base64,..." 形式

    Returns:
        生成されたExcelファイルのバイナリ
    """
    meta = _load_template_meta(template_id)
    template_path = os.path.join(TEMPLATES_DIR, template_id, meta["file"])

    # 作業用一時ディレクトリにZIP展開
    tmp_dir = tempfile.mkdtemp()
    try:
        extract_dir = os.path.join(tmp_dir, "extracted")
        with zipfile.ZipFile(template_path, "r") as zf:
            zf.extractall(extract_dir)

        product_idx = 0

        for sheet_def in meta["sheets"]:
            drawing_file = sheet_def["drawing_file"]
            drawing_path = os.path.join(extract_dir, "xl", "drawings", drawing_file)

            with open(drawing_path, "r", encoding="utf-8") as f:
                drawing_xml = f.read()

            # シートXMLのパスを特定
            sheet_name = sheet_def.get("sheet_xml", "sheet1.xml")
            sheet_path = os.path.join(extract_dir, "xl", "worksheets", sheet_name)
            with open(sheet_path, "r", encoding="utf-8") as f:
                sheet_xml = f.read()

            for slot_name in ["top", "bottom"]:
                if product_idx >= len(products):
                    break

                slot = sheet_def["replacements"].get(slot_name)
                if not slot:
                    continue

                product = products[product_idx]
                product_idx += 1

                # 商品名の差し替え
                if "product_name_shape" in slot:
                    drawing_xml = _replace_shape_text(
                        drawing_xml, slot["product_name_shape"], product["product_name"]
                    )

                # 税抜売価の差し替え（Shape）
                if "price_excl_shape" in slot:
                    price_text = f"{product['selling_price']}円*"
                    drawing_xml = _replace_shape_text(
                        drawing_xml, slot["price_excl_shape"], price_text
                    )

                # 税込価格の差し替え（ShapeまたはAnchor）
                tax_included = calc_tax_included(
                    product["selling_price"], product["tax_rate"]
                )
                if "price_incl_shape" in slot:
                    incl_text = f"(税込:{tax_included}円)"
                    drawing_xml = _replace_shape_text(
                        drawing_xml, slot["price_incl_shape"], incl_text
                    )
                elif "price_incl_anchor" in slot:
                    incl_text = f"(税込:{tax_included}円)"
                    drawing_xml = _replace_anchor_text(
                        drawing_xml, slot["price_incl_anchor"], incl_text
                    )

                # おすすめ文言の差し替え
                recommendation = product.get("recommendation", "")
                if "recommendation_anchor" in slot:
                    drawing_xml = _replace_anchor_text(
                        drawing_xml, slot["recommendation_anchor"], recommendation
                    )
                if "recommendation_anchors" in slot:
                    lines = recommendation.split("\n") if recommendation else [""]
                    for j, anchor_idx in enumerate(slot["recommendation_anchors"]):
                        text = lines[j] if j < len(lines) else ""
                        drawing_xml = _replace_anchor_text(
                            drawing_xml, anchor_idx, text
                        )

                # 商品写真の差し替え
                photo_b64 = product.get("photo_base64", "")
                if photo_b64 and "photo_media" in slot:
                    # base64 data URIからバイナリに変換
                    if "," in photo_b64:
                        photo_b64 = photo_b64.split(",", 1)[1]
                    photo_bytes = base64.b64decode(photo_b64)

                    media_path = os.path.join(
                        extract_dir, "xl", "media", slot["photo_media"]
                    )
                    # 既存画像のサイズを参考にリサイズ
                    if os.path.exists(media_path):
                        existing_img = Image.open(media_path)
                        target_w, target_h = existing_img.size
                        existing_img.close()
                        photo_bytes = _resize_image_to_fit(
                            photo_bytes, target_w, target_h
                        )
                    with open(media_path, "wb") as f:
                        f.write(photo_bytes)

                # セル値の差し替え（売価・税率）
                if "price_cell" in slot:
                    sheet_xml = _replace_cell_value(
                        sheet_xml, slot["price_cell"], str(product["selling_price"])
                    )
                if "tax_rate_cell" in slot:
                    sheet_xml = _replace_cell_value(
                        sheet_xml, slot["tax_rate_cell"], str(product["tax_rate"])
                    )

            # 差し替え後のXMLを書き戻し
            with open(drawing_path, "w", encoding="utf-8") as f:
                f.write(drawing_xml)
            with open(sheet_path, "w", encoding="utf-8") as f:
                f.write(sheet_xml)

        # ZIP再パッケージ
        output_buf = io.BytesIO()
        with zipfile.ZipFile(output_buf, "w", zipfile.ZIP_DEFLATED) as zf_out:
            for root, _dirs, files in os.walk(extract_dir):
                for fname in files:
                    file_path = os.path.join(root, fname)
                    arcname = os.path.relpath(file_path, extract_dir)
                    zf_out.write(file_path, arcname)

        return output_buf.getvalue()

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

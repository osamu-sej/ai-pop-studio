"""excel_writerの正規表現ベース差し替え関数のユニットテスト"""

from services.excel_writer import (
    _replace_shape_text,
    _replace_anchor_text,
    _replace_cell_value,
)


SAMPLE_DRAWING_XML = """\
<xdr:wsDr xmlns:xdr="http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"
          xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <xdr:twoCellAnchor>
    <xdr:sp>
      <xdr:nvSpPr><xdr:cNvPr id="8" name="正方形/長方形 8"/></xdr:nvSpPr>
      <xdr:txBody>
        <a:p><a:r><a:t>元の商品名</a:t></a:r></a:p>
      </xdr:txBody>
    </xdr:sp>
  </xdr:twoCellAnchor>
  <xdr:twoCellAnchor>
    <xdr:sp>
      <xdr:nvSpPr><xdr:cNvPr id="9" name="正方形/長方形 9"/></xdr:nvSpPr>
      <xdr:txBody>
        <a:p><a:r><a:t>100円*</a:t></a:r></a:p>
      </xdr:txBody>
    </xdr:sp>
  </xdr:twoCellAnchor>
  <xdr:twoCellAnchor>
    <xdr:sp>
      <xdr:nvSpPr><xdr:cNvPr id="50" name="おすすめ文言"/></xdr:nvSpPr>
      <xdr:txBody>
        <a:p><a:r><a:t>おすすめ元テキスト</a:t></a:r></a:p>
      </xdr:txBody>
    </xdr:sp>
  </xdr:twoCellAnchor>
</xdr:wsDr>"""


SAMPLE_SHEET_XML = """\
<worksheet>
  <sheetData>
    <row r="36">
      <c r="S36" s="1" t="n"><v>100</v></c>
      <c r="T36" s="1" t="n"><v>1.08</v></c>
    </row>
  </sheetData>
</worksheet>"""


def test_replace_shape_text():
    result = _replace_shape_text(SAMPLE_DRAWING_XML, "正方形/長方形 8", "新しい商品名")
    assert "新しい商品名" in result
    assert "元の商品名" not in result
    # 他のShapeは変更されていないこと
    assert "100円*" in result


def test_replace_shape_text_not_found():
    result = _replace_shape_text(SAMPLE_DRAWING_XML, "存在しないShape", "テスト")
    assert result == SAMPLE_DRAWING_XML


def test_replace_anchor_text():
    result = _replace_anchor_text(SAMPLE_DRAWING_XML, 0, "アンカー0の新テキスト")
    assert "アンカー0の新テキスト" in result
    assert "元の商品名" not in result
    # Anchor 1は変更されていないこと
    assert "100円*" in result


def test_replace_anchor_text_out_of_range():
    result = _replace_anchor_text(SAMPLE_DRAWING_XML, 99, "テスト")
    assert result == SAMPLE_DRAWING_XML


def test_replace_cell_value():
    result = _replace_cell_value(SAMPLE_SHEET_XML, "S36", "220")
    assert "<v>220</v>" in result
    # T36は変更されていないこと
    assert "<v>1.08</v>" in result


def test_replace_cell_value_not_found():
    result = _replace_cell_value(SAMPLE_SHEET_XML, "Z99", "999")
    assert result == SAMPLE_SHEET_XML

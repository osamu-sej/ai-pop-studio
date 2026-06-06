"""画像生成サービス。

現在はモック実装。プロンプト文字列から色とテキストを埋め込んだ
プレースホルダー画像（PNG）を生成する。

将来 OpenAI / Stability AI などの実APIへ差し替える際は、
`generate_image()` の中身だけを置き換えれば良い。
インターフェース（引数・戻り値）は維持する。
"""

from __future__ import annotations

import colorsys
import hashlib
import io

from PIL import Image, ImageDraw, ImageFont

# 生成する画像サイズ（正方形）
IMAGE_SIZE = 512


def _color_from_seed(seed: str, lightness: float = 0.55, saturation: float = 0.55) -> tuple[int, int, int]:
    """文字列シードから安定した RGB 色を作る。"""
    h = int(hashlib.sha256(seed.encode("utf-8")).hexdigest(), 16)
    hue = (h % 360) / 360.0
    r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
    return int(r * 255), int(g * 255), int(b * 255)


def _vertical_gradient(size: int, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    """上下のグラデーション背景を生成する。"""
    base = Image.new("RGB", (size, size), top)
    draw = ImageDraw.Draw(base)
    for y in range(size):
        t = y / max(size - 1, 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        draw.line([(0, y), (size, y)], fill=(r, g, b))
    return base


def _load_font(size: int) -> ImageFont.ImageFont:
    """利用可能ならTrueTypeフォント、無ければデフォルトフォントを読み込む。"""
    candidates = [
        # 日本語対応フォントを優先
        "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf",
        "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
        "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        # フォールバック（英数字のみ）
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap_text(text: str, max_chars: int) -> list[str]:
    """文字数ベースで折り返す（日本語は空白が無いため文字数で分割）。"""
    text = text.strip()
    if not text:
        return ["(no prompt)"]
    lines: list[str] = []
    current = ""
    for ch in text:
        if ch == "\n":
            lines.append(current)
            current = ""
            continue
        current += ch
        if len(current) >= max_chars:
            lines.append(current)
            current = ""
    if current:
        lines.append(current)
    return lines[:6]  # 最大6行まで


def generate_image(prompt: str, *, style: str | None = None) -> bytes:
    """プロンプトから画像（PNGバイト列）を生成する。

    モック実装: プロンプトのハッシュから配色を決め、
    グラデーション背景にプロンプト文字列を描画する。
    """
    seed = f"{prompt}|{style or ''}"
    top = _color_from_seed(seed + "-top", lightness=0.62, saturation=0.5)
    bottom = _color_from_seed(seed + "-bottom", lightness=0.42, saturation=0.6)

    img = _vertical_gradient(IMAGE_SIZE, top, bottom)
    draw = ImageDraw.Draw(img)

    # 中央の「お皿」風の円
    plate_margin = IMAGE_SIZE // 6
    draw.ellipse(
        [plate_margin, plate_margin, IMAGE_SIZE - plate_margin, IMAGE_SIZE - plate_margin],
        fill=_color_from_seed(seed + "-plate", lightness=0.85, saturation=0.25),
        outline=(255, 255, 255),
        width=4,
    )

    # プロンプト文字列を中央に描画
    font = _load_font(28)
    lines = _wrap_text(prompt, max_chars=12)
    line_height = 36
    total_h = line_height * len(lines)
    y = (IMAGE_SIZE - total_h) // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (IMAGE_SIZE - w) // 2
        # 読みやすさのため影付き
        draw.text((x + 1, y + 1), line, font=font, fill=(0, 0, 0))
        draw.text((x, y), line, font=font, fill=(255, 255, 255))
        y += line_height

    # 右下に MOCK ラベル
    small_font = _load_font(18)
    label = "MOCK"
    if style:
        label += f" · {style}"
    draw.text((14, IMAGE_SIZE - 28), label, font=small_font, fill=(255, 255, 255))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

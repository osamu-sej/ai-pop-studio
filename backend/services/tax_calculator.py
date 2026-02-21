"""税込価格計算サービス"""

from decimal import Decimal, ROUND_HALF_UP


def calc_tax_included(price: int, tax_rate: float) -> str:
    """税抜価格から税込価格を計算する

    Args:
        price: 税抜売価（整数）
        tax_rate: 税率（1.08 or 1.10）

    Returns:
        税込価格（小数第2位まで、例: "237.60"）
    """
    result = Decimal(str(price)) * Decimal(str(tax_rate))
    return str(result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

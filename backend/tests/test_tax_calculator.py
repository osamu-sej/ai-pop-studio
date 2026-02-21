from services.tax_calculator import calc_tax_included


def test_8_percent_tax():
    assert calc_tax_included(220, 1.08) == "237.60"


def test_10_percent_tax():
    assert calc_tax_included(220, 1.10) == "242.00"


def test_zero_price():
    assert calc_tax_included(0, 1.08) == "0.00"


def test_rounding():
    # 178 * 1.08 = 192.24
    assert calc_tax_included(178, 1.08) == "192.24"


def test_large_price():
    # 648 * 1.08 = 699.84
    assert calc_tax_included(648, 1.08) == "699.84"

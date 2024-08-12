from src.bond import create_default_bond
from src.price import update_price


def test_simple():
    data = [create_default_bond(index=1)]
    update_price(data, rate_data=[{"Rate": 0.05, "Year": 0}, {"Rate": 0.05, "Year": 5}])
    assert data[0]["Price"] == "$101.798925"

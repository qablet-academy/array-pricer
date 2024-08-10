from src.bond import create_default_bond
from src.price import update_price


def simple_test():
    data = [create_default_bond(index=1)]
    update_price(data, rate_data=[{"Rate": 0.05, "Term": 1}])
    assert data[0]["Price"] == 105.0

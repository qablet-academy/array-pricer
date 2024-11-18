from datetime import datetime

import pytest

from src.price import calculate_key_rate_duration


# Sample bond data and rate data
@pytest.fixture
def bond_data_example():
    return [
        {
            "Bond": "Bond 1",
            "Currency": "USD",
            "Coupon": 5.0,
            "Accrual Start": "2024-01-02",
            "Maturity": "2025-01-02",
            "Frequency": 1,
            "Notional": 1000000,
        }
    ]


@pytest.fixture
def rate_data_example():
    return [
        {"Year": 1 / 12, "Rate": 5.55},
        {"Year": 2 / 12, "Rate": 5.54},
        {"Year": 3 / 12, "Rate": 5.46},
        {"Year": 4 / 12, "Rate": 5.41},
        {"Year": 6 / 12, "Rate": 5.24},
        {"Year": 1, "Rate": 4.80},
        {"Year": 2, "Rate": 4.33},
        {"Year": 3, "Rate": 4.09},
        {"Year": 5, "Rate": 3.93},
        {"Year": 7, "Rate": 3.95},
        {"Year": 10, "Rate": 3.95},
        {"Year": 20, "Rate": 4.25},
        {"Year": 30, "Rate": 4.08},
    ]


def test_calculate_key_rate_duration(bond_data_example, rate_data_example):
    # Set the pricing date
    pricing_datetime = datetime(2024, 1, 2)

    # Call the calculate_key_rate_duration function
    krd_result = calculate_key_rate_duration(
        bond_data_example, rate_data_example, pricing_datetime
    )

    # Check that the result is not empty and contains the expected structure
    assert len(krd_result) == 1
    assert krd_result[0]["Bond"] == "Bond 1"
    assert "Maturity (Years)" in krd_result[0]
    assert "1 Mo" in krd_result[0]
    assert "1 Yr" in krd_result[0]
    assert "30 Yr" in krd_result[0]

    # Optionally print the result for review
    print("KRD Result:", krd_result)

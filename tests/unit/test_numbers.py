"""Unit tests for Indian currency and count parsing."""

from app.numbers import parse_count, parse_money_to_inr


def test_golden_money_cases() -> None:
    """Verify all offline golden cases for INR monetary parsing."""
    assert parse_money_to_inr("Rs 50 lakh") == 5000000.0
    assert parse_money_to_inr("1.2 crore") == 12000000.0
    assert parse_money_to_inr("Rs 5,00,000") == 500000.0
    assert parse_money_to_inr("75,000") == 75000.0
    assert parse_money_to_inr("no money here") is None


def test_additional_money_cases() -> None:
    """Verify edge cases with prefixes, decimals, and slash notation."""
    assert parse_money_to_inr("Rs. 2,50,000/-") == 250000.0
    assert parse_money_to_inr("INR 10.5 Lakh") == 1050000.0
    assert parse_money_to_inr("₹ 3.5 Crore") == 35000000.0
    assert parse_money_to_inr("Rs 50,00,000") == 5000000.0
    assert parse_money_to_inr("") is None


def test_parse_count() -> None:
    """Verify integer extraction from count descriptions."""
    assert parse_count("At least 2 orders required") == 2
    assert parse_count("Experience in 3 projects") == 3
    assert parse_count("Order count: 15 units") == 15
    assert parse_count("No numbers here") is None
    assert parse_count("") is None

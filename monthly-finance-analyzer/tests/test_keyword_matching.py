"""Tests for safe keyword matching (word-boundary aware)."""
import pandas as pd
from pathlib import Path

from finance_analyzer.keyword_match import keyword_matches, contains_any
from finance_analyzer.categorizer import categorize_transactions


def test_fee_does_not_match_coffee():
    """'fee' keyword must not fire on 'COFFEE SHOP'."""
    assert not keyword_matches("coffee shop", "fee"), (
        "'fee' should not match inside 'coffee'"
    )


def test_fee_matches_standalone():
    """'fee' keyword must match when it appears as a standalone word."""
    assert keyword_matches("late fee charged", "fee")


def test_late_fee_matches():
    assert keyword_matches("late fee", "late fee")


def test_interest_charge_matches():
    assert keyword_matches("interest charge posted", "interest")


def test_coffee_shop_not_classified_as_fee():
    """COFFEE SHOP should not be categorised as Fees via the category rules."""
    df = pd.DataFrame([{
        "Month": "2026-05",
        "Transaction ID": "ID-001",
        "Raw Description": "COFFEE SHOP",
        "Cleaned Merchant": "Coffee Shop",
        "Category": "Needs Review",
        "Subcategory": "Needs Review",
        "Necessary Label": "Needs Review",
        "Notes": "",
    }])
    result = categorize_transactions(df, Path("rules/category_rules.yaml"))
    assert result.loc[0, "Category"] != "Fees", (
        "COFFEE SHOP must not be categorized as Fees"
    )


def test_late_fee_classified_as_fee():
    """LATE FEE should be categorised as Fees."""
    df = pd.DataFrame([{
        "Month": "2026-05",
        "Transaction ID": "ID-001",
        "Raw Description": "LATE FEE",
        "Cleaned Merchant": "Bank",
        "Category": "Needs Review",
        "Subcategory": "Needs Review",
        "Necessary Label": "Needs Review",
        "Notes": "",
    }])
    result = categorize_transactions(df, Path("rules/category_rules.yaml"))
    assert result.loc[0, "Category"] == "Fees", (
        "LATE FEE must be categorized as Fees"
    )


def test_interest_charge_classified_as_fee():
    """INTEREST CHARGE should be categorised as Fees."""
    df = pd.DataFrame([{
        "Month": "2026-05",
        "Transaction ID": "ID-001",
        "Raw Description": "INTEREST CHARGE",
        "Cleaned Merchant": "Bank",
        "Category": "Needs Review",
        "Subcategory": "Needs Review",
        "Necessary Label": "Needs Review",
        "Notes": "",
    }])
    result = categorize_transactions(df, Path("rules/category_rules.yaml"))
    assert result.loc[0, "Category"] == "Fees", (
        "INTEREST CHARGE must be categorized as Fees"
    )

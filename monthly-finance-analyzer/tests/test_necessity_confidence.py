"""Tests for Necessity Confidence and Necessity Reason fields."""
from pathlib import Path

import pandas as pd

from finance_analyzer.categorizer import categorize_transactions
from finance_analyzer.necessity_classifier import classify_necessity, NECESSITY_CONFIDENCE


def _make_row(txn_id, raw_desc, merchant, category="Needs Review"):
    return {
        "Month": "2026-05",
        "Transaction ID": txn_id,
        "Raw Description": raw_desc,
        "Cleaned Merchant": merchant,
        "Category": category,
        "Subcategory": "Needs Review",
        "Necessary Label": "Needs Review",
        "Notes": "",
    }


def test_netflix_possibly_unnecessary_with_confidence():
    """Netflix / Subscriptions → Possibly Unnecessary with confidence 0.75."""
    df = pd.DataFrame([_make_row("ID-001", "NETFLIX.COM", "Netflix")])
    categorized = categorize_transactions(df, Path("rules/category_rules.yaml"))
    classified = classify_necessity(categorized, Path("rules/necessity_rules.yaml"))

    row = classified.iloc[0]
    assert row["Necessary Label"] == "Possibly Unnecessary"
    assert row["Necessity Confidence"] == NECESSITY_CONFIDENCE["Possibly Unnecessary"]
    assert row["Necessity Reason"] != ""


def test_fee_unnecessary_with_confidence():
    """Fees → Unnecessary with confidence 0.95."""
    df = pd.DataFrame([_make_row("ID-001", "LATE FEE", "Bank")])
    categorized = categorize_transactions(df, Path("rules/category_rules.yaml"))
    classified = classify_necessity(categorized, Path("rules/necessity_rules.yaml"))

    row = classified.iloc[0]
    assert row["Necessary Label"] == "Unnecessary"
    assert row["Necessity Confidence"] == NECESSITY_CONFIDENCE["Unnecessary"]
    assert row["Necessity Reason"] != ""


def test_unknown_merchant_needs_review_with_confidence():
    """Unknown merchant → Needs Review with confidence 0.30."""
    df = pd.DataFrame([_make_row("ID-001", "XYZZY UNKNOWN CO", "Unknown Merchant")])
    categorized = categorize_transactions(df, Path("rules/category_rules.yaml"))
    classified = classify_necessity(categorized, Path("rules/necessity_rules.yaml"))

    row = classified.iloc[0]
    assert row["Necessary Label"] == "Needs Review"
    assert row["Necessity Confidence"] == NECESSITY_CONFIDENCE["Needs Review"]
    assert "review" in row["Necessity Reason"].lower()


def test_necessary_has_confidence_but_no_reason():
    """Necessary label has confidence 0.90 and empty reason string."""
    df = pd.DataFrame([_make_row("ID-001", "WALMART", "Walmart", category="Groceries")])
    classified = classify_necessity(df, Path("rules/necessity_rules.yaml"))

    row = classified.iloc[0]
    assert row["Necessary Label"] == "Necessary"
    assert row["Necessity Confidence"] == NECESSITY_CONFIDENCE["Necessary"]
    assert row["Necessity Reason"] == ""

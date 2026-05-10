"""Tests for transfer and payment excluded totals.

The excluded amount must reflect one side of the matched pair (not sum both
sides and get zero).
"""
from pathlib import Path

import pandas as pd

from finance_analyzer.analytics import run_analytics
from finance_analyzer.transfer_detector import detect_transfers_and_duplicates


def _row(txn_id, account, date, desc, merchant, amount, direction, txn_type, include):
    return {
        "Transaction ID": txn_id,
        "Month": "2026-05",
        "Account": account,
        "Transaction Date": date,
        "Raw Description": desc,
        "Cleaned Merchant": merchant,
        "Amount": amount,
        "Direction": direction,
        "Type": txn_type,
        "Include in Spending": include,
        "Category": "Transfers",
        "Necessary Label": "Needs Review",
        "Notes": "",
    }


def _analytics_row(txn_id, account, date, desc, merchant, amount, txn_type, include, necessary="Needs Review", category="Transfers"):
    return {
        "Month": "2026-05",
        "Transaction ID": txn_id,
        "Account": account,
        "Transaction Date": date,
        "Raw Description": desc,
        "Cleaned Merchant": merchant,
        "Amount": amount,
        "Type": txn_type,
        "Include in Spending": include,
        "Category": category,
        "Necessary Label": necessary,
        "Notes": "",
    }


def test_transfer_excluded_not_zero():
    """Checking→Savings transfer should report 500 excluded, not 0."""
    df = pd.DataFrame([
        _analytics_row("ID-001", "Checking", "2026-05-10", "TRANSFER TO SAVINGS", "Savings", -500.0, "Transfer", "Exclude"),
        _analytics_row("ID-002", "Savings", "2026-05-10", "TRANSFER FROM CHECKING", "Checking", 500.0, "Transfer", "Exclude"),
    ])

    result = run_analytics(df, "2026-05")
    assert result["summary"]["transfers_excluded"] == 500.0, (
        f"Expected 500.0, got {result['summary']['transfers_excluded']}"
    )


def test_credit_card_payment_excluded_not_zero():
    """CC payment from checking + matching received on CC should report 100 excluded, not 0."""
    df = pd.DataFrame([
        _analytics_row("ID-001", "Checking", "2026-05-10", "CC PAYMENT", "Credit Card", -100.0, "Payment", "Exclude"),
        _analytics_row("ID-002", "Credit Card", "2026-05-11", "PAYMENT RECEIVED", "Credit Card", 100.0, "Payment", "Exclude"),
    ])

    result = run_analytics(df, "2026-05")
    assert result["summary"]["credit_card_payments_excluded"] == 100.0, (
        f"Expected 100.0, got {result['summary']['credit_card_payments_excluded']}"
    )


def test_transfer_detection_and_exclusion(tmp_path):
    """detect_transfers_and_duplicates correctly marks both sides; analytics reports outgoing only."""
    rules_path = Path("rules/transfer_rules.yaml")
    df = pd.DataFrame([
        _row("ID-001", "Checking", "2026-05-10", "TRANSFER TO SAVINGS", "Savings", -500.0, "Money Out", "Expense", "Include"),
        _row("ID-002", "Savings", "2026-05-10", "TRANSFER FROM CHECKING", "Checking", 500.0, "Money In", "Income", "Exclude"),
    ])

    result = detect_transfers_and_duplicates(df, rules_path)
    assert set(result["Type"].tolist()) == {"Transfer"}
    assert set(result["Include in Spending"].tolist()) == {"Exclude"}


def test_payment_detection_and_exclusion():
    """Credit card payment detection marks both rows; analytics reports outgoing only."""
    rules_path = Path("rules/transfer_rules.yaml")
    df = pd.DataFrame([
        _row("ID-001", "Checking", "2026-05-10", "AUTOPAY CREDIT CARD PAYMENT", "Credit Card", -100.0, "Money Out", "Expense", "Include"),
        _row("ID-002", "Credit Card", "2026-05-11", "PAYMENT RECEIVED", "Credit Card", 100.0, "Money In", "Income", "Exclude"),
    ])

    result = detect_transfers_and_duplicates(df, rules_path)
    assert set(result["Type"].tolist()) == {"Payment"}
    assert set(result["Include in Spending"].tolist()) == {"Exclude"}

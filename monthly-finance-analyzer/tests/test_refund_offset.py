"""Tests for refund offset math: Gross Spending, Refund Offsets, Net Spending."""
import pandas as pd

from finance_analyzer.analytics import run_analytics


def _base_row(txn_id, month, amount, txn_type, include, necessary="Necessary", category="Groceries"):
    return {
        "Month": month,
        "Transaction ID": txn_id,
        "Account": "Checking",
        "Transaction Date": "2026-05-01",
        "Raw Description": "TEST",
        "Cleaned Merchant": "Test Merchant",
        "Amount": amount,
        "Type": txn_type,
        "Include in Spending": include,
        "Category": category,
        "Necessary Label": necessary,
        "Notes": "",
    }


def test_refund_reduces_net_spending():
    df = pd.DataFrame([
        _base_row("ID-001", "2026-05", 3000.0, "Income", "Exclude"),
        _base_row("ID-002", "2026-05", -100.0, "Expense", "Include"),
        _base_row("ID-003", "2026-05", 25.0, "Refund", "Offset"),
    ])

    result = run_analytics(df, "2026-05")
    s = result["summary"]

    assert s["gross_spending"] == 100.0, f"Expected gross_spending=100, got {s['gross_spending']}"
    assert s["refund_offsets"] == 25.0, f"Expected refund_offsets=25, got {s['refund_offsets']}"
    assert s["net_spending"] == 75.0, f"Expected net_spending=75, got {s['net_spending']}"


def test_net_cash_flow_uses_net_spending():
    df = pd.DataFrame([
        _base_row("ID-001", "2026-05", 3000.0, "Income", "Exclude"),
        _base_row("ID-002", "2026-05", -100.0, "Expense", "Include"),
        _base_row("ID-003", "2026-05", 25.0, "Refund", "Offset"),
    ])

    result = run_analytics(df, "2026-05")
    s = result["summary"]

    # Net cash flow = Income - Net Spending = 3000 - 75 = 2925
    assert s["net_cash_flow"] == 2925.0


def test_refund_not_offset_does_not_reduce_spending():
    """A refund marked Exclude (not Offset) should not reduce net spending."""
    df = pd.DataFrame([
        _base_row("ID-001", "2026-05", 3000.0, "Income", "Exclude"),
        _base_row("ID-002", "2026-05", -100.0, "Expense", "Include"),
        _base_row("ID-003", "2026-05", 25.0, "Refund", "Exclude"),
    ])

    result = run_analytics(df, "2026-05")
    s = result["summary"]

    assert s["gross_spending"] == 100.0
    assert s["refund_offsets"] == 0.0
    assert s["net_spending"] == 100.0

"""Tests for stable transaction IDs in loader.

Same credit card account must keep the same CC prefix across all rows.
Two different credit card accounts must receive different stable prefixes.
"""
import pandas as pd
import pytest
import openpyxl
from pathlib import Path
import tempfile

from finance_analyzer.loader import load_transactions, _build_account_short_map


def _make_workbook(rows: list[dict], tmp_path: Path) -> Path:
    """Write a minimal Transactions workbook for testing."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Transactions"

    headers = [
        "Month", "Account", "Account Type", "Transaction Date", "Posted Date",
        "Raw Description", "Cleaned Merchant", "Amount", "Direction", "Type",
        "Category", "Subcategory", "Necessary Label", "Include in Spending",
        "Notes", "Reviewed",
    ]
    ws.append(headers)
    for row in rows:
        ws.append([row.get(h, "") for h in headers])

    path = tmp_path / "test_transactions.xlsx"
    wb.save(str(path))
    return path


def _base_row(account, account_type="Credit Card"):
    return {
        "Month": "2026-05",
        "Account": account,
        "Account Type": account_type,
        "Transaction Date": "2026-05-01",
        "Posted Date": "2026-05-01",
        "Raw Description": "PURCHASE",
        "Cleaned Merchant": "Merchant",
        "Amount": -50.0,
        "Direction": "Money Out",
        "Type": "Expense",
        "Category": "Shopping",
        "Subcategory": "General",
        "Necessary Label": "Possibly Unnecessary",
        "Include in Spending": "Include",
        "Notes": "",
        "Reviewed": False,
    }


def test_same_credit_card_keeps_same_prefix(tmp_path):
    rows = [_base_row("My Visa Card") for _ in range(3)]
    path = _make_workbook(rows, tmp_path)
    df = load_transactions(path)

    prefixes = set(df["Account Short"].tolist())
    assert len(prefixes) == 1, f"All rows from same account should share one prefix, got {prefixes}"
    assert list(prefixes)[0] == "CC1"


def test_two_credit_cards_get_different_prefixes(tmp_path):
    rows = [
        _base_row("My Visa Card"),
        _base_row("My Mastercard"),
        _base_row("My Visa Card"),
    ]
    path = _make_workbook(rows, tmp_path)
    df = load_transactions(path)

    visa_prefix = df.loc[df["Account"] == "My Visa Card", "Account Short"].iloc[0]
    mc_prefix = df.loc[df["Account"] == "My Mastercard", "Account Short"].iloc[0]
    assert visa_prefix != mc_prefix, "Different accounts must get different prefixes"
    assert {visa_prefix, mc_prefix} == {"CC1", "CC2"}


def test_build_account_short_map_stable():
    """_build_account_short_map assigns stable codes per unique account."""
    accounts = pd.Series(["My Visa Card", "My Visa Card", "My Mastercard", "Checking", "My Visa Card"])
    m = _build_account_short_map(accounts)
    assert m["my visa card"] == "CC1"
    assert m["my mastercard"] == "CC2"
    assert m["checking"] == "CHK"

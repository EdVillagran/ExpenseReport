"""Tests for blank and invalid Posted Date handling in the validator."""
import pandas as pd
import pytest

from finance_analyzer.validator import validate_transactions


def _base_row(posted_date):
    return {
        "Month": "2026-05",
        "Account": "Checking",
        "Account Type": "Checking",
        "Transaction Date": "2026-05-01",
        "Posted Date": posted_date,
        "Raw Description": "WALMART",
        "Cleaned Merchant": "Walmart",
        "Amount": -25.0,
        "Direction": "Money Out",
        "Type": "Expense",
        "Category": "Groceries",
        "Subcategory": "Grocery Stores",
        "Necessary Label": "Necessary",
        "Include in Spending": "Include",
        "Notes": "",
        "Reviewed": True,
        "Original Row Number": 2,
        "Transaction ID": "2026-05-CHK-001",
    }


def test_blank_posted_date_is_allowed():
    """A blank Posted Date must not produce an 'Invalid date' issue."""
    df = pd.DataFrame([_base_row("")])
    _, issues = validate_transactions(df)
    posted_date_issues = issues[
        (issues["Issue"] == "Invalid date") & (issues["Detail"] == "Posted Date")
    ] if not issues.empty else pd.DataFrame()
    assert posted_date_issues.empty, "Blank Posted Date should not flag an Invalid date issue"


def test_none_posted_date_is_allowed():
    """A None/NaN Posted Date must not produce an 'Invalid date' issue."""
    df = pd.DataFrame([_base_row(None)])
    _, issues = validate_transactions(df)
    posted_date_issues = issues[
        (issues["Issue"] == "Invalid date") & (issues["Detail"] == "Posted Date")
    ] if not issues.empty else pd.DataFrame()
    assert posted_date_issues.empty, "None Posted Date should not flag an Invalid date issue"


def test_bad_posted_date_is_flagged():
    """A non-blank unparseable Posted Date must still produce an 'Invalid date' issue."""
    df = pd.DataFrame([_base_row("not-a-date")])
    _, issues = validate_transactions(df)
    assert not issues.empty
    assert ((issues["Issue"] == "Invalid date") & (issues["Detail"] == "Posted Date")).any(), (
        "A non-blank invalid Posted Date should create an 'Invalid date' issue"
    )

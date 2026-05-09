import pandas as pd
import pytest

from finance_analyzer.loader import load_transactions
from finance_analyzer.models import REQUIRED_COLUMNS
from finance_analyzer.validator import validate_transactions


def _base_df() -> pd.DataFrame:
    data = {
        "Month": ["2026-05"],
        "Account": ["Checking"],
        "Account Type": ["Checking"],
        "Transaction Date": ["2026-05-01"],
        "Posted Date": ["2026-05-01"],
        "Raw Description": ["WAL-MART #123"],
        "Cleaned Merchant": [""],
        "Amount": [-25.0],
        "Direction": ["Money Out"],
        "Type": ["Expense"],
        "Category": ["Needs Review"],
        "Subcategory": ["Needs Review"],
        "Necessary Label": ["Needs Review"],
        "Include in Spending": ["Include"],
        "Notes": [""],
        "Reviewed": [False],
    }
    df = pd.DataFrame(data)
    df["Original Row Number"] = [2]
    df["Transaction ID"] = ["2026-05-CHK-001"]
    return df


def test_missing_required_columns_raises():
    df = pd.DataFrame({"Month": ["2026-05"]})
    with pytest.raises(ValueError):
        validate_transactions(df)


def test_invalid_amount_flagged():
    df = _base_df()
    df.loc[0, "Amount"] = "bad"
    _, issues = validate_transactions(df)
    assert (issues["Issue"] == "Invalid amount").any()


def test_duplicate_detection_flags_rows():
    df = pd.concat([_base_df(), _base_df()], ignore_index=True)
    df.loc[1, "Transaction ID"] = "2026-05-CHK-002"
    df.loc[1, "Original Row Number"] = 3
    _, issues = validate_transactions(df)
    assert (issues["Issue"] == "Duplicate-looking row").any()

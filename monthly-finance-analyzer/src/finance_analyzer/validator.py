from __future__ import annotations

import re
from typing import Iterable

import pandas as pd

from .models import (
    REQUIRED_COLUMNS,
    VALID_DIRECTIONS,
    VALID_INCLUDE_VALUES,
    VALID_NECESSITY_LABELS,
    VALID_TYPES,
)


_MONTH_PATTERN = re.compile(r"^\d{4}-\d{2}$")


def _string(value: object) -> str:
    return "" if pd.isna(value) else str(value).strip()


def _issue(txn_id: str, row: int, issue: str, detail: str) -> dict:
    return {
        "Transaction ID": txn_id,
        "Row Number": row,
        "Issue": issue,
        "Detail": detail,
    }


def _append_issue(issues: list[dict], row: pd.Series, issue: str, detail: str) -> None:
    issues.append(_issue(_string(row.get("Transaction ID")), int(row.get("Original Row Number", -1)), issue, detail))


def _find_duplicate_candidates(df: pd.DataFrame) -> Iterable[tuple[int, int]]:
    work = df.copy()
    work["_desc"] = work["Raw Description"].fillna("").astype(str).str.strip().str.lower()
    work["_dt"] = pd.to_datetime(work["Transaction Date"], errors="coerce")
    grouped = work.groupby(["Account", "_desc", "Amount"], dropna=False)
    for _, group in grouped:
        if len(group) < 2:
            continue
        idxs = list(group.index)
        for i, left in enumerate(idxs):
            for right in idxs[i + 1 :]:
                ldt = work.at[left, "_dt"]
                rdt = work.at[right, "_dt"]
                if pd.isna(ldt) or pd.isna(rdt):
                    yield left, right
                elif abs((ldt - rdt).days) <= 3:
                    yield left, right


def validate_transactions(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

    work = df.copy()
    issues: list[dict] = []

    work["Amount"] = pd.to_numeric(work["Amount"], errors="coerce")
    work["Transaction Date Parsed"] = pd.to_datetime(work["Transaction Date"], errors="coerce")
    work["Posted Date Parsed"] = pd.to_datetime(work["Posted Date"], errors="coerce")

    for idx, row in work.iterrows():
        txn_id = _string(row.get("Transaction ID"))

        month = _string(row["Month"])
        if not _MONTH_PATTERN.match(month):
            _append_issue(issues, row, "Invalid month", f"Month must be YYYY-MM, got '{month}'")

        for field in ["Month", "Account", "Transaction Date", "Raw Description", "Amount", "Direction", "Type"]:
            if _string(row.get(field, "")) == "" or pd.isna(row.get(field)):
                _append_issue(issues, row, "Missing required field", field)

        if pd.isna(row["Transaction Date Parsed"]):
            _append_issue(issues, row, "Invalid date", "Transaction Date")
        if pd.isna(row["Posted Date Parsed"]):
            _append_issue(issues, row, "Invalid date", "Posted Date")
        if pd.isna(row["Amount"]):
            _append_issue(issues, row, "Invalid amount", "Amount must be numeric")

        txn_type = _string(row["Type"])
        if txn_type not in VALID_TYPES:
            _append_issue(issues, row, "Invalid type", txn_type)

        direction = _string(row["Direction"])
        if direction not in VALID_DIRECTIONS:
            _append_issue(issues, row, "Invalid direction", direction)

        include_value = _string(row["Include in Spending"])
        if include_value and include_value not in VALID_INCLUDE_VALUES:
            _append_issue(issues, row, "Invalid include value", include_value)

        necessity = _string(row["Necessary Label"])
        if necessity and necessity not in VALID_NECESSITY_LABELS:
            _append_issue(issues, row, "Invalid necessity label", necessity)

        amount = row["Amount"]
        if not pd.isna(amount):
            if direction == "Money Out" and amount > 0:
                _append_issue(issues, row, "Amount/direction conflict", "Money Out should be negative")
            if direction == "Money In" and amount < 0:
                _append_issue(issues, row, "Amount/direction conflict", "Money In should be positive")

        if include_value == "Include" and txn_type in {"Transfer", "Payment"}:
            _append_issue(issues, row, "Include conflict", f"{txn_type} should not be Include")

        cleaned = _string(row["Cleaned Merchant"])
        raw = _string(row["Raw Description"])
        if cleaned == "" and raw == "":
            _append_issue(issues, row, "Unknown merchant", "Both Cleaned Merchant and Raw Description are blank")

        if (
            include_value == "Needs Review"
            or necessity == "Needs Review"
            or _string(row["Category"]) == "Needs Review"
            or _string(row["Subcategory"]) == "Needs Review"
            or _string(row["Reviewed"]).lower() in {"false", "no", "0", ""}
        ):
            _append_issue(issues, row, "Needs review", "Row has unresolved review fields")

    for left, right in _find_duplicate_candidates(work):
        left_row = work.loc[left]
        right_row = work.loc[right]
        _append_issue(issues, left_row, "Duplicate-looking row", f"Potential match with {right_row.get('Transaction ID', '')}")
        _append_issue(issues, right_row, "Duplicate-looking row", f"Potential match with {left_row.get('Transaction ID', '')}")

    issues_df = pd.DataFrame(issues)
    if not issues_df.empty:
        issues_df = issues_df.sort_values(["Row Number", "Issue"]).reset_index(drop=True)

    return work, issues_df

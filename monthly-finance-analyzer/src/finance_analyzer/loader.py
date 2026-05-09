from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .models import REQUIRED_COLUMNS


def _normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", str(name).strip()).lower()


def _build_account_short_map(accounts: "pd.Series[str]") -> dict[str, str]:
    """Assign a stable short code to each unique account name.

    Credit card accounts get CC1, CC2, … in first-seen order.
    Checking → CHK, Savings → SVG, everything else → first 3 alphanum chars.
    """
    result: dict[str, str] = {}
    cc_counter = 0
    for account in accounts.astype(str):
        key = account.lower().strip()
        if key in result:
            continue
        if "checking" in key:
            result[key] = "CHK"
        elif "savings" in key:
            result[key] = "SVG"
        elif "credit" in key or "card" in key:
            cc_counter += 1
            result[key] = f"CC{cc_counter}"
        else:
            cleaned = re.sub(r"[^A-Za-z0-9]", "", key).upper()
            result[key] = (cleaned[:3] or "ACC").ljust(3, "X")
    return result


def load_transactions(input_path: Path) -> pd.DataFrame:
    workbook = pd.read_excel(input_path, sheet_name="Transactions", engine="openpyxl")

    normalized = {_normalize_name(col): col for col in workbook.columns}
    missing = [col for col in REQUIRED_COLUMNS if _normalize_name(col) not in normalized]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    ordered = workbook[[normalized[_normalize_name(c)] for c in REQUIRED_COLUMNS]].copy()
    ordered.columns = REQUIRED_COLUMNS

    ordered["Original Row Number"] = ordered.index + 2
    ordered["_month_safe"] = ordered["Month"].astype(str).str.strip()

    # Build a stable account → short-code map before assigning Transaction IDs so
    # every row belonging to the same account always gets the same prefix.
    account_short_map = _build_account_short_map(ordered["Account"])
    ordered["Account Short"] = [
        account_short_map[str(a).lower().strip()] for a in ordered["Account"].astype(str)
    ]

    ordered["Transaction ID"] = [
        f"{month}-{short}-{row_num:03d}"
        for month, short, row_num in zip(
            ordered["_month_safe"], ordered["Account Short"], range(1, len(ordered) + 1)
        )
    ]
    ordered.drop(columns=["_month_safe"], inplace=True)
    return ordered

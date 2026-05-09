from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .models import REQUIRED_COLUMNS


def _normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", str(name).strip()).lower()


def _account_short_name(account: str, index: int = 1) -> str:
    value = str(account or "").lower()
    if "checking" in value:
        return "CHK"
    if "savings" in value:
        return "SVG"
    if "credit" in value or "card" in value:
        return f"CC{index}"
    cleaned = re.sub(r"[^A-Za-z0-9]", "", value).upper()
    return (cleaned[:3] or "ACC").ljust(3, "X")


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

    account_counters: dict[str, int] = {}
    account_short_values = []
    for account in ordered["Account"].astype(str):
        key = account.lower().strip()
        account_counters.setdefault(key, 0)
        if "credit" in key or "card" in key:
            account_counters[key] += 1
            short = _account_short_name(account, account_counters[key])
        else:
            short = _account_short_name(account)
        account_short_values.append(short)

    ordered["Account Short"] = account_short_values
    ordered["Transaction ID"] = [
        f"{month}-{short}-{row_num:03d}"
        for month, short, row_num in zip(
            ordered["_month_safe"], ordered["Account Short"], range(1, len(ordered) + 1)
        )
    ]
    ordered.drop(columns=["_month_safe"], inplace=True)
    return ordered

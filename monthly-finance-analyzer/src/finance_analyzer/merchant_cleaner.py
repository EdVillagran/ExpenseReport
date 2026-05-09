from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .config import load_yaml


def _derive_conservative_name(raw_description: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9 ]", " ", raw_description or "")
    parts = [p for p in cleaned.split() if p]
    if not parts:
        return "Needs Review"
    return " ".join(parts[:3]).title()


def clean_merchants(df: pd.DataFrame, rules_path: Path) -> pd.DataFrame:
    rules_data = load_yaml(rules_path)
    rules = rules_data.get("rules", [])

    work = df.copy()

    for idx, row in work.iterrows():
        raw = str(row.get("Raw Description", "") or "")
        existing = str(row.get("Cleaned Merchant", "") or "").strip()
        search_space = f"{existing} {raw}".lower()
        matched = None

        for rule in rules:
            canonical = rule.get("canonical")
            patterns = [str(p).lower() for p in rule.get("patterns", [])]
            if canonical and any(pattern in search_space for pattern in patterns):
                matched = canonical
                break

        if matched:
            work.at[idx, "Cleaned Merchant"] = matched
        elif existing:
            work.at[idx, "Cleaned Merchant"] = existing
        else:
            work.at[idx, "Cleaned Merchant"] = _derive_conservative_name(raw)

    return work

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import load_yaml


def _append_note(existing: str, note: str) -> str:
    existing = (existing or "").strip()
    if not existing:
        return note
    if note in existing:
        return existing
    return f"{existing}; {note}"


def categorize_transactions(df: pd.DataFrame, rules_path: Path) -> pd.DataFrame:
    rules_data = load_yaml(rules_path)
    rules = rules_data.get("rules", [])

    work = df.copy()
    if "Category Confidence" not in work.columns:
        work["Category Confidence"] = 0.0

    for idx, row in work.iterrows():
        desc = f"{row.get('Raw Description', '')} {row.get('Cleaned Merchant', '')}".lower()
        current_category = str(row.get("Category", "") or "").strip()

        matched_rule = None
        for rule in rules:
            patterns = [str(p).lower() for p in rule.get("patterns", [])]
            if patterns and any(pattern in desc for pattern in patterns):
                matched_rule = rule
                break

        if matched_rule:
            work.at[idx, "Category"] = matched_rule.get("category", current_category or "Needs Review")
            work.at[idx, "Subcategory"] = matched_rule.get("subcategory", "Needs Review")
            work.at[idx, "Category Confidence"] = float(matched_rule.get("confidence", 0.75))
            reason = matched_rule.get("reason", "Matched category rule")
            work.at[idx, "Notes"] = _append_note(str(row.get("Notes", "")), reason)
        else:
            if current_category in {"", "Unknown", "Needs Review"}:
                work.at[idx, "Category"] = "Needs Review"
                work.at[idx, "Subcategory"] = "Needs Review"
                work.at[idx, "Category Confidence"] = 0.30
                work.at[idx, "Notes"] = _append_note(
                    str(row.get("Notes", "")),
                    "Merchant was not matched by category rules",
                )

    return work

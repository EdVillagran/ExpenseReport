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


def classify_necessity(df: pd.DataFrame, rules_path: Path) -> pd.DataFrame:
    config = load_yaml(rules_path)
    default_labels = config.get("default_labels", {})
    default_reasons = config.get("label_reasons", {})

    work = df.copy()

    for idx, row in work.iterrows():
        category = str(row.get("Category", "") or "").strip()
        assigned = default_labels.get(category, "Needs Review")

        if category == "Needs Review":
            assigned = "Needs Review"

        work.at[idx, "Necessary Label"] = assigned

        if assigned in {"Possibly Unnecessary", "Unnecessary"}:
            reason = default_reasons.get(assigned, "This transaction may be discretionary.")
            work.at[idx, "Notes"] = _append_note(str(row.get("Notes", "")), reason)
        elif assigned == "Needs Review":
            work.at[idx, "Notes"] = _append_note(
                str(row.get("Notes", "")),
                "Necessity could not be determined and needs manual review",
            )

    return work

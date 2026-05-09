from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import load_yaml

# Default confidence scores by necessity label.
NECESSITY_CONFIDENCE: dict[str, float] = {
    "Necessary": 0.90,
    "Possibly Unnecessary": 0.75,
    "Unnecessary": 0.95,
    "Needs Review": 0.30,
}


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
    if "Necessity Confidence" not in work.columns:
        work["Necessity Confidence"] = 0.0
    if "Necessity Reason" not in work.columns:
        work["Necessity Reason"] = ""

    for idx, row in work.iterrows():
        category = str(row.get("Category", "") or "").strip()
        assigned = default_labels.get(category, "Needs Review")

        if category == "Needs Review":
            assigned = "Needs Review"

        work.at[idx, "Necessary Label"] = assigned
        work.at[idx, "Necessity Confidence"] = NECESSITY_CONFIDENCE.get(assigned, 0.30)

        if assigned in {"Possibly Unnecessary", "Unnecessary"}:
            reason = default_reasons.get(assigned, "This transaction may be discretionary.")
            work.at[idx, "Necessity Reason"] = reason
            work.at[idx, "Notes"] = _append_note(str(row.get("Notes", "")), reason)
        elif assigned == "Needs Review":
            reason = "Necessity could not be determined and needs manual review"
            work.at[idx, "Necessity Reason"] = reason
            work.at[idx, "Notes"] = _append_note(str(row.get("Notes", "")), reason)
        else:
            work.at[idx, "Necessity Reason"] = ""

    return work

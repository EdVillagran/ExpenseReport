from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import load_yaml


def _contains_any(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def _append_note(existing: str, note: str) -> str:
    existing = (existing or "").strip()
    if not existing:
        return note
    if note in existing:
        return existing
    return f"{existing}; {note}"


def detect_transfers_and_duplicates(df: pd.DataFrame, rules_path: Path) -> pd.DataFrame:
    rules = load_yaml(rules_path)
    transfer_keywords = rules.get("transfer_keywords", [])
    payment_keywords = rules.get("payment_keywords", [])
    refund_keywords = rules.get("refund_keywords", [])
    reversal_keywords = rules.get("reversal_keywords", [])
    fee_keywords = rules.get("fee_keywords", [])
    window_days = int(rules.get("date_matching_window_days", 3))
    tolerance = float(rules.get("amount_matching_tolerance", 0.01))

    work = df.copy()
    if "Matched Transaction ID" not in work.columns:
        work["Matched Transaction ID"] = ""

    work["_tx_date"] = pd.to_datetime(work["Transaction Date"], errors="coerce")

    for idx, row in work.iterrows():
        desc = f"{row.get('Raw Description', '')} {row.get('Cleaned Merchant', '')}".lower()
        amount = float(row.get("Amount", 0.0) or 0.0)

        if _contains_any(desc, fee_keywords) and amount < 0:
            work.at[idx, "Type"] = "Fee"
            work.at[idx, "Include in Spending"] = "Include"
            work.at[idx, "Notes"] = _append_note(str(row.get("Notes", "")), "Classified as fee/interest")

        if _contains_any(desc, refund_keywords) and amount > 0:
            work.at[idx, "Type"] = "Refund"
            work.at[idx, "Include in Spending"] = "Offset"
            work.at[idx, "Notes"] = _append_note(str(row.get("Notes", "")), "Classified as refund")

        if _contains_any(desc, reversal_keywords):
            work.at[idx, "Type"] = "Reversal"
            work.at[idx, "Include in Spending"] = "Exclude"
            work.at[idx, "Notes"] = _append_note(str(row.get("Notes", "")), "Classified as reversal")

    indices = list(work.index)
    for i, left_idx in enumerate(indices):
        for right_idx in indices[i + 1 :]:
            left = work.loc[left_idx]
            right = work.loc[right_idx]

            left_date = left["_tx_date"]
            right_date = right["_tx_date"]
            if pd.isna(left_date) or pd.isna(right_date):
                continue
            if abs((left_date - right_date).days) > window_days:
                continue

            left_amt = float(left.get("Amount", 0.0) or 0.0)
            right_amt = float(right.get("Amount", 0.0) or 0.0)

            if abs(abs(left_amt) - abs(right_amt)) > tolerance:
                continue

            left_desc = f"{left.get('Raw Description', '')} {left.get('Cleaned Merchant', '')}".lower()
            right_desc = f"{right.get('Raw Description', '')} {right.get('Cleaned Merchant', '')}".lower()
            combined = f"{left_desc} {right_desc}"

            is_opposite = left_amt * right_amt < 0
            if is_opposite and _contains_any(combined, payment_keywords):
                for idx in [left_idx, right_idx]:
                    work.at[idx, "Type"] = "Payment"
                    work.at[idx, "Include in Spending"] = "Exclude"
                    work.at[idx, "Matched Transaction ID"] = (
                        right.get("Transaction ID") if idx == left_idx else left.get("Transaction ID")
                    )
                    work.at[idx, "Notes"] = _append_note(str(work.at[idx, "Notes"]), "Matched as credit card payment")
                continue

            if is_opposite and _contains_any(combined, transfer_keywords):
                for idx in [left_idx, right_idx]:
                    work.at[idx, "Type"] = "Transfer"
                    work.at[idx, "Include in Spending"] = "Exclude"
                    work.at[idx, "Matched Transaction ID"] = (
                        right.get("Transaction ID") if idx == left_idx else left.get("Transaction ID")
                    )
                    work.at[idx, "Notes"] = _append_note(str(work.at[idx, "Notes"]), "Matched as transfer")
                continue

            if (
                left_amt < 0
                and right_amt < 0
                and str(left.get("Cleaned Merchant", "")).strip().lower()
                == str(right.get("Cleaned Merchant", "")).strip().lower()
            ):
                work.at[left_idx, "Include in Spending"] = "Needs Review"
                work.at[right_idx, "Include in Spending"] = "Needs Review"
                work.at[left_idx, "Notes"] = _append_note(str(work.at[left_idx, "Notes"]), "Potential duplicate transaction")
                work.at[right_idx, "Notes"] = _append_note(str(work.at[right_idx, "Notes"]), "Potential duplicate transaction")

    work.drop(columns=["_tx_date"], inplace=True)
    return work

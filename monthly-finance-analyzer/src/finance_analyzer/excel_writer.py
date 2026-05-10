from __future__ import annotations

from pathlib import Path

import pandas as pd


def _build_enriched_issues(transactions: pd.DataFrame) -> pd.DataFrame:
    """Build data quality issues from the fully-enriched transaction DataFrame.

    These supplement the structural validation issues produced by the validator
    and cover post-enrichment concerns such as unknown categories, low
    confidence scores, and transactions still needing review.
    """
    rows: list[dict] = []

    def _s(value: object) -> str:
        return "" if pd.isna(value) else str(value).strip()

    for _, row in transactions.iterrows():
        txn_id = _s(row.get("Transaction ID"))
        row_num = int(row.get("Original Row Number", -1))

        category = _s(row.get("Category"))
        if category in {"Needs Review", "Unknown", ""}:
            rows.append({
                "Transaction ID": txn_id,
                "Row Number": row_num,
                "Issue": "Unknown category",
                "Detail": f"Category is '{category}' after enrichment",
            })

        cleaned = _s(row.get("Cleaned Merchant"))
        raw = _s(row.get("Raw Description"))
        if cleaned in {"", "Unknown"} and raw in {"", "Unknown"}:
            rows.append({
                "Transaction ID": txn_id,
                "Row Number": row_num,
                "Issue": "Unknown merchant",
                "Detail": "Cleaned Merchant and Raw Description are both blank/Unknown",
            })

        include = _s(row.get("Include in Spending"))
        if include == "Needs Review":
            rows.append({
                "Transaction ID": txn_id,
                "Row Number": row_num,
                "Issue": "Include in Spending needs review",
                "Detail": "Transaction could not be reliably included or excluded from spending",
            })

        notes = _s(row.get("Notes")).lower()
        if "duplicate" in notes:
            rows.append({
                "Transaction ID": txn_id,
                "Row Number": row_num,
                "Issue": "Potential duplicate",
                "Detail": _s(row.get("Notes")),
            })

        cat_conf = row.get("Category Confidence")
        try:
            cat_conf_f = float(cat_conf) if cat_conf is not None and not pd.isna(cat_conf) else None
        except (TypeError, ValueError):
            cat_conf_f = None
        if cat_conf_f is not None and cat_conf_f < 0.50:
            rows.append({
                "Transaction ID": txn_id,
                "Row Number": row_num,
                "Issue": "Low category confidence",
                "Detail": f"Category Confidence is {cat_conf_f:.2f} for category '{category}'",
            })

        nec_conf = row.get("Necessity Confidence")
        try:
            nec_conf_f = float(nec_conf) if nec_conf is not None and not pd.isna(nec_conf) else None
        except (TypeError, ValueError):
            nec_conf_f = None
        if nec_conf_f is not None and nec_conf_f < 0.50:
            necessity = _s(row.get("Necessary Label"))
            rows.append({
                "Transaction ID": txn_id,
                "Row Number": row_num,
                "Issue": "Low necessity confidence",
                "Detail": f"Necessity Confidence is {nec_conf_f:.2f} for label '{necessity}'",
            })

    if not rows:
        return pd.DataFrame(columns=["Transaction ID", "Row Number", "Issue", "Detail"])
    return pd.DataFrame(rows).sort_values(["Row Number", "Issue"]).reset_index(drop=True)


def write_output_workbook(
    output_path: Path,
    transactions: pd.DataFrame,
    analytics_result: dict,
    review_issues: pd.DataFrame,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = analytics_result["summary"]
    net_spending = summary.get("net_spending", summary.get("total_spending", 0.0))

    # Combine validator issues with post-enrichment data quality issues.
    enriched_issues = _build_enriched_issues(transactions)
    if review_issues is not None and not review_issues.empty:
        combined_issues = pd.concat([review_issues, enriched_issues], ignore_index=True)
    else:
        combined_issues = enriched_issues

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        transactions.to_excel(writer, sheet_name="Master Transactions", index=False)

        # "Gross Spending by Category" — totals are before refund offsets (gross, not net).
        analytics_result["spending_by_category"].to_excel(writer, sheet_name="Gross Spending by Category", index=False)

        def _pct(amount: float) -> str:
            if net_spending > 0:
                return f"{amount / net_spending * 100:.1f}%"
            return "N/A"

        necessity_rows = []
        for label, amount_key, count_key in [
            ("Necessary", "necessary_spending", "necessary_count"),
            ("Possibly Unnecessary", "possibly_unnecessary_spending", "possibly_unnecessary_count"),
            ("Unnecessary", "unnecessary_spending", "unnecessary_count"),
        ]:
            amt = summary.get(amount_key, 0.0)
            cnt = summary.get(count_key, 0)
            necessity_rows.append(
                {
                    "Label": label,
                    "Amount": amt,
                    "Transaction Count": cnt,
                    "Percent of Net Spending": _pct(amt),
                    "Notes": "",
                }
            )
        pd.DataFrame(necessity_rows).to_excel(writer, sheet_name="Necessary vs Unnecessary", index=False)

        # Flagged Transactions — all flagged rows, not just top 10.
        analytics_result["top_flagged"].to_excel(writer, sheet_name="Flagged Transactions", index=False)

        # Transfers and Payments sheet with defined columns.
        tp_cols = [
            "Transaction ID",
            "Matched Transaction ID",
            "Transaction Date",
            "Account",
            "Cleaned Merchant",
            "Amount",
            "Type",
            "Include in Spending",
            "Notes",
        ]
        transfer_payment = transactions[transactions["Type"].isin(["Transfer", "Payment", "Refund", "Reversal"])].copy()
        existing_tp_cols = [c for c in tp_cols if c in transfer_payment.columns]
        transfer_payment[existing_tp_cols].to_excel(writer, sheet_name="Transfers and Payments", index=False)

        analytics_result["subscriptions"].to_excel(writer, sheet_name="Subscriptions", index=False)

        summary_df = pd.DataFrame([{"Metric": k, "Value": v} for k, v in summary.items()])
        summary_df.to_excel(writer, sheet_name="Monthly Summary", index=False)

        if combined_issues.empty:
            pd.DataFrame([{"Issue": "No data quality issues detected"}]).to_excel(
                writer,
                sheet_name="Data Quality Issues",
                index=False,
            )
        else:
            combined_issues.to_excel(writer, sheet_name="Data Quality Issues", index=False)


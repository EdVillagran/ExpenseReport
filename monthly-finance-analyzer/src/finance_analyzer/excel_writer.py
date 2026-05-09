from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_output_workbook(
    output_path: Path,
    transactions: pd.DataFrame,
    analytics_result: dict,
    review_issues: pd.DataFrame,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = analytics_result["summary"]
    net_spending = summary.get("net_spending", summary.get("total_spending", 0.0))

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        transactions.to_excel(writer, sheet_name="Master Transactions", index=False)
        analytics_result["spending_by_category"].to_excel(writer, sheet_name="Category Summary", index=False)

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

        if review_issues is None or review_issues.empty:
            pd.DataFrame([{"Issue": "No data quality issues detected"}]).to_excel(
                writer,
                sheet_name="Data Quality Issues",
                index=False,
            )
        else:
            review_issues.to_excel(writer, sheet_name="Data Quality Issues", index=False)


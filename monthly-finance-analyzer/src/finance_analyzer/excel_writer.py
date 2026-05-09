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

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        transactions.to_excel(writer, sheet_name="Master Transactions", index=False)
        analytics_result["spending_by_category"].to_excel(writer, sheet_name="Category Summary", index=False)

        necessity = pd.DataFrame(
            [
                {"Label": "Necessary", "Amount": analytics_result["summary"]["necessary_spending"]},
                {
                    "Label": "Possibly Unnecessary",
                    "Amount": analytics_result["summary"]["possibly_unnecessary_spending"],
                },
                {"Label": "Unnecessary", "Amount": analytics_result["summary"]["unnecessary_spending"]},
            ]
        )
        necessity.to_excel(writer, sheet_name="Necessary vs Unnecessary", index=False)

        analytics_result["top_flagged"].to_excel(writer, sheet_name="Flagged Transactions", index=False)

        transfer_payment = transactions[transactions["Type"].isin(["Transfer", "Payment", "Refund", "Reversal"])].copy()
        transfer_payment.to_excel(writer, sheet_name="Transfers and Payments", index=False)

        analytics_result["subscriptions"].to_excel(writer, sheet_name="Subscriptions", index=False)

        summary = pd.DataFrame(
            [{"Metric": k, "Value": v} for k, v in analytics_result["summary"].items()]
        )
        summary.to_excel(writer, sheet_name="Monthly Summary", index=False)

        if review_issues.empty:
            pd.DataFrame([{"Issue": "No data quality issues detected"}]).to_excel(
                writer,
                sheet_name="Data Quality Issues",
                index=False,
            )
        else:
            review_issues.to_excel(writer, sheet_name="Data Quality Issues", index=False)

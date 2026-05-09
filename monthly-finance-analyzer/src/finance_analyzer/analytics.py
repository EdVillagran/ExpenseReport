from __future__ import annotations

import math
from collections import OrderedDict

import pandas as pd


def _safe_sum(series: pd.Series) -> float:
    if series.empty:
        return 0.0
    return float(series.fillna(0).sum())


def run_analytics(df: pd.DataFrame, month: str, review_issues: pd.DataFrame | None = None) -> dict:
    work = df.copy()
    work = work[work["Month"].astype(str) == month].copy()

    work["Amount"] = pd.to_numeric(work["Amount"], errors="coerce").fillna(0.0)

    include_spending_mask = (work["Include in Spending"] == "Include") & work["Type"].isin(["Expense", "Fee"])
    include_spending = work[include_spending_mask]

    total_income = _safe_sum(work.loc[work["Type"] == "Income", "Amount"])
    total_spending = abs(_safe_sum(include_spending["Amount"]))
    net_cash_flow = total_income - total_spending
    savings_rate = (net_cash_flow / total_income) if not math.isclose(total_income, 0.0) else 0.0

    by_category = (
        include_spending.assign(Spending=include_spending["Amount"].abs())
        .groupby("Category", dropna=False)["Spending"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    by_account = (
        include_spending.assign(Spending=include_spending["Amount"].abs())
        .groupby("Account", dropna=False)["Spending"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    by_merchant = (
        include_spending.assign(Spending=include_spending["Amount"].abs())
        .groupby("Cleaned Merchant", dropna=False)["Spending"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    necessary_spending = abs(_safe_sum(include_spending.loc[include_spending["Necessary Label"] == "Necessary", "Amount"]))
    possibly_unnecessary_spending = abs(
        _safe_sum(include_spending.loc[include_spending["Necessary Label"] == "Possibly Unnecessary", "Amount"])
    )
    unnecessary_spending = abs(_safe_sum(include_spending.loc[include_spending["Necessary Label"] == "Unnecessary", "Amount"]))

    fee_interest = abs(
        _safe_sum(
            include_spending.loc[
                (include_spending["Type"] == "Fee")
                | include_spending["Raw Description"].fillna("").str.lower().str.contains("interest"),
                "Amount",
            ]
        )
    )

    refunds_credits = _safe_sum(work.loc[(work["Type"] == "Refund") & (work["Include in Spending"] == "Offset"), "Amount"])
    transfers_excluded = abs(_safe_sum(work.loc[work["Type"] == "Transfer", "Amount"]))
    payments_excluded = abs(_safe_sum(work.loc[work["Type"] == "Payment", "Amount"]))

    top_purchases = (
        include_spending.sort_values("Amount", ascending=True)
        .head(10)
        [["Transaction ID", "Transaction Date", "Cleaned Merchant", "Amount", "Category", "Notes"]]
        .copy()
    )
    if not top_purchases.empty:
        top_purchases["Amount"] = top_purchases["Amount"].abs()

    flagged_mask = (
        (work["Include in Spending"] == "Needs Review")
        | (work["Category"] == "Needs Review")
        | (work["Necessary Label"] == "Needs Review")
        | work["Notes"].fillna("").str.lower().str.contains("duplicate|review")
    )
    flagged = work.loc[flagged_mask].copy()
    top_flagged = flagged.head(10)[
        ["Transaction ID", "Transaction Date", "Cleaned Merchant", "Amount", "Type", "Include in Spending", "Notes"]
    ]

    subscriptions = (
        work[work["Category"] == "Subscriptions"]
        .groupby("Cleaned Merchant", dropna=False)
        .agg(Count=("Transaction ID", "count"), Total=("Amount", lambda s: abs(float(s.sum()))))
        .reset_index()
        .sort_values(["Count", "Total"], ascending=[False, False])
    )
    subscriptions = subscriptions[subscriptions["Count"] >= 2]

    duplicate_candidates = work[work["Notes"].fillna("").str.lower().str.contains("duplicate")].copy()

    review_count = len(flagged.index)
    if review_issues is not None and not review_issues.empty:
        review_count += len(review_issues.index)

    summary = OrderedDict(
        total_income=round(total_income, 2),
        total_spending=round(total_spending, 2),
        net_cash_flow=round(net_cash_flow, 2),
        savings_rate=savings_rate,
        necessary_spending=round(necessary_spending, 2),
        possibly_unnecessary_spending=round(possibly_unnecessary_spending, 2),
        unnecessary_spending=round(unnecessary_spending, 2),
        fees_and_interest=round(fee_interest, 2),
        refunds_and_credits=round(refunds_credits, 2),
        transfers_excluded=round(transfers_excluded, 2),
        credit_card_payments_excluded=round(payments_excluded, 2),
        review_needed_count=int(review_count),
    )

    return {
        "summary": summary,
        "spending_by_category": by_category,
        "spending_by_account": by_account,
        "spending_by_merchant": by_merchant,
        "top_purchases": top_purchases,
        "top_flagged": top_flagged,
        "subscriptions": subscriptions,
        "duplicate_candidates": duplicate_candidates,
        "monthly_transactions": work,
    }

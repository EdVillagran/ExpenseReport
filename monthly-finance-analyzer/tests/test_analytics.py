import math

import pandas as pd

from finance_analyzer.analytics import run_analytics


def test_total_spending_and_savings_rate():
    df = pd.DataFrame(
        [
            {
                "Month": "2026-05",
                "Transaction ID": "2026-05-CHK-001",
                "Account": "Checking",
                "Transaction Date": "2026-05-01",
                "Raw Description": "PAYROLL",
                "Cleaned Merchant": "Employer",
                "Amount": 3000.0,
                "Type": "Income",
                "Include in Spending": "Exclude",
                "Category": "Income",
                "Necessary Label": "Necessary",
                "Notes": "",
            },
            {
                "Month": "2026-05",
                "Transaction ID": "2026-05-CHK-002",
                "Account": "Checking",
                "Transaction Date": "2026-05-02",
                "Raw Description": "WALMART",
                "Cleaned Merchant": "Walmart",
                "Amount": -200.0,
                "Type": "Expense",
                "Include in Spending": "Include",
                "Category": "Groceries",
                "Necessary Label": "Necessary",
                "Notes": "",
            },
            {
                "Month": "2026-05",
                "Transaction ID": "2026-05-CHK-003",
                "Account": "Checking",
                "Transaction Date": "2026-05-03",
                "Raw Description": "CC PAYMENT",
                "Cleaned Merchant": "Credit Card",
                "Amount": -500.0,
                "Type": "Payment",
                "Include in Spending": "Exclude",
                "Category": "Debt Payments",
                "Necessary Label": "Needs Review",
                "Notes": "",
            },
        ]
    )

    result = run_analytics(df, "2026-05")
    assert result["summary"]["total_spending"] == 200.0
    assert math.isclose(result["summary"]["savings_rate"], (3000.0 - 200.0) / 3000.0, rel_tol=1e-9)
    assert result["summary"]["credit_card_payments_excluded"] == 500.0

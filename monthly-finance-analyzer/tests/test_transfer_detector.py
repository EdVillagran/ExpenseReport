from pathlib import Path

import pandas as pd

from finance_analyzer.transfer_detector import detect_transfers_and_duplicates


def test_transfer_matching_and_cc_payment_exclusion():
    df = pd.DataFrame(
        [
            {
                "Transaction ID": "2026-05-CHK-001",
                "Month": "2026-05",
                "Account": "Checking",
                "Transaction Date": "2026-05-10",
                "Raw Description": "AUTOPAY CREDIT CARD PAYMENT",
                "Cleaned Merchant": "Credit Card",
                "Amount": -100.0,
                "Direction": "Money Out",
                "Type": "Expense",
                "Include in Spending": "Include",
                "Category": "Debt Payments",
                "Necessary Label": "Needs Review",
                "Notes": "",
            },
            {
                "Transaction ID": "2026-05-CC1-002",
                "Month": "2026-05",
                "Account": "Credit Card",
                "Transaction Date": "2026-05-11",
                "Raw Description": "PAYMENT RECEIVED",
                "Cleaned Merchant": "Credit Card",
                "Amount": 100.0,
                "Direction": "Money In",
                "Type": "Income",
                "Include in Spending": "Exclude",
                "Category": "Debt Payments",
                "Necessary Label": "Needs Review",
                "Notes": "",
            },
        ]
    )

    out = detect_transfers_and_duplicates(df, Path("rules/transfer_rules.yaml"))
    assert set(out["Type"].tolist()) == {"Payment"}
    assert set(out["Include in Spending"].tolist()) == {"Exclude"}
    assert out["Matched Transaction ID"].str.len().min() > 0

from pathlib import Path

import pandas as pd

from finance_analyzer.categorizer import categorize_transactions
from finance_analyzer.necessity_classifier import classify_necessity


def test_category_rule_matching_and_necessity_assignment():
    df = pd.DataFrame(
        [
            {
                "Month": "2026-05",
                "Transaction ID": "2026-05-CHK-001",
                "Raw Description": "NETFLIX.COM",
                "Cleaned Merchant": "Netflix",
                "Category": "Needs Review",
                "Subcategory": "Needs Review",
                "Necessary Label": "Needs Review",
                "Notes": "",
            }
        ]
    )

    categorized = categorize_transactions(df, Path("rules/category_rules.yaml"))
    assert categorized.loc[0, "Category"] == "Subscriptions"

    classified = classify_necessity(categorized, Path("rules/necessity_rules.yaml"))
    assert classified.loc[0, "Necessary Label"] == "Possibly Unnecessary"
    assert "discretionary" in classified.loc[0, "Notes"].lower()

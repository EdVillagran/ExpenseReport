from __future__ import annotations

import argparse
from pathlib import Path

from .analytics import run_analytics
from .categorizer import categorize_transactions
from .config import REPORT_TEMPLATE, RULES_DIR
from .excel_writer import write_output_workbook
from .loader import load_transactions
from .merchant_cleaner import clean_merchants
from .necessity_classifier import classify_necessity
from .report_generator import generate_report
from .transfer_detector import detect_transfers_and_duplicates
from .validator import validate_transactions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local monthly finance analysis.")
    parser.add_argument("--input", required=True, help="Path to input workbook")
    parser.add_argument("--month", required=True, help="Month in YYYY-MM")
    parser.add_argument("--output-dir", default="data/output", help="Base output directory")
    return parser.parse_args()


def run_pipeline(input_path: Path, month: str, output_dir: Path) -> dict:
    transactions = load_transactions(input_path)
    transactions, review_issues = validate_transactions(transactions)
    transactions = clean_merchants(transactions, RULES_DIR / "merchant_cleanup_rules.yaml")
    transactions = detect_transfers_and_duplicates(transactions, RULES_DIR / "transfer_rules.yaml")
    transactions = categorize_transactions(transactions, RULES_DIR / "category_rules.yaml")
    transactions = classify_necessity(transactions, RULES_DIR / "necessity_rules.yaml")

    analytics_result = run_analytics(transactions, month, review_issues)

    month_dir = output_dir / month
    workbook_path = month_dir / f"processed_transactions_{month}.xlsx"
    report_path = month_dir / f"monthly_report_{month}.md"

    write_output_workbook(workbook_path, transactions, analytics_result, review_issues)
    generate_report(month, analytics_result, REPORT_TEMPLATE, report_path)

    return {
        "transactions": transactions,
        "review_issues": review_issues,
        "analytics": analytics_result,
        "workbook_path": workbook_path,
        "report_path": report_path,
    }


def main() -> None:
    args = parse_args()
    result = run_pipeline(Path(args.input), args.month, Path(args.output_dir))
    print(f"Workbook written: {result['workbook_path']}")
    print(f"Report written: {result['report_path']}")


if __name__ == "__main__":
    main()

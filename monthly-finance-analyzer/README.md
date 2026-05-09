# monthly-finance-analyzer

A local-first, deterministic Python pipeline for monthly personal finance analysis from a single manually maintained Excel workbook.

## Why local/offline
- Runs entirely on your machine.
- No bank syncing, no cloud APIs, no telemetry, no model calls.
- Keeps sensitive transaction data private.

## Install
```bash
cd monthly-finance-analyzer
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Input workbook
The input workbook must include a tab named **Transactions** with these required columns:

- Month
- Account
- Account Type
- Transaction Date
- Posted Date
- Raw Description
- Cleaned Merchant
- Amount
- Direction
- Type
- Category
- Subcategory
- Necessary Label
- Include in Spending
- Notes
- Reviewed

### Key validation rules
- Month: `YYYY-MM`
- Amount: numeric
- Expenses negative, income positive
- Direction: `Money In` or `Money Out`
- Type: `Income | Expense | Transfer | Fee | Refund | Payment | Reversal | Unknown`
- Include in Spending: `Include | Exclude | Offset | Needs Review`
- Necessary Label: `Necessary | Possibly Unnecessary | Unnecessary | Needs Review`

## Run analyzer
```bash
python -m finance_analyzer.main --input data/input/sample_transactions.xlsx --month 2026-05
```

Outputs go to:
`data/output/2026-05/`

- `processed_transactions_2026-05.xlsx`
- `monthly_report_2026-05.md`

## Edit rules
- Category mapping: `rules/category_rules.yaml`
- Merchant cleanup: `rules/merchant_cleanup_rules.yaml`
- Necessity labels: `rules/necessity_rules.yaml`
- Transfer/payment matching: `rules/transfer_rules.yaml`

## Output workbook tabs
- Master Transactions
- Category Summary
- Necessary vs Unnecessary
- Flagged Transactions
- Transfers and Payments
- Subscriptions
- Monthly Summary
- Data Quality Issues

## Report usage
The Markdown report includes executive summary, income/expense views, category breakdown, necessity split, top purchases, subscriptions, transfers/refunds/payments, trends note, savings opportunities, action plan, and data quality section.

## Known limitations
- Deterministic keyword and pattern matching can miss edge-case merchants.
- Transfer/payment matching is heuristic and may require manual review.
- Trend analysis is limited without prior-month data.

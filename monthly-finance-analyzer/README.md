# monthly-finance-analyzer

A local-first, deterministic Python pipeline for monthly personal finance analysis from a single manually maintained Excel workbook.

> ⚠️ **Do not rely on this for final financial decisions until all Review Needed rows are resolved.**

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
- Amount: numeric; expenses are **negative**, income is **positive**
- Direction: `Money In` or `Money Out`
- Type: `Income | Expense | Transfer | Fee | Refund | Payment | Reversal | Unknown`
- Include in Spending: `Include | Exclude | Offset | Needs Review`
- Necessary Label: `Necessary | Possibly Unnecessary | Unnecessary | Needs Review`
- Posted Date may be left blank; only a non-blank unparseable value is flagged.

## How to fill out the workbook

### Entering regular expenses
- Set **Amount** to a negative number (e.g. `-42.50`).
- Set **Direction** to `Money Out`, **Type** to `Expense`, **Include in Spending** to `Include`.

### Entering income
- Set **Amount** to a positive number, **Direction** to `Money In`, **Type** to `Income`, **Include in Spending** to `Exclude`.

### Entering refunds
- Enter the refund as a positive **Amount** (money came back to you).
- Set **Direction** to `Money In`, **Type** to `Refund`, **Include in Spending** to `Offset`.
- The pipeline will subtract refund offsets from gross spending to calculate **Net Spending**.

### Entering transfers (checking → savings)
- Enter both sides of the transfer (outgoing negative, incoming positive).
- Set **Type** to `Transfer` and **Include in Spending** to `Exclude` on **both** rows.
- The pipeline counts only the outgoing (negative) side as **Transfers Excluded**; the pair does not cancel to zero.

### Entering credit card payments
- Enter the payment from checking (negative amount, `Money Out`) and the payment received on the credit card (positive amount, `Money In`).
- Set **Type** to `Payment` and **Include in Spending** to `Exclude` on **both** rows.
- Only the outgoing side is reported under **Credit Card Payments Excluded**.

### Marking unknown merchants
- Leave **Category** and **Necessary Label** as `Needs Review`.
- Set **Include in Spending** to `Needs Review` if you are unsure whether to count it.
- Set **Reviewed** to `False` so the pipeline flags it in the Data Quality Issues sheet.

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

### Updating YAML rules
- Open the relevant YAML file in any text editor.
- Add a new entry under `rules:` with `category`, `subcategory`, `patterns`, and `confidence`.
- Patterns use word-boundary matching — short words like `fee` will not accidentally match `coffee`.

## Output workbook tabs
- **Master Transactions** — all transactions with pipeline-enriched fields
- **Category Summary** — net spending by category
- **Necessary vs Unnecessary** — amount, count, and percent of net spending per necessity label
- **Flagged Transactions** — all rows flagged for review
- **Transfers and Payments** — transfer/payment/refund/reversal rows with matched pair info
- **Subscriptions** — recurring charges grouped by merchant
- **Monthly Summary** — key financial metrics (gross spending, refund offsets, net spending, etc.)
- **Data Quality Issues** — validation issues that need resolution before trusting the report

## Gross Spending vs Net Spending
- **Gross Spending** = sum of all included expenses and fees (before any refunds).
- **Refund Offsets** = sum of refund transactions marked `Offset` in *Include in Spending*.
- **Net Spending** = Gross Spending − Refund Offsets.
- **Net Cash Flow** = Total Income − Net Spending.
- The Markdown report and Monthly Summary sheet always show all three so you can tell how much came back.

## Resolving Data Quality Issues
1. Open `Data Quality Issues` in the output workbook.
2. For each row, go back to your input workbook and correct the flagged field.
3. Re-run the pipeline until no critical issues remain.
4. Do not trust totals or savings rates until all `Needs Review` rows are resolved.

## Report usage
The Markdown report includes:
- Executive summary with gross spending, refund offsets, and net spending
- Income and expense overview
- Category breakdown and spending by account
- Necessary vs Unnecessary breakdown with counts
- Largest purchases
- Top unnecessary and possibly unnecessary purchases
- Subscriptions
- Fees and interest detail
- Transfers, refunds, and payments summary
- Practical action plan with specific dollar amounts
- Review Needed section listing all flagged rows

## Known limitations
- Deterministic keyword and pattern matching can miss edge-case merchants.
- Transfer/payment matching is heuristic and may require manual review.
- Trend analysis is limited without prior-month data.
- Do not rely on this tool for final financial decisions until all Review Needed rows are resolved.


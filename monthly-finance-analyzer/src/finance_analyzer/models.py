from __future__ import annotations

from dataclasses import dataclass
from typing import Final

REQUIRED_COLUMNS: Final[list[str]] = [
    "Month",
    "Account",
    "Account Type",
    "Transaction Date",
    "Posted Date",
    "Raw Description",
    "Cleaned Merchant",
    "Amount",
    "Direction",
    "Type",
    "Category",
    "Subcategory",
    "Necessary Label",
    "Include in Spending",
    "Notes",
    "Reviewed",
]

VALID_TYPES: Final[set[str]] = {
    "Income",
    "Expense",
    "Transfer",
    "Fee",
    "Refund",
    "Payment",
    "Reversal",
    "Unknown",
}

VALID_DIRECTIONS: Final[set[str]] = {"Money In", "Money Out"}

VALID_INCLUDE_VALUES: Final[set[str]] = {"Include", "Exclude", "Offset", "Needs Review"}

VALID_NECESSITY_LABELS: Final[set[str]] = {
    "Necessary",
    "Possibly Unnecessary",
    "Unnecessary",
    "Needs Review",
}


@dataclass(frozen=True)
class ValidationIssue:
    transaction_id: str
    row_number: int
    issue: str
    detail: str

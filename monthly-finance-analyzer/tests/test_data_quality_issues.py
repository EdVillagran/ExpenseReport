"""Tests for enriched Data Quality Issues output in the workbook."""
import pandas as pd
import pytest
import openpyxl
from pathlib import Path

from finance_analyzer.excel_writer import _build_enriched_issues


def _base_row(**kwargs):
    defaults = {
        "Transaction ID": "ID-001",
        "Original Row Number": 2,
        "Category": "Groceries",
        "Cleaned Merchant": "Walmart",
        "Raw Description": "WALMART",
        "Include in Spending": "Include",
        "Notes": "",
        "Category Confidence": 0.95,
        "Necessity Confidence": 0.90,
        "Necessary Label": "Necessary",
    }
    defaults.update(kwargs)
    return defaults


def test_unknown_category_flagged():
    df = pd.DataFrame([_base_row(Category="Needs Review")])
    issues = _build_enriched_issues(df)
    assert (issues["Issue"] == "Unknown category").any()


def test_unknown_merchant_flagged():
    df = pd.DataFrame([_base_row(**{"Cleaned Merchant": "", "Raw Description": ""})])
    issues = _build_enriched_issues(df)
    assert (issues["Issue"] == "Unknown merchant").any()


def test_needs_review_inclusion_flagged():
    df = pd.DataFrame([_base_row(**{"Include in Spending": "Needs Review"})])
    issues = _build_enriched_issues(df)
    assert (issues["Issue"] == "Include in Spending needs review").any()


def test_potential_duplicate_flagged():
    df = pd.DataFrame([_base_row(Notes="Potential duplicate transaction")])
    issues = _build_enriched_issues(df)
    assert (issues["Issue"] == "Potential duplicate").any()


def test_low_category_confidence_flagged():
    df = pd.DataFrame([_base_row(**{"Category Confidence": 0.30})])
    issues = _build_enriched_issues(df)
    assert (issues["Issue"] == "Low category confidence").any()


def test_low_necessity_confidence_flagged():
    df = pd.DataFrame([_base_row(**{"Necessity Confidence": 0.30})])
    issues = _build_enriched_issues(df)
    assert (issues["Issue"] == "Low necessity confidence").any()


def test_clean_row_produces_no_issues():
    df = pd.DataFrame([_base_row()])
    issues = _build_enriched_issues(df)
    assert issues.empty, f"Expected no issues for a clean row, got: {issues}"

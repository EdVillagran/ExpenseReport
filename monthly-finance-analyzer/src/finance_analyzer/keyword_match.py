"""Safe keyword matching helpers.

Short keywords like 'fee' must not accidentally match words that contain them
(e.g. 'coffee'). This module provides word-boundary aware matching so that
single-word keywords only fire when they appear as standalone words.
Multi-word phrases (e.g. 'late fee') are matched as complete phrases with
surrounding word boundaries.
"""
from __future__ import annotations

import re


def _make_pattern(keyword: str) -> re.Pattern[str]:
    """Return a compiled regex pattern that matches *keyword* as a whole phrase."""
    return re.compile(r"\b" + re.escape(keyword.strip().lower()) + r"\b")


# Pre-compile patterns are cached here to avoid repeated compilation inside loops.
_pattern_cache: dict[str, re.Pattern[str]] = {}


def keyword_matches(text: str, keyword: str) -> bool:
    """Return True if *keyword* appears as a whole word/phrase in *text*."""
    key = keyword.strip().lower()
    if key not in _pattern_cache:
        _pattern_cache[key] = _make_pattern(key)
    return bool(_pattern_cache[key].search(text.lower()))


def contains_any(text: str, keywords: list[str]) -> bool:
    """Return True if any of *keywords* match *text* with word-boundary safety."""
    lowered = text.lower()
    return any(keyword_matches(lowered, kw) for kw in keywords)

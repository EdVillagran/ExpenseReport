from __future__ import annotations

from pathlib import Path
import yaml


ROOT_DIR = Path(__file__).resolve().parents[2]
RULES_DIR = ROOT_DIR / "rules"
REPORT_TEMPLATE = ROOT_DIR / "reports" / "templates" / "monthly_report.md.j2"


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}

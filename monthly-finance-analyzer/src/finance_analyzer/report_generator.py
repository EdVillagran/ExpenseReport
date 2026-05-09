from __future__ import annotations

from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def _format_month(month: str) -> str:
    dt = datetime.strptime(month, "%Y-%m")
    return dt.strftime("%B %Y")


def generate_report(month: str, analytics_result: dict, template_path: Path, output_path: Path) -> None:
    env = Environment(loader=FileSystemLoader(str(template_path.parent)), autoescape=False)
    template = env.get_template(template_path.name)

    rendered = template.render(
        month=month,
        month_label=_format_month(month),
        summary=analytics_result["summary"],
        by_category=analytics_result["spending_by_category"].to_dict(orient="records"),
        by_account=analytics_result["spending_by_account"].to_dict(orient="records"),
        by_merchant=analytics_result["spending_by_merchant"].head(10).to_dict(orient="records"),
        top_purchases=analytics_result["top_purchases"].to_dict(orient="records"),
        top_flagged=analytics_result["top_flagged"].to_dict(orient="records"),
        subscriptions=analytics_result["subscriptions"].to_dict(orient="records"),
        trend_note="No prior-month data was provided, so trend analysis is limited.",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")

"""Chart, CSV and PDF generation for the Business Report Bot.

Nothing in this file calculates business numbers; it only presents the
metrics produced by analytics.py as charts, a CSV summary and a PDF report.
"""

import csv
from datetime import date
from pathlib import Path

import pandas as pd
from matplotlib.figure import Figure
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from analytics import build_insights, format_lkr

BRAND_DARK = colors.HexColor("#1f3b57")
BRAND_ROW_ALT = colors.HexColor("#eef3f8")
BRAND_BORDER = colors.HexColor("#b8c4cf")

TABLE_STYLE = TableStyle(
    [
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_ROW_ALT]),
        ("GRID", (0, 0), (-1, -1), 0.4, BRAND_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
)


def _as_thousands(values) -> list:
    """Convert rupee amounts to thousands so the chart axes stay readable."""
    return [float(value) / 1000 for value in values]


def _new_chart() -> tuple:
    """Create a fresh matplotlib figure sized for the PDF page."""
    figure = Figure(figsize=(8, 4.2), dpi=150)
    return figure, figure.add_subplot()


def _save_chart(figure: Figure, path: Path) -> None:
    """Write the figure to disk and release its memory."""
    figure.tight_layout()
    figure.savefig(path)


def create_trend_chart(monthly: pd.DataFrame, path: Path) -> None:
    """Line chart comparing revenue and profit for every month."""
    figure, axis = _new_chart()
    positions = list(range(len(monthly)))

    axis.plot(positions, _as_thousands(monthly["revenue"]), marker="o", linewidth=2,
              color="#1f77b4", label="Revenue")
    axis.plot(positions, _as_thousands(monthly["profit"]), marker="s", linewidth=2,
              color="#2e7d32", label="Profit")
    axis.set_xticks(positions)
    axis.set_xticklabels(monthly["label"], rotation=30, ha="right")
    axis.set_title("Monthly Revenue and Profit Trend", fontsize=13, pad=12)
    axis.set_ylabel("Amount (LKR thousands)")
    axis.grid(axis="y", alpha=0.3)
    axis.legend(frameon=False)
    _save_chart(figure, path)


def create_product_chart(top_products: pd.DataFrame, path: Path) -> None:
    """Horizontal bar chart of the best-selling products by revenue."""
    chart_data = top_products.iloc[::-1]
    figure, axis = _new_chart()

    values = _as_thousands(chart_data["revenue"])
    axis.barh(chart_data["product"], values, color="#1f77b4")
    for position, value in enumerate(values):
        axis.text(value, position, f" {value:,.0f}", va="center", fontsize=8)
    axis.set_title("Top Products by Revenue", fontsize=13, pad=12)
    axis.set_xlabel("Revenue (LKR thousands)")
    axis.grid(axis="x", alpha=0.3)
    axis.set_xlim(0, max(values) * 1.2)
    _save_chart(figure, path)


def create_category_chart(category_stats: pd.DataFrame, path: Path) -> None:
    """Vertical bar chart of revenue for every product category."""
    figure, axis = _new_chart()

    values = _as_thousands(category_stats["revenue"])
    bars = axis.bar(category_stats["category"], values, color="#2a6f97")
    for bar, value in zip(bars, values):
        axis.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{value:,.0f}",
                  ha="center", va="bottom", fontsize=8)
    axis.set_title("Revenue by Category", fontsize=13, pad=12)
    axis.set_ylabel("Revenue (LKR thousands)")
    axis.grid(axis="y", alpha=0.3)
    axis.set_ylim(0, max(values) * 1.2)
    for label in axis.get_xticklabels():
        label.set_rotation(20)
        label.set_ha("right")
    _save_chart(figure, path)


def write_summary_csv(metrics: dict, path: Path) -> None:
    """Write the key metrics plus the monthly breakdown to a CSV summary."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "value"])
        writer.writerows(
            [
                ["generated_on", date.today().isoformat()],
                ["total_revenue_lkr", f"{metrics['total_revenue']:.2f}"],
                ["total_cost_lkr", f"{metrics['total_cost']:.2f}"],
                ["total_profit_lkr", f"{metrics['total_profit']:.2f}"],
                ["profit_margin_pct", f"{metrics['profit_margin_pct']:.2f}"],
                ["total_transactions", metrics["transaction_count"]],
                ["units_sold", f"{metrics['units_sold']:.0f}"],
                ["avg_transaction_value_lkr", f"{metrics['avg_transaction_value']:.2f}"],
                ["best_month_by_revenue", metrics["best_month_revenue_label"]],
                ["best_month_by_profit", metrics["best_month_profit_label"]],
                ["best_category", metrics["best_category"]],
            ]
        )
        writer.writerow([])
        writer.writerow(["month", "revenue_lkr", "profit_lkr", "margin_pct", "transactions"])
        for _, row in metrics["monthly"].iterrows():
            writer.writerow([row["label"], f"{row['revenue']:.2f}", f"{row['profit']:.2f}",
                             f"{row['margin_pct']:.2f}", int(row["transactions"])])


def _styled_table(rows: list, column_widths_cm: list) -> Table:
    """Build a report table with the shared business styling."""
    table = Table(rows, colWidths=[width * cm for width in column_widths_cm])
    table.setStyle(TABLE_STYLE)
    return table


def _share_of(part: float, total: float) -> float:
    """Percentage of a total, guarding against a zero total."""
    return part / total * 100 if total else 0.0


def _executive_summary_text(metrics: dict) -> str:
    """One paragraph that sums up the reporting period in plain language."""
    start, end = metrics["date_range"]
    return (
        f"Between {start:%B %Y} and {end:%B %Y}, the business completed "
        f"{metrics['transaction_count']} sales transactions and sold "
        f"{metrics['units_sold']:,.0f} units. These sales generated "
        f"{format_lkr(metrics['total_revenue'])} in revenue against "
        f"{format_lkr(metrics['total_cost'])} in costs, leaving a profit of "
        f"{format_lkr(metrics['total_profit'])} (a profit margin of "
        f"{metrics['profit_margin_pct']:.1f}%). The average transaction was worth "
        f"{format_lkr(metrics['avg_transaction_value'])}."
    )


def _kpi_table(metrics: dict) -> Table:
    """Headline indicators shown right after the executive summary."""
    rows = [
        ["Indicator", "Value"],
        ["Total revenue", format_lkr(metrics["total_revenue"])],
        ["Total cost", format_lkr(metrics["total_cost"])],
        ["Total profit", format_lkr(metrics["total_profit"])],
        ["Profit margin", f"{metrics['profit_margin_pct']:.1f}%"],
        ["Total transactions", str(metrics["transaction_count"])],
        ["Units sold", f"{metrics['units_sold']:,.0f}"],
        ["Average transaction value", format_lkr(metrics["avg_transaction_value"])],
    ]
    return _styled_table(rows, [8, 7.5])


def _monthly_table(metrics: dict) -> Table:
    """Revenue, profit and margin for each month in the dataset."""
    rows = [["Month", "Revenue", "Profit", "Margin"]]
    rows += [
        [row["label"], format_lkr(row["revenue"]), format_lkr(row["profit"]),
         f"{row['margin_pct']:.1f}%"]
        for _, row in metrics["monthly"].iterrows()
    ]
    return _styled_table(rows, [3.5, 4.7, 4.7, 2.6])


def _product_table(metrics: dict) -> Table:
    """The five products that bring in the most revenue."""
    rows = [["#", "Product", "Revenue", "Profit", "Units"]]
    rows += [
        [str(position), row["product"], format_lkr(row["revenue"]),
         format_lkr(row["profit"]), f"{row['units']:,.0f}"]
        for position, (_, row) in enumerate(metrics["top_products"].iterrows(), start=1)
    ]
    return _styled_table(rows, [1, 6.5, 3.6, 3.6, 1.8])


def _category_table(metrics: dict) -> Table:
    """Revenue, share and profit for each product category."""
    rows = [["Category", "Revenue", "Share of revenue", "Profit"]]
    rows += [
        [row["category"], format_lkr(row["revenue"]),
         f"{_share_of(row['revenue'], metrics['total_revenue']):.1f}%",
         format_lkr(row["profit"])]
        for _, row in metrics["category_stats"].iterrows()
    ]
    return _styled_table(rows, [4.5, 4.2, 3.4, 3.4])


def _chart_image(path: Path, width_cm: float = 15.5) -> Image:
    """Place a saved chart on the page, scaled to the given width in cm."""
    image_width, image_height = ImageReader(str(path)).getSize()
    height_cm = width_cm * image_height / image_width
    return Image(str(path), width=width_cm * cm, height=height_cm * cm)


def _build_styles() -> dict:
    """Paragraph styles used across the PDF report."""
    base = getSampleStyleSheet()

    def style(name: str, parent: str, **options) -> ParagraphStyle:
        return ParagraphStyle(f"Bot{name}", parent=base[parent], **options)

    grey = colors.HexColor("#7a8691")
    return {
        "title": style("Title", "Title", fontSize=20, leading=24, textColor=BRAND_DARK),
        "subtitle": style("Subtitle", "Normal", fontSize=10, alignment=TA_CENTER,
                          textColor=colors.HexColor("#5a6b7a")),
        "meta": style("Meta", "Normal", fontSize=9, alignment=TA_CENTER, textColor=grey),
        "heading": style("Heading", "Heading2", textColor=BRAND_DARK, spaceBefore=12, spaceAfter=6),
        "body": style("Body", "BodyText", fontSize=9.5, leading=14),
        "bullet": style("Bullet", "BodyText", fontSize=9.5, leading=14, leftIndent=14,
                        bulletIndent=4, spaceAfter=4),
        "footer": style("Footer", "Normal", fontSize=8, textColor=grey),
    }


def generate_pdf_report(metrics: dict, insights: list, chart_paths: list, pdf_path: Path) -> None:
    """Build the full multi-page PDF business report."""
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title="Business Performance Report",
        author="Business Report Bot",
    )
    styles = _build_styles()
    trend_path, product_path, category_path = chart_paths

    story = [
        Paragraph("Business Performance Report", styles["title"]),
        Paragraph("Prepared automatically by Business Report Bot", styles["subtitle"]),
        Paragraph(f"Generated on {date.today().strftime('%d %B %Y')}", styles["meta"]),
        Spacer(1, 14),
        Paragraph("1. Executive Summary", styles["heading"]),
        Paragraph(_executive_summary_text(metrics), styles["body"]),
        Spacer(1, 6),
        Paragraph("2. Key Performance Indicators", styles["heading"]),
        _kpi_table(metrics),
        PageBreak(),
        Paragraph("3. Monthly Revenue and Profit", styles["heading"]),
        _monthly_table(metrics),
        Spacer(1, 10),
        _chart_image(trend_path),
        Spacer(1, 10),
        Paragraph("4. Top-Performing Products", styles["heading"]),
        _product_table(metrics),
        Spacer(1, 10),
        _chart_image(product_path),
        Spacer(1, 10),
        Paragraph("5. Revenue by Category", styles["heading"]),
        _category_table(metrics),
        Spacer(1, 10),
        _chart_image(category_path),
        PageBreak(),
        Paragraph("6. Business Insights", styles["heading"]),
    ]
    for insight in insights:
        story.append(Paragraph(insight, styles["bullet"], bulletText="\u2022"))
    story.append(Spacer(1, 18))
    story.append(
        Paragraph(
            "All figures are calculated directly from sales.csv. "
            "Report generated by Business Report Bot.",
            styles["footer"],
        )
    )
    doc.build(story)


def generate_all_reports(metrics: dict, output_dir: Path) -> dict:
    """Create the charts, summary CSV and PDF report inside output_dir.

    The directory is created automatically when it does not exist yet.
    Returns the generated file paths so the menu can show them to the user.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    trend_path = output_dir / "monthly_trend.png"
    product_path = output_dir / "top_products.png"
    category_path = output_dir / "category_revenue.png"
    summary_path = output_dir / "business_summary.csv"
    pdf_path = output_dir / "business_report.pdf"

    create_trend_chart(metrics["monthly"], trend_path)
    create_product_chart(metrics["top_products"], product_path)
    create_category_chart(metrics["category_stats"], category_path)
    write_summary_csv(metrics, summary_path)
    generate_pdf_report(metrics, build_insights(metrics),
                        [trend_path, product_path, category_path], pdf_path)

    return {
        "pdf": pdf_path,
        "summary_csv": summary_path,
        "charts": [trend_path, product_path, category_path],
    }

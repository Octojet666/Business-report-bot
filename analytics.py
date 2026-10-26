"""Business calculations for the Business Report Bot.

Every number shown in the terminal, the charts or the PDF report is produced
here, so the financial rules stay in one place:

    revenue = quantity * unit_price
    cost    = quantity * unit_cost
    profit  = revenue - cost
    margin  = profit / revenue * 100
"""

import pandas as pd


def format_lkr(value: float) -> str:
    """Format an amount as Sri Lankan rupees, for example 'LKR 1,234,567.89'."""
    return f"LKR {value:,.2f}"


def _safe_div(numerator: float, denominator: float) -> float:
    """Divide two numbers but return 0.0 instead of failing on a zero denominator."""
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _monthly_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Group the sales by calendar month with revenue, profit and margin."""
    monthly = (
        df.groupby("month")
        .agg(
            revenue=("revenue", "sum"),
            profit=("profit", "sum"),
            transactions=("transaction_id", "count"),
        )
        .sort_index()
        .reset_index()
    )
    monthly["label"] = monthly["month"].dt.strftime("%b %Y")
    monthly["margin_pct"] = [
        _safe_div(row["profit"], row["revenue"]) * 100 for _, row in monthly.iterrows()
    ]
    return monthly


def _product_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Revenue, profit and units per product, best seller first."""
    return (
        df.groupby("product")
        .agg(revenue=("revenue", "sum"), profit=("profit", "sum"), units=("quantity", "sum"))
        .sort_values("revenue", ascending=False)
        .reset_index()
    )


def _category_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Revenue, profit and units per category, strongest category first."""
    return (
        df.groupby("category")
        .agg(revenue=("revenue", "sum"), profit=("profit", "sum"), units=("quantity", "sum"))
        .sort_values("revenue", ascending=False)
        .reset_index()
    )


def build_metrics(df: pd.DataFrame) -> dict:
    """Calculate every metric the menu and the reports need, from clean sales data."""
    if df.empty:
        raise ValueError("No sales data to analyse. Check that sales.csv contains data rows.")

    total_revenue = float(df["revenue"].sum())
    total_cost = float(df["cost"].sum())
    total_profit = float(df["profit"].sum())
    transaction_count = int(len(df))
    units_sold = float(df["quantity"].sum())

    monthly = _monthly_breakdown(df)
    product_stats = _product_breakdown(df)
    category_stats = _category_breakdown(df)
    best_revenue_month = monthly.loc[monthly["revenue"].idxmax()]
    best_profit_month = monthly.loc[monthly["profit"].idxmax()]

    return {
        "total_revenue": total_revenue,
        "total_cost": total_cost,
        "total_profit": total_profit,
        "profit_margin_pct": _safe_div(total_profit, total_revenue) * 100,
        "transaction_count": transaction_count,
        "units_sold": units_sold,
        "avg_transaction_value": _safe_div(total_revenue, transaction_count),
        "monthly": monthly,
        "product_stats": product_stats,
        "category_stats": category_stats,
        "top_products": product_stats.head(5),
        "best_month_revenue_label": str(best_revenue_month["label"]),
        "best_month_revenue_value": float(best_revenue_month["revenue"]),
        "best_month_profit_label": str(best_profit_month["label"]),
        "best_month_profit_value": float(best_profit_month["profit"]),
        "best_category": str(category_stats.iloc[0]["category"]),
        "best_category_value": float(category_stats.iloc[0]["revenue"]),
        "date_range": (df["date"].min(), df["date"].max()),
    }


def build_insights(metrics: dict) -> list:
    """Turn the metrics into short insight sentences for the report.

    Only statements that can be traced back to the dataset are produced;
    nothing here is invented or hardcoded.
    """
    insights = []

    top_product = metrics["top_products"].iloc[0]
    product_share = _safe_div(top_product["revenue"], metrics["total_revenue"]) * 100
    insights.append(
        f"{top_product['product']} is the strongest product, generating "
        f"{format_lkr(top_product['revenue'])} ({product_share:.1f}% of total revenue)."
    )

    top_category = metrics["category_stats"].iloc[0]
    category_share = _safe_div(top_category["revenue"], metrics["total_revenue"]) * 100
    insights.append(
        f"The {top_category['category']} category leads the business with "
        f"{format_lkr(top_category['revenue'])} in revenue ({category_share:.1f}% of the total)."
    )

    insights.append(
        f"{metrics['best_month_revenue_label']} recorded the highest revenue at "
        f"{format_lkr(metrics['best_month_revenue_value'])}."
    )

    if metrics["best_month_profit_label"] == metrics["best_month_revenue_label"]:
        insights.append(
            f"That same month, {metrics['best_month_profit_label']}, was also the most "
            f"profitable with {format_lkr(metrics['best_month_profit_value'])} in profit."
        )
    else:
        insights.append(
            f"{metrics['best_month_profit_label']} was the most profitable month instead, "
            f"earning {format_lkr(metrics['best_month_profit_value'])}."
        )

    if metrics["total_revenue"] > 0:
        insights.append(
            f"Overall the business kept {metrics['profit_margin_pct']:.1f}% of its revenue "
            f"as profit across {metrics['transaction_count']} transactions."
        )

    return insights



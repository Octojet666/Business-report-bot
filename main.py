"""Business Report Bot.

Reads sales.csv, calculates the key business numbers and turns them into a
PDF report, charts and a CSV summary. Run it with:

    python main.py
"""

from pathlib import Path

from analytics import build_metrics, format_lkr
from data import DataValidationError, load_sales_data
from reports import generate_all_reports

DATA_FILE = Path(__file__).resolve().parent / "sales.csv"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"

MENU = """
=========================================
           BUSINESS REPORT BOT
=========================================
 1. Generate complete business report
 2. View business summary
 3. View top-performing products
 4. Exit
"""


def show_summary(metrics: dict) -> None:
    """Print the key business metrics in a readable block."""
    print("\n" + "=" * 46)
    print("BUSINESS SUMMARY")
    print("=" * 46)
    print(f"Total revenue            : {format_lkr(metrics['total_revenue'])}")
    print(f"Total cost               : {format_lkr(metrics['total_cost'])}")
    print(f"Total profit             : {format_lkr(metrics['total_profit'])}")
    print(f"Profit margin            : {metrics['profit_margin_pct']:.1f}%")
    print(f"Total transactions       : {metrics['transaction_count']}")
    print(f"Units sold               : {metrics['units_sold']:,.0f}")
    print(f"Avg transaction value    : {format_lkr(metrics['avg_transaction_value'])}")
    print(f"Best month by revenue    : {metrics['best_month_revenue_label']}")
    print(f"Best month by profit     : {metrics['best_month_profit_label']}")
    print(f"Best category            : {metrics['best_category']}")

    print("\nMonthly performance:")
    for _, row in metrics["monthly"].iterrows():
        print(
            f"  {row['label']:<9} revenue {format_lkr(row['revenue']):>20}"
            f"  profit {format_lkr(row['profit']):>20}"
        )


def show_top_products(metrics: dict) -> None:
    """Print the five products that bring in the most revenue."""
    print("\n" + "=" * 46)
    print("TOP 5 PRODUCTS BY REVENUE")
    print("=" * 46)
    for position, (_, row) in enumerate(metrics["top_products"].iterrows(), start=1):
        print(
            f"{position}. {row['product']:<26} {format_lkr(row['revenue']):>20}"
            f"  ({row['units']:,.0f} units)"
        )


def generate_report(metrics: dict) -> None:
    """Create the PDF report, charts and CSV summary inside output/."""
    print("\nGenerating report files, please wait...")
    try:
        paths = generate_all_reports(metrics, OUTPUT_DIR)
    except OSError as exc:
        print(f"Report generation failed while writing files: {exc}")
        return
    except Exception as exc:
        print(f"Report generation failed unexpectedly: {exc}")
        return

    print("Done! Your report is ready:")
    print(f"  PDF report  : output/{paths['pdf'].name}")
    print(f"  Summary CSV : output/{paths['summary_csv'].name}")
    for chart in paths["charts"]:
        print(f"  Chart       : output/{chart.name}")


def main() -> None:
    """Entry point: load the data once, then serve the menu until the user exits."""
    print("Loading sales data from sales.csv ...")
    try:
        sales = load_sales_data(DATA_FILE)
    except DataValidationError as exc:
        print(f"\nDATA PROBLEM\n{exc}")
        return

    metrics = build_metrics(sales)
    start, end = metrics["date_range"]
    print(f"Loaded {len(sales)} transactions ({start:%b %Y} to {end:%b %Y}).")

    while True:
        print(MENU)
        try:
            choice = input("Select an option (1-4): ").strip()
        except EOFError:
            print("\nGoodbye!")
            break

        if choice == "1":
            generate_report(metrics)
        elif choice == "2":
            show_summary(metrics)
        elif choice == "3":
            show_top_products(metrics)
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number from 1 to 4.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGoodbye!")

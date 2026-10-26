# Business Report Bot

A small Python tool that turns a plain `sales.csv` file into a professional PDF business report, charts and a metric summary.

This was built as a project to demonstrate practical Python skills: data validation, pandas analysis, matplotlib visualisation, reportlab PDF generation and clean command-line tooling.

---

## The problem being solved

Small businesses already track sales in spreadsheets, but turning those rows into an actual *report* — totals, margins, trends, best performers: usually means an hour of manual spreadsheet work every month.

Business Report Bot automates that step. Drop a `sales.csv` file into the folder, run one command, and get a consistent, professional report in seconds. Crucially, the bot **refuses to analyse data it cannot trust**: if the CSV has missing values, invalid dates, non-numeric prices or duplicate transaction IDs, it explains exactly what is wrong (with row numbers) instead of producing a misleading report.

## Features

- Loads and validates `sales.csv`, reporting *every* problem found (missing file, missing columns, blank cells, bad dates, non-numeric values, negative quantities, duplicate transaction IDs) with spreadsheet-style row numbers
- Calculates revenue, cost, profit, profit margin, transaction count, units sold, average transaction value, monthly trends, product/category rankings and best-performing month — all derived live from the data, nothing hardcoded
- Generates a multi-page PDF report with an executive summary, KPI table, monthly analysis, top products, category breakdown, embedded charts and data-driven insights
- Creates three charts: monthly revenue/profit trend, top products, revenue by category
- Exports a CSV summary of the key metrics
- Interactive terminal menu with input validation
- All financial figures formatted in Sri Lankan rupees (LKR)

## Technology stack

| Tool | Purpose |
| --- | --- |
| Python 3.9+ | Core language (standard library: `csv`, `pathlib`, `datetime`) |
| pandas | Data loading, validation and aggregation |
| matplotlib | Chart rendering |
| reportlab | PDF report generation |


Generated files land in `output/`, which the bot creates automatically:

```
output/
├── business_report.pdf    # The full PDF report
├── business_summary.csv   # Key metrics + monthly breakdown
├── monthly_trend.png      # Revenue and profit per month
├── top_products.png       # Best products by revenue
└── category_revenue.png   # Revenue per category
```

## Installation

```bash
# Create a virtual environment
python -m venv .venv
```

Activate it:

```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Run it:
```bash
python main.py
```

You will see the menu:

```
=========================================
           BUSINESS REPORT BOT
=========================================
 1. Generate complete business report
 2. View business summary
 3. View top-performing products
 4. Exit

Select an option (1-4):
```

- **Option 1** generates the PDF report, the three charts and the CSV summary into `output/`
- **Option 2** prints the key business metrics in the terminal
- **Option 3** prints the top five products by revenue
- **Option 4** exits cleanly


## Sample report description

The generated PDF (`output/business_report.pdf`) is a clean A4 business document containing:

1. **Executive summary** — a plain-language paragraph describing the period, transaction volume, revenue, cost, profit and margin
2. **Key performance indicators** — a styled table of the headline numbers
3. **Monthly revenue and profit** — a table per month plus a trend line chart
4. **Top-performing products** — the five biggest earners with a horizontal bar chart
5. **Revenue by category** — category table with revenue share plus a bar chart
6. **Business insights** — short conclusions generated from the data itself (best product, best category, best month, retained margin)

Every figure is calculated from `sales.csv` at run time — change the CSV and the report changes with it.

## Sample dataset disclaimer

**The included `sales.csv` is entirely fictional** and exists only for demonstration. The 100 transactions describe an imaginary Sri Lankan homeware and hospitality supplies business across six months (May–October 2025). All product names, prices, costs and dates were invented; they do not represent any real company or real financial results. Replace `sales.csv` with your own data (same columns) to analyse a real business.


## Notes

- The `output/` folder is generated at run time and excluded from version control via `.gitignore`
- Financial rules are kept in one place (`analytics.py`): revenue = quantity × unit price, cost = quantity × unit cost, profit = revenue − cost, margin = profit ÷ revenue × 100

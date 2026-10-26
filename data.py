"""Loading and validation of the sales dataset.

The bot refuses to analyse data it cannot trust. load_sales_data() reads
sales.csv as plain text, checks every column against the validation rules
and either returns a clean DataFrame ready for analysis, or raises a
DataValidationError that lists every problem found in the file.
"""

from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = (
    "transaction_id",
    "date",
    "product",
    "category",
    "quantity",
    "unit_price",
    "unit_cost",
)

NUMBER_COLUMNS = ("quantity", "unit_price", "unit_cost")


class DataValidationError(Exception):
    """Raised when the sales file is missing, empty or fails validation."""


def _row_numbers(mask: pd.Series) -> list:
    """Turn a boolean mask into spreadsheet-style row numbers (row 1 = header)."""
    return [int(row) + 2 for row in mask.index[mask]]


def _examples(values: pd.Series, limit: int = 3) -> str:
    """Show a few of the offending values inside an error message."""
    return ", ".join(str(value) for value in values.head(limit))


def load_sales_data(csv_path) -> pd.DataFrame:
    """Read and validate the sales CSV, then return a clean analysis-ready table.

    The returned DataFrame keeps the original columns and adds `month`,
    `revenue`, `cost` and `profit`. Raises DataValidationError with a readable
    summary of every problem when the file cannot be trusted.
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise DataValidationError(
            f"Could not find the data file: {csv_path}\n"
            "Make sure sales.csv is in the project folder and try again."
        )

    try:
        raw = pd.read_csv(csv_path, dtype=str, skipinitialspace=True)
    except pd.errors.EmptyDataError:
        raise DataValidationError(f"{csv_path.name} is empty. Add at least one sales row.")
    except OSError as exc:
        raise DataValidationError(f"Could not read {csv_path.name}: {exc}")

    raw.columns = [column.strip() for column in raw.columns]
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in raw.columns]
    if missing_columns:
        raise DataValidationError(
            f"{csv_path.name} is missing required column(s): {', '.join(missing_columns)}.\n"
            f"Expected columns: {', '.join(REQUIRED_COLUMNS)}"
        )

    raw = raw[list(REQUIRED_COLUMNS)].copy()
    raw = raw.fillna("")
    for column in raw.columns:
        raw[column] = raw[column].str.strip()

    problems = []

    for column in REQUIRED_COLUMNS:
        blank = raw[column] == ""
        if blank.any():
            problems.append(f"column '{column}' has blank values in row(s) {_row_numbers(blank)}")

    numbers = {}
    for column in NUMBER_COLUMNS:
        parsed = pd.to_numeric(raw[column], errors="coerce")
        invalid = parsed.isna() & (raw[column] != "")
        if invalid.any():
            problems.append(
                f"column '{column}' has non-numeric values in row(s) {_row_numbers(invalid)} "
                f"(examples: {_examples(raw.loc[invalid, column])})"
            )
        numbers[column] = parsed

    try:
        dates = pd.to_datetime(raw["date"], errors="coerce")
    except ValueError:
        dates = pd.to_datetime(raw["date"], errors="coerce", format="mixed")
    invalid_dates = dates.isna() & (raw["date"] != "")
    if invalid_dates.any():
        problems.append(
            f"column 'date' has invalid dates in row(s) {_row_numbers(invalid_dates)} "
            f"(examples: {_examples(raw.loc[invalid_dates, 'date'])}); use the YYYY-MM-DD format"
        )

    negative_quantity = numbers["quantity"] < 0
    if negative_quantity.any():
        problems.append(
            f"column 'quantity' has negative values in row(s) {_row_numbers(negative_quantity)}"
        )

    duplicated_ids = (raw["transaction_id"] != "") & raw["transaction_id"].duplicated(keep=False)
    if duplicated_ids.any():
        duplicated_values = sorted(raw.loc[duplicated_ids, "transaction_id"].unique())
        problems.append(
            f"column 'transaction_id' has duplicate value(s) {', '.join(duplicated_values)} "
            f"in row(s) {_row_numbers(duplicated_ids)}"
        )

    if problems:
        details = "\n  - ".join(problems)
        raise DataValidationError(
            f"{csv_path.name} failed validation with {len(problems)} problem(s):\n"
            f"  - {details}\n"
            "Fix these rows in the CSV and run the bot again. Invalid records are never "
            "silently skipped, so the reports stay trustworthy."
        )

    if raw.empty:
        raise DataValidationError(
            f"{csv_path.name} has a header but no data rows. Add at least one sale."
        )

    clean = pd.DataFrame(
        {
            "transaction_id": raw["transaction_id"],
            "date": dates,
            "product": raw["product"],
            "category": raw["category"],
            "quantity": numbers["quantity"].astype(float),
            "unit_price": numbers["unit_price"].astype(float),
            "unit_cost": numbers["unit_cost"].astype(float),
        }
    )
    clean["revenue"] = clean["quantity"] * clean["unit_price"]
    clean["cost"] = clean["quantity"] * clean["unit_cost"]
    clean["profit"] = clean["revenue"] - clean["cost"]
    clean["month"] = clean["date"].dt.to_period("M")
    return clean

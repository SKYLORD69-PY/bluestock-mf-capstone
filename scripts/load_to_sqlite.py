"""
load_to_sqlite.py
==================
Bluestock Fintech - Mutual Fund Analytics Capstone
Day 2, Task 5: Build data/db/bluestock_mf.db from sql/schema.sql, then
load all 10 cleaned CSVs (data/processed/) using SQLAlchemy's
create_engine() + DataFrame.to_sql(), and verify the row counts loaded
into SQLite match the row counts in the source cleaned CSVs.

Run from the project root:
    python scripts/load_to_sqlite.py
"""

from pathlib import Path
import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DB_DIR = PROJECT_ROOT / "data" / "db"
SQL_DIR = PROJECT_ROOT / "sql"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "bluestock_mf.db"
SCHEMA_PATH = SQL_DIR / "schema.sql"


def build_dim_date(start: str, end: str) -> pd.DataFrame:
    """Generate a full calendar-day date dimension covering every date used
    anywhere in the fact tables (nav, transactions, aum, benchmark, perf)."""
    dates = pd.date_range(start, end, freq="D")
    return pd.DataFrame({
        "date_id": dates.strftime("%Y-%m-%d"),
        "year": dates.year,
        "month": dates.month,
        "quarter": dates.quarter,
        "day_name": dates.day_name(),
        "is_weekday": (dates.weekday < 5).astype(int),
    })


def create_schema(engine) -> None:
    raw_conn = engine.raw_connection()
    try:
        raw_conn.executescript(SCHEMA_PATH.read_text())
        raw_conn.commit()
    finally:
        raw_conn.close()
    print(f"Schema created from {SCHEMA_PATH.relative_to(PROJECT_ROOT)}")


def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()  # rebuild from scratch every run, for idempotency
    engine = create_engine(f"sqlite:///{DB_PATH}")
    create_schema(engine)

    # ---- dim_date: derive from the actual min/max date across all sources ----
    nav = pd.read_csv(PROCESSED_DIR / "02_nav_history_clean.csv")
    tx = pd.read_csv(PROCESSED_DIR / "08_investor_transactions_clean.csv")
    aum = pd.read_csv(PROCESSED_DIR / "03_aum_by_fund_house_clean.csv")
    bench = pd.read_csv(PROCESSED_DIR / "10_benchmark_indices_clean.csv")

    all_dates = pd.concat([
        pd.to_datetime(nav["date"]), pd.to_datetime(tx["transaction_date"]),
        pd.to_datetime(aum["date"]), pd.to_datetime(bench["date"]),
    ])
    start, end = all_dates.min().strftime("%Y-%m-%d"), all_dates.max().strftime("%Y-%m-%d")
    dim_date = build_dim_date(start, end)
    print(f"dim_date: {len(dim_date)} calendar days, {start} -> {end}")

    as_of_date = nav["date"].max()  # most recent NAV date = performance snapshot date

    loads = []  # (table_name, dataframe, source_csv_for_verification)

    loads.append(("dim_date", dim_date, None))

    fm = pd.read_csv(PROCESSED_DIR / "01_fund_master_clean.csv")
    loads.append(("dim_fund", fm, "01_fund_master_clean.csv"))

    loads.append(("fact_nav", nav, "02_nav_history_clean.csv"))

    loads.append(("fact_aum", aum, "03_aum_by_fund_house_clean.csv"))

    sip = pd.read_csv(PROCESSED_DIR / "04_monthly_sip_inflows_clean.csv")
    loads.append(("fact_sip_industry", sip, "04_monthly_sip_inflows_clean.csv"))

    cat = pd.read_csv(PROCESSED_DIR / "05_category_inflows_clean.csv")
    loads.append(("fact_category_inflow", cat, "05_category_inflows_clean.csv"))

    folio = pd.read_csv(PROCESSED_DIR / "06_industry_folio_count_clean.csv")
    loads.append(("fact_folio", folio, "06_industry_folio_count_clean.csv"))

    perf = pd.read_csv(PROCESSED_DIR / "07_scheme_performance_clean.csv")
    perf.insert(1, "as_of_date", as_of_date)
    loads.append(("fact_performance", perf, "07_scheme_performance_clean.csv"))

    loads.append(("fact_transactions", tx, "08_investor_transactions_clean.csv"))

    hold = pd.read_csv(PROCESSED_DIR / "09_portfolio_holdings_clean.csv")
    loads.append(("fact_portfolio", hold, "09_portfolio_holdings_clean.csv"))

    loads.append(("fact_benchmark", bench, "10_benchmark_indices_clean.csv"))

    print("\nLoading tables ...")
    for table, df, _ in loads:
        df.to_sql(table, engine, if_exists="append", index=False)
        print(f"  loaded {table:24s} {len(df):>7d} rows")

    print("\nVerifying row counts (SQLite vs. source CSV) ...")
    all_match = True
    with engine.connect() as conn:
        for table, df, source_csv in loads:
            db_count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            expected = len(df)
            status = "OK" if db_count == expected else "MISMATCH"
            if db_count != expected:
                all_match = False
            note = f"(source: {source_csv})" if source_csv else "(generated dimension, no source CSV)"
            print(f"  [{status}] {table:24s} sqlite={db_count:>7d}  expected={expected:>7d}  {note}")

    print(f"\n{'ALL ROW COUNTS MATCH' if all_match else 'SOME ROW COUNTS DO NOT MATCH - see above'}")
    print(f"Database written to: {DB_PATH} ({DB_PATH.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()

"""
data_ingestion.py
==================
Bluestock Fintech - Mutual Fund Analytics Capstone
Day 1, Task 3, 6 & 7: Load all 10 provided datasets, profile them
(shape / dtypes / head), explore the fund master, and validate AMFI
scheme-code referential integrity across tables.

This script does NOT clean or rewrite the data - that is Day 2's job.
It only reads, inspects, and reports. Output: a console report plus a
written data-quality summary at reports/day1_data_quality_summary.txt

Run from the project root:
    python scripts/data_ingestion.py
"""

from pathlib import Path
import pandas as pd

pd.set_option("display.max_columns", 20)
pd.set_option("display.width", 140)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

DATASETS = [
    "01_fund_master.csv",
    "02_nav_history.csv",
    "03_aum_by_fund_house.csv",
    "04_monthly_sip_inflows.csv",
    "05_category_inflows.csv",
    "06_industry_folio_count.csv",
    "07_scheme_performance.csv",
    "08_investor_transactions.csv",
    "09_portfolio_holdings.csv",
    "10_benchmark_indices.csv",
]


def load_all_datasets() -> dict[str, pd.DataFrame]:
    """Load every CSV in DATASETS into a dict of {filename: DataFrame}."""
    frames = {}
    for filename in DATASETS:
        path = RAW_DIR / filename
        if not path.exists():
            print(f"  [MISSING] {filename} not found in {RAW_DIR}")
            continue
        frames[filename] = pd.read_csv(path)
    return frames


def profile_dataset(name: str, df: pd.DataFrame, log_lines: list[str]) -> None:
    """Print and log shape, dtypes and head() for one dataset."""
    header = f"\n{'=' * 70}\n{name}\n{'=' * 70}"
    print(header)
    log_lines.append(header)

    shape_line = f"Shape: {df.shape[0]} rows x {df.shape[1]} columns"
    print(shape_line)
    log_lines.append(shape_line)

    print("\nDtypes:")
    print(df.dtypes)
    log_lines.append("\nDtypes:\n" + df.dtypes.to_string())

    print("\nHead:")
    print(df.head(3))
    log_lines.append("\nHead:\n" + df.head(3).to_string())


def detect_anomalies(name: str, df: pd.DataFrame, log_lines: list[str]) -> None:
    """Flag structural anomalies: junk columns, fully-blank rows, dup rows."""
    notes = []

    # Unnamed / junk columns (usually trailing commas in the source CSV)
    junk_cols = [c for c in df.columns if str(c).startswith("Unnamed")]
    if junk_cols:
        notes.append(f"  - {len(junk_cols)} junk 'Unnamed' column(s) detected: {junk_cols}")

    # Fully blank rows (every real column is NaN)
    real_cols = [c for c in df.columns if not str(c).startswith("Unnamed")]
    blank_rows = df[real_cols].isna().all(axis=1).sum()
    if blank_rows:
        notes.append(f"  - {blank_rows} fully blank row(s) out of {len(df)} total rows")

    # Exact full-row duplicates
    dup_rows = df.duplicated().sum()
    if dup_rows:
        notes.append(f"  - {dup_rows} exact duplicate row(s)")

    if notes:
        msg = f"\n[ANOMALY] {name}:\n" + "\n".join(notes)
    else:
        msg = f"\n[OK] {name}: no structural anomalies detected"
    print(msg)
    log_lines.append(msg)


def explore_fund_master(fm_raw: pd.DataFrame, log_lines: list[str]) -> pd.DataFrame:
    """
    Day 1 Task 6: print unique fund houses, categories, sub-categories,
    risk grades. Returns a de-junked, blank-row-free copy for use in the
    AMFI code validation step (in-memory only - not written to disk;
    real cleaning happens on Day 2).
    """
    header = f"\n{'=' * 70}\nFUND MASTER EXPLORATION (Day 1, Task 6)\n{'=' * 70}"
    print(header)
    log_lines.append(header)

    real_cols = [c for c in fm_raw.columns if not str(c).startswith("Unnamed")]
    fm = fm_raw[real_cols].dropna(subset=["amfi_code"]).copy()
    fm["amfi_code"] = fm["amfi_code"].astype(int)

    lines = [
        f"Real scheme rows after dropping blanks/junk columns: {len(fm)} (raw file reported {len(fm_raw)} rows)",
        f"\nUnique fund houses ({fm['fund_house'].nunique()}):",
        f"  {sorted(fm['fund_house'].unique())}",
        f"\nUnique categories ({fm['category'].nunique()}):",
        f"  {sorted(fm['category'].unique())}",
        f"\nUnique sub-categories ({fm['sub_category'].nunique()}):",
        f"  {sorted(fm['sub_category'].unique())}",
        f"\nUnique risk grades / risk_category ({fm['risk_category'].nunique()}):",
        f"  {sorted(fm['risk_category'].unique())}",
        f"\nUnique plans ({fm['plan'].nunique()}):",
        f"  {sorted(fm['plan'].unique())}",
        f"\nUnique SEBI category codes ({fm['sebi_category_code'].nunique()}):",
        f"  {sorted(fm['sebi_category_code'].unique())}",
        "\nNote on AMFI / SEBI scheme-code structure:",
        "  Real AMFI codes are 5-6 digit integers issued sequentially by AMFI/RTAs",
        "  per scheme x plan combination (e.g. Growth, Direct-Growth, IDCW each get",
        "  their own code). The 'sebi_category_code' column here is a project-internal",
        "  shorthand (ECxx = Equity Category xx, DCxx = Debt Category xx, EIxx = Equity",
        "  Index) and is NOT an official AMFI/SEBI code format.",
    ]
    for line in lines:
        print(line)
    log_lines.append("\n".join(lines))

    return fm


def validate_amfi_codes(fm: pd.DataFrame, frames: dict[str, pd.DataFrame], log_lines: list[str]) -> None:
    """
    Day 1 Task 7: confirm every amfi_code referenced in the other tables
    exists in the (cleaned) fund_master master list, and vice versa.
    """
    header = f"\n{'=' * 70}\nAMFI CODE VALIDATION (Day 1, Task 7)\n{'=' * 70}"
    print(header)
    log_lines.append(header)

    master_codes = set(fm["amfi_code"])
    summary = [f"Master fund_master.csv has {len(master_codes)} unique, valid amfi_codes after cleaning.\n"]

    checks = {
        "02_nav_history.csv": "amfi_code",
        "07_scheme_performance.csv": "amfi_code",
        "08_investor_transactions.csv": "amfi_code",
        "09_portfolio_holdings.csv": "amfi_code",
    }

    all_clean = True
    for fname, col in checks.items():
        df = frames.get(fname)
        if df is None:
            continue
        codes = set(df[col].unique())
        missing_from_master = codes - master_codes
        missing_from_file = master_codes - codes
        line = f"{fname}: {len(codes)} unique codes referenced."
        if missing_from_master:
            all_clean = False
            orphan_rows = df[df[col].isin(missing_from_master)]
            line += (
                f"\n  [FAIL] {len(missing_from_master)} code(s) NOT in fund_master: "
                f"{sorted(missing_from_master)} -> affects {len(orphan_rows)} row(s)"
            )
        else:
            line += "  [PASS] every code exists in fund_master."
        if fname == "09_portfolio_holdings.csv" and missing_from_file:
            line += f"\n  Note: {len(missing_from_file)} master fund(s) have no portfolio holdings row (expected - only equity funds hold stocks)."
        summary.append(line)

    print("\n".join(summary))
    log_lines.append("\n".join(summary))

    verdict = (
        "\nOVERALL: All cross-table AMFI code references are clean - every code used "
        "in nav_history, scheme_performance, investor_transactions and portfolio_holdings "
        "exists in fund_master."
        if all_clean
        else "\nOVERALL: One or more orphan AMFI codes were found - see FAIL lines above."
    )
    print(verdict)
    log_lines.append(verdict)


def deeper_quality_checks(frames: dict[str, pd.DataFrame], log_lines: list[str]) -> None:
    """A few extra sanity checks worth calling out before Day 2 cleaning."""
    header = f"\n{'=' * 70}\nADDITIONAL DATA QUALITY NOTES\n{'=' * 70}"
    print(header)
    log_lines.append(header)

    notes = []

    nav = frames.get("02_nav_history.csv")
    if nav is not None:
        nav_dates = pd.to_datetime(nav["date"])
        notes.append(f"- NAV history spans {nav_dates.min().date()} to {nav_dates.max().date()}.")
        notes.append(f"  NAV <= 0: {(nav['nav'] <= 0).sum()} rows. Duplicate (amfi_code,date) rows: "
                     f"{nav.duplicated(subset=['amfi_code','date']).sum()}.")
        notes.append(f"  Weekend rows present: {(pd.to_datetime(nav['date']).dt.weekday >= 5).sum()} "
                      "(0 is expected - NAV is only published on business days).")

    perf = frames.get("07_scheme_performance.csv")
    if perf is not None:
        out_of_range = ((perf["expense_ratio_pct"] < 0.1) | (perf["expense_ratio_pct"] > 2.5)).sum()
        notes.append(f"- scheme_performance: expense ratios all within 0.1%-2.5% sanity band: "
                      f"{'YES' if out_of_range == 0 else f'NO ({out_of_range} outliers)'}. "
                      f"Negative Sharpe ratios: {(perf['sharpe_ratio'] < 0).sum()}.")

    tx = frames.get("08_investor_transactions.csv")
    if tx is not None:
        notes.append(f"- investor_transactions: {tx['investor_id'].nunique()} unique investors, "
                      f"{tx['amount_inr'].le(0).sum()} non-positive amounts, "
                      f"transaction types = {sorted(tx['transaction_type'].unique())}.")

    print("\n".join(notes))
    log_lines.append("\n".join(notes))


def main() -> None:
    log_lines: list[str] = [
        "BLUESTOCK MF CAPSTONE — DAY 1 DATA QUALITY SUMMARY",
        "Generated by data_ingestion.py",
    ]

    print("Loading all 10 datasets from data/raw/ ...")
    frames = load_all_datasets()
    print(f"Loaded {len(frames)} / {len(DATASETS)} files.\n")

    for name, df in frames.items():
        profile_dataset(name, df, log_lines)
        detect_anomalies(name, df, log_lines)

    fm_clean = explore_fund_master(frames["01_fund_master.csv"], log_lines)
    validate_amfi_codes(fm_clean, frames, log_lines)
    deeper_quality_checks(frames, log_lines)

    out_path = REPORTS_DIR / "day1_data_quality_summary.txt"
    out_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"\nData quality summary written to: {out_path}")


if __name__ == "__main__":
    main()

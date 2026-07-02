"""
recommender.py
==============
Bluestock Fintech - Mutual Fund Analytics Capstone
Day 6, Task 5: Simple fund recommender.

Usage:
    python scripts/recommender.py             -> interactive prompt
    python scripts/recommender.py Low         -> non-interactive
    python scripts/recommender.py Moderate
    python scripts/recommender.py High

Input  : investor risk appetite  ->  Low | Moderate | High
Output : top 3 funds by Sharpe ratio within the matching risk_grade(s)
         printed as a formatted table and returned as a DataFrame.
"""
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PERF_CSV = PROJECT_ROOT / "data" / "processed" / "07_scheme_performance_clean.csv"

# Risk appetite -> allowed SEBI risk_grade values
RISK_MAP = {
    "Low":      ["Low"],
    "Moderate": ["Moderate"],
    "High":     ["High", "Moderately High", "Very High"],
}


def recommend(risk_appetite: str, top_n: int = 3) -> pd.DataFrame:
    """
    Return a DataFrame of top_n funds matching the given risk_appetite,
    ranked by Sharpe ratio (descending).

    Parameters
    ----------
    risk_appetite : str
        One of 'Low', 'Moderate', 'High'  (case-sensitive).
    top_n : int
        Number of funds to return (default 3).

    Returns
    -------
    pd.DataFrame with columns:
        scheme_name, fund_house, risk_grade, sharpe_ratio,
        return_3yr_pct, expense_ratio_pct
    """
    if risk_appetite not in RISK_MAP:
        raise ValueError(
            f"Invalid risk_appetite '{risk_appetite}'. "
            f"Must be one of: {list(RISK_MAP)}"
        )

    valid_grades = RISK_MAP[risk_appetite]
    perf = pd.read_csv(PERF_CSV)
    subset = perf[perf["risk_grade"].isin(valid_grades)].copy()

    if subset.empty:
        raise ValueError(
            f"No funds found for risk_appetite='{risk_appetite}'. "
            f"Checked risk_grade in {valid_grades}."
        )

    top = (
        subset.sort_values("sharpe_ratio", ascending=False)
        .head(top_n)
        .reset_index(drop=True)[
            ["scheme_name", "fund_house", "risk_grade",
             "sharpe_ratio", "return_3yr_pct", "expense_ratio_pct"]
        ]
    )
    return top


def print_recommendations(risk_appetite: str, top_n: int = 3) -> None:
    """Print a formatted recommendation table to stdout."""
    rec = recommend(risk_appetite, top_n)

    divider = "=" * 78
    print(f"\n{divider}")
    print(f"  BLUESTOCK MF CAPSTONE — Fund Recommender")
    print(f"  Risk appetite: {risk_appetite}   |   Top {top_n} funds by Sharpe ratio")
    print(divider)
    header = f"  {'#':>2}  {'Scheme':<38}  {'Sharpe':>7}  {'3yr %':>7}  {'ER %':>6}  {'Risk Grade'}"
    print(header)
    print("-" * 78)
    for i, row in rec.iterrows():
        name = row["scheme_name"][:38]
        print(f"  {i+1:>2}  {name:<38}  {row['sharpe_ratio']:>7.2f}  "
              f"{row['return_3yr_pct']:>7.2f}  {row['expense_ratio_pct']:>6.2f}  {row['risk_grade']}")
    print(divider)
    print(f"  Note: Rf = 6.5% (RBI repo rate proxy). Higher Sharpe = better")
    print(f"  risk-adjusted return. This is for educational purposes only.")
    print(f"{divider}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        appetite = sys.argv[1]
    else:
        print("Enter risk appetite (Low / Moderate / High): ", end="")
        appetite = input().strip()

    print_recommendations(appetite)

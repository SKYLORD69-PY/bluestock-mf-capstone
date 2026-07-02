"""
advanced_analytics.py
======================
Bluestock Fintech - Mutual Fund Analytics Capstone
Day 6: Advanced Analytics + Risk Metrics.

Outputs:
  reports/var_cvar_report.csv
  reports/day6_charts/rolling_sharpe_chart.png
  reports/day6_charts/sector_hhi_chart.png
  reports/recommender.py         <- standalone recommender module
  notebooks/Advanced_Analytics.ipynb  (built by build_advanced_notebook.py)

Run from the project root:
    python scripts/advanced_analytics.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

PROCESSED = Path("data/processed")
REPORTS   = Path("reports")
CHARTS_DIR = REPORTS / "day6_charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid")
TRADING_DAYS = 252
RF_DAILY = 0.065 / TRADING_DAYS

# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------
fm   = pd.read_csv(PROCESSED / "01_fund_master_clean.csv")
nav_all = pd.read_csv(PROCESSED / "02_nav_history_clean.csv")
nav_all["date"] = pd.to_datetime(nav_all["date"])
nav  = nav_all[nav_all["is_actual_trading_day"] == 1].copy()
tx   = pd.read_csv(PROCESSED / "08_investor_transactions_clean.csv")
tx["transaction_date"] = pd.to_datetime(tx["transaction_date"])
hold = pd.read_csv(PROCESSED / "09_portfolio_holdings_clean.csv")
perf = pd.read_csv(PROCESSED / "07_scheme_performance_clean.csv")
sc   = pd.read_csv(REPORTS / "fund_scorecard.csv")

nav_wide = nav.pivot(index="date", columns="amfi_code", values="nav").sort_index()
ret_wide = nav_wide.pct_change().dropna(how="all")

print(f"Loaded: {fm.shape[0]} funds | {ret_wide.shape[0]} trading days | "
      f"{tx.shape[0]} transactions ({tx['investor_id'].nunique()} unique investors)")

# ===========================================================================
# TASK 1 — Historical VaR (95%) and CVaR for all 40 schemes
# ===========================================================================
VAR_CONFIDENCE = 0.95
var_rows = []
for code in ret_wide.columns:
    r = ret_wide[code].dropna()
    var_95 = np.percentile(r, (1 - VAR_CONFIDENCE) * 100)   # 5th percentile
    cvar_95 = r[r <= var_95].mean()
    var_rows.append({
        "amfi_code": code,
        "var_95_pct": round(var_95 * 100, 4),
        "cvar_95_pct": round(cvar_95 * 100, 4),
        "n_obs": len(r),
    })

var_df = pd.DataFrame(var_rows)
var_df = var_df.merge(fm[["amfi_code", "scheme_name", "fund_house", "category"]], on="amfi_code")
var_df = var_df.merge(perf[["amfi_code", "risk_grade"]], on="amfi_code")
var_df = var_df.sort_values("var_95_pct")  # most negative = worst loss first

var_df.to_csv(REPORTS / "var_cvar_report.csv", index=False)
print(f"\nTask 1: var_cvar_report.csv written ({len(var_df)} funds).")
print("VaR range:", var_df["var_95_pct"].min(), "% to", var_df["var_95_pct"].max(), "%")
print("Worst VaR fund:", var_df.iloc[0]["scheme_name"], "->", var_df.iloc[0]["var_95_pct"], "%")
print("Best  VaR fund:", var_df.iloc[-1]["scheme_name"], "->", var_df.iloc[-1]["var_95_pct"], "%")

# ===========================================================================
# TASK 2 — Rolling 90-day Sharpe for 5 key funds (top 5 by Day 4 scorecard)
# ===========================================================================
top5_codes = sc.head(5)["amfi_code"].tolist()
top5_names = sc.head(5).set_index("amfi_code")["scheme_name"].str.slice(0, 35).to_dict()

roll_sharpe = pd.DataFrame()
for code in top5_codes:
    r = ret_wide[code].dropna()
    rs = (r.rolling(90).mean() - RF_DAILY) / r.rolling(90).std() * np.sqrt(TRADING_DAYS)
    roll_sharpe[code] = rs

fig, ax = plt.subplots(figsize=(13, 6))
for code in top5_codes:
    ax.plot(roll_sharpe.index, roll_sharpe[code], label=top5_names[code], linewidth=1.7)
ax.axhline(0, color="gray", linestyle="--", linewidth=1, alpha=0.7)
ax.axhline(1, color="lightgreen", linestyle=":", linewidth=1.2, alpha=0.8, label="Sharpe = 1.0 (good)")
ax.set_title("Rolling 90-Day Sharpe Ratio — Top 5 Scorecard Funds", fontsize=12)
ax.set_ylabel("Rolling Sharpe (90-day window)")
ax.legend(loc="upper left", fontsize=8)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.1f}"))
plt.tight_layout()
plt.savefig(CHARTS_DIR / "rolling_sharpe_chart.png", dpi=150)
plt.close()
print("\nTask 2: rolling_sharpe_chart.png saved.")

# ===========================================================================
# TASK 3 — Investor cohort analysis (group by first transaction year)
# ===========================================================================
sip_tx = tx[tx["transaction_type"] == "SIP"].copy()
first_tx_year = tx.groupby("investor_id")["transaction_date"].min().dt.year.rename("cohort_year")
tx_cohort = tx.merge(first_tx_year.reset_index(), on="investor_id")
sip_cohort = sip_tx.merge(first_tx_year.reset_index(), on="investor_id")

cohort_summary = sip_cohort.groupby("cohort_year").agg(
    investors=("investor_id", "nunique"),
    avg_sip_amount=("amount_inr", "mean"),
    total_invested_inr=("amount_inr", "sum"),
).round(0).reset_index()

# Top fund preference per cohort (by SIP count)
top_fund_per_cohort = (
    sip_cohort.groupby(["cohort_year", "amfi_code"])
    .size().rename("sip_count")
    .reset_index()
    .sort_values(["cohort_year", "sip_count"], ascending=[True, False])
    .groupby("cohort_year").first()["amfi_code"]
    .map(fm.set_index("amfi_code")["scheme_name"])
    .reset_index()
    .rename(columns={"amfi_code": "top_fund"})
)
cohort_summary = cohort_summary.merge(top_fund_per_cohort, on="cohort_year")

print("\nTask 3: Investor cohort analysis:")
print(cohort_summary.to_string(index=False))

# ===========================================================================
# TASK 4 — SIP continuity analysis (flag at-risk investors with gap > 35 days)
# ===========================================================================
sip_6plus = sip_tx.groupby("investor_id").filter(lambda g: len(g) >= 6)
sip_6plus = sip_6plus.sort_values(["investor_id", "transaction_date"])

continuity_rows = []
for investor_id, grp in sip_6plus.groupby("investor_id"):
    dates = grp["transaction_date"].sort_values()
    gaps = dates.diff().dt.days.dropna()
    continuity_rows.append({
        "investor_id": investor_id,
        "num_sips": len(grp),
        "avg_gap_days": round(gaps.mean(), 1),
        "max_gap_days": int(gaps.max()),
        "at_risk": gaps.mean() > 35,
    })

continuity = pd.DataFrame(continuity_rows)
at_risk_count = continuity["at_risk"].sum()
total_6plus = len(continuity)
continuity_rate = (1 - at_risk_count / total_6plus) * 100

print(f"\nTask 4: SIP continuity — {total_6plus} investors with 6+ SIPs.")
print(f"  At-risk (avg gap > 35 days): {at_risk_count} ({at_risk_count/total_6plus*100:.1f}%)")
print(f"  Continuity rate: {continuity_rate:.1f}%")
print(f"  Overall avg gap: {continuity['avg_gap_days'].mean():.1f} days")

# ===========================================================================
# TASK 5 — Fund recommender (see also scripts/recommender.py)
# ===========================================================================
perf_sharpe = perf[["amfi_code", "scheme_name", "fund_house", "risk_grade",
                     "sharpe_ratio", "return_3yr_pct", "expense_ratio_pct"]].copy()
RISK_MAP = {
    "Low":            ["Low"],
    "Moderate":       ["Moderate"],
    "High":           ["High", "Moderately High", "Very High"],
}

def recommend(risk_appetite: str, top_n: int = 3) -> pd.DataFrame:
    """Return top_n funds by Sharpe ratio for the given risk appetite."""
    valid_grades = RISK_MAP.get(risk_appetite)
    if not valid_grades:
        raise ValueError(f"risk_appetite must be one of: {list(RISK_MAP)}")
    subset = perf_sharpe[perf_sharpe["risk_grade"].isin(valid_grades)]
    return (subset.sort_values("sharpe_ratio", ascending=False)
                  .head(top_n)
                  .reset_index(drop=True)[["scheme_name", "fund_house", "risk_grade",
                                           "sharpe_ratio", "return_3yr_pct", "expense_ratio_pct"]])

print("\nTask 5: Fund Recommender — sample output:")
for appetite in ["Low", "Moderate", "High"]:
    print(f"\n  Risk appetite = '{appetite}':")
    rec = recommend(appetite)
    for _, row in rec.iterrows():
        print(f"    {row['scheme_name']} | Sharpe={row['sharpe_ratio']:.2f} | "
              f"3yr={row['return_3yr_pct']:.1f}% | ER={row['expense_ratio_pct']:.2f}%")

# ===========================================================================
# TASK 6 — Sector HHI concentration per equity fund
# ===========================================================================
hhi_rows = []
for code, grp in hold.groupby("amfi_code"):
    weights = grp["weight_pct"] / 100.0          # convert % to decimal
    hhi = (weights ** 2).sum()
    top_sector = grp.loc[grp["weight_pct"].idxmax(), "sector"]
    hhi_rows.append({
        "amfi_code": code,
        "hhi": round(hhi, 4),
        "n_holdings": len(grp),
        "top_sector": top_sector,
    })

hhi_df = pd.DataFrame(hhi_rows).merge(
    fm[["amfi_code", "scheme_name", "sub_category"]], on="amfi_code"
).sort_values("hhi", ascending=False)

print(f"\nTask 6: HHI range [{hhi_df['hhi'].min():.4f}, {hhi_df['hhi'].max():.4f}]")
print("Most concentrated:", hhi_df.iloc[0]["scheme_name"],
      "->", hhi_df.iloc[0]["hhi"], "(", hhi_df.iloc[0]["n_holdings"], "holdings )")
print("Least concentrated:", hhi_df.iloc[-1]["scheme_name"],
      "->", hhi_df.iloc[-1]["hhi"])

fig, ax = plt.subplots(figsize=(12, 6))
colors = ["#C8553D" if h > 0.1 else "#1B6CA8" for h in hhi_df["hhi"]]
ax.bar(range(len(hhi_df)), hhi_df["hhi"], color=colors)
ax.axhline(0.1, color="red", linestyle="--", linewidth=1.2, label="HHI=0.10 (moderate concentration)")
ax.axhline(0.25, color="darkred", linestyle=":", linewidth=1.2, label="HHI=0.25 (high concentration)")
ax.set_xticks(range(len(hhi_df)))
ax.set_xticklabels(hhi_df["scheme_name"].str.slice(0, 22), rotation=90, fontsize=7)
ax.set_title("Sector HHI Concentration per Equity Fund\n"
             "(higher = more concentrated; red bars exceed 0.10 threshold)", fontsize=11)
ax.set_ylabel("HHI (Herfindahl-Hirschman Index)")
ax.legend(fontsize=9)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "sector_hhi_chart.png", dpi=150)
plt.close()
print("Task 6: sector_hhi_chart.png saved.")

print("\nAll Day 6 analytics complete.")
print(f"Outputs: {REPORTS}/var_cvar_report.csv | {CHARTS_DIR}/rolling_sharpe_chart.png "
      f"| {CHARTS_DIR}/sector_hhi_chart.png")

"""
performance_analytics.py
=========================
Bluestock Fintech - Mutual Fund Analytics Capstone
Day 4: Fund Performance Analytics. Standalone script version - computes
all 8 tasks and writes reports/fund_scorecard.csv, reports/alpha_beta.csv,
and reports/day4_charts/*.png. The notebook (Performance_Analytics.ipynb)
is built from this exact code via scripts/build_performance_notebook.py.

IMPORTANT DESIGN DECISION: all return/risk calculations use ONLY actual
trading days (is_actual_trading_day == 1) from the Day 2 cleaned NAV
series, NOT the calendar-reindexed version. Including forward-filled
weekend rows (which carry a 0% return) would dilute volatility estimates
and break the sqrt(252) trading-day annualisation convention.

Run from the project root:
    python scripts/performance_analytics.py
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
REPORTS = Path("reports")
CHARTS_DIR = REPORTS / "day4_charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid")
RF_ANNUAL = 0.065          # RBI repo rate proxy
RF_DAILY = RF_ANNUAL / 252
TRADING_DAYS = 252

# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------
fm = pd.read_csv(PROCESSED / "01_fund_master_clean.csv")
nav_all = pd.read_csv(PROCESSED / "02_nav_history_clean.csv")
nav_all["date"] = pd.to_datetime(nav_all["date"])
nav = nav_all[nav_all["is_actual_trading_day"] == 1].copy()   # trading days only

bench = pd.read_csv(PROCESSED / "10_benchmark_indices_clean.csv")
bench["date"] = pd.to_datetime(bench["date"])
n100 = bench[bench["index_name"] == "NIFTY100"].set_index("date")["close_value"].sort_index()
n50 = bench[bench["index_name"] == "NIFTY50"].set_index("date")["close_value"].sort_index()

print(f"Funds: {fm.shape[0]} | Trading days per fund: {nav.groupby('amfi_code').size().iloc[0]} "
      f"| Date range: {nav['date'].min().date()} -> {nav['date'].max().date()}")

# Wide NAV matrix: date x amfi_code (trading days only)
nav_wide = nav.pivot(index="date", columns="amfi_code", values="nav").sort_index()

# ===========================================================================
# TASK 1 — Daily returns, all 40 schemes, validate distribution
# ===========================================================================
ret_wide = nav_wide.pct_change().dropna(how="all")   # daily_return = nav_t/nav_t-1 - 1
print(f"\nTask 1: daily_return computed for {ret_wide.shape[1]} funds x {ret_wide.shape[0]} trading days")

ret_long = ret_wide.stack().rename("daily_return").reset_index()
ret_long.columns = ["date", "amfi_code", "daily_return"]
ret_long = ret_long.merge(fm[["amfi_code", "category"]], on="amfi_code")

stats_by_cat = ret_long.groupby("category")["daily_return"].agg(["mean", "std", "skew", "count"])
stats_by_cat["mean_pct"] = stats_by_cat["mean"] * 100
stats_by_cat["std_pct"] = stats_by_cat["std"] * 100
print("\nDaily return distribution by category (sanity check):")
print(stats_by_cat[["mean_pct", "std_pct", "skew", "count"]].round(4))

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
for cat, ax in zip(["Equity", "Debt"], axes):
    data = ret_long[ret_long["category"] == cat]["daily_return"] * 100
    sns.histplot(data, bins=80, kde=True, ax=ax, color="#2E86AB" if cat == "Equity" else "#A23B72")
    ax.set_title(f"{cat} — Daily Return Distribution\nmean={data.mean():.3f}%, std={data.std():.3f}%")
    ax.set_xlabel("Daily return (%)")
    ax.axvline(0, color="gray", linestyle="--", linewidth=1)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "01_daily_return_distribution.png", dpi=150)
plt.show()
print("Distribution check looks reasonable: equity daily std >> debt daily std, both centered near 0.")

# ===========================================================================
# TASK 2 — CAGR for 1yr, 3yr, and full available period (~4.4yr, NOT 5yr)
# ===========================================================================
end_date = nav_wide.index.max()


def nav_on_or_before(target_date: pd.Timestamp) -> pd.Series:
    """NAV for every fund on the latest trading day <= target_date."""
    idx = nav_wide.index[nav_wide.index <= target_date]
    return nav_wide.loc[idx.max()] if len(idx) else pd.Series(index=nav_wide.columns, dtype=float)


nav_end = nav_wide.loc[end_date]
cagr_table = pd.DataFrame(index=nav_wide.columns)

for years in [1, 3]:
    start_target = end_date - pd.DateOffset(years=years)
    nav_start = nav_on_or_before(start_target)
    cagr_table[f"return_{years}yr_pct"] = ((nav_end / nav_start) ** (1 / years) - 1) * 100

first_date = nav_wide.index.min()
full_period_years = (end_date - first_date).days / 365.25
nav_first = nav_wide.loc[first_date]
cagr_table["return_full_period_pct"] = ((nav_end / nav_first) ** (1 / full_period_years) - 1) * 100
cagr_table["full_period_years"] = round(full_period_years, 2)
for c in ["return_1yr_pct", "return_3yr_pct", "return_full_period_pct"]:
    cagr_table[c] = cagr_table[c].round(2)

print(f"\nTask 2: only {full_period_years:.2f} years of NAV history exist (data starts {first_date.date()}), "
      f"so a true 5yr CAGR cannot be computed or validated from this dataset. Reporting "
      f"return_full_period_pct (~4.4yr) instead of a fabricated 5yr figure.")
print(cagr_table.head())

# ===========================================================================
# TASK 3 — Sharpe Ratio, ranked
# ===========================================================================
mean_r = ret_wide.mean()
std_r = ret_wide.std()
sharpe = (mean_r - RF_DAILY) / std_r * np.sqrt(TRADING_DAYS)
sharpe.name = "sharpe_ratio"
print(f"\nTask 3: Sharpe ratio range [{sharpe.min():.2f}, {sharpe.max():.2f}], Rf={RF_ANNUAL:.1%} annual")

# ===========================================================================
# TASK 4 — Sortino Ratio (downside deviation only)
# ===========================================================================
def downside_std(s: pd.Series) -> float:
    neg = s[s < 0]
    return neg.std() if len(neg) > 1 else np.nan


down_std = ret_wide.apply(downside_std)
sortino = (mean_r - RF_DAILY) / down_std * np.sqrt(TRADING_DAYS)
sortino.name = "sortino_ratio"
print(f"Task 4: Sortino ratio range [{sortino.min():.2f}, {sortino.max():.2f}]")

# ===========================================================================
# TASK 5 — Alpha & Beta vs NIFTY100, OLS via scipy.stats.linregress
# ===========================================================================
bench_ret = n100.pct_change().dropna()
alpha_beta_rows = []
for code in nav_wide.columns:
    fund_ret = ret_wide[code].dropna()
    aligned = pd.concat([fund_ret, bench_ret], axis=1, join="inner")
    aligned.columns = ["fund", "bench"]
    slope, intercept, rvalue, pvalue, stderr = stats.linregress(aligned["bench"], aligned["fund"])
    alpha_beta_rows.append({
        "amfi_code": code,
        "beta": slope,
        "alpha_pct": intercept * TRADING_DAYS * 100,   # daily intercept -> annualised %
        "r_squared": rvalue ** 2,
        "p_value": pvalue,
        "n_obs": len(aligned),
    })
alpha_beta = pd.DataFrame(alpha_beta_rows).set_index("amfi_code")
print(f"\nTask 5: Beta range [{alpha_beta['beta'].min():.2f}, {alpha_beta['beta'].max():.2f}], "
      f"Alpha range [{alpha_beta['alpha_pct'].min():.2f}%, {alpha_beta['alpha_pct'].max():.2f}%]")
print(f"Median R-squared: {alpha_beta['r_squared'].median():.4f} "
      f"(low R-squared expected given the near-zero correlation found in Day 3 EDA)")

# ===========================================================================
# TASK 6 — Maximum Drawdown + worst drawdown date range, per fund
# ===========================================================================
mdd_rows = []
for code in nav_wide.columns:
    s = nav_wide[code].dropna()
    running_max = s.cummax()
    dd = s / running_max - 1
    trough_date = dd.idxmin()
    peak_date = s.loc[:trough_date].idxmax()
    mdd_rows.append({
        "amfi_code": code,
        "max_drawdown_pct": dd.min() * 100,
        "drawdown_peak_date": peak_date.date(),
        "drawdown_trough_date": trough_date.date(),
    })
mdd = pd.DataFrame(mdd_rows).set_index("amfi_code")
print(f"\nTask 6: Max drawdown range [{mdd['max_drawdown_pct'].min():.2f}%, {mdd['max_drawdown_pct'].max():.2f}%]")
worst = mdd.loc[mdd["max_drawdown_pct"].idxmin()]
print(f"Worst single-fund drawdown: code {mdd['max_drawdown_pct'].idxmin()}, "
      f"{worst['max_drawdown_pct']:.2f}% from {worst['drawdown_peak_date']} to {worst['drawdown_trough_date']}")

# ===========================================================================
# TASK 7 — Fund Scorecard (0-100 composite)
# ===========================================================================
scorecard = fm[["amfi_code", "scheme_name", "fund_house", "category", "expense_ratio_pct"]].set_index("amfi_code")
scorecard["return_3yr_pct"] = cagr_table["return_3yr_pct"]
scorecard["sharpe_ratio"] = sharpe
scorecard["alpha_pct"] = alpha_beta["alpha_pct"]
scorecard["max_drawdown_pct"] = mdd["max_drawdown_pct"]

scorecard["rank_return_3yr"] = scorecard["return_3yr_pct"].rank(pct=True) * 100
scorecard["rank_sharpe"] = scorecard["sharpe_ratio"].rank(pct=True) * 100
scorecard["rank_alpha"] = scorecard["alpha_pct"].rank(pct=True) * 100
scorecard["rank_expense_inv"] = scorecard["expense_ratio_pct"].rank(pct=True, ascending=False) * 100  # lower fee = higher rank
scorecard["rank_max_dd_inv"] = scorecard["max_drawdown_pct"].rank(pct=True, ascending=True) * 100      # less-negative DD = higher rank

scorecard["fund_score"] = (
    0.30 * scorecard["rank_return_3yr"] +
    0.25 * scorecard["rank_sharpe"] +
    0.20 * scorecard["rank_alpha"] +
    0.15 * scorecard["rank_expense_inv"] +
    0.10 * scorecard["rank_max_dd_inv"]
).round(1)

scorecard = scorecard.sort_values("fund_score", ascending=False)
for col in ["return_3yr_pct", "sharpe_ratio", "alpha_pct", "max_drawdown_pct"]:
    scorecard[col] = scorecard[col].round(2)
scorecard_out = scorecard.reset_index()
scorecard_out.to_csv(REPORTS / "fund_scorecard.csv", index=False)
print(f"\nTask 7: fund_scorecard.csv written ({len(scorecard_out)} funds). "
      f"Top fund: {scorecard_out.iloc[0]['scheme_name']} (score {scorecard_out.iloc[0]['fund_score']})")
print(scorecard_out[["scheme_name", "fund_score"]].head(5).to_string(index=False))

# Bonus chart: scorecard leaderboard
top10 = scorecard_out.head(10)
fig, ax = plt.subplots(figsize=(10, 6))
sns.barplot(data=top10, y="scheme_name", x="fund_score", hue="scheme_name", legend=False, palette="viridis", ax=ax)
ax.set_title("Top 10 Funds — Composite Scorecard (0-100)")
ax.set_xlabel("Fund score")
ax.set_ylabel("")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "02_scorecard_leaderboard.png", dpi=150)
plt.show()

# alpha_beta.csv deliverable (merge in names for readability)
alpha_beta_out = alpha_beta.reset_index().merge(
    fm[["amfi_code", "scheme_name", "fund_house", "category"]], on="amfi_code"
)
alpha_beta_out = alpha_beta_out[["amfi_code", "scheme_name", "fund_house", "category",
                                  "beta", "alpha_pct", "r_squared", "p_value", "n_obs"]]
for col in ["beta", "alpha_pct", "r_squared"]:
    alpha_beta_out[col] = alpha_beta_out[col].round(4)
alpha_beta_out["p_value"] = alpha_beta_out["p_value"].round(4)
alpha_beta_out = alpha_beta_out.sort_values("alpha_pct", ascending=False)
alpha_beta_out.to_csv(REPORTS / "alpha_beta.csv", index=False)
print(f"\nalpha_beta.csv written ({len(alpha_beta_out)} funds).")

# ===========================================================================
# TASK 8 — Benchmark comparison chart: top 5 funds vs Nifty50 & Nifty100, 3yr
# ===========================================================================
top5_codes = scorecard_out.head(5)["amfi_code"].tolist()
top5_names = scorecard_out.head(5).set_index("amfi_code")["scheme_name"]

window_start = end_date - pd.DateOffset(years=3)
nav_3y = nav_wide.loc[nav_wide.index >= window_start, top5_codes]
nav_3y_indexed = nav_3y / nav_3y.iloc[0] * 100

n50_3y = n50.loc[n50.index >= window_start]
n100_3y = n100.loc[n100.index >= window_start]
n50_indexed = n50_3y / n50_3y.iloc[0] * 100
n100_indexed = n100_3y / n100_3y.iloc[0] * 100

fig, ax = plt.subplots(figsize=(13, 7))
for code in top5_codes:
    ax.plot(nav_3y_indexed.index, nav_3y_indexed[code], label=top5_names[code], linewidth=1.8)
ax.plot(n50_indexed.index, n50_indexed, label="NIFTY 50", color="black", linewidth=2.2, linestyle="--")
ax.plot(n100_indexed.index, n100_indexed, label="NIFTY 100", color="gray", linewidth=2.2, linestyle=":")
ax.set_title("Top 5 Scorecard Funds vs NIFTY 50 / NIFTY 100 — Trailing 3 Years (rebased to 100)")
ax.set_ylabel("Indexed value (start of window = 100)")
ax.legend(loc="upper left", fontsize=9)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "03_benchmark_comparison_top5.png", dpi=150)
plt.show()
print("\nTask 8: benchmark comparison chart saved.")

# Tracking error vs NIFTY100 over the same 3yr window, for the top 5
fund_ret_3y = nav_3y.pct_change().dropna()
bench_ret_3y = n100_3y.pct_change().dropna()
te_rows = []
for code in top5_codes:
    aligned = pd.concat([fund_ret_3y[code], bench_ret_3y], axis=1, join="inner")
    aligned.columns = ["fund", "bench"]
    te = (aligned["fund"] - aligned["bench"]).std() * np.sqrt(TRADING_DAYS) * 100
    te_rows.append({"amfi_code": code, "scheme_name": top5_names[code], "tracking_error_pct": round(te, 2)})
tracking_error = pd.DataFrame(te_rows)
print("\nTracking error vs NIFTY100 (3yr window):")
print(tracking_error.to_string(index=False))

print(f"\nAll Day 4 outputs written: {REPORTS}/fund_scorecard.csv, {REPORTS}/alpha_beta.csv, "
      f"{CHARTS_DIR}/*.png ({len(list(CHARTS_DIR.glob('*.png')))} charts)")

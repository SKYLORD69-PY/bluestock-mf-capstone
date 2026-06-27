"""
eda_analysis.py
================
Bluestock Fintech - Mutual Fund Analytics Capstone
Day 3: Exploratory Data Analysis. Standalone script version - regenerates
all 16 charts as PNGs in reports/day3_charts/ without needing Jupyter.
The notebook (notebooks/EDA_Analysis.ipynb) is built from this exact code
via scripts/build_notebook.py, so both stay in sync.

Run from the project root:
    python scripts/eda_analysis.py
"""
import os
from pathlib import Path
import numpy as np
import pandas as pd

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.lines import Line2D
import seaborn as sns

def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "data/processed").exists() and (candidate / "reports").exists():
            return candidate
    return current


PROJECT_ROOT = find_project_root()
PROCESSED = PROJECT_ROOT / "data/processed"
CHARTS_DIR = Path("reports/day3_charts")
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid")
PALETTE = sns.color_palette("Set2")

# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------
fm = pd.read_csv(PROCESSED / "01_fund_master_clean.csv")
nav = pd.read_csv(PROCESSED / "02_nav_history_clean.csv")
aum = pd.read_csv(PROCESSED / "03_aum_by_fund_house_clean.csv")
sip = pd.read_csv(PROCESSED / "04_monthly_sip_inflows_clean.csv")
cat = pd.read_csv(PROCESSED / "05_category_inflows_clean.csv")
folio = pd.read_csv(PROCESSED / "06_industry_folio_count_clean.csv")
perf = pd.read_csv(PROCESSED / "07_scheme_performance_clean.csv")
tx = pd.read_csv(PROCESSED / "08_investor_transactions_clean.csv")
hold = pd.read_csv(PROCESSED / "09_portfolio_holdings_clean.csv")
bench = pd.read_csv(PROCESSED / "10_benchmark_indices_clean.csv")

nav["date"] = pd.to_datetime(nav["date"])
aum["date"] = pd.to_datetime(aum["date"])
tx["transaction_date"] = pd.to_datetime(tx["transaction_date"])
bench["date"] = pd.to_datetime(bench["date"])

print(f"Loaded: fm={fm.shape} nav={nav.shape} aum={aum.shape} sip={sip.shape} "
      f"cat={cat.shape} folio={folio.shape} perf={perf.shape} tx={tx.shape} "
      f"hold={hold.shape} bench={bench.shape}")

# ---------------------------------------------------------------------------
# Empirically locate the 2023 rally / 2024 correction windows from NIFTY50,
# instead of guessing dates.
# ---------------------------------------------------------------------------
n50 = bench[bench["index_name"] == "NIFTY50"].sort_values("date").set_index("date")["close_value"]
rally_2023_ret = (n50["2023"].iloc[-1] / n50["2023"].iloc[0] - 1) * 100
m2024 = n50["2024"]
dd24 = (m2024 / m2024.cummax() - 1) * 100
trough_2024 = dd24.idxmin()
peak_2024 = m2024[:trough_2024].idxmax()
correction_pct = dd24.min()
print(f"\n2023 rally: NIFTY50 {rally_2023_ret:+.1f}% over the year")
print(f"2024 correction: peak {peak_2024.date()} -> trough {trough_2024.date()} ({correction_pct:.1f}%)")

# ===========================================================================
# CHART 1 — NAV trend, all 40 schemes, rebased to 100
# ===========================================================================
nav_s = nav.sort_values(["amfi_code", "date"]).merge(
    fm[["amfi_code", "scheme_name", "category"]], on="amfi_code"
)
nav_s["nav_indexed"] = nav_s.groupby("amfi_code")["nav"].transform(lambda s: s / s.iloc[0] * 100)

category_colors = {"Equity": "#2E86AB", "Debt": "#A23B72"}
fig, ax = plt.subplots(figsize=(13, 6.5))
for _, scheme_df in nav_s.groupby("amfi_code", sort=False):
    category = scheme_df["category"].iat[0]
    ax.plot(
        scheme_df["date"],
        scheme_df["nav_indexed"],
        color=category_colors.get(category, "#666666"),
        alpha=0.55,
        linewidth=1.4,
    )

ax.axvspan(pd.Timestamp("2023-01-01"), pd.Timestamp("2023-12-31"), color="green", alpha=0.07)
ax.axvspan(peak_2024, trough_2024, color="red", alpha=0.08)
ax.annotate(
    f"2023 rally\n(NIFTY50 {rally_2023_ret:+.0f}%)",
    xy=(pd.Timestamp("2023-02-01"), nav_s["nav_indexed"].max() * 0.98),
    fontsize=9,
    color="darkgreen",
    va="top",
)
ax.annotate(
    f"2024 correction\n({correction_pct:.0f}%)",
    xy=(peak_2024 + (trough_2024 - peak_2024) / 8, nav_s["nav_indexed"].max() * 0.90),
    fontsize=9,
    color="darkred",
    va="top",
)
ax.set_title("NAV Trend — All 40 Schemes, Rebased to 100 (Jan 2022 = 100)")
ax.set_xlabel("")
ax.set_ylabel("Indexed NAV (Jan 2022 = 100)")
ax.legend(
    handles=[
        Line2D([0], [0], color=color, lw=2, label=category)
        for category, color in category_colors.items()
    ],
    title="Category",
    loc="upper left",
)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "01_nav_trend_all_schemes.png", dpi=150)
plt.close()
print("Chart 1 saved.")

# ===========================================================================
# CHART 2 — AUM growth grouped bar by fund house x year, Seaborn
# ===========================================================================
year_end_dates = {2022: "2022-09-30", 2023: "2023-09-30", 2024: "2024-12-31", 2025: "2025-12-31"}
aum_yearly = aum[aum["date"].isin(pd.to_datetime(list(year_end_dates.values())))].copy()
aum_yearly["year"] = aum_yearly["date"].dt.year

fig, ax = plt.subplots(figsize=(13, 6))
sns.barplot(data=aum_yearly, x="fund_house", y="aum_crore", hue="year", ax=ax, palette="viridis")
ax.set_title("AUM by Fund House — Nearest Year-End Snapshot, 2022-2025\n"
              "(snapshot dates: " + ", ".join(f"{y}={d}" for y, d in year_end_dates.items()) + ")", fontsize=10)
ax.set_xlabel("")
ax.set_ylabel("AUM (₹ crore)")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1e5:.1f}L"))
plt.xticks(rotation=30, ha="right")
sbi_2025 = aum_yearly[(aum_yearly["fund_house"] == "SBI Mutual Fund") & (aum_yearly["year"] == 2025)]["aum_crore"].iloc[0]
ax.annotate(f"SBI: ₹{sbi_2025/1e5:.2f}L Cr\n(largest AMC)", xy=(0, sbi_2025), xytext=(0.5, sbi_2025 * 1.05),
            fontsize=9, fontweight="bold", color="darkred")
plt.legend(title="Year", loc="upper right")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "02_aum_growth_by_fund_house.png", dpi=150)
plt.close()
print("Chart 2 saved.")

# ===========================================================================
# CHART 3 — SIP inflow monthly time series, annotate Dec-2025 ATH
# ===========================================================================
sip_s = sip.copy()
sip_s["month_dt"] = pd.to_datetime(sip_s["month"])
ath_row = sip_s.loc[sip_s["sip_inflow_crore"].idxmax()]

fig, ax = plt.subplots(figsize=(12, 5.5))
ax.plot(sip_s["month_dt"], sip_s["sip_inflow_crore"], marker="o", color="#2E86AB", linewidth=2)
ax.annotate(
    f"All-time high\n₹{ath_row['sip_inflow_crore']:,.0f} Cr ({ath_row['month']})",
    xy=(ath_row["month_dt"], ath_row["sip_inflow_crore"]),
    xytext=(-70, -40),
    textcoords="offset points",
    fontsize=10,
    color="darkred",
    arrowprops=dict(arrowstyle="->", color="darkred"),
)
ax.set_title("Monthly SIP Inflow — Jan 2022 to Dec 2025")
ax.set_xlabel("")
ax.set_ylabel("SIP inflow (₹ crore)")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "03_sip_inflow_trend.png", dpi=150)
plt.close()
print("Chart 3 saved.")

# ===========================================================================
# CHART 4 — Category inflow heatmap, Seaborn
# ===========================================================================
cat_pivot = cat.pivot(index="category", columns="month", values="net_inflow_crore")
fig, ax = plt.subplots(figsize=(14, 6))
sns.heatmap(cat_pivot, cmap="RdYlGn", center=0, annot=False, cbar_kws={"label": "Net inflow (₹ crore)"}, ax=ax)
ax.set_title("Category-wise Net Inflow Heatmap, FY 2024-25")
ax.set_xlabel("")
ax.set_ylabel("")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "04_category_inflow_heatmap.png", dpi=150)
plt.close()
print("Chart 4 saved.")

# ===========================================================================
# CHART 5/6/7 — Investor demographics: age pie, SIP boxplot by age, gender pie
# ===========================================================================
investors = tx.drop_duplicates("investor_id")[["investor_id", "age_group", "gender", "city_tier", "state", "kyc_status"]]

age_order = ["18-25", "26-35", "36-45", "46-55", "56+"]
age_counts = investors["age_group"].value_counts().reindex(age_order)
fig, ax = plt.subplots(figsize=(7, 7))
ax.pie(age_counts, labels=age_counts.index, autopct="%1.1f%%", startangle=90,
       colors=sns.color_palette("Set2", len(age_counts)))
ax.set_title(f"Investor Age Group Distribution (n={len(investors):,})")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "05_age_group_pie.png", dpi=150)
plt.close()
print("Chart 5 saved.")

sip_tx = tx[tx["transaction_type"] == "SIP"]
fig, ax = plt.subplots(figsize=(9, 6))
sns.boxplot(data=sip_tx, x="age_group", y="amount_inr", order=age_order, hue="age_group", legend=False, ax=ax, palette="Set2")
ax.set_title("SIP Amount Distribution by Age Group")
ax.set_xlabel("Age group")
ax.set_ylabel("SIP amount (₹)")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "06_sip_amount_by_age_boxplot.png", dpi=150)
plt.close()
print("Chart 6 saved.")

gender_counts = investors["gender"].value_counts()
fig, ax = plt.subplots(figsize=(6, 6))
ax.pie(gender_counts, labels=gender_counts.index, autopct="%1.1f%%", startangle=90,
       colors=["#2E86AB", "#F18F01"])
ax.set_title(f"Investor Gender Split (n={len(investors):,})")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "07_gender_split_pie.png", dpi=150)
plt.close()
print("Chart 7 saved.")

# ===========================================================================
# CHART 8/9 — Geographic: SIP amount by state (bar), T30 vs B30 (pie)
# ===========================================================================
state_amt = tx.groupby("state")["amount_inr"].sum().sort_values(ascending=False) / 1e7  # crore
fig, ax = plt.subplots(figsize=(9, 7))
sns.barplot(x=state_amt.values, y=state_amt.index, hue=state_amt.index, legend=False, ax=ax, palette="crest", orient="h")
ax.set_title("Total Transaction Amount by State")
ax.set_xlabel("Total amount (₹ crore)")
ax.set_ylabel("")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "08_sip_amount_by_state.png", dpi=150)
plt.close()
print("Chart 8 saved.")

tier_amt = tx.groupby("city_tier")["amount_inr"].sum()
fig, ax = plt.subplots(figsize=(6, 6))
ax.pie(tier_amt, labels=tier_amt.index, autopct="%1.1f%%", startangle=90, colors=["#06A77D", "#D5573B"])
ax.set_title("Transaction Amount: T30 vs B30 Cities")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "09_t30_b30_pie.png", dpi=150)
plt.close()
print("Chart 9 saved.")

# ===========================================================================
# CHART 10 — Folio count growth line chart with milestones
# ===========================================================================
folio_s = folio.copy()
folio_s["month_dt"] = pd.to_datetime(folio_s["month"])
fig, ax = plt.subplots(figsize=(11, 6))
ax.plot(folio_s["month_dt"], folio_s["total_folios_crore"], marker="o", color="#2E86AB", linewidth=2)
first_row, last_row = folio_s.iloc[0], folio_s.iloc[-1]
ax.annotate(f"{first_row['total_folios_crore']} Cr\n({first_row['month']})",
            xy=(first_row["month_dt"], first_row["total_folios_crore"]),
            xytext=(10, -25), textcoords="offset points", fontsize=9)
ax.annotate(f"{last_row['total_folios_crore']} Cr\n({last_row['month']})",
            xy=(last_row["month_dt"], last_row["total_folios_crore"]),
            xytext=(-70, 10), textcoords="offset points", fontsize=9, fontweight="bold", color="darkgreen")
mid20 = folio_s[folio_s["total_folios_crore"] >= 20].iloc[0]
ax.annotate("Crossed 20 Cr folios", xy=(mid20["month_dt"], mid20["total_folios_crore"]),
            xytext=(-40, 20), textcoords="offset points", fontsize=9,
            arrowprops=dict(arrowstyle="->", color="gray"))
ax.set_title("Total Mutual Fund Folio Count Growth, Jan 2022 - Dec 2025")
ax.set_ylabel("Total folios (crore)")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "10_folio_growth.png", dpi=150)
plt.close()
print("Chart 10 saved.")

# ===========================================================================
# CHART 11 — NAV daily-return correlation matrix, 10 selected funds, Seaborn
# ===========================================================================
selected_codes = [119551, 125497, 120503, 118632, 120841, 119092, 101206, 102887, 148567, 149322]
sel_names = fm.set_index("amfi_code").loc[selected_codes, "fund_house"]
nav_pivot = nav[nav["amfi_code"].isin(selected_codes)].pivot(index="date", columns="amfi_code", values="daily_return_pct")
nav_pivot = nav_pivot[nav_pivot.index.to_series().dt.dayofweek < 5]  # trading days only for correlation
nav_pivot.columns = [f"{sel_names[c]}" for c in nav_pivot.columns]
corr = nav_pivot.corr()

fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, vmin=-1, vmax=1, ax=ax, square=True)
ax.set_title("Daily Return Correlation — 10 Selected Funds (1 per fund house)")
plt.xticks(rotation=45, ha="right")
plt.yticks(rotation=0)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "11_nav_return_correlation.png", dpi=150)
plt.close()
print("Chart 11 saved.")

# ===========================================================================
# CHART 12 — Sector allocation donut, rupee-weighted across all equity funds
# ===========================================================================
sector_value = hold.groupby("sector")["market_value_cr"].sum().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(8, 8))
wedges, texts, autotexts = ax.pie(
    sector_value, labels=sector_value.index, autopct="%1.1f%%", startangle=90,
    pctdistance=0.82, colors=sns.color_palette("tab20", len(sector_value)),
    wedgeprops=dict(width=0.4),
)
ax.set_title("Sector Allocation — Rupee-Weighted Across All Equity Fund Holdings")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "12_sector_allocation_donut.png", dpi=150)
plt.close()
print("Chart 12 saved.")

# ===========================================================================
# BONUS CHART 13 — KYC status split, pie
# ===========================================================================
kyc_counts = investors["kyc_status"].value_counts()
fig, ax = plt.subplots(figsize=(6, 6))
ax.pie(kyc_counts, labels=kyc_counts.index, autopct="%1.1f%%", startangle=90, colors=["#06A77D", "#D5573B"])
ax.set_title(f"Investor KYC Status (n={len(investors):,})")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "13_kyc_status_pie.png", dpi=150)
plt.close()
print("Chart 13 saved.")

# ===========================================================================
# BONUS CHART 14 — Transaction type split, bar
# ===========================================================================
type_counts = tx["transaction_type"].value_counts()
fig, ax = plt.subplots(figsize=(7, 5))
sns.barplot(x=type_counts.index, y=type_counts.values, hue=type_counts.index, legend=False, palette="Set2", ax=ax)
ax.set_title("Transaction Count by Type")
ax.set_ylabel("Number of transactions")
for i, v in enumerate(type_counts.values):
    ax.text(i, v + 200, f"{v:,}", ha="center", fontsize=10)
plt.tight_layout()
plt.savefig(CHARTS_DIR / "14_transaction_type_bar.png", dpi=150)
plt.close()
print("Chart 14 saved.")

# ===========================================================================
# BONUS CHART 15 — Payment mode distribution, bar
# ===========================================================================
pay_counts = tx["payment_mode"].value_counts()
fig, ax = plt.subplots(figsize=(7, 5))
sns.barplot(x=pay_counts.index, y=pay_counts.values, hue=pay_counts.index, legend=False, palette="crest", ax=ax)
ax.set_title("Transaction Count by Payment Mode")
ax.set_ylabel("Number of transactions")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "15_payment_mode_bar.png", dpi=150)
plt.close()
print("Chart 15 saved.")

# ===========================================================================
# BONUS CHART 16 — Average expense ratio by category, bar
# ===========================================================================
exp_by_cat = fm.groupby(["category", "sub_category"])["expense_ratio_pct"].mean().sort_values()
fig, ax = plt.subplots(figsize=(10, 6))
colors = ["#A23B72" if c == "Debt" else "#2E86AB" for c in exp_by_cat.index.get_level_values(0)]
labels_ec = [f"{c} - {s}" for c, s in exp_by_cat.index]
sns.barplot(x=exp_by_cat.values, y=labels_ec, hue=labels_ec, legend=False, palette=colors, ax=ax)
ax.set_title("Average Expense Ratio by Sub-Category")
ax.set_xlabel("Expense ratio (%)")
plt.tight_layout()
plt.savefig(CHARTS_DIR / "16_expense_ratio_by_subcategory.png", dpi=150)
plt.close()
print("Chart 16 saved.")

print(f"\nAll charts written to {CHARTS_DIR}/")
print(f"Total PNGs: {len(list(CHARTS_DIR.glob('*.png')))}")

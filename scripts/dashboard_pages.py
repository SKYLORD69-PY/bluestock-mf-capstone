"""
dashboard_pages.py
===================
Bluestock Fintech - Mutual Fund Analytics Capstone
Day 5: Dashboard Development. Since Power BI Desktop / a .pbix file cannot
be produced programmatically (proprietary binary format, no API, no GUI
environment available here), this script builds the 4 dashboard pages as
real, data-accurate composite PNGs - genuine charts from genuine numbers,
laid out to mirror what each Power BI page would show. These are combined
into Dashboard.pdf. See dashboard/POWER_BI_BUILD_GUIDE.md for exact
step-by-step instructions to build the real .pbix from this same data.

Run from the project root:
    python scripts/dashboard_pages.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.ticker as mticker
import seaborn as sns
from scipy import stats

PROCESSED = Path("data/processed")
REPORTS = Path("reports")
OUT_DIR = Path("dashboard")
OUT_DIR.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid")

# Bluestock-style palette (professional fintech blue/navy; no official brand
# assets were provided for this project, so this is a reasonable default —
# swap for the real Bluestock brand colors in Power BI if you have them)
NAVY = "#0B2545"
BLUE = "#1B6CA8"
TEAL = "#13A89E"
GOLD = "#B8791C"
RED = "#C8553D"
GRAY = "#6B7280"
BG = "#F4F6F8"

SHORT_NAME = {
    "SBI Mutual Fund": "SBI MF",
    "ICICI Prudential MF": "ICICI Pru MF",
    "HDFC Mutual Fund": "HDFC MF",
    "Nippon India MF": "Nippon India MF",
    "Kotak Mahindra MF": "Kotak MF",
    "Aditya Birla Sun Life MF": "ABSL MF",
    "UTI Mutual Fund": "UTI MF",
    "Axis Mutual Fund": "Axis MF",
    "Mirae Asset MF": "Mirae Asset MF",
    "DSP Mutual Fund": "DSP MF",
}

plt.rcParams.update({
    "font.size": 10,
    "axes.edgecolor": "#D0D5DD",
    "figure.facecolor": "white",
})

# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------
fm = pd.read_csv(PROCESSED / "01_fund_master_clean.csv")
nav_all = pd.read_csv(PROCESSED / "02_nav_history_clean.csv")
nav_all["date"] = pd.to_datetime(nav_all["date"])
nav = nav_all[nav_all["is_actual_trading_day"] == 1].copy()
aum = pd.read_csv(PROCESSED / "03_aum_by_fund_house_clean.csv")
aum["date"] = pd.to_datetime(aum["date"])
sip = pd.read_csv(PROCESSED / "04_monthly_sip_inflows_clean.csv")
cat = pd.read_csv(PROCESSED / "05_category_inflows_clean.csv")
folio = pd.read_csv(PROCESSED / "06_industry_folio_count_clean.csv")
perf07 = pd.read_csv(PROCESSED / "07_scheme_performance_clean.csv")
tx = pd.read_csv(PROCESSED / "08_investor_transactions_clean.csv")
tx["transaction_date"] = pd.to_datetime(tx["transaction_date"])
bench = pd.read_csv(PROCESSED / "10_benchmark_indices_clean.csv")
bench["date"] = pd.to_datetime(bench["date"])
scorecard = pd.read_csv(REPORTS / "fund_scorecard.csv")

nav_wide = nav.pivot(index="date", columns="amfi_code", values="nav").sort_index()
ret_wide = nav_wide.pct_change().dropna(how="all")


def kpi_card(ax, label, value, sublabel="", color=NAVY):
    ax.set_facecolor(color)
    ax.text(0.5, 0.62, value, ha="center", va="center", fontsize=22, fontweight="bold", color="white")
    ax.text(0.5, 0.30, label, ha="center", va="center", fontsize=11, color="#D7E3F4")
    if sublabel:
        ax.text(0.5, 0.10, sublabel, ha="center", va="center", fontsize=8, color="#9FB6D4")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def page_header(fig, title, page_no):
    fig.text(0.02, 0.975, "BLUESTOCK", fontsize=13, fontweight="bold", color=NAVY, family="sans-serif")
    fig.text(0.02, 0.955, "Mutual Fund Analytics", fontsize=8, color=GRAY)
    fig.text(0.5, 0.975, title, fontsize=15, fontweight="bold", color=NAVY, ha="center")
    fig.text(0.98, 0.965, f"Page {page_no} / 4", fontsize=9, color=GRAY, ha="right")
    fig.add_artist(plt.Line2D([0.02, 0.98], [0.945, 0.945], color="#D0D5DD", linewidth=1, transform=fig.transFigure))


print(f"Loaded {fm.shape[0]} funds, {nav_wide.shape[0]} trading days, scorecard top fund: "
      f"{scorecard.iloc[0]['scheme_name']}")

# ===========================================================================
# PAGE 1 — Industry Overview
# ===========================================================================
fig = plt.figure(figsize=(15, 9.5))
page_header(fig, "Page 1 — Industry Overview", 1)
gs = gridspec.GridSpec(3, 4, figure=fig, top=0.91, bottom=0.06, left=0.04, right=0.97,
                        hspace=0.55, wspace=0.35, height_ratios=[0.55, 1, 1])

sip_latest = sip.iloc[-1]
folio_latest = folio.iloc[-1]
kpi_specs = [
    ("Total Industry AUM", "Rs 81L Cr", "Dec 2025, AMFI\n(full industry)", NAVY),
    ("Monthly SIP Inflow", f"Rs {sip_latest['sip_inflow_crore']:,.0f} Cr", f"{sip_latest['month']} (ATH)", BLUE),
    ("Total Folios", f"{folio_latest['total_folios_crore']:.2f} Cr", f"{folio_latest['month']}", TEAL),
    ("Total Schemes", "1,908", "Dec 2025, AMFI\n(full industry)", GOLD),
]
for i, (label, value, sub, color) in enumerate(kpi_specs):
    ax = fig.add_subplot(gs[0, i])
    kpi_card(ax, label, value, sub, color)

# Line: Top-10-AMC pool AUM trend (our dataset's own AMCs, not full industry)
ax1 = fig.add_subplot(gs[1, 0])
amc_trend = aum.groupby("date")["aum_crore"].sum().sort_index()
ax1.plot(amc_trend.index, amc_trend.values / 1e5, marker="o", color=BLUE, linewidth=2)
ax1.set_title("AUM Trend — Sum of the 10 Fund\nHouses in This Dataset, 2022-2025", fontsize=9.5)
ax1.set_ylabel("AUM (Rs lakh crore)")
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.1f}L"))
plt.setp(ax1.get_xticklabels(), rotation=30, ha="right")

# Bar: AUM by AMC, latest snapshot
ax2 = fig.add_subplot(gs[1, 1:])
latest_date = aum["date"].max()
amc_latest = aum[aum["date"] == latest_date].sort_values("aum_crore", ascending=False).copy()
amc_latest["fund_house_short"] = amc_latest["fund_house"].map(SHORT_NAME).fillna(amc_latest["fund_house"])
sns.barplot(data=amc_latest, x="aum_crore", y="fund_house_short", hue="fund_house_short", legend=False,
            palette="Blues_r", ax=ax2)
ax2.set_title(f"AUM by Fund House — {latest_date.date()}", fontsize=9.5)
ax2.set_xlabel("AUM (Rs crore)")
ax2.set_ylabel("")
ax2.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1e5:.1f}L"))
ax2.tick_params(axis="y", labelsize=8.5)

# Line: SIP inflow trend (full width)
ax3 = fig.add_subplot(gs[2, :])
sip_s = sip.copy()
sip_s["month_dt"] = pd.to_datetime(sip_s["month"])
ax3.bar(sip_s["month_dt"], sip_s["sip_inflow_crore"], width=20, color=TEAL, alpha=0.85)
ax3.set_title("Monthly SIP Inflow Trend, Jan 2022 - Dec 2025", fontsize=10)
ax3.set_ylabel("SIP inflow (Rs crore)")

fig.savefig(OUT_DIR / "page1_industry_overview.png", dpi=150, facecolor="white")
plt.close(fig)
print("Page 1 saved.")

# ===========================================================================
# PAGE 2 — Fund Performance
# ===========================================================================
fig = plt.figure(figsize=(15, 9.5))
page_header(fig, "Page 2 — Fund Performance", 2)
gs = gridspec.GridSpec(2, 2, figure=fig, top=0.91, bottom=0.06, left=0.05, right=0.97,
                        hspace=0.38, wspace=0.28, height_ratios=[1.1, 1])

scored = scorecard.set_index("amfi_code")

# Scatter: return_3yr (X) vs risk/StdDev (Y), bubble = AUM, color = category
ax1 = fig.add_subplot(gs[0, 0])
perf07_idx = perf07.set_index("amfi_code")
scatter_df = scored.join(perf07_idx[["aum_crore"]])
for cat_name, color in [("Equity", BLUE), ("Debt", RED)]:
    sub = scatter_df[scatter_df["category"] == cat_name]
    ax1.scatter(sub["return_3yr_pct"], sub["risk_std_pct"], s=sub["aum_crore"] / 150,
                color=color, alpha=0.6, edgecolor="white", linewidth=0.5, label=cat_name)
ax1.set_xlabel("3yr return (%)")
ax1.set_ylabel("Risk — annualised std dev (%)")
ax1.set_title("Return vs Risk (bubble size = AUM)", fontsize=10)
ax1.legend(title="Category", loc="upper left", fontsize=8)

# Sortable fund scorecard table (top 12 by score)
ax2 = fig.add_subplot(gs[0, 1])
ax2.axis("off")
top12 = scorecard.head(12)[["scheme_name", "return_3yr_pct", "sharpe_ratio", "fund_score"]].copy()
top12["scheme_name"] = top12["scheme_name"].str.slice(0, 38)
top12.columns = ["Scheme", "3yr Ret %", "Sharpe", "Score"]
tbl = ax2.table(cellText := top12.round(2).values, colLabels=top12.columns,
                loc="center", cellLoc="left", colWidths=[0.64, 0.12, 0.12, 0.12])
tbl.auto_set_font_size(False)
tbl.set_fontsize(8)
tbl.scale(1, 1.35)
for (row, col), cell in tbl.get_celld().items():
    if row == 0:
        cell.set_facecolor(NAVY)
        cell.set_text_props(color="white", fontweight="bold")
    else:
        cell.set_facecolor("#F4F6F8" if row % 2 == 0 else "white")
ax2.set_title("Fund Scorecard — Top 12 (sortable by any column in Power BI)", fontsize=10, pad=12)

# NAV vs benchmark — top scorecard fund vs NIFTY100, 3yr
ax3 = fig.add_subplot(gs[1, :])
top_code = scorecard.iloc[0]["amfi_code"]
top_name = scorecard.iloc[0]["scheme_name"]
end_date = nav_wide.index.max()
win_start = end_date - pd.DateOffset(years=3)
fund_3y = nav_wide.loc[nav_wide.index >= win_start, top_code]
fund_3y_idx = fund_3y / fund_3y.iloc[0] * 100
n100_3y = bench[(bench["index_name"] == "NIFTY100") & (bench["date"] >= win_start)].set_index("date")["close_value"]
n100_3y_idx = n100_3y / n100_3y.iloc[0] * 100
ax3.plot(fund_3y_idx.index, fund_3y_idx.values, color=BLUE, linewidth=2, label=top_name)
ax3.plot(n100_3y_idx.index, n100_3y_idx.values, color=GRAY, linewidth=2, linestyle="--", label="NIFTY 100")
ax3.set_title(f"NAV vs Benchmark — {top_name} (top-ranked fund) vs NIFTY 100, Trailing 3yr", fontsize=10)
ax3.set_ylabel("Indexed (start = 100)")
ax3.legend(loc="upper left", fontsize=9)
fig.text(0.5, 0.015, "Interactive slicers in Power BI: Fund House | Category | Plan",
         ha="center", fontsize=9, color=GRAY, style="italic")

fig.savefig(OUT_DIR / "page2_fund_performance.png", dpi=150, facecolor="white")
plt.close(fig)
print("Page 2 saved.")

# ===========================================================================
# PAGE 3 — Investor Analytics
# ===========================================================================
fig = plt.figure(figsize=(15, 9.5))
page_header(fig, "Page 3 — Investor Analytics", 3)
gs = gridspec.GridSpec(2, 2, figure=fig, top=0.91, bottom=0.10, left=0.11, right=0.97,
                        hspace=0.45, wspace=0.30)

# Bar: transaction amount by state
ax1 = fig.add_subplot(gs[0, 0])
state_amt = tx.groupby("state")["amount_inr"].sum().sort_values(ascending=False) / 1e7
sns.barplot(x=state_amt.values, y=state_amt.index, hue=state_amt.index, legend=False,
            palette="Blues_r", ax=ax1)
ax1.set_title("Transaction Amount by State", fontsize=10)
ax1.set_xlabel("Total amount (Rs crore)")
ax1.set_ylabel("")

# Donut: SIP/Lumpsum/Redemption split (by amount)
ax2 = fig.add_subplot(gs[0, 1])
type_amt = tx.groupby("transaction_type")["amount_inr"].sum()
colors_donut = [BLUE, TEAL, RED]
ax2.pie(type_amt, labels=type_amt.index, autopct="%1.1f%%", startangle=90,
        colors=colors_donut, wedgeprops=dict(width=0.42), pctdistance=0.78)
ax2.set_title("Transaction Amount Split — SIP / Lumpsum / Redemption", fontsize=10)

# Bar: age group vs avg SIP amount
ax3 = fig.add_subplot(gs[1, 0])
age_order = ["18-25", "26-35", "36-45", "46-55", "56+"]
sip_tx = tx[tx["transaction_type"] == "SIP"]
avg_by_age = sip_tx.groupby("age_group")["amount_inr"].mean().reindex(age_order)
sns.barplot(x=avg_by_age.index, y=avg_by_age.values, hue=avg_by_age.index, legend=False,
            palette="viridis", ax=ax3)
ax3.set_title("Average SIP Amount by Age Group", fontsize=10)
ax3.set_ylabel("Avg SIP amount (Rs)")
ax3.set_xlabel("Age group")

# Line: monthly transaction volume
ax4 = fig.add_subplot(gs[1, 1])
tx_monthly = tx.set_index("transaction_date").resample("ME").size()
ax4.plot(tx_monthly.index, tx_monthly.values, marker="o", color=TEAL, linewidth=2)
ax4.set_title("Monthly Transaction Volume (count)", fontsize=10)
ax4.set_ylabel("Number of transactions")
plt.setp(ax4.get_xticklabels(), rotation=30, ha="right")

fig.text(0.5, 0.012, "Interactive slicers in Power BI: State | Age Group | City Tier",
         ha="center", fontsize=9, color=GRAY, style="italic")
fig.savefig(OUT_DIR / "page3_investor_analytics.png", dpi=150, facecolor="white")
plt.close(fig)
print("Page 3 saved.")

# ===========================================================================
# PAGE 4 — SIP & Market Trends
# ===========================================================================
fig = plt.figure(figsize=(15, 9.5))
page_header(fig, "Page 4 — SIP & Market Trends", 4)
gs = gridspec.GridSpec(2, 2, figure=fig, top=0.91, bottom=0.10, left=0.13, right=0.95,
                        hspace=0.48, wspace=0.32)

# Dual-axis: SIP inflow (bar) + Nifty50 (line), 2022-2025
ax1 = fig.add_subplot(gs[0, :])
n50_monthly = bench[bench["index_name"] == "NIFTY50"].set_index("date")["close_value"].resample("ME").last()
ax1.bar(sip_s["month_dt"], sip_s["sip_inflow_crore"], width=20, color=TEAL, alpha=0.85, label="SIP inflow (Rs Cr)")
ax1.set_ylabel("SIP inflow (Rs crore)", color=TEAL)
ax1.tick_params(axis="y", labelcolor=TEAL)
ax1b = ax1.twinx()
ax1b.plot(n50_monthly.index, n50_monthly.values, color=NAVY, linewidth=2, label="NIFTY 50")
ax1b.set_ylabel("NIFTY 50", color=NAVY)
ax1b.tick_params(axis="y", labelcolor=NAVY)
ax1.set_title("SIP Inflow (bar) vs NIFTY 50 (line), 2022-2025", fontsize=10)
ax1.grid(False)
ax1b.grid(False)

# Category inflow heatmap
ax2 = fig.add_subplot(gs[1, 0])
cat_pivot = cat.pivot(index="category", columns="month", values="net_inflow_crore")
sns.heatmap(cat_pivot, cmap="RdYlGn", center=0, cbar_kws={"label": "Net inflow (Rs Cr)"}, ax=ax2)
ax2.set_title("Category Net Inflow Heatmap, FY 2024-25", fontsize=10)
ax2.set_xlabel("")
ax2.set_ylabel("")
plt.setp(ax2.get_xticklabels(), rotation=45, ha="right", fontsize=7)

# Top 5 categories by net inflow FY25
ax3 = fig.add_subplot(gs[1, 1])
fy25 = cat[cat["month"].between("2024-04", "2025-03")]
top5_cat = fy25.groupby("category")["net_inflow_crore"].sum().sort_values(ascending=False).head(5)
sns.barplot(x=top5_cat.values / 1000, y=top5_cat.index, hue=top5_cat.index, legend=False,
            palette="Greens_r", ax=ax3)
ax3.set_title("Top 5 Categories by Net Inflow, FY 2024-25", fontsize=10)
ax3.set_xlabel("Net inflow (Rs '000 crore)")
ax3.set_ylabel("")

fig.savefig(OUT_DIR / "page4_sip_market_trends.png", dpi=150, facecolor="white")
plt.close(fig)
print("Page 4 saved.")

print(f"\nAll 4 dashboard pages written to {OUT_DIR}/")

# ---------------------------------------------------------------------------
# Combine all 4 pages into Dashboard.pdf
# ---------------------------------------------------------------------------
from PIL import Image

page_files = [
    OUT_DIR / "page1_industry_overview.png",
    OUT_DIR / "page2_fund_performance.png",
    OUT_DIR / "page3_investor_analytics.png",
    OUT_DIR / "page4_sip_market_trends.png",
]
images = [Image.open(p).convert("RGB") for p in page_files]
images[0].save(OUT_DIR / "Dashboard.pdf", save_all=True, append_images=images[1:])
print(f"Dashboard.pdf written ({(OUT_DIR / 'Dashboard.pdf').stat().st_size / 1024:.0f} KB, 4 pages)")

# ===========================================================================
# BONUS — export data for the interactive HTML dashboard
# (scripts/build_dashboard_html.py reads this and builds the .html file)
# ===========================================================================
import json


def agg_for_states(states_subset: pd.DataFrame) -> dict:
    """The 3 cross-filterable Page-3 charts, computed for a given tx slice."""
    type_amt = states_subset.groupby("transaction_type")["amount_inr"].sum()
    sip_sub = states_subset[states_subset["transaction_type"] == "SIP"]
    avg_age = sip_sub.groupby("age_group")["amount_inr"].mean().reindex(age_order)
    monthly = states_subset.set_index("transaction_date").resample("ME").size()
    return {
        "type_donut": {"labels": type_amt.index.tolist(), "values": type_amt.round(0).tolist()},
        "age_bar": {"labels": age_order, "values": avg_age.round(0).fillna(0).tolist()},
        "tx_volume": {"labels": monthly.index.strftime("%Y-%m").tolist(), "values": monthly.tolist()},
    }


age_order = ["18-25", "26-35", "36-45", "46-55", "56+"]
by_state = {"ALL": agg_for_states(tx)}
for st in sorted(tx["state"].unique()):
    by_state[st] = agg_for_states(tx[tx["state"] == st])

# NAV vs benchmark series for the top 10 scorecard funds (3yr window, indexed to 100)
top10_codes = scorecard.head(10)["amfi_code"].tolist()
top10_names = scorecard.head(10).set_index("amfi_code")["scheme_name"].to_dict()
win_start = nav_wide.index.max() - pd.DateOffset(years=3)
nav_3y_all = nav_wide.loc[nav_wide.index >= win_start, top10_codes]
nav_3y_all_idx = nav_3y_all / nav_3y_all.iloc[0] * 100
n100_3y_all = bench[(bench["index_name"] == "NIFTY100") & (bench["date"] >= win_start)].set_index("date")["close_value"]
n100_3y_all_idx = (n100_3y_all / n100_3y_all.iloc[0] * 100).reindex(nav_3y_all_idx.index)

amc_trend_s = aum.groupby("date")["aum_crore"].sum().sort_index()
amc_latest_for_json = aum[aum["date"] == aum["date"].max()].sort_values("aum_crore", ascending=False).copy()
amc_latest_for_json["short"] = amc_latest_for_json["fund_house"].map(SHORT_NAME).fillna(amc_latest_for_json["fund_house"])

scorecard_with_aum = scorecard.head(40).merge(
    perf07[["amfi_code", "aum_crore"]], on="amfi_code", how="left"
)

cat_pivot_json = cat.pivot(index="category", columns="month", values="net_inflow_crore")
fy25_json = cat[cat["month"].between("2024-04", "2025-03")]
top5_cat_json = fy25_json.groupby("category")["net_inflow_crore"].sum().sort_values(ascending=False).head(5)

html_data = {
    "kpi": {
        "total_aum": "Rs 81L Cr",
        "sip_inflow": f"Rs {sip_s.iloc[-1]['sip_inflow_crore']:,.0f} Cr",
        "folios": f"{folio.iloc[-1]['total_folios_crore']:.2f} Cr",
        "schemes": "1,908",
    },
    "amc_trend": {
        "labels": amc_trend_s.index.strftime("%Y-%m").tolist(),
        "values": (amc_trend_s / 1e5).round(2).tolist(),
    },
    "amc_bar": {
        "labels": amc_latest_for_json["short"].tolist(),
        "values": (amc_latest_for_json["aum_crore"] / 1e5).round(2).tolist(),
    },
    "sip_trend": {
        "labels": sip_s["month"].tolist(),
        "values": sip_s["sip_inflow_crore"].tolist(),
    },
    "scorecard": scorecard_with_aum[[
        "amfi_code", "scheme_name", "fund_house", "category",
        "return_3yr_pct", "risk_std_pct", "sharpe_ratio", "alpha_pct", "fund_score", "aum_crore",
    ]].to_dict("records"),
    "nav_vs_bench": {
        "labels": nav_3y_all_idx.index.strftime("%Y-%m-%d").tolist(),
        "fund_names": {str(k): v for k, v in top10_names.items()},
        "funds": {str(c): nav_3y_all_idx[c].round(2).tolist() for c in top10_codes},
        "nifty100": n100_3y_all_idx.round(2).tolist(),
    },
    "state_bar": by_state["ALL"],  # placeholder key unused by JS directly; real per-state data below
    "by_state": {st: v for st, v in by_state.items()},
    "state_amounts": {
        "labels": (tx.groupby("state")["amount_inr"].sum().sort_values(ascending=False) / 1e7).round(2).index.tolist(),
        "values": (tx.groupby("state")["amount_inr"].sum().sort_values(ascending=False) / 1e7).round(2).tolist(),
    },
    "type_donut": by_state["ALL"]["type_donut"],
    "age_bar": by_state["ALL"]["age_bar"],
    "tx_volume": by_state["ALL"]["tx_volume"],
    "states_list": sorted(tx["state"].unique().tolist()),
    "nifty50_monthly": {
        "values": bench[bench["index_name"] == "NIFTY50"].set_index("date")["close_value"]
        .resample("ME").last().round(1).tolist(),
    },
    "cat_heatmap": {
        "categories": cat_pivot_json.index.tolist(),
        "months": cat_pivot_json.columns.tolist(),
        "values": cat_pivot_json.round(0).fillna(0).values.tolist(),
    },
    "top5_cat": {
        "labels": top5_cat_json.index.tolist(),
        "values": (top5_cat_json / 1000).round(1).tolist(),
    },
    "fund_houses": sorted(fm["fund_house"].unique().tolist()),
    "categories": sorted(fm["category"].unique().tolist()),
}

json_path = OUT_DIR / "_data_for_html.json"
json_path.write_text(json.dumps(html_data))
print(f"HTML data export written: {json_path} ({json_path.stat().st_size / 1024:.0f} KB)")





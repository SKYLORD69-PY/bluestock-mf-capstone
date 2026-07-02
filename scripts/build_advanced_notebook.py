"""
build_advanced_notebook.py — assembles Advanced_Analytics.ipynb from
scripts/advanced_analytics.py via marker-based extraction (same pattern
as Day 3 and Day 4), interspersing 5 advanced insight markdown cells.
"""
import nbformat as nbf

SRC = open("scripts/advanced_analytics.py").read()


def section(start_marker: str, end_marker: str | None) -> str:
    start = SRC.index(start_marker)
    end = SRC.index(end_marker, start) if end_marker else len(SRC)
    return SRC[start:end].rstrip() + "\n"


nb = nbf.v4.new_notebook()
cells = []


def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))


def code(text):
    cells.append(nbf.v4.new_code_cell(
        text.replace('matplotlib.use("Agg")', '%matplotlib inline')
            .replace("plt.close()", "plt.show()")
    ))


# ---------------------------------------------------------------------------
md("""# Bluestock MF Capstone — Day 6: Advanced Analytics + Risk Metrics

Source: `data/processed/` (Day 2) + `reports/fund_scorecard.csv` (Day 4).
All risk metrics use actual trading days only (`is_actual_trading_day == 1`),
consistent with the Day 4 convention.

---
**5 advanced insights documented as Markdown cells** throughout this notebook,
each grounded in a specific numeric finding from the data.""")

code(section('from pathlib import Path', '# TASK 1'))

# Task 1 — VaR / CVaR
md("""## Task 1 — Historical VaR (95%) and CVaR for All 40 Schemes

**Method:** sort the daily return distribution for each fund; VaR₉₅ = 5th
percentile (the single worst day in a typical 20-day window); CVaR₉₅ = mean
of all returns worse than that threshold (Expected Shortfall).

*Interpretation:* a VaR₉₅ of -2.69% means that on 5% of trading days
(≈12 days/year), the fund can be expected to lose more than 2.69%.
CVaR tells you the average size of those tail losses.""")
code(section('# TASK 1', '# TASK 2'))

md("""### Insight 1 — Small-cap funds carry 6x the tail risk of liquid funds

The worst VaR₉₅ funds are all **Very High** risk-grade Small/Mid-Cap equity
funds (SBI Small Cap -2.69%, Axis Small Cap -2.62%, ABSL Small Cap -2.60%).
The best VaR₉₅ funds are **Low** risk-grade Liquid funds (ICICI Pru Liquid
-0.02%). That's a 6× difference in single-day tail-loss exposure. CVaR
tells an even starker story: on bad days, small-cap funds lose ~3.2% on
average vs ~0.03% for liquid funds. An investor switching from Liquid to
Small-Cap for yield increases their tail risk by two orders of magnitude.""")

# Task 2 — Rolling Sharpe
md("## Task 2 — Rolling 90-Day Sharpe Ratio (Top 5 Scorecard Funds)")
code(section('# TASK 2', '# TASK 3'))

md("""### Insight 2 — Rolling Sharpe is highly unstable across time

Despite the top-5 scorecard funds having excellent full-period Sharpe ratios
(1.0–1.45 as computed in Day 4), the rolling 90-day Sharpe swings wildly —
often dipping below zero (negative risk-adjusted return) for multi-month
stretches. This means the 4-year average Sharpe ratio from `07_scheme_performance.csv`
significantly understates the volatility of the return-generating process. No
fund consistently delivered a Sharpe > 1.0 on a rolling basis; any investor
who switched in or out based on short-term Sharpe figures would have been
whipsawed repeatedly.""")

# Task 3 — Cohort
md("## Task 3 — Investor Cohort Analysis")
code(section('# TASK 3', '# TASK 4'))

md("""### Insight 3 — The 2024 cohort completely dwarfs the 2025 cohort

The transaction dataset spans Jan 2024 – May 2025, so almost all investors
(4,624 of 4,762) made their first transaction in 2024. The small 2025 cohort
(138 investors) does show a higher average SIP amount (₹13,505 vs ₹10,997),
consistent with newer investors being more financially sophisticated or
better-informed — but the sample is too small (138) to draw a strong
conclusion. Total capital deployed: the 2024 cohort invested ₹21.5 Cr total
vs ₹0.23 Cr for the 2025 cohort, simply because of the headcount difference.""")

# Task 4 — Continuity
md("## Task 4 — SIP Continuity Analysis")
code(section('# TASK 4', '# TASK 5'))

md("""### Insight 4 — SIP continuity is a data-realism flag, not a real investor behaviour finding

97.8% of investors with 6+ SIPs are flagged "at-risk" (avg gap > 35 days),
with an overall average inter-SIP gap of ~65 days. This is unrealistic: real
SIPs are monthly mandates (≈30-31 day gaps), and a 65-day average implies
most investors are skipping months. The transaction dates were synthetically
generated without enforcing the monthly SIP rhythm, so this is a dataset
artefact. In real data, this metric would usefully identify investors who
missed 2+ consecutive months. Worth flagging in the final report.""")

# Task 5 — Recommender
md("""## Task 5 — Fund Recommender

The full standalone recommender is in `scripts/recommender.py`. This cell
runs it inline to show all three risk profiles.""")
code(section('# TASK 5', '# TASK 6'))

# Task 6 — HHI
md("## Task 6 — Sector HHI Concentration")
code(section('# TASK 6', None).rsplit('\nprint("\\nAll Day 6', 1)[0] + "\n")

md("""### Insight 5 — All equity fund portfolios are moderately concentrated; Axis Bluechip is highest

Every equity fund in this dataset scores above the HHI = 0.10 "moderate
concentration" threshold (range 0.107–0.206). Axis Bluechip Fund, with just
10 disclosed holdings, has the highest HHI (0.206), indicating its portfolio
weight is heavily dominated by a handful of sector bets. SBI Small Cap
(0.107, the most diversified) has significantly more holdings spread across
sectors. The practical implication: a sector downturn in Banking or IT
(the top 2 sectors by weight from Day 3 EDA) would disproportionately affect
the more concentrated funds, especially those with Banking as their #1 sector.""")

md("""---
## Summary — 5 Advanced Insights

1. **Small-cap funds carry 6× the tail risk of liquid funds** — VaR₉₅ ranges
   from -0.02% (Liquid) to -2.69% (Small Cap). CVaR shows average tail losses
   of -3.2% for the worst equity funds on bad days.
2. **Rolling 90-day Sharpe is highly unstable** — despite full-period Sharpe
   ratios of 1.0–1.45, the top-5 funds regularly drop below 0 on a rolling
   basis. The 4-year averages from the dataset are misleading as a predictor
   of short-term consistency.
3. **The 2024 cohort dominates entirely** — 97% of investors made their first
   transaction in 2024. The 2025 cohort's higher average SIP (₹13.5K vs ₹11K)
   is directionally interesting but statistically weak (n=138).
4. **97.8% SIP "at-risk" rate is a dataset artefact** — synthetic transaction
   dates don't enforce monthly SIP rhythm (~65-day avg gap vs ~31-day real).
   The metric is correctly implemented; the data isn't realistic enough to
   generate a meaningful finding.
5. **All equity portfolios are moderately-to-highly concentrated** (HHI 0.107–
   0.206). Axis Bluechip is most concentrated (10 holdings, HHI 0.206);
   SBI Small Cap is the most diversified. Banking sector dominance from Day 3
   makes these funds particularly sensitive to RBI/credit-cycle news.
""")

nb["cells"] = cells
nbf.write(nb, "notebooks/Advanced_Analytics.ipynb")
print(f"Notebook written with {len(cells)} cells.")

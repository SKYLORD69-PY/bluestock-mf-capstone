"""
build_performance_notebook.py — assembles Performance_Analytics.ipynb from
scripts/performance_analytics.py (extracted by marker text, robust to
line-number drift) plus markdown cells for section headers and discussion.
Run once; output is then executed via nbclient.
"""
import nbformat as nbf

SRC = open("scripts/performance_analytics.py").read()


def section(start_marker: str, end_marker: str | None) -> str:
    start = SRC.index(start_marker)
    end = SRC.index(end_marker, start) if end_marker else len(SRC)
    text = SRC[start:end].rstrip() + "\n"
    text = text.replace("plt.show()", "plt.show()")  # already plt.show(), no-op (kept for parity with Day3 pattern)
    return text


nb = nbf.v4.new_notebook()
cells = []


def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))


def code(text):
    cells.append(nbf.v4.new_code_cell(text))


# ---------------------------------------------------------------------------
md("""# Bluestock MF Capstone — Day 4: Fund Performance Analytics

Source: `data/processed/` (Day 2 cleaned CSVs). All metrics below are
computed independently from the raw NAV history — not read from
`07_scheme_performance_clean.csv` — so they can be cross-checked against
that file's pre-computed values.

**Design decision:** every calculation uses only *actual trading days*
(`is_actual_trading_day == 1`), not the Day 2 calendar-reindexed series.
Including forward-filled weekend rows (0% return) would dilute volatility
estimates and break the `sqrt(252)` trading-day annualisation convention.

**Risk-free rate:** Rf = 6.5% annual (RBI repo rate proxy), used throughout.""")

code(section('from pathlib import Path', '# ---------------------------------------------------------------------------\n# Load')
     .replace('import matplotlib\nmatplotlib.use("Agg")\n', '%matplotlib inline\n'))
code(section('# ---------------------------------------------------------------------------\n# Load', '# TASK 1'))

# ---- Task 1 ----
md("""## Task 1 — Daily Returns, All 40 Schemes

`daily_return = nav_t / nav_t-1 - 1`, computed on actual trading days only.
Validated by inspecting the distribution by category below.""")
code(section('# TASK 1', '# TASK 2'))
md("""**Check:** Equity daily returns are centered near 0 with ~1.11% daily
std (≈17.6% annualised vol — plausible for diversified equity); Debt is
far tighter at ~0.18% daily std. Both distributions look like reasonable,
well-behaved return series — no obvious data artifacts.""")

# ---- Task 2 ----
md("""## Task 2 — CAGR (1yr, 3yr, and full-period)

**Caveat:** the brief asks for a 5yr CAGR, but the NAV history only spans
**4.40 years** (Jan 2022 – May 2026). A genuine 5-year lookback would need
data back to mid-2021, which doesn't exist. Rather than silently produce a
wrong number, this computes `return_full_period_pct` over the maximum
available ~4.4yr window instead, clearly labelled as such — and flags that
`07_scheme_performance.csv`'s own `return_5yr_pct` column **cannot be
independently verified** from the data provided.""")
code(section('# TASK 2', '# TASK 3'))

# ---- Task 3 ----
md("## Task 3 — Sharpe Ratio, Ranked")
code(section('# TASK 3', '# TASK 4'))

# ---- Task 4 ----
md("## Task 4 — Sortino Ratio (downside deviation only)")
code(section('# TASK 4', '# TASK 5'))

# ---- Task 5 ----
md("""## Task 5 — Alpha & Beta vs NIFTY 100 (OLS Regression)

`scipy.stats.linregress(benchmark_return, fund_return)` per fund;
`alpha_pct = intercept × 252 × 100`, `beta = slope`.""")
code(section('# TASK 5', '# TASK 6'))
md("""**Important caveat:** median R² across all 40 funds is ~0.0003 —
essentially **no explanatory power**. Beta is near zero for every fund
(-0.07 to 0.10). This is the same pattern Day 3's EDA found (near-zero
fund-to-fund return correlation): these funds' NAV paths don't appear to
be driven by the broader market the way real equity funds are. Treat the
alpha/beta figures below as correctly-computed but **statistically weak**
— they're capturing each fund's average excess return, not a genuine
market-risk relationship.""")

# ---- Task 6 ----
md("## Task 6 — Maximum Drawdown + Worst Drawdown Window")
code(section('# TASK 6', '# TASK 7'))

# ---- Task 7 ----
md("""## Task 7 — Fund Scorecard (0-100 Composite)

`score = 30%×return_3yr_rank + 25%×Sharpe_rank + 20%×alpha_rank + 15%×expense_ratio_rank(inverse) + 10%×max_DD_rank(inverse)`,
all ranks as percentiles (0-100) across the 40 funds.""")
code(section('# TASK 7', '# TASK 8'))

# ---- Task 8 ----
md("""## Task 8 — Benchmark Comparison: Top 5 Scorecard Funds vs NIFTY 50 / 100

Trailing 3 years, all series rebased to 100 at the window start.""")
code(section('# TASK 8', None))
md("""**Striking finding:** every one of the top 5 funds climbed to
220-265 (indexed) over the trailing 3 years, while NIFTY 50 actually
**fell** to ~75 and NIFTY 100 only reached ~125 over the same window. This
is the clearest visual confirmation yet of the Day 3/Task 5 finding — fund
NAVs in this dataset move essentially independently of the real benchmark
path, not in line with it. Tracking error vs NIFTY100 for the top 5 funds
is correspondingly huge (18.7%-23.3% annualised) — for real-world index-
aware active funds, tracking error vs. a broad benchmark is typically in
the low single digits, so this further confirms the simulated NAVs aren't
benchmark-relative.""")

nb["cells"] = cells
nbf.write(nb, "notebooks/Performance_Analytics.ipynb")
print(f"Notebook written with {len(cells)} cells.")

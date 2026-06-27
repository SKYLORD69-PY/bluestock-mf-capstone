"""
build_notebook.py — assembles EDA_Analysis.ipynb from scripts/eda_analysis.py
(extracted by marker text, NOT line numbers, so it's robust to future edits)
plus markdown cells for section headers and the 10 key EDA findings.
Run once; output is then executed via nbclient.
"""
import nbformat as nbf

SRC = open("scripts/eda_analysis.py").read()


def section(start_marker: str, end_marker: str | None) -> str:
    """Extract SRC between start_marker (inclusive) and end_marker (exclusive,
    or end-of-file if None). Marker-based, so it survives line-number drift."""
    start = SRC.index(start_marker)
    end = SRC.index(end_marker, start) if end_marker else len(SRC)
    text = SRC[start:end].rstrip() + "\n"
    text = text.replace("plt.close()", "plt.show()")
    if "write_image(" in text:
        for n, fname in [(1, "01_nav_trend_all_schemes.png"), (3, "03_sip_inflow_trend.png")]:
            marker = f'print("Chart {n} saved.")'
            if marker in text:
                text = text.replace(
                    marker,
                    f'from IPython.display import Image, display\n'
                    f'display(Image(filename=str(CHARTS_DIR / "{fname}")))\n' + marker
                )
    return text


nb = nbf.v4.new_notebook()
cells = []


def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))


def code(text):
    cells.append(nbf.v4.new_code_cell(text))


# ---------------------------------------------------------------------------
md("""# Bluestock MF Capstone — Day 3: Exploratory Data Analysis

Source: `data/processed/` (Day 2 cleaned CSVs). All charts are also exported
as PNGs to `reports/day3_charts/` for the final report.

16 charts total (12 from the brief + 4 bonus), 10 key findings documented
as markdown cells next to their supporting chart.""")

code(section('from pathlib import Path', '# ---------------------------------------------------------------------------\n# Load')
     .replace('import matplotlib\nmatplotlib.use("Agg")\n', '%matplotlib inline\n'))
code(section('# ---------------------------------------------------------------------------\n# Load',
             '# ---------------------------------------------------------------------------\n# Empirically locate'))

md("""## Locating the 2023 rally / 2024 correction windows

Rather than guessing dates, the actual rally/correction windows are
computed from the real NIFTY50 benchmark series.""")
code(section('# ---------------------------------------------------------------------------\n# Empirically locate',
             '# ===========================================================================\n# CHART 1'))

# ---- Chart 1: NAV trend ----
md("## Chart 1 — NAV Trend, All 40 Schemes (rebased to 100)")
code(section('# CHART 1', '# ===========================================================================\n# CHART 2'))
md("""**Finding 1:** Although NIFTY50 fell -24.5% in its real Mar-Oct 2024
correction, the simulated equity scheme NAVs show **no corresponding dip**
in the same window (Chart 1) — confirming scheme-level NAVs were generated
independently of the benchmark's actual day-to-day path, not as a real
tracked product.""")

# ---- Chart 2: AUM growth ----
md("## Chart 2 — AUM Growth by Fund House, 2022-2025")
code(section('# CHART 2', '# ===========================================================================\n# CHART 3'))
md("""**Finding 2:** SBI Mutual Fund is the dominant AMC at every year-end
snapshot, reaching ₹12.50L Cr by Dec 2025 — about 20% of the top-10 AMC
pool and ~17% ahead of #2 ICICI Prudential MF (Chart 2).""")

# ---- Chart 3: SIP inflow ----
md("## Chart 3 — Monthly SIP Inflow Trend")
code(section('# CHART 3', '# ===========================================================================\n# CHART 4'))
md("""**Finding 3:** Monthly SIP inflows grew **169%**, from ₹11,517 Cr
(Jan 2022) to an all-time-high ₹31,002 Cr (Dec 2025), with growth visibly
accelerating from mid-2024 onward (Chart 3).""")

# ---- Chart 4: Category heatmap ----
md("## Chart 4 — Category-wise Net Inflow Heatmap (FY 2024-25)")
code(section('# CHART 4', '# ===========================================================================\n# CHART 5'))
md("""**Finding 4:** Liquid funds dominate category-level net inflows in
FY 2024-25 (₹4.51L Cr, ~64% of the FY total) — far above any equity
category (e.g. ELSS at just ₹6,080 Cr). This reflects Liquid funds' high
turnover/churn behaviour, not low equity demand (Chart 4).""")

# ---- Chart 5/6/7: Demographics ----
md("""## Charts 5-7 — Investor Demographics
Age distribution, SIP amount by age, and gender split.""")
code(section('# CHART 5/6/7', '# ===========================================================================\n# CHART 8'))
md("""**Finding 5:** Average SIP amount is nearly flat across age groups
(₹10,885-11,575) — there's no meaningful age-based ticket-size pattern in
this data, unlike typical real-world investor behaviour where ticket size
usually scales with age/income (Chart 6).""")

# ---- Chart 8/9: Geographic ----
md("""## Charts 8-9 — Geographic Distribution
SIP amount by state, and T30 vs B30 city tier split.""")
code(section('# CHART 8/9', '# ===========================================================================\n# CHART 10'))
md("""**Finding 6:** The investor base skews Tier-1 and male: 65.9% of
transaction value comes from T30 cities and 66.7% of investors are male,
versus 34.1% / 33.3% from B30 / female investors respectively
(Charts 7-9).""")

# ---- Chart 10: Folio growth ----
md("## Chart 10 — Folio Count Growth")
code(section('# CHART 10', '# ===========================================================================\n# CHART 11'))
md("""**Finding 7:** Total mutual fund folios nearly doubled (**+97%**),
from 13.26 Cr (Jan 2022) to 26.12 Cr (Dec 2025), crossing the 20 Cr
milestone around Aug-Sep 2024 (Chart 10).""")

# ---- Chart 11: Correlation ----
md("## Chart 11 — NAV Return Correlation Matrix (10 Selected Funds)")
code(section('# CHART 11', '# ===========================================================================\n# CHART 12'))
md("""**Finding 8:** Daily returns across the 10 sampled funds show
essentially **zero pairwise correlation** (all |r| < 0.08) — real-world
equity funds typically move together (r of 0.7-0.95) due to shared market
exposure. This indicates each fund's NAV path was simulated independently
rather than driven by a common market factor (Chart 11).""")

# ---- Chart 12: Sector donut ----
md("## Chart 12 — Sector Allocation (Rupee-Weighted)")
code(section('# CHART 12', '# ===========================================================================\n# BONUS CHART 13'))
md("""**Finding 9:** Equity portfolios are concentrated in Banking (19.3%)
and IT (11.8%); the top 4 sectors (Banking, IT, Pharma, Automobile) account
for ~52% of all disclosed equity holdings (Chart 12).""")

# ---- Chart 13: KYC ----
md("## Chart 13 (Bonus) — KYC Status Split")
code(section('# BONUS CHART 13', '# ===========================================================================\n# BONUS CHART 14'))
md("""**Finding 10:** KYC compliance is high (92.2% Verified) but a
non-trivial **7.8%** of investors remain Pending — a clear, sizeable
segment for targeted KYC-completion outreach (Chart 13).""")

# ---- Bonus charts 14-16 ----
md("## Charts 14-16 (Bonus) — Transaction Type, Payment Mode, Expense Ratio")
code(section('# BONUS CHART 14', '# ===========================================================================\n# BONUS CHART 15'))
code(section('# BONUS CHART 15', '# ===========================================================================\n# BONUS CHART 16'))
code(section('# BONUS CHART 16', None).rsplit('\nprint(f"\\nAll charts written', 1)[0].rstrip() + '\n')

md("""## Summary — 10 Key EDA Findings

1. Equity NAVs show no dip during NIFTY50's real 2024 correction — scheme
   NAVs are simulated independently of the benchmark's actual path. (Chart 1)
2. SBI Mutual Fund is the dominant AMC throughout 2022-2025, reaching
   ₹12.50L Cr AUM by Dec 2025. (Chart 2)
3. Monthly SIP inflows grew 169% to an all-time-high ₹31,002 Cr (Dec 2025).
   (Chart 3)
4. Liquid funds dominate FY24-25 category net inflows (~64% of the total),
   reflecting churn, not low equity demand. (Chart 4)
5. SIP amount is nearly flat across investor age groups — no meaningful
   age-based ticket-size pattern. (Chart 6)
6. The investor base skews T30/male: 65.9% of transaction value from T30
   cities, 66.7% of investors male. (Charts 7-9)
7. Total folios nearly doubled (+97%) from 13.26 Cr to 26.12 Cr,
   crossing 20 Cr around Aug-Sep 2024. (Chart 10)
8. The 10 sampled funds show ~zero pairwise return correlation — unlike
   real equity funds (typically 0.7-0.95), implying independent NAV
   simulation rather than a shared market factor. (Chart 11)
9. Equity holdings are concentrated in Banking (19.3%) and IT (11.8%); top
   4 sectors = ~52% of all holdings. (Chart 12)
10. KYC is 92.2% Verified / 7.8% Pending — a clear outreach segment.
   (Chart 13)
""")

nb["cells"] = cells
nbf.write(nb, "notebooks/EDA_Analysis.ipynb")
print(f"Notebook written with {len(cells)} cells.")

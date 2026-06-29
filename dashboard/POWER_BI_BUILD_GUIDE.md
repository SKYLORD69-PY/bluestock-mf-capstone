# Power BI Build Guide — Bluestock MF Dashboard

This is an exact, step-by-step guide to build `bluestock_mf_dashboard.pbix`
in real Power BI Desktop, using the data this project already produced.
Nothing here is generic — every table, column, and DAX formula below
matches this repo's actual schema.

Estimated build time following this guide: 60-90 minutes.

---

## 1. Connect to data

**Option A — Import the cleaned CSVs (simplest, recommended):**
`Home -> Get Data -> Text/CSV` and import each file in `data/processed/`:

| File | Power BI table name |
|---|---|
| `01_fund_master_clean.csv` | `dim_fund` |
| `02_nav_history_clean.csv` | `fact_nav` |
| `03_aum_by_fund_house_clean.csv` | `fact_aum` |
| `04_monthly_sip_inflows_clean.csv` | `fact_sip_industry` |
| `05_category_inflows_clean.csv` | `fact_category_inflow` |
| `06_industry_folio_count_clean.csv` | `fact_folio` |
| `08_investor_transactions_clean.csv` | `fact_transactions` |
| `10_benchmark_indices_clean.csv` | `fact_benchmark` |

Also import from `reports/`:
| File | Power BI table name |
|---|---|
| `fund_scorecard.csv` | `fund_scorecard` |
| `alpha_beta.csv` | `alpha_beta` |

**Option B — Connect via SQLite ODBC:** install the SQLite ODBC driver,
then `Get Data -> ODBC`, point it at `data/db/bluestock_mf.db`, and import
the same tables (they already exist there with these exact names — see
`sql/schema.sql`). Skip this if Option A is working fine; it's only worth
the setup effort if you want the dashboard to refresh automatically when
`bluestock_mf.db` is rebuilt.

**Verify:** `Model` view should show 10 tables. Row counts should match
`reports/day2_cleaning_log.txt` (e.g. `fact_nav` = 64,320 rows).

### Add a Context_KPIs table for industry-wide figures
Two KPI figures on Page 1 (`Total Industry AUM`, `Total Schemes`) are
**not in any provided dataset** — they're 81L Cr / 1,908 schemes for the
*entire* Indian MF industry (per AMFI), while every other table here only
covers the 10 AMCs / 40 schemes in this project's data. Don't try to
derive them from `fact_aum` (it'll be ~62L Cr, not 81L Cr — a real but
different number).

`Home -> Enter Data`, create a table named `Context_KPIs`:

| Metric | Value | AsOf | Source |
|---|---|---|---|
| Total Industry AUM (Rs Cr) | 8100000 | 2025-12-31 | AMFI |
| Total Schemes | 1908 | 2025-12-31 | AMFI |

### Create relationships
`Model` view, drag to connect:
- `dim_fund[amfi_code]` → `fact_nav[amfi_code]` (1:many)
- `dim_fund[amfi_code]` → `fact_transactions[amfi_code]` (1:many)
- `dim_fund[amfi_code]` → `fund_scorecard[amfi_code]` (1:1)
- `dim_fund[amfi_code]` → `alpha_beta[amfi_code]` (1:1)
- `fact_nav[date]` → a new `dim_date` table (see below) on `date_id`

You need a real date table for the dual-axis and time-series charts to
filter consistently. `Modeling -> New Table`:
```dax
dim_date = CALENDAR(DATE(2022,1,1), DATE(2026,5,31))
```
Then add columns: `Year = YEAR(dim_date[Date])`, `Month = FORMAT(dim_date[Date], "YYYY-MM")`.
Relate `dim_date[Date]` → `fact_nav[date]`, `fact_transactions[transaction_date]`,
`fact_aum[date]`, `fact_benchmark[date]` (1:many each, single direction).

---

## 2. Page 1 — Industry Overview

**4 KPI Cards** (`Insert -> Card` (the new-style "Card" visual, not multi-row)):
1. Field: `Context_KPIs` filtered to "Total Industry AUM" row, or create:
   ```dax
   Total Industry AUM = "Rs 81L Cr"
   ```
2. SIP Inflow:
   ```dax
   Latest SIP Inflow = 
   VAR LatestMonth = MAX(fact_sip_industry[month])
   RETURN CALCULATE(SUM(fact_sip_industry[sip_inflow_crore]), fact_sip_industry[month] = LatestMonth)
   ```
3. Folios:
   ```dax
   Latest Folios = 
   VAR LatestMonth = MAX(fact_folio[month])
   RETURN CALCULATE(SUM(fact_folio[total_folios_crore]), fact_folio[month] = LatestMonth)
   ```
4. Schemes: `Context_KPIs` "Total Schemes" row (1908).

**Line chart** — AUM trend: X = `fact_aum[date]`, Y = `Sum(fact_aum[aum_crore])`.
Add a Y-axis label noting "Sum of 10 AMCs in this dataset" — it will NOT
match the 81L Cr KPI card (see `README.md` Day 5 notes on why).

**Bar chart** — AUM by AMC: X = `Sum(fact_aum[aum_crore])`, Y = `fact_aum[fund_house]`,
filtered/sorted to the latest date, descending.

---

## 3. Page 2 — Fund Performance

**Scatter chart**: X = `fund_scorecard[return_3yr_pct]`, Y = `fund_scorecard[risk_std_pct]`
(already included as a column — annualised std-dev of daily returns, same
methodology as Day 4's `performance_analytics.py`).
Size = `fact_performance[aum_crore]` (bubble = AUM).
Legend = `dim_fund[category]`.

**Table**: drag `fund_scorecard[scheme_name]`, `[return_3yr_pct]`,
`[sharpe_ratio]`, `[fund_score]` into a Table visual. Click the column
header to sort — sortable by default, no extra config needed.

**Line chart** (NAV vs benchmark): X = `dim_date[Date]`,
Y1 = `fact_nav[nav]` filtered to a selected `amfi_code` (use a slicer or
drill-through, see below), Y2 = a measure pulling `fact_benchmark[close_value]`
filtered to `index_name = "NIFTY100"`. Both need to be **indexed to 100**
at the window start for a fair comparison — add:
```dax
NAV Indexed = DIVIDE([Selected Fund NAV], CALCULATE([Selected Fund NAV], FIRSTDATE(dim_date[Date]))) * 100
```

**Slicers**: add 3 Slicer visuals bound to `dim_fund[fund_house]`,
`dim_fund[category]`, `dim_fund[plan]`.

---

## 4. Page 3 — Investor Analytics

- **Bar** — transaction amount by state: X = `Sum(fact_transactions[amount_inr])`, Y = `fact_transactions[state]`.
- **Donut** — transaction type split: Legend = `fact_transactions[transaction_type]`, Values = `Sum(fact_transactions[amount_inr])`.
- **Bar** — avg SIP by age group: X = `fact_transactions[age_group]`, Y = `Average(fact_transactions[amount_inr])`, filtered to `transaction_type = "SIP"` (use a visual-level filter).
- **Line** — monthly transaction volume: X = `dim_date[Date]` (by month), Y = `Count(fact_transactions[tx_id])`.
- **Slicers**: `fact_transactions[state]`, `[age_group]`, `[city_tier]`.

---

## 5. Page 4 — SIP & Market Trends

- **Dual-axis chart**: use the "Line and stacked column chart" visual.
  Column Y = `Sum(fact_sip_industry[sip_inflow_crore])`. Line Y = a measure
  pulling `fact_benchmark[close_value]` filtered to `index_name = "NIFTY50"`.
  Shared X = `dim_date[Date]` (by month).
- **Category heatmap**: Power BI has no built-in heatmap chart. Use a
  **Matrix** visual: Rows = `fact_category_inflow[category]`, Columns =
  `fact_category_inflow[month]`, Values = `Sum(net_inflow_crore)`, then
  `Format -> Conditional formatting -> Background color` on the Values
  field, color scale (e.g. red-yellow-green diverging) to approximate the
  heatmap in `reports/day5_dashboard/page4_sip_market_trends.png`.
- **Bar** — top 5 categories: X = `Sum(net_inflow_crore)`, Y = `category`,
  filtered to FY 2024-25 (`month` between "2024-04" and "2025-03"),
  Top N filter = 5.

---

## 6. Interactivity, theme, drill-through

**Drill-through**: create a new page "Fund Detail" with a NAV line chart
+ key metrics. On the Page 2 scorecard Table visual, `Format -> Drill
through` is set per-page: go to "Fund Detail" page settings, add
`dim_fund[amfi_code]` (or `scheme_name`) as the drill-through field. Right-
click any row in the Page 2 table -> "Drill through -> Fund Detail".

**Tooltips**: every native Power BI visual shows field values on hover by
default. For richer tooltips, create a tooltip page (small page, "Used as
tooltip" in page settings) and assign it via the visual's
`Format -> Tooltip -> Type: Report page`.

**Theme**: `View -> Themes -> Browse for themes`, import this JSON
(no official Bluestock brand assets exist for this project — these are the
colors used in the static `day5_dashboard/*.png` previews; swap in real
brand colors if you get them):
```json
{
  "name": "Bluestock",
  "dataColors": ["#1B6CA8", "#13A89E", "#E8A33D", "#C8553D", "#0B2545", "#6B7280"],
  "background": "#FFFFFF",
  "foreground": "#0B2545",
  "tableAccent": "#1B6CA8"
}
```
Save as `bluestock_theme.json` and import via the dialog above.

---

## 7. Export

1. `File -> Save As -> bluestock_mf_dashboard.pbix`
2. `File -> Export -> Export to PDF` -> `Dashboard.pdf`
   (this repo's `reports/day5_dashboard/Dashboard.pdf` is a script-built
   stand-in — replace it with the real Power BI export once you have it)
3. For PNG screenshots per page: `File -> Export -> Export to PDF`, then
   convert each PDF page to PNG, OR just screenshot each page at full
   screen (Power BI doesn't have a native "export page as PNG" — PDF
   export + page extraction is the standard workaround).

## Where to put the final files
```
dashboard/bluestock_mf_dashboard.pbix   <- your real Power BI file
dashboard/Dashboard.pdf                 <- real export (replaces the stand-in)
dashboard/page1_industry_overview.png   <- real screenshots (replace stand-ins)
dashboard/page2_fund_performance.png
dashboard/page3_investor_analytics.png
dashboard/page4_sip_market_trends.png
```

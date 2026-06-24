# Bluestock MF Capstone — Data Dictionary

Documents every table in `data/db/bluestock_mf.db`, built from the cleaned
CSVs in `data/processed/` (see `sql/schema.sql` for DDL and
`reports/day2_cleaning_log.txt` for the cleaning rules applied to each
source file).

**Source legend:** AMFI = real AMFI India published data · mfapi.in = real
historical NAV anchor · Simulated = synthetically generated with realistic
parameters (per the project brief's "Note on Data Authenticity") · Derived =
computed by our ETL pipeline, not present in the raw file.

---

## dim_fund
*40 rows · one row per mutual fund scheme · source: `01_fund_master.csv`*

| Column | Type | Business definition | Source |
|---|---|---|---|
| amfi_code | INTEGER (PK) | Unique AMFI scheme identifier. | AMFI |
| fund_house | TEXT | Asset Management Company (AMC) that manages the scheme. | AMFI |
| scheme_name | TEXT | Full official AMFI scheme name, including plan (Regular/Direct) and option (Growth/IDCW). | AMFI |
| category | TEXT | Top-level SEBI category: `Equity` or `Debt`. | AMFI |
| sub_category | TEXT | SEBI sub-category, e.g. `Large Cap`, `Mid Cap`, `Small Cap`, `ELSS`, `Liquid`, `Gilt`, `Index`. | AMFI |
| plan | TEXT | `Regular` (via distributor, higher expense ratio) or `Direct` (lower expense ratio). | AMFI |
| launch_date | TEXT | Scheme inception date, `YYYY-MM-DD`. | AMFI |
| benchmark | TEXT | Official benchmark index the scheme is measured against (e.g. `NIFTY 100 TRI`). | AMFI |
| expense_ratio_pct | REAL | Annual expense ratio charged to investors, in %. Sanity range 0.1%–2.5%. | AMFI |
| exit_load_pct | REAL | Exit load % charged on early redemption (0 for Liquid/Index funds). | AMFI |
| min_sip_amount | REAL | Minimum SIP installment amount (₹). | AMFI |
| min_lumpsum_amount | REAL | Minimum lumpsum investment amount (₹). | AMFI |
| fund_manager | TEXT | Name of the scheme's primary fund manager. | AMFI |
| risk_category | TEXT | SEBI riskometer grade: `Low`, `Moderate`, `Moderately High`, `High`, `Very High`. | AMFI |
| sebi_category_code | TEXT | Project-internal shorthand (ECxx = Equity Category, DCxx = Debt Category, EIxx = Equity Index). **Not** an official AMFI/SEBI code format. | Project-internal |

**Cleaning applied:** the raw `01_fund_master.csv` had 959 fully-blank rows
and 11 junk trailing `Unnamed` columns (stray commas in the source header).
Both were dropped; 40 real rows survive, matching the brief.

---

## dim_date
*1,608 rows · one row per calendar day, 2022-01-03 → 2026-05-29 · Derived*

| Column | Type | Business definition |
|---|---|---|
| date_id | TEXT (PK) | Calendar date, `YYYY-MM-DD`. Joined against by every fact table's date column. |
| year | INTEGER | Calendar year. |
| month | INTEGER | Calendar month (1–12). |
| quarter | INTEGER | Calendar quarter (1–4). |
| day_name | TEXT | Day of week name (`Monday` … `Sunday`). |
| is_weekday | INTEGER | 1 = Monday–Friday, 0 = Saturday/Sunday. Does **not** account for stock-market holidays — see fact_nav.is_actual_trading_day for that. |

---

## fact_nav
*64,320 rows · one row per (fund, calendar day) · source: `02_nav_history.csv`*

| Column | Type | Business definition | Source |
|---|---|---|---|
| amfi_code | INTEGER (PK, FK → dim_fund) | Scheme this NAV belongs to. | AMFI |
| date | TEXT (PK, FK → dim_date) | Calendar date, `YYYY-MM-DD`. | AMFI |
| nav | REAL | Net Asset Value per unit, ₹. On non-trading days this is forward-filled from the last published value. | mfapi.in anchor + simulated path |
| daily_return_pct | REAL | `(nav_t / nav_t-1 - 1) * 100`, computed on the continuous daily series. 0% on forward-filled (non-trading) days, since NAV is unchanged. | Derived |
| is_actual_trading_day | INTEGER | 1 = NAV genuinely published that day (present in the raw file); 0 = weekend/holiday, NAV forward-filled from the prior trading day. | Derived |

**Cleaning applied:** validated NAV > 0, removed exact and (amfi_code, date)
duplicate rows, reindexed every fund onto a continuous calendar-day range
and forward-filled gaps (18,320 weekend/holiday rows added across 40 funds;
46,000 raw rows → 64,320 continuous rows).

---

## fact_transactions
*32,778 rows · one row per investor transaction · source: `08_investor_transactions.csv`*

| Column | Type | Business definition | Source |
|---|---|---|---|
| tx_id | INTEGER (PK) | Surrogate transaction ID, generated during cleaning (raw file has no natural key). | Derived |
| investor_id | TEXT | Anonymised investor identifier, `INV000001`–`INV005000`. | Simulated |
| transaction_date | TEXT (FK → dim_date) | Date the transaction was processed, `YYYY-MM-DD`. | Simulated |
| amfi_code | INTEGER (FK → dim_fund) | Fund the transaction was made in. | Simulated |
| transaction_type | TEXT | `SIP`, `Lumpsum`, or `Redemption`. | Simulated |
| amount_inr | INTEGER | Transaction amount in ₹. Validated > 0. | Simulated |
| state | TEXT | Investor's state (12 Indian states covered). | Simulated, realistic distribution |
| city | TEXT | Investor's city. | Simulated, realistic distribution |
| city_tier | TEXT | `T30` (AMFI Top-30 cities) or `B30` (Beyond Top-30). | Simulated |
| age_group | TEXT | `18-25`, `26-35`, `36-45`, `46-55`, `56+`. | Simulated |
| gender | TEXT | `Male` or `Female`. | Simulated |
| annual_income_lakh | REAL | Investor's annual income, ₹ lakh. | Simulated |
| payment_mode | TEXT | `UPI`, `Net Banking`, `Mandate`, or `Cheque`. | Simulated |
| kyc_status | TEXT | `Verified` (~92% of investors) or `Pending` (~8%). | Simulated |

**Cleaning applied:** standardised `transaction_type` casing, validated
`amount_inr` > 0, validated `kyc_status` against the 2-value enum, checked
(but found clean) `city_tier`/`gender`/`payment_mode` enums, removed exact
duplicates, generated the surrogate `tx_id`.

---

## fact_performance
*40 rows · one row per scheme · source: `07_scheme_performance.csv`*

| Column | Type | Business definition | Source |
|---|---|---|---|
| amfi_code | INTEGER (PK, FK → dim_fund) | Scheme these metrics describe. | Computed from NAV history |
| as_of_date | TEXT (FK → dim_date) | Snapshot date the metrics are valid as of. **Assumption**: set to the most recent date in `fact_nav` (2026-05-29), since the raw file had no explicit as-of date. | Derived assumption |
| scheme_name, fund_house, category, plan | TEXT | Denormalised copies from dim_fund, kept here for convenient single-table reporting. | AMFI |
| return_1yr_pct | REAL | Trailing 1-year absolute return, %. | Computed |
| return_3yr_pct | REAL | Trailing 3-year CAGR, %. | Computed |
| return_5yr_pct | REAL | Trailing 5-year CAGR, %. | Computed |
| benchmark_3yr_pct | REAL | Benchmark index's 3-year CAGR, for comparison. | Computed |
| alpha | REAL | `return_3yr_pct - benchmark_3yr_pct` — excess return over benchmark. | Computed |
| beta | REAL | Sensitivity to market moves (1.0 = moves with the market). | Computed |
| sharpe_ratio | REAL | Risk-adjusted return using total volatility; Rf = 6.5% (RBI repo rate proxy). >1 is considered good. | Computed |
| sortino_ratio | REAL | Like Sharpe, but penalises only downside volatility. | Computed |
| std_dev_ann_pct | REAL | Annualised standard deviation of daily returns, %. | Computed |
| max_drawdown_pct | REAL | Worst peak-to-trough decline, % (negative value). | Computed |
| aum_crore | REAL | Scheme-level AUM, ₹ crore. | AMFI |
| expense_ratio_pct | REAL | Annual expense ratio, %. Duplicated from dim_fund for convenience. | AMFI |
| morningstar_rating | INTEGER | 1–5 star rating (simulated, derived from Sharpe ratio). | Simulated |
| risk_grade | TEXT | SEBI riskometer grade — same domain as dim_fund.risk_category. | AMFI |

**Cleaning applied:** coerced all return/risk columns to numeric, ran 6
anomaly checks (negative Sharpe, positive max-drawdown, non-positive std
dev, beta outside [0,2], rating outside [1,5], expense ratio outside
[0.1%, 2.5%]) — all passed clean on this dataset, so no rows were dropped.

---

## fact_aum
*90 rows · one row per (fund house, quarter) · source: `03_aum_by_fund_house.csv`*

| Column | Type | Business definition | Source |
|---|---|---|---|
| fund_house | TEXT (PK) | Asset Management Company. | AMFI |
| date | TEXT (PK, FK → dim_date) | Quarter-end reporting date, `YYYY-MM-DD`. | AMFI |
| aum_lakh_crore | REAL | Total AUM, ₹ lakh crore. | AMFI quarterly reports |
| aum_crore | REAL | Total AUM, ₹ crore (`aum_lakh_crore * 100,000`). | AMFI quarterly reports |
| num_schemes | INTEGER | Number of schemes the AMC offers as of that quarter. | AMFI |

---

## fact_sip_industry
*48 rows · one row per month · source: `04_monthly_sip_inflows.csv`*

| Column | Type | Business definition | Source |
|---|---|---|---|
| month | TEXT (PK) | `YYYY-MM`. | AMFI Monthly Note |
| sip_inflow_crore | REAL | Total industry-wide SIP inflow that month, ₹ crore. | AMFI Monthly Note |
| active_sip_accounts_crore | REAL | Number of actively contributing SIP accounts, crore. | AMFI Monthly Note |
| new_sip_accounts_lakh | REAL | New SIP registrations that month, lakh accounts. | AMFI Monthly Note |
| sip_aum_lakh_crore | REAL | Total SIP-driven AUM, ₹ lakh crore. | AMFI Monthly Note |
| yoy_growth_pct | REAL | Year-on-year % growth in `sip_inflow_crore`. Null for the first 12 months (no year-ago value to compare against) — verified by recomputation, 0 mismatches. | AMFI Monthly Note |

---

## fact_category_inflow
*144 rows · one row per (month, category) · source: `05_category_inflows.csv`*

| Column | Type | Business definition | Source |
|---|---|---|---|
| month | TEXT (PK) | `YYYY-MM`, FY 2024-25. | AMFI |
| category | TEXT (PK) | Fund category (Large Cap, Mid Cap, Small Cap, ELSS, Liquid, etc.). | AMFI |
| net_inflow_crore | REAL | Net inflow (can be negative = net outflow) for that category that month, ₹ crore. | AMFI |

---

## fact_folio
*21 rows · one row per reporting month · source: `06_industry_folio_count.csv`*

| Column | Type | Business definition | Source |
|---|---|---|---|
| month | TEXT (PK) | `YYYY-MM`. Reporting cadence is irregular (not strictly quarterly) — reflects actual AMFI publication dates, not a data error. | AMFI |
| total_folios_crore | REAL | Total mutual fund folios (investor accounts), crore. | AMFI published milestones |
| equity_folios_crore | REAL | Folios in equity schemes, crore. | AMFI |
| debt_folios_crore | REAL | Folios in debt schemes, crore. | AMFI |
| hybrid_folios_crore | REAL | Folios in hybrid schemes, crore. | AMFI |
| others_folios_crore | REAL | Folios in other scheme types, crore. | AMFI |

---

## fact_portfolio
*322 rows · one row per (fund, stock holding) · source: `09_portfolio_holdings.csv`*

| Column | Type | Business definition | Source |
|---|---|---|---|
| amfi_code | INTEGER (FK → dim_fund) | Equity fund this holding belongs to (debt/liquid funds have no rows here). | Factsheet-derived |
| stock_symbol | TEXT | NSE/BSE ticker symbol. | Factsheet-derived |
| stock_name | TEXT | Full company name. | Factsheet-derived |
| sector | TEXT | GICS-style sector classification. | Factsheet-derived |
| weight_pct | REAL | % of the fund's portfolio held in this stock as of `portfolio_date`. Every fund's holdings sum to ~100% (99.98–100.02%, rounding noise only) — this is a full portfolio disclosure, not a top-N excerpt. | Factsheet-derived |
| market_value_cr | REAL | Market value of the holding, ₹ crore. | Factsheet-derived |
| current_price_inr | REAL | Stock price at `portfolio_date`, ₹. | Factsheet-derived |
| portfolio_date | TEXT (PK) | Disclosure date — currently a single snapshot, 2025-12-31, for all funds. | Factsheet-derived |

---

## fact_benchmark
*8,050 rows · one row per (date, index) · source: `10_benchmark_indices.csv`*

| Column | Type | Business definition | Source |
|---|---|---|---|
| date | TEXT (PK, FK → dim_date) | Trading date, `YYYY-MM-DD`. | NSE/BSE |
| index_name | TEXT (PK) | One of: `NIFTY50`, `NIFTY100`, `NIFTY500`, `NIFTY_MIDCAP150`, `BSE_SMALLCAP`, `CRISIL_LIQUID`, `CRISIL_GILT`. | NSE/BSE |
| close_value | REAL | Index closing value that day. | NSE/BSE |

**Note:** unlike `fact_nav`, this table was **not** reindexed/forward-filled
onto a continuous calendar — it retains only the original published trading
days. Join carefully against `fact_nav` if comparing day-for-day.

---

## Known caveats (carried forward from Day 1 & Day 2 findings)

1. The 6 example scheme codes used in the Day 1 live-fetch exercise
   (`live_nav_fetch.py`) do **not** correspond to their stated fund names on
   the real mfapi.in API — this does not affect any table above, which all
   derive from the project's own internally-consistent 40-scheme dataset.
2. `fact_performance.as_of_date` is an assumption (latest NAV date), not a
   field present in the source CSV — flag this if exact reporting-date
   precision matters for downstream analysis.
3. `fact_folio`'s monthly cadence is irregular by design (real AMFI
   publication dates), not a gap to be filled.

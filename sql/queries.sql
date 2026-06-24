-- ============================================================================
-- Bluestock Fintech — Mutual Fund Analytics Capstone
-- Day 2, Task 6: 10 analytical SQL queries
-- Run against data/db/bluestock_mf.db (built by scripts/load_to_sqlite.py)
-- Verified to execute cleanly by scripts/run_queries.py
-- ============================================================================


-- Query 1: Top 5 funds by AUM (scheme-level)
-- ----------------------------------------------------------------------------
SELECT f.amfi_code, f.scheme_name, f.fund_house, p.aum_crore
FROM fact_performance p
JOIN dim_fund f ON f.amfi_code = p.amfi_code
ORDER BY p.aum_crore DESC
LIMIT 5;


-- Query 2: Average NAV per month, per scheme (showing one example scheme;
-- drop the WHERE to get every scheme)
-- ----------------------------------------------------------------------------
SELECT n.amfi_code, f.scheme_name, strftime('%Y-%m', n.date) AS year_month,
       ROUND(AVG(n.nav), 4) AS avg_nav
FROM fact_nav n
JOIN dim_fund f ON f.amfi_code = n.amfi_code
WHERE n.amfi_code = 119551
GROUP BY n.amfi_code, year_month
ORDER BY year_month;


-- Query 3: SIP inflow YoY growth trend (industry-wide, monthly)
-- ----------------------------------------------------------------------------
SELECT month, sip_inflow_crore, active_sip_accounts_crore, yoy_growth_pct
FROM fact_sip_industry
ORDER BY month;


-- Query 4: Transaction count & total amount by state
-- ----------------------------------------------------------------------------
SELECT state,
       COUNT(*) AS num_transactions,
       SUM(amount_inr) AS total_amount_inr,
       ROUND(AVG(amount_inr), 2) AS avg_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC;


-- Query 5: Funds with expense_ratio < 1%
-- ----------------------------------------------------------------------------
SELECT amfi_code, fund_house, scheme_name, category, expense_ratio_pct
FROM dim_fund
WHERE expense_ratio_pct < 1.0
ORDER BY expense_ratio_pct ASC;


-- Query 6: Top 5 fund houses by most recent quarter's AUM
-- ----------------------------------------------------------------------------
SELECT fund_house, date, aum_crore, num_schemes
FROM fact_aum
WHERE date = (SELECT MAX(date) FROM fact_aum)
ORDER BY aum_crore DESC
LIMIT 5;


-- Query 7: Category-wise net inflow leaderboard (FY 2024-25 total)
-- ----------------------------------------------------------------------------
SELECT category, SUM(net_inflow_crore) AS total_net_inflow_crore
FROM fact_category_inflow
WHERE month BETWEEN '2024-04' AND '2025-03'
GROUP BY category
ORDER BY total_net_inflow_crore DESC;


-- Query 8: Average SIP amount by investor age group
-- ----------------------------------------------------------------------------
SELECT age_group,
       COUNT(*) AS num_sips,
       ROUND(AVG(amount_inr), 2) AS avg_sip_amount_inr
FROM fact_transactions
WHERE transaction_type = 'SIP'
GROUP BY age_group
ORDER BY age_group;


-- Query 9: Top 3 funds by Sharpe ratio within each risk grade
-- ----------------------------------------------------------------------------
SELECT *
FROM (
    SELECT p.amfi_code, p.scheme_name, p.risk_grade, p.sharpe_ratio,
           RANK() OVER (PARTITION BY p.risk_grade ORDER BY p.sharpe_ratio DESC) AS rank_in_grade
    FROM fact_performance p
) ranked
WHERE rank_in_grade <= 3
ORDER BY risk_grade, rank_in_grade;


-- Query 10: Funds outperforming their 3-year benchmark (positive alpha),
-- ranked best to worst
-- ----------------------------------------------------------------------------
SELECT amfi_code, scheme_name, fund_house, return_3yr_pct, benchmark_3yr_pct, alpha
FROM fact_performance
WHERE alpha > 0
ORDER BY alpha DESC;

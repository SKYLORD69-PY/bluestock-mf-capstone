-- ============================================================================
-- Bluestock Fintech — Mutual Fund Analytics Capstone
-- Day 2, Task 4: SQLite star schema
-- ============================================================================
-- Naming convention: date FK columns keep their natural source-file name
-- (date / transaction_date / portfolio_date / as_of_date) and reference
-- dim_date(date_id) - the column name doesn't need to match the referenced
-- PK name in SQL, only the data type/values do.
--
-- This file is executed by scripts/load_to_sqlite.py to build
-- data/db/bluestock_mf.db from scratch every time it's re-run.
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- CORE STAR SCHEMA (explicitly requested: dim_fund, dim_date, fact_nav,
-- fact_transactions, fact_performance, fact_aum)
-- ----------------------------------------------------------------------------

DROP TABLE IF EXISTS dim_fund;
CREATE TABLE dim_fund (
    amfi_code           INTEGER PRIMARY KEY,
    fund_house          TEXT NOT NULL,
    scheme_name         TEXT NOT NULL,
    category            TEXT,
    sub_category        TEXT,
    plan                TEXT,
    launch_date         TEXT,            -- 'YYYY-MM-DD'
    benchmark           TEXT,
    expense_ratio_pct   REAL,
    exit_load_pct       REAL,
    min_sip_amount      REAL,
    min_lumpsum_amount  REAL,
    fund_manager        TEXT,
    risk_category       TEXT,
    sebi_category_code  TEXT
);

DROP TABLE IF EXISTS dim_date;
CREATE TABLE dim_date (
    date_id     TEXT PRIMARY KEY,   -- 'YYYY-MM-DD'
    year        INTEGER NOT NULL,
    month       INTEGER NOT NULL,
    quarter     INTEGER NOT NULL,
    day_name    TEXT NOT NULL,
    is_weekday  INTEGER NOT NULL CHECK (is_weekday IN (0, 1))
);

DROP TABLE IF EXISTS fact_nav;
CREATE TABLE fact_nav (
    amfi_code              INTEGER NOT NULL,
    date                    TEXT NOT NULL,
    nav                     REAL NOT NULL CHECK (nav > 0),
    daily_return_pct        REAL,
    is_actual_trading_day   INTEGER NOT NULL CHECK (is_actual_trading_day IN (0, 1)),
    PRIMARY KEY (amfi_code, date),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date) REFERENCES dim_date(date_id)
);

DROP TABLE IF EXISTS fact_transactions;
CREATE TABLE fact_transactions (
    tx_id               INTEGER PRIMARY KEY,
    investor_id         TEXT NOT NULL,
    transaction_date    TEXT NOT NULL,
    amfi_code           INTEGER NOT NULL,
    transaction_type    TEXT NOT NULL CHECK (transaction_type IN ('SIP', 'Lumpsum', 'Redemption')),
    amount_inr          INTEGER NOT NULL CHECK (amount_inr > 0),
    state               TEXT,
    city                TEXT,
    city_tier           TEXT CHECK (city_tier IN ('T30', 'B30')),
    age_group           TEXT,
    gender              TEXT,
    annual_income_lakh  REAL,
    payment_mode        TEXT,
    kyc_status          TEXT CHECK (kyc_status IN ('Verified', 'Pending')),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (transaction_date) REFERENCES dim_date(date_id)
);

DROP TABLE IF EXISTS fact_performance;
CREATE TABLE fact_performance (
    amfi_code           INTEGER PRIMARY KEY,
    as_of_date          TEXT NOT NULL,   -- snapshot date these metrics were computed as-of
    scheme_name         TEXT,
    fund_house          TEXT,
    category            TEXT,
    plan                TEXT,
    return_1yr_pct      REAL,
    return_3yr_pct      REAL,
    return_5yr_pct      REAL,
    benchmark_3yr_pct   REAL,
    alpha               REAL,
    beta                REAL,
    sharpe_ratio        REAL,
    sortino_ratio       REAL,
    std_dev_ann_pct     REAL,
    max_drawdown_pct    REAL,
    aum_crore           REAL,
    expense_ratio_pct   REAL,
    morningstar_rating  INTEGER CHECK (morningstar_rating BETWEEN 1 AND 5),
    risk_grade          TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (as_of_date) REFERENCES dim_date(date_id)
);

DROP TABLE IF EXISTS fact_aum;
CREATE TABLE fact_aum (
    fund_house      TEXT NOT NULL,
    date            TEXT NOT NULL,
    aum_lakh_crore  REAL,
    aum_crore       REAL NOT NULL CHECK (aum_crore > 0),
    num_schemes     INTEGER,
    PRIMARY KEY (fund_house, date),
    FOREIGN KEY (date) REFERENCES dim_date(date_id)
);

-- ----------------------------------------------------------------------------
-- EXTENSION TABLES — not explicitly named in Task 4, added so Task 5's
-- "load ALL cleaned datasets" requirement covers the remaining 4 provided
-- CSVs (04, 05, 06, 09) too. Skip these if you only need the 6 core tables.
-- ----------------------------------------------------------------------------

DROP TABLE IF EXISTS fact_sip_industry;
CREATE TABLE fact_sip_industry (
    month                       TEXT PRIMARY KEY,   -- 'YYYY-MM'
    sip_inflow_crore            REAL NOT NULL,
    active_sip_accounts_crore  REAL,
    new_sip_accounts_lakh      REAL,
    sip_aum_lakh_crore          REAL,
    yoy_growth_pct              REAL
);

DROP TABLE IF EXISTS fact_category_inflow;
CREATE TABLE fact_category_inflow (
    month             TEXT NOT NULL,
    category          TEXT NOT NULL,
    net_inflow_crore  REAL,
    PRIMARY KEY (month, category)
);

DROP TABLE IF EXISTS fact_folio;
CREATE TABLE fact_folio (
    month                 TEXT PRIMARY KEY,
    total_folios_crore    REAL,
    equity_folios_crore   REAL,
    debt_folios_crore     REAL,
    hybrid_folios_crore   REAL,
    others_folios_crore   REAL
);

DROP TABLE IF EXISTS fact_portfolio;
CREATE TABLE fact_portfolio (
    amfi_code           INTEGER NOT NULL,
    stock_symbol        TEXT NOT NULL,
    stock_name          TEXT,
    sector              TEXT,
    weight_pct          REAL,
    market_value_cr     REAL,
    current_price_inr   REAL,
    portfolio_date      TEXT NOT NULL,
    PRIMARY KEY (amfi_code, stock_symbol, portfolio_date),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

DROP TABLE IF EXISTS fact_benchmark;
CREATE TABLE fact_benchmark (
    date         TEXT NOT NULL,
    index_name   TEXT NOT NULL,
    close_value  REAL NOT NULL CHECK (close_value > 0),
    PRIMARY KEY (date, index_name),
    FOREIGN KEY (date) REFERENCES dim_date(date_id)
);

-- ----------------------------------------------------------------------------
-- Helpful indexes (amfi_code + date are the most common filter/join columns)
-- ----------------------------------------------------------------------------
CREATE INDEX idx_fact_nav_date ON fact_nav(date);
CREATE INDEX idx_fact_nav_amfi ON fact_nav(amfi_code);
CREATE INDEX idx_fact_tx_date ON fact_transactions(transaction_date);
CREATE INDEX idx_fact_tx_amfi ON fact_transactions(amfi_code);
CREATE INDEX idx_fact_tx_state ON fact_transactions(state);
CREATE INDEX idx_fact_portfolio_amfi ON fact_portfolio(amfi_code);

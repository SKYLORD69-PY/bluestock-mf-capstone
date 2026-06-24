"""
run_queries.py
==============
Bluestock Fintech - Mutual Fund Analytics Capstone
Day 2: Executes every query in sql/queries.sql against data/db/bluestock_mf.db
and prints a sample of results - a sanity check that queries.sql actually
runs cleanly, not just that it parses.

Run from the project root:
    python scripts/run_queries.py
"""

import re
import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "db" / "bluestock_mf.db"
QUERIES_PATH = PROJECT_ROOT / "sql" / "queries.sql"


def split_queries(sql_text: str) -> list[tuple[str, str]]:
    """Split queries.sql into (title, query) pairs using the '-- Query N:' markers."""
    blocks = re.split(r"\n(?=-- Query \d+:)", sql_text)
    out = []
    for block in blocks:
        m = re.match(r"-- (Query \d+: .+)", block)
        if not m:
            continue
        title = m.group(1).strip()
        # strip comment lines, keep the SQL
        sql_lines = [l for l in block.splitlines() if not l.strip().startswith("--")]
        query = "\n".join(sql_lines).strip().rstrip(";")
        if query:
            out.append((title, query))
    return out


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    queries = split_queries(QUERIES_PATH.read_text())
    print(f"Found {len(queries)} queries in {QUERIES_PATH.relative_to(PROJECT_ROOT)}\n")

    for title, query in queries:
        print("=" * 70)
        print(title)
        print("=" * 70)
        try:
            df = pd.read_sql_query(query, conn)
            print(f"  -> {len(df)} row(s) returned")
            print(df.head(5).to_string(index=False))
        except Exception as exc:
            print(f"  [FAILED] {exc}")
        print()

    conn.close()


if __name__ == "__main__":
    main()

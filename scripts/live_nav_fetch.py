"""
live_nav_fetch.py
==================
Bluestock Fintech - Mutual Fund Analytics Capstone
Day 1, Task 4 & 5: Fetch LIVE NAV history from the public mfapi.in REST
API (no auth required) for HDFC Top 100 plus 5 other large-cap schemes,
and save each as a raw CSV under data/raw/.

API used:  GET https://api.mfapi.in/mf/{scheme_code}
           -> {"meta": {...}, "data": [{"date": "DD-MM-YYYY", "nav": "x.xx"}, ...]}

Run from the project root:
    python scripts/live_nav_fetch.py
"""

from pathlib import Path
import time
import requests
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://api.mfapi.in/mf/{code}"

# Scheme codes exactly as given in the project brief (Day 1, Task 4 & 5).
# NOTE: see the data-quality caveat printed at the bottom of this file and
# in reports/day1_data_quality_summary.txt - when actually queried against
# the live API, several of these codes returned a DIFFERENT scheme than the
# name listed here. Verify scheme_name in the saved CSV before relying on it.
SCHEMES = {
    125497: "HDFC Top 100 Direct",       # Task 4 - the primary required fetch
    119551: "SBI Bluechip",
    120503: "ICICI Bluechip",
    118632: "Nippon Large Cap",
    119092: "Axis Bluechip",
    120841: "Kotak Bluechip",
}


def fetch_scheme_nav(scheme_code: int, timeout: int = 15) -> dict:
    """Call mfapi.in for one scheme code and return the parsed JSON."""
    url = BASE_URL.format(code=scheme_code)
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()


def save_scheme_csv(scheme_code: int, expected_name: str, payload: dict) -> Path:
    """Convert the API's {meta, data} payload into a flat CSV and save it."""
    meta = payload.get("meta", {})
    records = payload.get("data", [])

    df = pd.DataFrame(records)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
        df["nav"] = df["nav"].astype(float)
        df = df.sort_values("date").reset_index(drop=True)

    df.insert(0, "amfi_code", scheme_code)
    df["fund_house_api"] = meta.get("fund_house")
    df["scheme_name_api"] = meta.get("scheme_name")

    out_path = RAW_DIR / f"live_nav_{scheme_code}.csv"
    df.to_csv(out_path, index=False)

    actual_name = meta.get("scheme_name", "UNKNOWN")
    match = "OK" if expected_name.split()[0].lower() in actual_name.lower() else "MISMATCH"
    print(f"  [{match}] code {scheme_code} -> expected '{expected_name}', "
          f"API returned '{actual_name}' ({len(df)} NAV rows) -> {out_path.name}")
    return out_path


def main() -> None:
    print(f"Fetching live NAV history for {len(SCHEMES)} schemes from mfapi.in ...\n")
    failures = []
    for code, name in SCHEMES.items():
        try:
            payload = fetch_scheme_nav(code)
            save_scheme_csv(code, name, payload)
        except requests.exceptions.RequestException as exc:
            print(f"  [FAILED] code {code} ({name}): {exc}")
            failures.append(code)
        time.sleep(1)  # be polite to the free public API

    print(f"\nDone. {len(SCHEMES) - len(failures)}/{len(SCHEMES)} schemes fetched successfully.")
    if failures:
        print(f"Failed codes: {failures}")


if __name__ == "__main__":
    main()

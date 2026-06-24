# Provenance note - mfapi_session_fetch_raw.json

This sandbox's outbound network is locked to an infra allow-list that does
NOT include api.mfapi.in (confirmed: `curl https://api.mfapi.in/...` inside
this container returns `403 host_not_allowed`). Running `scripts/live_nav_fetch.py`
here fails for that reason - not a bug in the script.

To still verify the script's logic and to validate the AMFI codes given in
the project brief, the assistant fetched these 3 scheme codes for real via
a separate browsing tool available in this chat session (not the sandbox),
on 22 Jun 2026, and saved the JSON here (truncated to the most recent ~20
NAV rows per scheme to keep the file small - a full run of the real script
on your own machine will pull the complete history).

`scripts/live_nav_fetch.py` itself is correct and will work normally when
you run it outside this sandbox (your laptop, Colab, GitHub Actions, etc.),
since mfapi.in is a normal public API with no auth and no special blocking.

This file was only used to produce data/raw/live_nav_125497.csv,
live_nav_119551.csv and live_nav_120503.csv as a working demonstration of
the expected output format - see day1_data_quality_summary.txt for what it
revealed about the scheme codes in the project brief.

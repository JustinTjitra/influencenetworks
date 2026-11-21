# T27: Timeline main-test flag matches the registered summary

## Goal
The firm page and the sector page must say the same thing about whether an event is in
the main test. Today they do not: the firm page's timeline marks 8 events "yes", the
sector page marks 2.

## Read first
- `CLAUDE.md`
- `src/influence/app/timeline.py`, `src/influence/app/sector.py`
- `src/influence/connections/build_measures.py` (read only: where
  `connection_event_summary.csv` gets its `enough_clusters` and `main_test` columns)
- `data/processed/connection_event_summary.csv` (read only)

## Files you may create or edit
- `src/influence/app/timeline.py`
- `tests/test_app_timeline.py`

## Specification
- Background: `eventset.main_test_subset` is the event-level rule (not anticipated, not
  confounded, signed). The registered summary file's `main_test` also requires
  `enough_clusters`. The timeline uses the first, the sector page the second.
- In `timeline()`, replace the single `main_test` column by two columns, in this order
  and in the same position: `event_rule` ("yes"/"no": the event-level rule, from
  `eventset.main_test_subset` as now) and `main_test` ("yes"/"no": the `main_test`
  column of `data/processed/connection_event_summary.csv` for that event).
- Read the summary file once per call through a small helper with a `summary_path`
  argument that defaults to the real file. An event missing from the summary raises
  `KeyError` naming the event; it is not silently marked "no".
- Do not change `sector.py`, `streamlit_app.py` or any other file. The firm page shows
  whatever columns the timeline returns.
- Tests on the real data: for BBRI, `main_test == "yes"` exactly for the events whose
  summary row has `main_test == 1`; every row with `main_test == "yes"` also has
  `event_rule == "yes"`; at least one row has `event_rule == "yes"` and
  `main_test == "no"`; for each event in BBRI's timeline, `main_test` equals the value
  `sector.event_table(bundle, "bank")` shows for the same event; a summary file written
  to `tmp_path` that lacks an event raises `KeyError`. Update the existing tests that
  assert on `main_test`.

## Acceptance
`pytest -q tests/test_app_timeline.py tests/test_app_firm_page.py tests/test_app_sector.py`

## Out of scope
Changing the registered rule or the summary file, any price or results data, Streamlit
layout changes.

# T17: Monitor event timeline table

## Goal
For one firm, the list of registered events that apply to it, with what the firm's
connection measure was at each. Return columns for abnormal returns exist but stay
empty until the owner has run the event study.

## Read first
- `CLAUDE.md` (hard rule 1: no prices)
- `docs/DESIGN.md` section 7, "Event timeline"
- `src/influence/app/data.py`
- `data/events/events.csv` (columns), `data/processed/connection_measures.parquet`
  (columns, via pandas)

## Files you may create or edit
- `src/influence/app/timeline.py` (new)
- `tests/test_app_timeline.py` (new)

## Specification
- `timeline(bundle, ticker, results_dir=None) -> DataFrame`, one row per event whose
  sample includes the firm (`in_event_sample` in the measures table), ordered by date:
  `date, event_id, description, type, expected_sign, tested_measure, firm_value`
  (the firm's `tested_value`), `firm_connected` ("yes"/"no" from `tested_binary`),
  `main_test` ("yes"/"no": not anticipated, not confounded, signed), `source_url_1`,
  `source_url_2`, `car` and `sector_median_car`.
- `car` and `sector_median_car` are NaN unless `results_dir/cars.csv` exists; then use
  the market-model `[-1,+1]` CAR for the firm and the median over firms in the same
  `sector_bucket` for that event. Default `results_dir` is `data/processed/results`.
  Never read `data/processed/results_synthetic` here.
- `has_results(results_dir=None) -> bool`.
- Tests on the real data: BBRI has rows for the Danantara events with
  `firm_connected == "yes"`; a palm ticker has no bank-sector event; with no results
  directory `car` is all NaN; with a small fake `cars.csv` written to `tmp_path` the
  CAR and the sector median are filled correctly.

## Acceptance
`pytest -q tests/test_app_timeline.py`

## Out of scope
Computing returns, reading prices, Streamlit code.

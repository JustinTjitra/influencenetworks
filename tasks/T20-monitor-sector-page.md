# T20: Monitor sector page

## Goal
The Streamlit page that compares firms within a sector.

## Read first
- `CLAUDE.md` (hard rules 1 and 4)
- `docs/DESIGN.md` section 7, "Sector page"
- `src/influence/app/streamlit_app.py`, `data.py`, `exposure.py`

## Files you may create or edit
- `src/influence/app/sector.py` (new: pure functions)
- `src/influence/app/pages/1_Sector.py` (new: Streamlit page)
- `tests/test_app_sector.py` (new)

## Specification
- `sector.measures_table(bundle, sector, on) -> DataFrame`: one row per firm in the
  sector with the seven measures (computed on that date) and `n_board_known`.
- `sector.event_table(bundle, sector) -> DataFrame`: events whose sample includes the
  sector, with the number of connected firms and whether the event is in the main test,
  read from `data/processed/connection_event_summary.csv`.
- `sector.stacked_results(results_dir=None) -> DataFrame | None`: rows of
  `data/processed/results/stacked.csv` for the primary window and 0/1 connection, or
  None if the file does not exist. Never read `results_synthetic`.
- Page: sector selector, date slider, the measures table, the event table, and either
  the stacked results or "Results appear here after the event study has been run."
  The page calls `auth.require_password()` first. Same footer and language rules as T19.
- Tests on the real data: the bank table has 12 rows and the five state banks have
  `state_own` >= 0.5 on 2025-06-30; the palm event table lists the export-ban event;
  `stacked_results` returns None with no results directory.

## Acceptance
`pytest -q tests/test_app_sector.py`

## Out of scope
Deployment, charts of returns, a composite score.

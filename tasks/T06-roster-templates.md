# T06: Board roster CSV templates and validator

## Goal
A fixed, checked format for board rosters transcribed from annual reports, so that
extractions for 34 firms are uniform and errors are caught before they reach the graph.

## Read first
- `CLAUDE.md`
- `data/primary/btn_ar2025_edges.csv`, `data/primary/btn_ar2025_nodes.csv` and
  `data/primary/btn_ar2025_check.md` (the one finished example; read only)
- `src/influence/schema.py` (edge and node types; read only)

## Files you may create or edit
- `src/influence/intake/__init__.py` (create with a one-line docstring if missing)
- `src/influence/intake/rosters.py` (new)
- `tests/test_intake_rosters.py` (new)

## Specification
- A roster file is `data/intake/rosters/<doc_id>.csv` with columns:
  `doc_id, ticker, organ, person_name, role, start_date, end_date, page, appointed_by,
  note, government_post, government_body, post_start, post_end, post_page`.
  `organ` is `commissioners` or `directors`. Dates are `YYYY`, `YYYY-MM` or `YYYY-MM-DD`,
  or empty. `page` and `post_page` are positive integers (`post_page` empty when no post).
- `template(doc_id, ticker) -> str` returns the header line plus two commented example
  rows starting with `#`.
- `validate(df, tickers) -> list[str]`: required fields present; organ valid; ticker
  known; dates well formed and end not before start; page numbers positive; a
  `government_post` requires `government_body` and `post_page`; no duplicate
  (person_name, organ, start_date); names carry no leading or trailing spaces.
- `person_id(name) -> str`: `p_` plus the lower-cased name with every run of
  non-alphanumeric characters replaced by `_`, trimmed. This is only a proposal for a
  reviewer; it must not look up or merge with existing people.
- `to_edges(df) -> DataFrame` with the graph's edge columns (`source_id, target_id,
  type, source_url, source_type, confidence, role, start_date, end_date, pct,
  amount_usd, note`): one `board_seat` row per roster row with
  `source_url = doc:<doc_id>#p<page>`, `source_type = annual_report`,
  `confidence = high`, and `target_id` left as the ticker in a column `ticker` for a
  later mapping step (do not guess node ids). One `held_office` row per government post,
  with `target_id` empty and the body's name in `note` for a reviewer to map.
- `python -m influence.intake.rosters template --doc ID --ticker TICK` prints the
  template; `validate PATH` prints problems and exits 1 if any.
- Tests: template has the right header; each validation rule; `to_edges` on a three-row
  example gives the expected rows and citations.

## Acceptance
`pytest -q tests/test_intake_rosters.py && python -m influence.intake.rosters template --doc bbri_ar_2025 --ticker BBRI | head -3`

## Out of scope
Writing into `data/primary/` or `data/seed/`, mapping names to existing person nodes,
any change to the graph.

# T04: Fundamentals file schema and validator

## Goal
A checked format for `data/mappings/fundamentals.csv`, the hand-collected file of shares
outstanding, assets and liabilities that the event study's controls need.

## Read first
- `CLAUDE.md`
- `src/influence/events/controls.py` (read only: it defines how the file is used)
- `data/mappings/tickers.csv` (the 34 tickers)

## Files you may create or edit
- `src/influence/intake/__init__.py` (new, one-line docstring)
- `src/influence/intake/fundamentals.py` (new)
- `data/mappings/fundamentals.csv` (new: header row only)
- `tests/test_intake_fundamentals.py` (new)

## Specification
- Columns, in order: `ticker, fiscal_year_end, shares_outstanding, total_assets,
  total_liabilities, currency, unit, source_url, note`.
- `validate(df, tickers) -> list[str]` returns one message per problem:
  ticker not in the ticker list; `fiscal_year_end` not `YYYY-MM-DD`; duplicate
  (ticker, fiscal_year_end); non-positive shares or assets; liabilities negative or
  greater than 1.5 x assets; `currency` not `IDR`; `unit` not one of `1`, `1e3`, `1e6`,
  `1e9`; `source_url` neither `http(s)://...` nor `doc:<id>#p<page>`.
- `load(path) -> DataFrame` reads the file, raises `ValueError` listing every problem,
  and returns columns scaled to units of 1 (multiply assets and liabilities by `unit`;
  shares are always in single shares).
- `coverage(df, tickers, years) -> DataFrame` with one row per ticker and a boolean
  column per fiscal year saying whether a row exists.
- `python -m influence.intake.fundamentals` prints the coverage table for fiscal years
  2021 to 2025 and exits 1 if validation fails. With only the header row it prints the
  table with all False and exits 0.
- Tests: an empty file is valid; each rule above is triggered by a bad row; scaling;
  coverage table shape.

## Acceptance
`pytest -q tests/test_intake_fundamentals.py && python -m influence.intake.fundamentals | tail -3`

## Out of scope
Editing `controls.py` or anything under `src/influence/events/`. Filling in real numbers.

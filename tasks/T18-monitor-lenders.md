# T18: Monitor lenders table

## Goal
For a palm oil firm, the banks recorded as financing its group, by year and amount.

## Read first
- `CLAUDE.md`
- `docs/DESIGN.md` section 7, "Lenders"
- `data/primary/forests_finance_edges.csv` (first lines; read only) and
  `src/influence/load_financing.py` (how `role` distinguishes `credit:` from `holding:`)
- `src/influence/app/data.py`

## Files you may create or edit
- `src/influence/app/lenders.py` (new)
- `tests/test_app_lenders.py` (new)

## Specification
- `lenders(bundle, ticker) -> DataFrame`: `finances` edges into the firm's node or into
  any group it is a `member_of_group` of, with columns `bank, year, kind` ("credit" or
  "holding", from the `role` prefix), `detail` (the rest of `role`), `amount_usd_m`
  (amount / 1e6, rounded to 0.1), `source_url`, `confidence`.
- `credit_by_bank(df) -> DataFrame`: credit only, summed per bank, sorted descending.
  Credit and holdings are never added together; assert it in a test.
- `licence_note() -> str`: "Financing data: Forests & Finance, personal-use licence. Not
  for republication without permission from Rainforest Action Network."
- Firms with no financing edges return an empty frame with the same columns.
- Tests on the real data: SMAR (Sinar Mas group) has credit rows from at least two
  banks; BBCA (a bank) returns an empty frame; totals are per kind.

## Acceptance
`pytest -q tests/test_app_lenders.py`

## Out of scope
Streamlit code, charts, changing the financing loader.

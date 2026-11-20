# T16: Monitor exposure profile tables

## Goal
For one firm and one date, the connection measures and, under each number, the sourced
relationships that produce it.

## Read first
- `CLAUDE.md` (hard rule 4)
- `docs/DESIGN.md` section 7, "Exposure profile"
- `src/influence/connections/measures.py` (`compute_all`, `TIE_MEASURES`; read only)
- `src/influence/app/data.py`

## Files you may create or edit
- `src/influence/app/exposure.py` (new)
- `tests/test_app_exposure.py` (new)

## Specification
- `profile(bundle, ticker, on) -> DataFrame` with one row per measure in this order:
  `state_own, board_party, board_office, board_former, board_family, group_conn,
  dist_gov`; columns `measure, label, value, display, n_edges`. `label` is plain
  language ("State shareholding", "Board members with a governing-party role",
  "Board members holding government office", "Board members who left office in the last
  five years", "Board members related to a party chair or minister",
  "Owner holds office or a party role", "Steps to the state or a governing party").
  `display` formats `state_own` as a percentage, counts as integers, `group_conn` as
  "yes"/"no", and an infinite distance as "no path".
- `evidence(bundle, ticker, on, measure) -> DataFrame`: the edges behind that number,
  parsed from `compute_all(...)["evidence"]` strings
  (`source>target:type[start..end]<source_url>`), with columns `from_name, relation,
  to_name, start, end, source_url`. Names come from the graph's node names.
- `data_note(bundle, ticker, on) -> str`: a sentence saying how many board members are
  known for the firm on that date and, if the firm has no complete roster, that a count
  of zero means "none recorded", not "none exist".
- No composite score. The words "risk", "risky", "captured", "corrupt", "favoured",
  "crony" must not appear in this module.
- Tests on the real data: BBTN on 2025-06-30 has `board_office` >= 1 with evidence rows
  whose `source_url` starts with `doc:btn_ar_2025`; BBCA has `state_own` 0 and "no"
  for `group_conn`; evidence rows all have a source; `display` formats as specified.

## Acceptance
`pytest -q tests/test_app_exposure.py`

## Out of scope
Streamlit code, new measures, changing `measures.py`.

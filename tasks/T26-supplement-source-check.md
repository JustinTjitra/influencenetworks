# T26: Source check of the supplement edges

## Goal
An independent check of the edges added in `data/seed/supplement/` against their
sources, written up as a report. The project's rule is that extractions are checked by
someone who did not make them.

## Read first
- `CLAUDE.md` (hard rules 1, 2, 3)
- `data/seed/supplement/listed_entities_edges.csv`, `state_ownership_edges.csv`
  (read only)
- `data/primary/btn_ar2025_check.md` (the format of a check report)

## Files you may create or edit
- `docs/checks/supplement_check_2026-11.md` (new)

## Specification
- For each of the 13 state-ownership edges and each of the 19 listed-entity edges:
  search for the cited source (at most ONE web search per edge, 30 in total) and judge
  from the result whether it supports the holder, the percentage and the dates.
- Report as a table: row, edge, field, value in the file, what the source shows,
  verdict (`ok`, `wrong`, `unsupported`, `could not check`), note. Say for each whether
  you read the page or only a search snippet.
- A final list "Proposed corrections" for every `wrong` or `unsupported`, with the
  replacement value and source. Do NOT edit the CSV files: they are protected.
- Do not search for or report share prices or market reactions. No judgemental wording.

## Acceptance
`test -s docs/checks/supplement_check_2026-11.md && grep -c "|" docs/checks/supplement_check_2026-11.md && python tools/guard.py`

## Out of scope
Changing any data file, checking edges outside `data/seed/supplement/`.

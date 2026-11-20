# T14: Exchange profile parser

## Goal
Turn saved exchange profile responses into two tables: people on boards and shareholders.

## Read first
- `CLAUDE.md`
- `docs/HANDOFF_MODULES.md`, Module B, pipeline step 2
- The sample response the owner saved (path is given in `tasks/log/` when U04 is done)

## Files you may create or edit
- `src/influence/interlocks/parse_profiles.py` (new)
- `tests/test_interlocks_parse.py` (new)
- `tests/fixtures/idx_profile_sample.json` (new: a reduced copy of the real sample with
  at most 3 people and 3 holders; keep the real field names)

## Specification
Blocked until a real sample exists: the field names must come from the sample, not from
guesswork. When unblocked, the planner rewrites this section with the exact fields.
Outputs: `people_raw` (`record_id, name, role, organ, company, as_of, source_file`) and
`holders_raw` (`holder_name, pct, company, as_of, holder_kind, source_file`), with
custodians and nominee accounts flagged in `holder_kind`, never treated as owners.

## Acceptance
`pytest -q tests/test_interlocks_parse.py`

## Out of scope
Entity resolution (T11), writing to the graph.

# T25: Proposed party-status and event rows for amendment 1

## Goal
Turn what the web research verified into ready-to-apply rows, kept under `proposals/`
until the owner approves them: party status rows that close the Golkar and Gerindra
gap, the corrected Bakrie party role, and candidate events that had no sourced date.

## Read first
- `CLAUDE.md` (hard rules 2 and 3)
- `research_notes/Influence network project sources/cabinet_party_facts.md` and
  `event_dates.md`
- `data/seed/coalition_events.csv` (format; read only), `data/events/events.csv`
  (format; read only), `docs/paper/prereg.md` sections 3 and 13

## Files you may create or edit
- `proposals/amendment-1/coalition_rows.csv` (new: same columns as
  `data/seed/coalition_events.csv`)
- `proposals/amendment-1/person_edge_changes.md` (new)
- `proposals/amendment-1/event_rows.csv` (new: same columns as `data/events/events.csv`)
- `proposals/amendment-1/evidence_notes.md` (new)

## Specification
- Only facts the notes mark as verified, each with its URL copied exactly. Anything
  marked unverified is listed in `evidence_notes.md` under "Still open" and not turned
  into a row.
- `coalition_rows.csv`: baseline rows for Golkar and Gerindra under the 2019 cabinet,
  and corrections to any 2024 row the research contradicts (say which existing
  `event_id` each row replaces or follows).
- `person_edge_changes.md`: the proposed end date and later role for Aburizal Bakrie's
  Golkar edge, with sources, as a before/after table. No change to `build_seed_graph.py`.
- `event_rows.csv`: candidate rows for the 2024-02-14 election and the late-August 2025
  protests if the notes give two sources each. Signs follow the hypotheses in the
  pre-registration with the argument in `notes`; an event whose sign cannot be argued in
  one sentence is `ambiguous`. Scheduled events get `anticipation_flag = 1`.
  State in `evidence_notes.md` that the signs still need the independent sign check and
  that adding these rows changes confounder flags of neighbouring events (list which).
- No market reactions, no prices, no judgemental wording.

## Acceptance
`python - <<'PY'
import pandas as pd
c = pd.read_csv('proposals/amendment-1/coalition_rows.csv', dtype=str, keep_default_na=False)
ref = pd.read_csv('data/seed/coalition_events.csv', dtype=str, keep_default_na=False)
assert list(c.columns) == list(ref.columns), c.columns
assert c.source_url.str.match(r'^(https?://|doc:)').all()
e = pd.read_csv('proposals/amendment-1/event_rows.csv', dtype=str, keep_default_na=False)
assert list(e.columns) == list(pd.read_csv('data/events/events.csv', nrows=0).columns)
print(len(c), 'coalition rows;', len(e), 'event rows')
PY
python tools/guard.py`

## Out of scope
Editing `data/seed/`, `data/events/` or the pre-registration; new web searches unless a
single fact is missing and one search would settle it.

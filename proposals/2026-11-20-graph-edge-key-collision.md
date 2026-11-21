# Proposal: parallel edges with the same role overwrite each other in the graph

Status: for the owner to decide in an attended session. Nothing protected was changed.
Found on 2026-11-20 by the task loop while checking T18 (monitor lenders table).

## What happens

`src/influence/graph.py`, `build_graph`, adds each edge to a `networkx.MultiDiGraph`
with the key `type` plus `:role`. Two edges with the same source, target, type and role
text but different dates therefore share a key, and the later row in `edges.csv`
replaces the earlier one without any message.

## How much is affected today

Counted from `data/processed/edges.csv` (374 rows) against the loaded graph (274 edges):

- 100 rows are lost. All are `finances` edges: 180 in the file, 80 in the graph.
- No other edge type is affected at present (their counts match), but the same thing
  would happen to, for example, one person holding the same board role at the same
  company in two separate terms.
- `finances` rows by start year, file against graph:

| year | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| in `edges.csv` | 9 | 14 | 9 | 11 | 15 |
| in the graph | 5 | 5 | 7 | 7 | 15 |

  Which year survives depends on row order in the file (the last one wins).

## Why it matters for the registered study

`dist_gov` is registered as the shortest undirected path "over all active edges", and
`finances` edges are among them (see the log of 2026-11-20, run 4: BBCA reaches the
state in three steps through two banks lending to the same group). A snapshot on an
event date in 2021 to 2024 is missing some of that year's lending edges, so `dist_gov`,
`gov_proximity` and anything built on them (the composite, `tested_value` for events
whose tested measure is "all") can differ from what the registered definition implies.
The size of the difference has not been measured, because measuring it means changing
or re-running protected code.

No price data is involved, and none has been downloaded, so this can still be settled
before any outcome is seen.

## Options

1. Make the key unique per row, for example `type:role:start_date:end_date`, or a
   running index. Then rebuild `connection_measures.parquet` and the summary files, and
   record in the amendment which firm-event values changed.
2. Keep the key and decide that `finances` edges do not belong in `dist_gov` at all
   (the question raised in the run 4 log). The lost rows would then not affect any
   registered measure, though the graph would still be incomplete for other uses.
3. Both: fix the key, and decide separately whether lending counts as a path.

The loop's view: option 3. The collision is a plain defect whatever is decided about
lending, and a test that the graph has as many edges as the file has valid rows would
keep it from coming back.

## What the loop did in the meantime

T18 reads financing rows from the validated edge list (`load_edges`), not from the
graph, so the lenders table is complete. T15 (network map) excludes `finances` edges by
its brief and is not affected. T16 (exposure profile) calls the registered
`compute_all` unchanged, so it shows whatever the registered code computes.

## Files a fix would touch (all protected)

`src/influence/graph.py`, `data/processed/connection_*`, possibly `tests/test_schema.py`
or a new graph test, and `docs/paper/prereg.md` for the amendment text.

## Scope, added 2026-11-21 after reading section 4 of the pre-registration closely

The first version of this note said the lost edges could affect `tested_value` for
events whose tested measure is "all". More exactly:

- The two registered main-test events test `state_own` and `board_office`. Neither uses
  lending edges. **The registered main test is not affected.**
- For "all", the 0/1 indicator is 1 if any of the six tie measures is positive.
  `dist_gov` is not one of the six, so the main (0/1) specification for those events is
  not affected either.
- Affected: `dist_gov` itself, `gov_proximity`, the composite (first principal
  component) and therefore the scaled-value secondary specification for "all" events,
  and the monitor's "steps to the state" number.

This lowers the stakes but not the case for fixing the key: the graph should hold every
valid row of the edge file.

# T15: Monitor data layer

## Goal
Pure functions that load the project's data once and answer the questions the
Stakeholder Exposure Monitor asks. No Streamlit code here, so everything is testable.

## Read first
- `CLAUDE.md` (hard rules 3 and 4)
- `docs/DESIGN.md` section 7
- `src/influence/graph.py`, `src/influence/connections/build_measures.py` (`load_graph`),
  `src/influence/events/eventset.py` (read only)
- `data/processed/nodes.csv`, `edges.csv` (first lines), `data/mappings/tickers.csv`

## Files you may create or edit
- `src/influence/app/__init__.py` (new, one-line docstring)
- `src/influence/app/data.py` (new)
- `tests/test_app_data.py` (new)

## Specification
- `load() -> Bundle` (a dataclass, cached with `functools.lru_cache`): `graph` (from
  `build_measures.load_graph()`), `tickers` and `events` (from `eventset`), `measures`
  (`data/processed/connection_measures.parquet`).
- `firm_node(bundle, ticker) -> str` and `firm_label(bundle, ticker) -> str`.
- `network(bundle, ticker, on, hops=2) -> (nodes_df, edges_df)`: the firm's undirected
  neighbourhood within `hops` in `graph.snapshot(on)`, EXCLUDING `finances` and
  `publishes` edges (lenders have their own table; outlets are not stakeholders of a
  firm). `nodes_df`: `id, name, type, hop, stakeholder_group`; `edges_df`: `source,
  target, type, role, start, end, pct, source_url, confidence`.
- `stakeholder_group` from node type: person -> "People", party -> "Parties",
  govt_body -> "State", bank/company/business_group -> "Companies and groups",
  media_group/outlet -> "Media".
- `date_bounds(bundle) -> (date, date)`: 2021-01-01 to the latest event date.
- Every edge row keeps its `source_url`; a row without one must raise, not be dropped.
- Tests (they may load the real committed data): BBRI's network on 2025-06-30 contains a
  state node at hop 1 and at least one person; on 2022-06-30 the state node is the
  Republic node; hop limits are respected; `finances` edges never appear; every edge
  row has a source; unknown ticker raises `KeyError`.

## Acceptance
`pytest -q tests/test_app_data.py`

## Out of scope
Streamlit, plotting, prices or returns, editing any file outside the list.

# T12: Board interlock graph and classification

## Goal
From dated board seats, build the company-to-company graph of shared board members on a
given date and label each link.

## Read first
- `CLAUDE.md`
- `src/influence/graph.py` (`snapshot`; read only)
- `docs/HANDOFF_MODULES.md`, Module B, pipeline step 5 (first two bullets only)

## Files you may create or edit
- `src/influence/interlocks/__init__.py` (create with a one-line docstring if missing)
- `src/influence/interlocks/graph.py` (new)
- `tests/test_interlocks_graph.py` (new)

## Specification
- Input: a DataFrame `seats` with columns `person_key, company, role, start, end`
  (`start`/`end` are `datetime.date` or None; None means open-ended), and a DataFrame
  `companies` with columns `company, sub_industry, group` (`group` may be empty).
- `active(seats, on) -> DataFrame`: seats in effect on the date (inclusive at both ends).
- `interlocks(seats, companies, on) -> DataFrame` with one row per unordered pair of
  companies that share at least one person on that date: `company_a, company_b`
  (alphabetical), `n_shared`, `shared_people` (sorted, `;`-joined), `kind`.
- `kind`: `intra_group` when both companies have the same non-empty `group`;
  else `horizontal` when both have the same non-empty `sub_industry`; else `other`.
  (A pair in the same group and the same sub-industry is `intra_group`.)
- `summary(links, companies) -> dict`: number of companies, number with at least one
  link, counts by kind, and density = links / possible pairs.
- `to_networkx(links) -> networkx.Graph` with `n_shared` and `kind` as edge attributes.
- Definitions are a derived relationship, not a statement about conduct; say so in the
  module docstring in one sentence.
- Tests on a toy set of 5 companies and 6 people: a seat that ended the day before the
  date does not link; each `kind`; a person on three boards gives three links; summary
  numbers by hand.

## Acceptance
`pytest -q tests/test_interlocks_graph.py`

## Out of scope
Ownership concentration, MHHI, reading the project's real graph, plots.

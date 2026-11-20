# T11: Person merge candidates and review file

## Goal
List pairs of board members from different companies who might be the same person, and
write them to a file for a human to accept or reject. Nothing is merged automatically.

## Read first
- `CLAUDE.md` (hard rule 3)
- `src/influence/interlocks/names.py`
- `docs/HANDOFF_MODULES.md`, Module B, ground rule 3 and pipeline step 3

## Files you may create or edit
- `src/influence/interlocks/merges.py` (new)
- `tests/test_interlocks_merges.py` (new)

## Specification
- Input: a DataFrame `people` with columns `record_id, name, company, role, as_of`.
- `candidates(people) -> DataFrame` with columns `record_a, record_b, name_a, name_b,
  company_a, company_b, shared_tokens, token_overlap, same_printed, suggestion`:
  - compare only pairs that share at least one block key (`names.block_keys`) and are
    in different companies;
  - `token_overlap` = shared tokens / tokens in the shorter name;
  - `suggestion` is `same` when the normalised names are identical and have at least two
    tokens, `review` when `token_overlap` is 1.0 but the names differ (one is a subset
    of the other) or when identical single-token names, otherwise the pair is dropped;
  - sorted by `suggestion`, then names, so the file is stable between runs.
- `write_review(cands, path)` writes `person_merges.csv` with the columns above plus
  empty `decision` (to be filled with `same` or `different` by a person) and `decided_by`.
  If the file exists, keep decisions already made for the same (record_a, record_b).
- `apply_decisions(people, review) -> DataFrame` adds `person_key`: records joined by a
  `decision == "same"` share one key (union-find); every other record gets its own key.
  A pair with an empty decision is NOT merged, even when `suggestion` is `same`.
- Tests: identical two-token names in two companies give `same`; subset names give
  `review`; unrelated names give no row; same company gives no row; decisions survive a
  rewrite; undecided pairs stay separate; three records chained by two `same` decisions
  share one key.

## Acceptance
`pytest -q tests/test_interlocks_merges.py`

## Out of scope
Any automatic merge, string-distance or phonetic matching, touching the graph.

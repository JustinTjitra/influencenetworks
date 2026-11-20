# T10: Indonesian name normalisation

## Goal
A deterministic function that turns a person's name as printed in a filing into a
comparable form, the first step of matching people across companies (Phase 2).

## Read first
- `CLAUDE.md` (hard rule 3: no fuzzy or silent name matching)
- `docs/HANDOFF_MODULES.md`, Module B, pipeline step 3

## Files you may create or edit
- `src/influence/interlocks/__init__.py` (new, one-line docstring)
- `src/influence/interlocks/names.py` (new)
- `tests/test_interlocks_names.py` (new)

## Specification
- `normalise(name) -> str`: Unicode NFKC; strip; collapse whitespace; remove honorifics
  and degrees wherever they appear as separate tokens or after a comma, with or without
  dots, case-insensitive: H, Hj, Ir, Dr, Drs, Dra, Prof, Tn, Ny, KH, Raden, R, SE, SH,
  ST, SIP, SKom, SSos, MM, MBA, MSc, MSi, MH, MA, MKn, MHum, PhD, Ak, CA, CFA, CPA, BSc,
  LLM, LLB, "S.E.", "M.B.A." and the like; drop empty tokens; upper-case the result.
  Do not remove a token that is the whole name ("Ir" alone stays "IR"). Keep hyphens and
  apostrophes inside names.
- `tokens(name) -> tuple[str, ...]`: the normalised name split on spaces.
- `block_keys(name) -> set[str]`: every token of length 3 or more (exact tokens, used
  later to choose which pairs to compare). No phonetic or fuzzy keys.
- `same_printed(a, b) -> bool`: True only when the normalised forms are identical.
- Keep the title list as a module constant with a comment saying how to extend it.
- Tests: at least 20 cases, including "Ir. H. Joko Widodo" -> "JOKO WIDODO",
  "Dr. (H.C.) Ir. Airlangga Hartarto, M.B.A., M.M.T." -> "AIRLANGGA HARTARTO",
  "Sri Mulyani Indrawati, S.E., M.Sc., Ph.D." -> "SRI MULYANI INDRAWATI",
  single-name people ("Suharto"), names containing a title-like token inside a longer
  word ("Irawan" keeps "Ir"), double spaces, trailing commas, lower-case input.

## Acceptance
`pytest -q tests/test_interlocks_names.py`

## Out of scope
Merging people, similarity scores, any third-party library.

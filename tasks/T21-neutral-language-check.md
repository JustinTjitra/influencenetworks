# T21: Neutral-language check

## Goal
A test that fails when judgemental words appear in the app, the code or the user-facing
docs, so the rule in `CLAUDE.md` is enforced by machine.

## Read first
- `CLAUDE.md` (hard rule 4)
- `docs/DESIGN.md` section 7, "Design rules"

## Files you may create or edit
- `tests/test_language.py` (new)

## Specification
- Scan every `.py` file under `src/influence/` and every `.md` file under `docs/`
  except `docs/research/`, `docs/HANDOFF*.md` and `docs/DESIGN.md` (they quote the
  banned words to state the rule), plus `README.md`.
- Banned, as whole words, case-insensitive: `crony`, `cronies`, `cronyism`, `corrupt`,
  `corruption`, `captured` (when followed within the same line by `by`, `state`,
  `regulator` or `firm`), `favoured`, `favored`, `kleptocrat`, `oligarch`, `oligarchs`.
- Allow a line that contains the marker `language-rule-ok` (for lines that state the
  rule itself) and allow the words inside `src/influence/news/` (it handles news text).
- On failure, list file, line number and the word.
- If the scan finds existing violations, do NOT edit those files (many are protected):
  report them in your reply and add the marker only if the line is stating the rule.
  If a real violation exists in a file you may not edit, make the test list it under a
  clearly named `KNOWN_EXCEPTIONS` constant with a comment, so the test passes and the
  owner can see what is outstanding.

## Acceptance
`pytest -q tests/test_language.py`

## Out of scope
Editing any scanned file, changing wording anywhere.

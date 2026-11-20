# T02: Guard against protected-file and price-data changes

## Goal
A check the loop and continuous integration run before every commit: it fails if a
protected file was changed or if price data or secrets are about to be committed.

## Read first
- `CLAUDE.md` (section "Hard rules")
- `tasks/PROTECTED.txt`

## Files you may create or edit
- `tools/guard.py` (new)
- `tests/test_guard.py` (new)

## Specification
- Standard library only (use `subprocess` to call `git`).
- `python tools/guard.py` compares the working tree and index with `HEAD`
  (`git status --porcelain`, including untracked files) and exits 1 with one line per
  finding if:
  1. any changed, added, deleted or renamed path matches a pattern in
     `tasks/PROTECTED.txt` (blank lines and lines starting with `#` ignored; `fnmatch`
     on the repo-relative path with forward slashes; a pattern ending in `/**` matches
     everything under that directory);
  2. any changed or added path is under `data/raw/prices/`, `data/raw/docs/`,
     `data/raw/news/` or `data/raw/financing/`, or ends in `.pdf`, `.xlsx`, `.parquet`
     outside `data/processed/`;
  3. any changed or added text file under 1 MB contains a line that looks like a secret:
     a private-key header (`-----BEGIN ... PRIVATE KEY-----`), or
     `(api[_-]?key|secret|token|password)\s*[:=]\s*['"][^'"]{12,}['"]` (case-insensitive).
- `python tools/guard.py --range A..B` applies checks 1 and 2 to the paths changed
  between two commits (`git diff --name-status A B`), for continuous integration.
- `--allow-protected "<reason>"` skips check 1 and prints the reason. It exists for
  attended amendment sessions only; say so in the help text.
- Exit 0 and print `guard: ok` when nothing is found.
- Provide pure functions (`load_patterns`, `is_protected`, `forbidden_path`,
  `find_secret_lines`) and test them directly: pattern matching including `/**`,
  comments, a nested path; forbidden paths; secret patterns hit and a normal line such
  as `token = load_token()` does not. One test builds a temporary git repository with
  `subprocess` and checks the command-line behaviour end to end, including `--range`.

## Acceptance
`pytest -q tests/test_guard.py && python tools/guard.py --allow-protected "T02 acceptance run"`

## Out of scope
Changing `tasks/PROTECTED.txt`, git hooks, any network access.

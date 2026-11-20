# T03: Continuous integration workflow

## Goal
Every push and pull request runs the tests, the board check and the guard on GitHub, so
a bad unattended commit is visible at once.

## Read first
- `CLAUDE.md`
- `pyproject.toml`
- `tools/taskboard.py`, `tools/guard.py` (their command-line help)

## Files you may create or edit
- `.github/workflows/ci.yml` (new)

## Specification
- Triggers: `push` to `main`, and `pull_request`.
- One job on `ubuntu-latest`, Python 3.11, `actions/checkout@v4` with `fetch-depth: 0`,
  `actions/setup-python@v5` with pip caching.
- Steps: `pip install -e ".[dev]"`; `pytest -q`; `python tools/taskboard.py validate`;
  then the guard on the pushed range: for a push use
  `python tools/guard.py --range ${{ github.event.before }}..${{ github.sha }}` and skip
  it when `github.event.before` is all zeros (new branch); for a pull request use
  `origin/${{ github.base_ref }}..${{ github.sha }}`.
- The guard step must not fail a commit whose message contains `[amendment]`: in that
  case pass `--allow-protected "amendment commit"`.
- `permissions: contents: read`. No secrets, no deploy, no scheduled runs.
- Keep the file under 60 lines and comment each step in one line.

## Acceptance
`python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml'))" 2>/dev/null || python - <<'PY'
import re,sys
s=open('.github/workflows/ci.yml').read()
assert 'pytest -q' in s and 'taskboard.py validate' in s and 'guard.py' in s and 'pull_request' in s
print('ci.yml looks complete')
PY`

## Out of scope
Changing the tools, adding linters, badges in the README.

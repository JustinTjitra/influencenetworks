# T01: Task board tool

## Goal
A small command-line tool that reads `tasks/BOARD.md`, checks it, prints the next task
and changes a task's status, so the loop never edits the table by hand.

## Read first
- `CLAUDE.md`
- `tasks/README.md` (sections "The board" and "A brief")
- `tasks/BOARD.md`

## Files you may create or edit
- `tools/taskboard.py` (new)
- `tests/test_taskboard.py` (new)

## Specification
- Standard library only. Python 3.11+.
- Parse the single markdown table in `tasks/BOARD.md` whose header is
  `| id | title | tier | depends | status |`. Ignore every other line.
- `python tools/taskboard.py validate` exits 0 when all of this holds, otherwise prints
  each problem on its own line and exits 1:
  - ids match `^[TU]\d{2}$` and are unique;
  - tier is one of `haiku`, `sonnet`, `planner` for `T` rows and `owner` for `U` rows;
  - status is `todo`, `doing`, `done`, `failed`, or starts with `blocked:` followed by
    at least one character;
  - every id in `depends` exists (`-` means none);
  - no dependency cycle;
  - every `T` row has exactly one file `tasks/<id>-*.md`, every such file has a row, and
    each brief contains the six headings `## Goal`, `## Read first`,
    `## Files you may create or edit`, `## Specification`, `## Acceptance`,
    `## Out of scope`.
- `python tools/taskboard.py next` prints the id of the first row, in table order, that
  is a `T` row with status `todo` and whose dependencies are all `done`, followed by a
  space and the path of its brief. Prints nothing and exits 0 when there is none.
- `python tools/taskboard.py set <id> <status>` rewrites only that row's status cell,
  keeps every other byte of the file, and validates the new status as above. Unknown id
  or bad status: message and exit 1, file unchanged.
- `python tools/taskboard.py list` prints `id status tier title` per row.
- All commands accept `--board PATH` and `--tasks-dir PATH` (defaults `tasks/BOARD.md`
  and `tasks`) so tests can use temporary files.
- Tests (pytest, using `tmp_path`, calling the functions directly and through
  `main(argv)`): a valid board passes; each validation rule fails when broken; `next`
  skips rows with unmet dependencies and `blocked:` rows; `set` changes one cell only;
  a cycle is reported; the repository's real board validates.

## Acceptance
`pytest -q tests/test_taskboard.py && python tools/taskboard.py validate && python tools/taskboard.py next`

## Out of scope
Editing `tasks/BOARD.md` content, any other task, YAML or third-party parsers.

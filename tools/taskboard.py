#!/usr/bin/env python3
"""Read, check and update tasks/BOARD.md. Standard library only."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HEADER = ["id", "title", "tier", "depends", "status"]
ID_RE = re.compile(r"^[TU]\d{2}$")
T_TIERS = {"haiku", "sonnet", "planner"}
U_TIERS = {"owner"}
STATUSES = {"todo", "doing", "done", "failed"}
HEADINGS = [
    "## Goal",
    "## Read first",
    "## Files you may create or edit",
    "## Specification",
    "## Acceptance",
    "## Out of scope",
]


def _cells(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def parse_board(text: str) -> list[dict]:
    """Return rows of the single table with the board header, in table order."""
    rows: list[dict] = []
    in_table = False
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not in_table:
            if line.strip().startswith("|") and _cells(line) == HEADER:
                in_table = True
                start = i + 2  # skip the separator line
                for j in range(start, len(lines)):
                    if not lines[j].strip().startswith("|"):
                        break
                    c = _cells(lines[j])
                    if len(c) != len(HEADER):
                        c = c + [""] * (len(HEADER) - len(c))
                    row = dict(zip(HEADER, c[: len(HEADER)]))
                    row["line"] = j
                    rows.append(row)
                break
    return rows


def valid_status(status: str) -> bool:
    if status in STATUSES:
        return True
    return status.startswith("blocked:") and len(status) > len("blocked:") and "|" not in status


def _depends(row: dict) -> list[str]:
    d = row["depends"].strip()
    return [] if d in ("-", "") else d.split()


def _find_cycles(rows: list[dict]) -> list[list[str]]:
    graph = {r["id"]: [d for d in _depends(r)] for r in rows}
    cycles: list[list[str]] = []
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(n: str) -> None:
        state[n] = 1
        stack.append(n)
        for m in graph.get(n, []):
            if m not in graph:
                continue
            if state.get(m, 0) == 0:
                visit(m)
            elif state[m] == 1:
                cycles.append(stack[stack.index(m):] + [m])
        stack.pop()
        state[n] = 2

    for n in graph:
        if state.get(n, 0) == 0:
            visit(n)
    return cycles


def validate(rows: list[dict], tasks_dir: Path) -> list[str]:
    problems: list[str] = []
    if not rows:
        problems.append("no board table found (header: | id | title | tier | depends | status |)")
    seen: set[str] = set()
    for r in rows:
        rid = r["id"]
        if not ID_RE.match(rid):
            problems.append(f"{rid or '(empty)'}: id does not match ^[TU]\\d{{2}}$")
        if rid in seen:
            problems.append(f"{rid}: duplicate id")
        seen.add(rid)
        allowed = U_TIERS if rid.startswith("U") else T_TIERS
        if r["tier"] not in allowed:
            problems.append(f"{rid}: tier '{r['tier']}' not one of {sorted(allowed)}")
        if not valid_status(r["status"]):
            problems.append(f"{rid}: bad status '{r['status']}'")
        for d in _depends(r):
            if d not in {x["id"] for x in rows}:
                problems.append(f"{rid}: depends on unknown id {d}")
    for cyc in _find_cycles(rows):
        problems.append("dependency cycle: " + " -> ".join(cyc))

    t_ids = {r["id"] for r in rows if r["id"].startswith("T") and ID_RE.match(r["id"])}
    for tid in sorted(t_ids):
        files = sorted(tasks_dir.glob(f"{tid}-*.md"))
        if len(files) == 0:
            problems.append(f"{tid}: no brief file {tasks_dir}/{tid}-*.md")
            continue
        if len(files) > 1:
            problems.append(f"{tid}: more than one brief file: " + ", ".join(f.name for f in files))
            continue
        brief_lines = {ln.strip() for ln in files[0].read_text(encoding="utf-8").splitlines()}
        for h in HEADINGS:
            if h not in brief_lines:
                problems.append(f"{files[0].name}: missing heading '{h}'")
    if tasks_dir.is_dir():
        for f in sorted(tasks_dir.glob("T[0-9][0-9]-*.md")):
            if f.name[:3] not in t_ids:
                problems.append(f"{f.name}: brief has no row in the board")
    return problems


def next_task(rows: list[dict], tasks_dir: Path) -> str | None:
    status = {r["id"]: r["status"] for r in rows}
    for r in rows:
        if not r["id"].startswith("T") or r["status"] != "todo":
            continue
        if all(status.get(d) == "done" for d in _depends(r)):
            files = sorted(tasks_dir.glob(f"{r['id']}-*.md"))
            path = files[0] if files else tasks_dir / f"{r['id']}-*.md"
            return f"{r['id']} {path}"
    return None


def set_status(board: Path, rid: str, status: str) -> str | None:
    """Change one status cell. Return an error message or None on success."""
    if not valid_status(status):
        return f"bad status '{status}'"
    with open(board, encoding="utf-8", newline="") as fh:
        text = fh.read()
    rows = parse_board(text)
    match = [r for r in rows if r["id"] == rid]
    if not match:
        return f"unknown id '{rid}'"
    lines = text.splitlines(keepends=True)
    ln = lines[match[0]["line"]]
    body = ln.rstrip("\r\n")
    eol = ln[len(body):]
    stripped = body.rstrip()
    trailing_ws = body[len(stripped):]
    if not stripped.endswith("|"):
        return f"row {rid} has no closing '|'"
    inner = stripped[:-1]
    cut = inner.rfind("|")
    cell = inner[cut + 1:]
    lead = cell[: len(cell) - len(cell.lstrip())]
    trail = cell[len(cell.rstrip()):]
    lines[match[0]["line"]] = inner[: cut + 1] + lead + status + trail + "|" + trailing_ws + eol
    with open(board, "w", encoding="utf-8", newline="") as fh:
        fh.write("".join(lines))
    return None


def main(argv: list[str] | None = None) -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--board", default="tasks/BOARD.md")
    common.add_argument("--tasks-dir", default="tasks")
    p = argparse.ArgumentParser(prog="taskboard", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate", parents=[common])
    sub.add_parser("next", parents=[common])
    sub.add_parser("list", parents=[common])
    sp = sub.add_parser("set", parents=[common])
    sp.add_argument("id")
    sp.add_argument("status")
    args = p.parse_args(argv)

    board, tasks_dir = Path(args.board), Path(args.tasks_dir)
    if not board.is_file():
        print(f"board not found: {board}")
        return 1
    if args.cmd == "set":
        err = set_status(board, args.id, args.status)
        if err:
            print(err)
            return 1
        return 0
    rows = parse_board(board.read_text(encoding="utf-8"))
    if args.cmd == "validate":
        problems = validate(rows, tasks_dir)
        for pr in problems:
            print(pr)
        return 1 if problems else 0
    if args.cmd == "next":
        out = next_task(rows, tasks_dir)
        if out:
            print(out)
        return 0
    for r in rows:
        print(f"{r['id']} {r['status']} {r['tier']} {r['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

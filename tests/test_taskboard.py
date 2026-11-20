import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("taskboard", ROOT / "tools" / "taskboard.py")
tb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tb)

BRIEF = "\n".join(f"{h}\nx\n" for h in tb.HEADINGS)

HEAD = "# Board\n\nintro | not a table\n\n| id | title | tier | depends | status |\n|---|---|---|---|---|\n"


def make(tmp_path, rows, briefs=("T01", "T02", "T03"), tail="\nafter\n"):
    board = tmp_path / "BOARD.md"
    board.write_text(HEAD + "\n".join(rows) + "\n" + tail, encoding="utf-8")
    tdir = tmp_path / "tasks"
    tdir.mkdir(exist_ok=True)
    for b in briefs:
        (tdir / f"{b}-x.md").write_text(BRIEF, encoding="utf-8")
    return board, tdir


GOOD = [
    "| T01 | One | sonnet | - | done |",
    "| T02 | Two | haiku | T01 | todo |",
    "| T03 | Three | planner | T01 T02 | todo |",
    "| U01 | Own | owner | T03 | blocked:owner |",
]


def problems(board, tdir):
    return tb.validate(tb.parse_board(board.read_text()), tdir)


def run(board, tdir, *a):
    return tb.main([*a, "--board", str(board), "--tasks-dir", str(tdir)])


def test_valid_board(tmp_path):
    board, tdir = make(tmp_path, GOOD)
    assert problems(board, tdir) == []
    assert run(board, tdir, "validate") == 0


def test_bad_id_and_duplicate(tmp_path):
    rows = GOOD + ["| X1 | Bad | sonnet | - | todo |", "| T01 | Dup | sonnet | - | todo |"]
    board, tdir = make(tmp_path, rows)
    p = "\n".join(problems(board, tdir))
    assert "X1" in p and "duplicate id" in p
    assert run(board, tdir, "validate") == 1


def test_bad_tier(tmp_path):
    rows = [GOOD[0].replace("sonnet", "gpt"), GOOD[1], GOOD[2], "| U01 | Own | haiku | - | todo |"]
    board, tdir = make(tmp_path, rows)
    p = problems(board, tdir)
    assert any("T01" in x and "tier" in x for x in p)
    assert any("U01" in x and "tier" in x for x in p)


def test_bad_status(tmp_path):
    rows = [GOOD[0].replace("done", "blocked:"), GOOD[1].replace("todo", "wip"), GOOD[2], GOOD[3]]
    board, tdir = make(tmp_path, rows)
    p = problems(board, tdir)
    assert any("T01" in x and "status" in x for x in p)
    assert any("T02" in x and "status" in x for x in p)


def test_unknown_dependency(tmp_path):
    rows = [GOOD[0], GOOD[1].replace("T01", "T09"), GOOD[2], GOOD[3]]
    board, tdir = make(tmp_path, rows)
    assert any("unknown id T09" in x for x in problems(board, tdir))


def test_cycle(tmp_path):
    rows = ["| T01 | One | sonnet | T03 | todo |", GOOD[1], GOOD[2]]
    board, tdir = make(tmp_path, rows)
    assert any("cycle" in x for x in problems(board, tdir))


def test_missing_brief_and_orphan_brief(tmp_path):
    board, tdir = make(tmp_path, GOOD, briefs=("T01", "T02", "T07"))
    p = "\n".join(problems(board, tdir))
    assert "T03: no brief" in p
    assert "T07-x.md: brief has no row" in p


def test_two_briefs_and_missing_heading(tmp_path):
    board, tdir = make(tmp_path, GOOD)
    (tdir / "T01-y.md").write_text(BRIEF)
    (tdir / "T02-x.md").write_text(BRIEF.replace("## Acceptance", "## Other"))
    p = "\n".join(problems(board, tdir))
    assert "T01: more than one brief" in p
    assert "T02-x.md: missing heading '## Acceptance'" in p


def test_next_skips_unmet_and_blocked(tmp_path):
    rows = [
        "| T01 | One | sonnet | T02 | todo |",
        "| T02 | Two | haiku | - | blocked:owner |",
        "| T03 | Three | planner | T04 | todo |",
        "| T04 | Four | haiku | - | done |",
    ]
    board, tdir = make(tmp_path, rows, briefs=("T01", "T02", "T03", "T04"))
    out = tb.next_task(tb.parse_board(board.read_text()), tdir)
    assert out == f"T03 {tdir / 'T03-x.md'}"


def test_next_none(tmp_path, capsys):
    board, tdir = make(tmp_path, [GOOD[0], GOOD[3].replace("T03", "T01")], briefs=("T01",))
    assert run(board, tdir, "next") == 0
    assert capsys.readouterr().out == ""


def test_next_cli(tmp_path, capsys):
    board, tdir = make(tmp_path, GOOD)
    assert run(board, tdir, "next") == 0
    assert capsys.readouterr().out.split() == ["T02", str(tdir / "T02-x.md")]


def test_set_changes_one_cell_only(tmp_path):
    board, tdir = make(tmp_path, GOOD)
    before = board.read_text()
    assert run(board, tdir, "set", "T02", "doing") == 0
    after = board.read_text()
    assert after == before.replace("| T02 | Two | haiku | T01 | todo |", "| T02 | Two | haiku | T01 | doing |")
    assert run(board, tdir, "set", "U01", "blocked:waiting") == 0
    assert "blocked:waiting |" in board.read_text()


def test_set_errors_leave_file_unchanged(tmp_path, capsys):
    board, tdir = make(tmp_path, GOOD)
    before = board.read_bytes()
    assert run(board, tdir, "set", "T99", "done") == 1
    assert run(board, tdir, "set", "T02", "bogus") == 1
    assert run(board, tdir, "set", "T02", "blocked:") == 1
    assert board.read_bytes() == before


def test_set_preserves_crlf(tmp_path):
    board, tdir = make(tmp_path, GOOD)
    board.write_bytes(board.read_bytes().replace(b"\n", b"\r\n"))
    before = board.read_bytes()
    assert run(board, tdir, "set", "T02", "done") == 0
    assert board.read_bytes() == before.replace(b"| todo |\r\n| T03", b"| done |\r\n| T03")


def test_list(tmp_path, capsys):
    board, tdir = make(tmp_path, GOOD)
    assert run(board, tdir, "list") == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0] == "T01 done sonnet One"
    assert len(out) == 4


def test_real_board_validates():
    board = ROOT / "tasks" / "BOARD.md"
    rows = tb.parse_board(board.read_text())
    assert len(rows) > 20
    assert tb._find_cycles(rows) == []
    assert tb.validate(rows, ROOT / "tasks") == []

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import guard  # noqa: E402

GUARD = Path(guard.__file__).resolve()


def test_load_patterns_ignores_comments_and_blanks(tmp_path):
    f = tmp_path / "p.txt"
    f.write_text("# c\n\nfoo/bar.md\n  src/x/**  \n")
    assert guard.load_patterns(f) == ["foo/bar.md", "src/x/**"]


def test_is_protected():
    pats = ["docs/a.md", "src/x/**", "data/processed/connection_*"]
    assert guard.is_protected("docs/a.md", pats)
    assert not guard.is_protected("docs/b.md", pats)
    assert guard.is_protected("src/x/y.py", pats)
    assert guard.is_protected("src/x/deep/er/z.py", pats)
    assert not guard.is_protected("src/xy/z.py", pats)
    assert guard.is_protected("data/processed/connection_measures.csv", pats)


def test_forbidden_path():
    assert guard.forbidden_path("data/raw/prices/a.csv")
    assert guard.forbidden_path("data/raw/docs/a.txt")
    assert guard.forbidden_path("data/raw/news/a.txt")
    assert guard.forbidden_path("data/raw/financing/a.csv")
    assert guard.forbidden_path("reports/a.pdf")
    assert guard.forbidden_path("x/a.xlsx")
    assert guard.forbidden_path("x/a.parquet")
    assert not guard.forbidden_path("data/processed/a.parquet")
    assert not guard.forbidden_path("src/a.py")


def test_find_secret_lines():
    key = "api" + "_key"
    text = "\n".join([
        "token = load_token()",
        f'{key} = "abcdefghijklmnop"',
        "-----BEGIN RSA " + "PRIVATE KEY-----",
        'PASSWORD: "short"',
        'Sec' + 'ret="0123456789abcdef"',
    ])
    assert guard.find_secret_lines(text) == [2, 3, 5]


def run(args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def git(cwd, *a):
    r = run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *a], cwd)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def test_cli_end_to_end(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "tasks").mkdir()
    (tmp_path / "tasks" / "PROTECTED.txt").write_text("# x\nfrozen/**\nlocked.md\n")
    (tmp_path / "locked.md").write_text("a\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "base")
    base = git(tmp_path, "rev-parse", "HEAD")

    def cli(*a):
        return run([sys.executable, str(GUARD), *a], tmp_path)

    r = cli()
    assert r.returncode == 0 and "guard: ok" in r.stdout

    (tmp_path / "locked.md").write_text("b\n")
    r = cli()
    assert r.returncode == 1 and "locked.md" in r.stdout
    r = cli("--allow-protected", "because")
    assert r.returncode == 0 and "because" in r.stdout
    git(tmp_path, "checkout", "--", "locked.md")

    (tmp_path / "frozen").mkdir()
    (tmp_path / "frozen" / "n.txt").write_text("x\n")
    r = cli()
    assert r.returncode == 1 and "frozen/n.txt" in r.stdout
    (tmp_path / "frozen" / "n.txt").unlink()

    (tmp_path / "data" / "raw" / "prices").mkdir(parents=True)
    (tmp_path / "data" / "raw" / "prices" / "p.csv").write_text("1\n")
    r = cli()
    assert r.returncode == 1 and "data/raw/prices/p.csv" in r.stdout
    (tmp_path / "data" / "raw" / "prices" / "p.csv").unlink()

    (tmp_path / "s.py").write_text('API_' + 'KEY = "abcdefghijklmnop"\n')
    r = cli()
    assert r.returncode == 1 and "s.py:1" in r.stdout
    (tmp_path / "s.py").unlink()
    assert cli().returncode == 0

    # --range
    (tmp_path / "locked.md").write_text("c\n")
    (tmp_path / "r.pdf").write_text("x")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "bad")
    head = git(tmp_path, "rev-parse", "HEAD")
    r = cli("--range", f"{base}..{head}")
    assert r.returncode == 1
    assert "locked.md" in r.stdout and "r.pdf" in r.stdout
    r = cli("--range", f"{base}..{head}", "--allow-protected", "ok")
    assert r.returncode == 1 and "r.pdf" in r.stdout and "locked.md" not in r.stdout.split("\n", 1)[1]
    r = cli("--range", f"{head}..{head}")
    assert r.returncode == 0

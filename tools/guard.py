#!/usr/bin/env python3
"""Guard: fail if protected files, price data, raw documents or secrets are changed.

Run before every commit and in continuous integration.

    python tools/guard.py                      # working tree and index vs HEAD
    python tools/guard.py --range A..B         # paths changed between two commits
    python tools/guard.py --allow-protected "reason"
"""
from __future__ import annotations

import argparse
import fnmatch
import re
import subprocess
import sys
from pathlib import Path

FORBIDDEN_DIRS = (
    "data/raw/prices/",
    "data/raw/docs/",
    "data/raw/news/",
    "data/raw/financing/",
)
FORBIDDEN_SUFFIXES = (".pdf", ".xlsx", ".parquet")
MAX_SECRET_SCAN_BYTES = 1_000_000

PRIVATE_KEY_RE = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
SECRET_RE = re.compile(
    r"(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]{12,}['\"]",
    re.IGNORECASE,
)


def load_patterns(path) -> list[str]:
    """Read patterns from a file; blank lines and '#' comments are ignored."""
    patterns = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            patterns.append(line)
    return patterns


def is_protected(path: str, patterns: list[str]) -> bool:
    """True if the repo-relative path matches any pattern ('/**' = everything below)."""
    path = path.replace("\\", "/")
    for pat in patterns:
        if pat.endswith("/**"):
            base = pat[:-3]
            if path == base or path.startswith(base + "/"):
                return True
        elif fnmatch.fnmatchcase(path, pat):
            return True
    return False


def forbidden_path(path: str) -> str | None:
    """Return a reason if the path must never be committed, else None."""
    path = path.replace("\\", "/")
    for d in FORBIDDEN_DIRS:
        if path.startswith(d):
            return f"under {d}"
    if path.lower().endswith(FORBIDDEN_SUFFIXES) and not path.startswith("data/processed/"):
        return "binary data file type outside data/processed/"
    return None


def find_secret_lines(text: str) -> list[int]:
    """Return 1-based numbers of lines that look like a secret."""
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        if PRIVATE_KEY_RE.search(line) or SECRET_RE.search(line):
            hits.append(i)
    return hits


def _git(args: list[str], cwd) -> str:
    res = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {res.stderr.strip()}")
    return res.stdout


def repo_root(cwd=None) -> Path:
    return Path(_git(["rev-parse", "--show-toplevel"], cwd).strip())


def status_changes(root) -> list[tuple[str, list[str]]]:
    """(status, [paths]) from git status, untracked files listed individually."""
    out = _git(["status", "--porcelain", "-z", "-uall"], root)
    parts = out.split("\0")
    changes = []
    i = 0
    while i < len(parts):
        entry = parts[i]
        i += 1
        if len(entry) < 4:
            continue
        code, path = entry[:2], entry[3:]
        paths = [path]
        if "R" in code or "C" in code:
            paths.append(parts[i])  # original path follows
            i += 1
        status = "D" if code.strip() == "D" or code == "AD" else code.strip()[:1] or "M"
        changes.append((status, paths))
    return changes


def range_changes(root, rng: str) -> list[tuple[str, list[str]]]:
    a, sep, b = rng.partition("..")
    if not sep or not a or not b:
        raise ValueError("--range must look like A..B")
    out = _git(["diff", "--name-status", "-z", a, b], root)
    parts = out.split("\0")
    changes = []
    i = 0
    while i < len(parts):
        st = parts[i]
        i += 1
        if not st:
            continue
        n = 2 if st[0] in "RC" else 1
        changes.append((st[0], parts[i:i + n]))
        i += n
    return changes


def check_paths(changes, patterns, skip_protected: bool) -> list[str]:
    findings = []
    for status, paths in changes:
        for p in paths:
            if not skip_protected and is_protected(p, patterns):
                findings.append(f"protected file changed: {p}")
        if status != "D":
            p = paths[0]
            reason = forbidden_path(p)
            if reason:
                findings.append(f"forbidden path: {p} ({reason})")
    return findings


def check_secrets(root: Path, changes) -> list[str]:
    findings = []
    for status, paths in changes:
        if status == "D":
            continue
        f = root / paths[0]
        try:
            if not f.is_file() or f.stat().st_size >= MAX_SECRET_SCAN_BYTES:
                continue
            data = f.read_bytes()
        except OSError:
            continue
        if b"\0" in data:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        for n in find_secret_lines(text):
            findings.append(f"possible secret: {paths[0]}:{n}")
    return findings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--range", dest="rng", metavar="A..B",
                    help="check paths changed between two commits (checks 1 and 2 only)")
    ap.add_argument("--allow-protected", metavar="REASON",
                    help="skip the protected-file check and print the reason; for attended "
                         "pre-registration amendment sessions only, never unattended work")
    args = ap.parse_args(argv)

    try:
        root = repo_root()
        patterns = load_patterns(root / "tasks" / "PROTECTED.txt")
        changes = range_changes(root, args.rng) if args.rng else status_changes(root)
    except (RuntimeError, ValueError, OSError) as e:
        print(f"guard: error: {e}")
        return 2

    skip = args.allow_protected is not None
    if skip:
        print(f"guard: protected-file check skipped: {args.allow_protected}")
    findings = check_paths(changes, patterns, skip)
    if not args.rng:
        findings += check_secrets(root, changes)

    if findings:
        for line in findings:
            print(line)
        return 1
    print("guard: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())

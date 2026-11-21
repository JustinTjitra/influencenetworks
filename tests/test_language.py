"""Neutral-language check (CLAUDE.md hard rule 4).

Scans the app and user-facing docs for judgemental words. Lines that state the rule
itself carry the marker ``language-rule-ok``. Known existing hits in files that unattended
work may not edit are listed in ``KNOWN_EXCEPTIONS``; a stale entry fails the test.
"""

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

BANNED = (
    "crony",
    "cronies",
    "cronyism",
    "corrupt",
    "corruption",
    "favoured",
    "favored",
    "kleptocrat",
    "oligarch",
    "oligarchs",
)
CAPTURED_FOLLOWERS = ("by", "state", "regulator", "firm")
MARKER = "language-rule-ok"

_BANNED_RE = re.compile(r"\b(" + "|".join(BANNED) + r")\b", re.IGNORECASE)
_CAPTURED_RE = re.compile(
    r"\bcaptured\b(?=.*\b(?:" + "|".join(CAPTURED_FOLLOWERS) + r")\b)", re.IGNORECASE
)

NEWS_DIR = ("src", "influence", "news")

# Exact (relative path, stripped line text, word) entries for existing hits that cannot be
# fixed here. Each entry must match a current hit, or the test fails.
KNOWN_EXCEPTIONS = [
    # Real use, not a statement of the rule: the source-access report describes the
    # court-case category a search targets ("defendants in corruption cases"). The file is
    # not one this task may edit; the owner should decide whether to reword it.
    ('docs/source_access_report.md', '| putusan3.mahkamahagung.go.id | The homepage, a listing page and a decision page all returned CLIENT_ERROR [X]. **robots.txt was fetched [F].** | Search results show indexed listings by court and category, for example `/direktori/index/pengadilan/pn-tarakan/kategori/ite-1.html`, and decision pages `/direktori/putusan/{id}.html` [3P search index]. | HTML listings plus per-decision PDF (from search snippets, not verified) | Free | robots.txt [F] carries a Cloudflare-managed header `Content-Signal: search=yes,ai-train=no,use=reference`. It blocks AI and training bots (ClaudeBot, GPTBot, CCBot and others) site-wide, and gives Googlebot and Bing a 10–15 s crawl-delay. **There are two conflicting `User-agent: *` groups (Allow / and Disallow /).** | **Use with caution.** Run slow, targeted queries on named entities (for example the defendants in corruption cases). Do not bulk crawl: robots is ambiguous and probably restrictive, and Cloudflare is in front. | https://putusan3.mahkamahagung.go.id/robots.txt |', 'corruption'),
]


def scanned_files(root):
    """Return the files the language rule applies to, under ``root``."""
    files = []
    for path in sorted((root / "src" / "influence").rglob("*.py")):
        rel = path.relative_to(root)
        if rel.parts[: len(NEWS_DIR)] == NEWS_DIR:
            continue  # news text is handled by the news pipeline; words allowed there
        files.append(path)
    docs = root / "docs"
    if docs.is_dir():
        for path in sorted(docs.rglob("*.md")):
            rel = path.relative_to(root)
            if rel.parts[:2] == ("docs", "research"):
                continue  # research notes quote sources verbatim
            if rel.parent == Path("docs") and rel.name.startswith("HANDOFF"):
                continue  # handoff notes quote sources verbatim
            if rel == Path("docs/DESIGN.md"):
                continue  # states the rule by quoting the banned words
            files.append(path)
    readme = root / "README.md"
    if readme.is_file():
        files.append(readme)
    return files


def scan_text(text):
    """Return (line number, word, stripped line) for each banned hit in ``text``."""
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if MARKER in line:
            continue
        found = [m.group(1).lower() for m in _BANNED_RE.finditer(line)]
        if _CAPTURED_RE.search(line):
            found.append("captured")
        for word in found:
            hits.append((lineno, word, line.strip()))
    return hits


def scan_file(path):
    return scan_text(path.read_text(encoding="utf-8"))


def test_no_banned_words_outside_known_exceptions():
    hits = {}  # (rel path, stripped line, word) -> list of line numbers
    for path in scanned_files(REPO):
        rel = path.relative_to(REPO).as_posix()
        for lineno, word, text in scan_file(path):
            hits.setdefault((rel, text, word), []).append(lineno)

    known = set(KNOWN_EXCEPTIONS)
    unexpected = sorted(key for key in hits if key not in known)
    report = "\n".join(
        f"{rel}:{','.join(map(str, hits[(rel, text, word)]))}: "
        f"{word!r} in line: {text}"
        for rel, text, word in unexpected
    )
    assert not unexpected, "banned words found (fix, add the marker if the line states the rule, or list in KNOWN_EXCEPTIONS):\n" + report

    stale = sorted(known - set(hits))
    assert not stale, "KNOWN_EXCEPTIONS entries that match no line (remove them):\n" + "\n".join(
        f"{rel}: {word!r} in line: {text}" for rel, text, word in stale
    )


def test_scanner_selftest(tmp_path):
    # Which files are selected.
    layout = [
        "src/influence/app/page.py",
        "src/influence/news/crawl.py",
        "docs/guide.md",
        "docs/sub/notes.md",
        "docs/research/2026-11-09/README.md",
        "docs/DESIGN.md",
        "docs/HANDOFF.md",
        "README.md",
        "tests/test_something.py",
    ]
    for rel in layout:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("neutral text\n", encoding="utf-8")
    selected = sorted(p.relative_to(tmp_path).as_posix() for p in scanned_files(tmp_path))
    assert selected == [
        "README.md",
        "docs/guide.md",
        "docs/sub/notes.md",
        "src/influence/app/page.py",
    ]

    # Which words are caught, line by line.
    cases = [
        ("Crony deals were signed.", ["crony"]),
        ("Cronyism is the rule.", ["cronyism"]),
        ("Cronies met in private.", ["cronies"]),
        ("CORRUPT officials are named.", ["corrupt"]),
        ("Corruption is rising.", ["corruption"]),
        ("The board favoured the bank.", ["favoured"]),
        ("They favored the lender.", ["favored"]),
        ("A kleptocrat ruled.", ["kleptocrat"]),
        ("An oligarch owns it.", ["oligarch"]),
        ("Two Oligarchs own it.", ["oligarchs"]),
        ("The agency was Captured by the firm.", ["captured"]),
        ("Captured state institutions.", ["captured"]),
        ("Captured regulator named.", ["captured"]),
        ("Captured firm named.", ["captured"]),
        ("The fund captured the market.", []),
        ("Captured.", []),
        ("The firm captured returns.", []),
        ("It was incorruptible.", []),
        ("The stake was recaptured.", []),
        ("Captured by the state. language-rule-ok", []),
        ("Do not write corrupt. language-rule-ok", []),
    ]
    text = "\n".join(line for line, _ in cases) + "\n"
    path = tmp_path / "sample.md"
    path.write_text(text, encoding="utf-8")
    expected = [
        (lineno, word)
        for lineno, (_, words) in enumerate(cases, 1)
        for word in words
    ]
    actual = [(lineno, word) for lineno, word, _ in scan_file(path)]
    assert actual == expected

"""Locate the pages of an annual report that most likely hold the roster tables."""

from __future__ import annotations

import argparse
import shutil
import statistics
import subprocess

import pandas as pd

COMMISSIONERS = (
    "board of commissioners",
    "dewan komisaris",
    "komisaris independen",
    "independent commissioner",
    "president commissioner",
    "komisaris utama",
)
DIRECTORS = (
    "board of directors",
    "direksi",
    "president director",
    "direktur utama",
)
SHAREHOLDERS = (
    "shareholder",
    "pemegang saham",
    "share ownership",
    "kepemilikan saham",
)
APPOINTMENT = (
    "appointed",
    "diangkat",
    "general meeting",
    "rups",
    "term of office",
    "masa jabatan",
    "fit and proper",
    "effective",
)

KEYWORDS = {
    "commissioners": COMMISSIONERS,
    "directors": DIRECTORS,
    "shareholders": SHAREHOLDERS,
    "appointment": APPOINTMENT,
}
KINDS = ("commissioners", "directors", "shareholders")
SCANNED_MEDIAN_CHARS = 100


def page_texts(pdf_path) -> list[str]:
    """Return the text of each page, using one `pdftotext -layout` run."""
    if shutil.which("pdftotext") is None:
        raise RuntimeError(
            "pdftotext is not installed; install poppler-utils (or poppler) to read PDFs"
        )
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    pages = result.stdout.split("\f")
    if pages and pages[-1].strip() == "":
        pages = pages[:-1]
    return pages


def _hits(text: str, words) -> int:
    lowered = text.lower()
    return sum(lowered.count(w) for w in words)


def score_pages(texts: list[str]) -> pd.DataFrame:
    """Keyword hit counts per page (page numbers are 1-based)."""
    rows = []
    for i, text in enumerate(texts, start=1):
        row = {"page": i, "chars": len(text)}
        for name, words in KEYWORDS.items():
            row[name] = _hits(text, words)
        rows.append(row)
    columns = ["page", "chars", "commissioners", "directors", "shareholders", "appointment"]
    return pd.DataFrame(rows, columns=columns)


def likely_pages(scores: pd.DataFrame, kind: str, top: int = 10) -> list[int]:
    """Pages ranked by hits for `kind` plus half the appointment hits."""
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}, got {kind!r}")
    ranked = scores.assign(_rank=scores[kind] + 0.5 * scores["appointment"])
    ranked = ranked[ranked["_rank"] > 0]
    ranked = ranked.sort_values(["_rank", "page"], ascending=[False, True])
    return [int(p) for p in ranked["page"].head(top)]


def is_scanned(texts: list[str]) -> bool:
    """True when the median page has fewer than 100 characters of text."""
    if not texts:
        return True
    return statistics.median(len(t.strip()) for t in texts) < SCANNED_MEDIAN_CHARS


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path")
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args(argv)
    texts = page_texts(args.path)
    if is_scanned(texts):
        print("WARNING: this file looks scanned (little or no text layer); OCR is needed")
    scores = score_pages(texts)
    for kind in KINDS:
        print(f"{kind}: {likely_pages(scores, kind, args.top)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

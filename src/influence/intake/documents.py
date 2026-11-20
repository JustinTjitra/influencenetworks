"""Register primary documents in data/raw/documents.csv with their sha256."""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data" / "raw"
REGISTRY = RAW / "documents.csv"
COLUMNS = ["doc_id", "filename", "sha256", "title", "publisher", "year",
           "obtained_from", "note"]
_ID = re.compile(r"^[a-z0-9_]+$")


def sha256_of(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def page_count(path) -> int | None:
    if shutil.which("pdfinfo") is None:
        return None
    try:
        out = subprocess.run(["pdfinfo", str(path)], capture_output=True,
                             text=True, timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.search(r"^Pages:\s+(\d+)", out, re.M)
    return int(m.group(1)) if m else None


def has_text_layer(path, sample_pages: int = 5) -> bool | None:
    if shutil.which("pdftotext") is None:
        return None
    try:
        out = subprocess.run(
            ["pdftotext", "-f", "1", "-l", str(sample_pages), str(path), "-"],
            capture_output=True, text=True, timeout=120).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    return len("".join(out.split())) >= 200


def _read(registry_csv) -> list[dict]:
    p = Path(registry_csv)
    if not p.exists():
        return []
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _relative(pdf: Path, raw_root: Path) -> str:
    try:
        return pdf.resolve().relative_to(raw_root.resolve()).as_posix()
    except ValueError:
        return "docs/" + pdf.name


def register(registry_csv, pdf_path, doc_id, title, publisher, year,
             obtained_from, note="") -> dict:
    registry_csv = Path(registry_csv)
    pdf = Path(pdf_path)
    if not _ID.match(doc_id or ""):
        raise ValueError(f"invalid doc_id {doc_id!r}: use lowercase letters, digits, underscore")
    if not pdf.is_file():
        raise ValueError(f"file not found: {pdf}")
    digest = sha256_of(pdf)
    rows = _read(registry_csv)
    for r in rows:
        if r["doc_id"] == doc_id:
            if r["sha256"] != digest:
                raise ValueError(f"id {doc_id} already registered with a different sha256")
            return r
    for r in rows:
        if r["sha256"] == digest:
            raise ValueError(f"same file already registered as {r['doc_id']}")
    pages = page_count(pdf)
    text = has_text_layer(pdf)
    auto = (f"{pages} pages" if pages is not None else "pages unknown") + "; text layer: " + \
        ("yes" if text else "no" if text is False else "unknown")
    row = {
        "doc_id": doc_id,
        "filename": _relative(pdf, registry_csv.parent),
        "sha256": digest,
        "title": title,
        "publisher": publisher,
        "year": str(year),
        "obtained_from": obtained_from,
        "note": f"{note}; {auto}" if note else auto,
    }
    new = not registry_csv.exists() or registry_csv.stat().st_size == 0
    registry_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(registry_csv, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        if new:
            w.writeheader()
        w.writerow(row)
    return row


def verify(registry_csv=REGISTRY, root=RAW) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). Missing files are warnings only."""
    errors: list[str] = []
    warnings: list[str] = []
    for r in _read(registry_csv):
        p = Path(root) / r["filename"]
        if not p.is_file():
            warnings.append(f"missing: {r['doc_id']} ({r['filename']})")
        elif sha256_of(p) != r["sha256"]:
            errors.append(f"hash mismatch: {r['doc_id']} ({r['filename']})")
    return errors, warnings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="influence.intake.documents")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("register")
    r.add_argument("--pdf", required=True)
    r.add_argument("--id", required=True)
    r.add_argument("--title", required=True)
    r.add_argument("--publisher", required=True)
    r.add_argument("--year", required=True)
    r.add_argument("--from", dest="obtained_from", required=True)
    r.add_argument("--note", default="")
    r.add_argument("--registry", default=str(REGISTRY))
    v = sub.add_parser("verify")
    v.add_argument("--registry", default=str(REGISTRY))
    v.add_argument("--root", default=str(RAW))
    a = ap.parse_args(argv)
    if a.cmd == "register":
        try:
            row = register(a.registry, a.pdf, a.id, a.title, a.publisher, a.year,
                           a.obtained_from, a.note)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        print(f"registered {row['doc_id']} {row['sha256']}")
        return 0
    errors, warnings = verify(a.registry, a.root)
    for w in warnings:
        print("warning:", w)
    for e in errors:
        print("error:", e)
    print(f"{len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

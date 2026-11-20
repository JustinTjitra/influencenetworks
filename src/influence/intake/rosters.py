"""Board roster CSV template, validator and edge converter (no name matching)."""

from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TICKERS_PATH = ROOT / "data" / "mappings" / "tickers.csv"
COLUMNS = ["doc_id", "ticker", "organ", "person_name", "role", "start_date",
           "end_date", "page", "appointed_by", "note", "government_post",
           "government_body", "post_start", "post_end", "post_page"]
EDGE_COLUMNS = ["source_id", "target_id", "type", "source_url", "source_type",
                "confidence", "role", "start_date", "end_date", "pct",
                "amount_usd", "note"]
ORGANS = {"commissioners", "directors"}
REQUIRED = ["doc_id", "ticker", "organ", "person_name", "role", "page"]
_DATE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")


def template(doc_id: str, ticker: str) -> str:
    header = ",".join(COLUMNS)
    ex1 = [doc_id, ticker, "commissioners", "Example Person One",
           "President Commissioner", "2025-03-26", "", "168", "AGM", "", "", "",
           "", "", ""]
    ex2 = [doc_id, ticker, "directors", "Example Person Two", "Director",
           "2024", "", "172", "", "", "Deputy Minister", "Example Ministry",
           "2024-10", "", "40"]
    return "\n".join([header, "# " + ",".join(ex1), "# " + ",".join(ex2)]) + "\n"


def person_id(name: str) -> str:
    """Proposed id only; never looked up or merged with existing people."""
    return "p_" + re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")


def _s(v) -> str:
    return "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v)


def _date_ok(s: str) -> bool:
    if not _DATE.match(s):
        return False
    parts = [int(p) for p in s.split("-")]
    if len(parts) >= 2 and not 1 <= parts[1] <= 12:
        return False
    if len(parts) == 3:
        try:
            pd.Timestamp(s)
        except ValueError:
            return False
    return True


def _pos_int(s: str) -> bool:
    return bool(re.fullmatch(r"\d+", s)) and int(s) > 0


def _end_before_start(start: str, end: str) -> bool:
    # Compare on the common prefix length so YYYY vs YYYY-MM-DD works.
    n = min(len(start), len(end))
    return end[:n] < start[:n]


def validate(df: pd.DataFrame, tickers) -> list[str]:
    problems: list[str] = []
    known = set(tickers)
    for c in COLUMNS:
        if c not in df.columns:
            problems.append(f"missing column: {c}")
    if problems:
        return problems
    seen: dict[tuple, int] = {}
    for i, row in df.iterrows():
        n = i + 2
        r = {c: _s(row[c]) for c in COLUMNS}
        for c in REQUIRED:
            if not r[c].strip():
                problems.append(f"row {n}: {c} is required")
        if r["organ"] and r["organ"] not in ORGANS:
            problems.append(f"row {n}: organ {r['organ']!r} must be commissioners or directors")
        if r["ticker"] and r["ticker"] not in known:
            problems.append(f"row {n}: unknown ticker {r['ticker']!r}")
        for a, b in (("start_date", "end_date"), ("post_start", "post_end")):
            ok = True
            for c in (a, b):
                if r[c] and not _date_ok(r[c]):
                    problems.append(f"row {n}: {c} {r[c]!r} is not YYYY, YYYY-MM or YYYY-MM-DD")
                    ok = False
            if ok and r[a] and r[b] and _end_before_start(r[a], r[b]):
                problems.append(f"row {n}: {b} {r[b]} is before {a} {r[a]}")
        if r["page"] and not _pos_int(r["page"]):
            problems.append(f"row {n}: page {r['page']!r} must be a positive integer")
        if r["post_page"] and not _pos_int(r["post_page"]):
            problems.append(f"row {n}: post_page {r['post_page']!r} must be a positive integer")
        if r["government_post"]:
            if not r["government_body"]:
                problems.append(f"row {n}: government_post requires government_body")
            if not r["post_page"]:
                problems.append(f"row {n}: government_post requires post_page")
        if r["person_name"] != r["person_name"].strip():
            problems.append(f"row {n}: person_name has leading or trailing spaces")
        key = (r["person_name"], r["organ"], r["start_date"])
        if key in seen:
            problems.append(f"row {n}: duplicate of row {seen[key]} (person_name, organ, start_date)")
        else:
            seen[key] = n
    return problems


def to_edges(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        r = {c: _s(row.get(c, "")) for c in COLUMNS}
        pid = person_id(r["person_name"])
        rows.append({
            "source_id": pid, "target_id": "", "ticker": r["ticker"],
            "type": "board_seat", "source_url": f"doc:{r['doc_id']}#p{r['page']}",
            "source_type": "annual_report", "confidence": "high",
            "role": r["role"], "start_date": r["start_date"],
            "end_date": r["end_date"], "pct": "", "amount_usd": "",
            "note": r["note"],
        })
        if r["government_post"]:
            rows.append({
                "source_id": pid, "target_id": "", "ticker": "",
                "type": "held_office",
                "source_url": f"doc:{r['doc_id']}#p{r['post_page']}",
                "source_type": "annual_report", "confidence": "high",
                "role": r["government_post"], "start_date": r["post_start"],
                "end_date": r["post_end"], "pct": "", "amount_usd": "",
                "note": r["government_body"],
            })
    return pd.DataFrame(rows, columns=EDGE_COLUMNS[:1] + ["target_id", "ticker"]
                        + EDGE_COLUMNS[2:])


def tickers_from_file(path: Path = TICKERS_PATH) -> list[str]:
    return sorted(pd.read_csv(path)["ticker"].dropna().unique())


def read_roster(path) -> pd.DataFrame:
    """Read a roster, skipping only lines whose first non-space character is #."""
    text = Path(path).read_text(encoding="utf-8") if not hasattr(path, "read") else path.read()
    kept = [ln for ln in text.splitlines() if not ln.lstrip().startswith("#")]
    return pd.read_csv(io.StringIO("\n".join(kept) + "\n"), dtype=str,
                       keep_default_na=False)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="influence.intake.rosters")
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("template")
    t.add_argument("--doc", required=True)
    t.add_argument("--ticker", required=True)
    v = sub.add_parser("validate")
    v.add_argument("path")
    a = ap.parse_args(argv)
    if a.cmd == "template":
        sys.stdout.write(template(a.doc, a.ticker))
        return 0
    problems = validate(read_roster(a.path), tickers_from_file())
    for p in problems:
        print(p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

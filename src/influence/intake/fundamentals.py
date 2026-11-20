"""Schema and validator for data/mappings/fundamentals.csv (hand-collected, no prices)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "data" / "mappings" / "fundamentals.csv"
TICKERS_PATH = ROOT / "data" / "mappings" / "tickers.csv"
COLUMNS = ["ticker", "fiscal_year_end", "shares_outstanding", "total_assets",
           "total_liabilities", "currency", "unit", "source_url", "note"]
UNITS = {"1": 1.0, "1e3": 1e3, "1e6": 1e6, "1e9": 1e9}
YEARS = [2021, 2022, 2023, 2024, 2025]
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_URL = re.compile(r"^https?://\S+$")
_DOC = re.compile(r"^doc:[^\s#]+#p\d+$")


def _is_date(s) -> bool:
    if not isinstance(s, str) or not _DATE.match(s):
        return False
    try:
        pd.Timestamp(s)
    except ValueError:
        return False
    return True


def _num(x) -> float:
    return float(pd.to_numeric(x, errors="coerce"))


def validate(df: pd.DataFrame, tickers) -> list[str]:
    problems: list[str] = []
    known = set(tickers)
    seen: set = set()
    for i, r in enumerate(df.to_dict("records")):
        where = f"row {i + 2}"
        t = r.get("ticker")
        if t not in known:
            problems.append(f"{where}: ticker {t!r} not in the ticker list")
        fye = r.get("fiscal_year_end")
        if not _is_date(fye):
            problems.append(f"{where}: fiscal_year_end {fye!r} is not YYYY-MM-DD")
        key = (t, fye)
        if key in seen:
            problems.append(f"{where}: duplicate (ticker, fiscal_year_end) {key}")
        seen.add(key)
        shares, assets, liab = (_num(r.get(c)) for c in
                                ("shares_outstanding", "total_assets", "total_liabilities"))
        if not shares > 0:
            problems.append(f"{where}: shares_outstanding must be positive")
        if not assets > 0:
            problems.append(f"{where}: total_assets must be positive")
        if not liab >= 0:
            problems.append(f"{where}: total_liabilities must not be negative")
        elif assets > 0 and liab > 1.5 * assets:
            problems.append(f"{where}: total_liabilities exceed 1.5 x total_assets")
        if r.get("currency") != "IDR":
            problems.append(f"{where}: currency {r.get('currency')!r} is not IDR")
        if str(r.get("unit")) not in UNITS:
            problems.append(f"{where}: unit {r.get('unit')!r} not one of 1, 1e3, 1e6, 1e9")
        url = r.get("source_url")
        if not isinstance(url, str) or not (_URL.match(url) or _DOC.match(url)):
            problems.append(f"{where}: source_url {url!r} is neither http(s)://... nor doc:<id>#p<page>")
    return problems


def tickers_from_file(path: Path = TICKERS_PATH) -> list[str]:
    return sorted(pd.read_csv(path)["ticker"].dropna().unique())


def load(path: Path = PATH, tickers=None) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"unit": str, "ticker": str, "fiscal_year_end": str})
    if tickers is None:
        tickers = tickers_from_file()
    problems = validate(df, tickers)
    if problems:
        raise ValueError("fundamentals.csv has problems:\n" + "\n".join(problems))
    out = df.copy()
    scale = out["unit"].map(UNITS)
    for c in ("total_assets", "total_liabilities"):
        out[c] = pd.to_numeric(out[c]) * scale
    out["shares_outstanding"] = pd.to_numeric(out["shares_outstanding"])
    out["unit"] = "1"
    return out


def coverage(df: pd.DataFrame, tickers, years=YEARS) -> pd.DataFrame:
    have = set()
    for t, f in zip(df["ticker"], df["fiscal_year_end"]):
        have.add((t, pd.Timestamp(f).year))
    rows = [{"ticker": t, **{y: (t, y) in have for y in years}} for t in tickers]
    return pd.DataFrame(rows, columns=["ticker", *years])


def main() -> int:
    tickers = tickers_from_file()
    try:
        df = load(PATH, tickers)
    except ValueError as e:
        print(e)
        return 1
    print(coverage(df, tickers, YEARS).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

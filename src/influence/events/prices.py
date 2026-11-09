"""Daily prices: download (on the project owner's machine), load, coverage report.

    python -m influence.events.prices download            # all tickers + ^JKSE, from 2019
    python -m influence.events.prices report              # coverage of the latest download

Raw files go to data/raw/prices/<download_date>/<ticker>.parquet and are never
edited or committed. Each download is a new folder, so results can always be traced
to the exact files they came from.

Pre-registration guard. `download` refuses to run until docs/paper/prereg.md exists
and records the commit at which it was registered, and that commit exists in this
repository. The event set, signs, models and windows are fixed before any price is
seen; this function is where that rule is enforced in code.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import date
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data" / "raw" / "prices"
PREREG = ROOT / "docs" / "paper" / "prereg.md"
MARKET = "^JKSE"
PANEL_COLUMNS = ["date", "ticker", "close", "adj_close", "volume"]
_HASH_LINE = re.compile(r"^Registration commit:\s*`?([0-9a-f]{7,40})`?\s*$", re.M)


class PreregistrationError(RuntimeError):
    pass


def registration_commit(prereg: Path = PREREG, repo: Path = ROOT) -> str:
    """Return the registered commit hash, or raise if registration is not complete."""
    if not prereg.exists():
        raise PreregistrationError(f"{prereg} does not exist: register the design first")
    m = _HASH_LINE.search(prereg.read_text(encoding="utf-8"))
    if not m:
        raise PreregistrationError(
            f"{prereg.name} has no 'Registration commit: <hash>' line; "
            "commit and push the pre-registration, then record its hash")
    sha = m.group(1)
    ok = subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{sha}^{{commit}}"],
                        capture_output=True).returncode == 0
    if not ok:
        raise PreregistrationError(f"registration commit {sha} is not in this repository")
    return sha


def yahoo_symbol(ticker: str) -> str:
    return ticker if ticker.startswith("^") else f"{ticker}.JK"


def download(tickers: Iterable[str], start: str = "2019-01-01", end: Optional[str] = None,
             out_root: Path = RAW, prereg: Path = PREREG) -> Path:
    """Download daily bars with yfinance into a new dated folder. Returns the folder."""
    sha = registration_commit(prereg)
    import yfinance as yf                      # imported here: not needed for analysis

    end = end or date.today().isoformat()
    out = out_root / date.today().isoformat()
    out.mkdir(parents=True, exist_ok=True)
    wanted = list(dict.fromkeys([MARKET, *tickers]))
    manifest = dict(downloaded=date.today().isoformat(), start=start, end=end,
                    registration_commit=sha, yfinance=yf.__version__, tickers={})
    for t in wanted:
        raw = yf.download(yahoo_symbol(t), start=start, end=end, auto_adjust=False,
                          actions=True, progress=False, threads=False)
        if raw is None or raw.empty:
            manifest["tickers"][t] = dict(rows=0, note="no data returned")
            continue
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
        df = raw.rename(columns=lambda c: str(c).lower().replace(" ", "_")).reset_index()
        df = df.rename(columns={"Date": "date", "index": "date"})
        df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
        df.insert(1, "ticker", t)
        df.to_parquet(out / f"{t.replace('^', 'IDX_')}.parquet", index=False)
        manifest["tickers"][t] = dict(rows=len(df), first=str(df.date.min().date()),
                                      last=str(df.date.max().date()))
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return out


def latest_dir(root: Path = RAW) -> Path:
    dirs = sorted(d for d in root.glob("*") if d.is_dir() and (d / "manifest.json").exists())
    if not dirs:
        raise FileNotFoundError(f"no price download under {root}; see docs/RUNNING.md")
    return dirs[-1]


def load(price_dir: Optional[Path] = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (tidy panel, coverage report) for one download folder.

    The panel has one row per (date, ticker) with close, adj_close and volume, and
    includes the market index under the ticker "^JKSE".
    """
    price_dir = Path(price_dir) if price_dir else latest_dir()
    frames = []
    for f in sorted(price_dir.glob("*.parquet")):
        df = pd.read_parquet(f)
        if "adj_close" not in df.columns and "close" in df.columns:
            df["adj_close"] = df["close"]
        frames.append(df[[c for c in PANEL_COLUMNS if c in df.columns]])
    if not frames:
        raise FileNotFoundError(f"no parquet files in {price_dir}")
    panel = pd.concat(frames, ignore_index=True)
    panel["date"] = pd.to_datetime(panel["date"]).dt.normalize()
    panel = panel.dropna(subset=["adj_close"]).sort_values(["ticker", "date"]).reset_index(drop=True)
    return panel, coverage_report(panel)


def coverage_report(panel: pd.DataFrame, market: str = MARKET) -> pd.DataFrame:
    """Per ticker: span, days missing against the exchange calendar, days with no
    trade, the longest gap and the longest run of an unchanged price."""
    cal = pd.DatetimeIndex(sorted(panel.loc[panel.ticker == market, "date"].unique()))
    rows = []
    for t, df in panel.groupby("ticker", sort=True):
        if t == market:
            continue
        df = df.set_index("date").sort_index()
        span = cal[(cal >= df.index.min()) & (cal <= df.index.max())]
        present = span.isin(df.index)
        gaps = _longest_run(~present)
        px = df["adj_close"].reindex(span)
        stale = _longest_run((px.diff() == 0).to_numpy())
        vol = df["volume"].reindex(span) if "volume" in df else pd.Series(np.nan, index=span)
        rows.append(dict(
            ticker=t, first_date=df.index.min().date(), last_date=df.index.max().date(),
            calendar_days=len(span), missing_days=int((~present).sum()),
            zero_volume_days=int((vol == 0).sum()),
            zero_volume_share=float((vol == 0).mean()) if len(span) else float("nan"),
            longest_gap_days=gaps, longest_unchanged_price_run=stale,
            off_calendar_rows=int((~df.index.isin(cal)).sum()),
            ends_before_calendar=bool(len(cal) and df.index.max() < cal.max()),
        ))
    return pd.DataFrame(rows)


def _longest_run(flags: np.ndarray) -> int:
    best = cur = 0
    for f in flags:
        cur = cur + 1 if f else 0
        best = max(best, cur)
    return int(best)


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("download")
    d.add_argument("--start", default="2019-01-01")
    d.add_argument("--end", default=None)
    r = sub.add_parser("report")
    r.add_argument("--dir", default=None)
    args = ap.parse_args(argv)
    if args.cmd == "download":
        from .eventset import load_tickers
        out = download(load_tickers().ticker.tolist(), args.start, args.end)
        print(f"wrote {out}")
        args.dir = out
    _, cov = load(args.dir)
    print(cov.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

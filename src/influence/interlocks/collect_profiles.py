"""Save the exchange's company profile for each ticker, raw and dated.

Run on the owner's own machine (the exchange site is behind Cloudflare and cannot be
reached from cloud sessions). Responses are written unchanged to
data/raw/idx_profiles/<YYYY-MM-DD>/<TICKER>.json; parsing is a separate step.
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import sys
import time
from datetime import date
from pathlib import Path
from typing import Callable, Iterable, List, Sequence, Tuple
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT = ROOT / "data" / "raw" / "idx_profiles"
DEFAULT_TICKERS = ROOT / "data" / "mappings" / "tickers.csv"

# The endpoint is reported by third-party scrapers, not confirmed by the exchange's
# own documentation. Keep the base and the path here so they are easy to correct.
BASE_URL = "https://www.idx.co.id"
PROFILE_PATH = "/primary/ListedCompany/GetCompanyProfilesDetail"

MAX_CONSECUTIVE_FAILURES = 3

Fetch = Callable[[str], Tuple[int, bytes]]


def profile_url(ticker: str, base: str = BASE_URL) -> str:
    return f"{base.rstrip('/')}{PROFILE_PATH}?KodeEmiten={quote(ticker.strip().upper())}&language=en-us"


def out_path(root, day: str, ticker: str) -> Path:
    return Path(root) / str(day) / f"{ticker.strip().upper()}.json"


def load_tickers(csv_path) -> List[str]:
    """Distinct non-empty tickers from the `ticker` column, in file order."""
    seen: List[str] = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            t = (row.get("ticker") or "").strip().upper()
            if t and t not in seen:
                seen.append(t)
    return seen


def plan(tickers: Iterable[str], root, day: str) -> List[str]:
    """Tickers whose output file is missing or empty."""
    todo = []
    for t in tickers:
        p = out_path(root, day, t)
        if not (p.exists() and p.stat().st_size > 0):
            todo.append(t)
    return todo


def _looks_like_json(body: bytes) -> bool:
    """False for empty bodies and for HTML block pages served with status 200."""
    if body.startswith(b"\xef\xbb\xbf"):
        body = body[3:]
    return body.lstrip()[:1] in (b"{", b"[")


def fetch_all(tickers: Sequence[str], root, day: str, fetch: Fetch, sleep: Callable[[float], None],
              min_delay: float = 3.0, max_delay: float = 6.0) -> List[Tuple[str, int, int]]:
    """Fetch each pending ticker; returns (ticker, status, bytes_written) per request made.

    Stops after 3 consecutive failures (non-200 status, a body not starting with { or [, or an exception).
    """
    results: List[Tuple[str, int, int]] = []
    failures = 0
    first = True
    for t in plan(tickers, root, day):
        if not first:
            sleep(random.uniform(min_delay, max_delay))
        first = False
        try:
            status, body = fetch(profile_url(t))
        except Exception:
            status, body = 0, b""
        written = 0
        if status == 200 and _looks_like_json(body):
            p = out_path(root, day, t)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(body)
            written = len(body)
            failures = 0
        else:
            failures += 1
        results.append((t, status, written))
        if failures >= MAX_CONSECUTIVE_FAILURES:
            break
    return results


def make_http_fetch() -> Fetch:
    contact = os.environ.get("CONTACT_EMAIL", "").strip()
    if not contact:
        raise SystemExit("CONTACT_EMAIL is not set. Set it to an address the exchange can "
                         "reach you on, then run again (it goes in the User-Agent).")
    import httpx

    client = httpx.Client(headers={"User-Agent": f"influencenetworks-research (contact: {contact})"},
                          timeout=30, follow_redirects=True)

    def fetch(url: str) -> Tuple[int, bytes]:
        r = client.get(url)
        return r.status_code, r.content

    return fetch


def make_browser_fetch() -> Tuple[Fetch, Callable[[], None]]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("Playwright is not installed. Run: pip install playwright && "
                         "playwright install chromium")
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=False)
    page = browser.new_context().new_page()
    page.goto(BASE_URL, wait_until="domcontentloaded")  # let the site set its cookies first

    def fetch(url: str) -> Tuple[int, bytes]:
        resp = page.context.request.get(url)
        return resp.status, resp.body()

    def close() -> None:
        browser.close()
        pw.stop()

    return fetch, close


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Save raw IDX company profiles, one JSON file per ticker.")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--browser", action="store_true", help="fetch through Playwright (needed if plain HTTP is blocked)")
    mode.add_argument("--http", action="store_true", help="fetch with httpx; requires CONTACT_EMAIL")
    ap.add_argument("--tickers-file", default=str(DEFAULT_TICKERS))
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="output root (not committed)")
    ap.add_argument("--limit", type=int, default=None, help="only the first N tickers still to fetch")
    ap.add_argument("--day", default=None, help="YYYY-MM-DD folder name (default: today)")
    args = ap.parse_args(argv)

    close = lambda: None
    if args.http:
        fetch = make_http_fetch()
    else:
        fetch, close = make_browser_fetch()
    day = args.day or date.today().isoformat()
    tickers = load_tickers(args.tickers_file)
    todo = plan(tickers, args.out, day)
    if args.limit is not None:
        todo = todo[: args.limit]
    try:
        results = fetch_all(todo, args.out, day, fetch, time.sleep)
    finally:
        close()
    for t, status, n in results:
        print(f"{t}\t{status}\t{n}")
    ok = sum(1 for _, s, n in results if n)
    print(f"{ok}/{len(todo)} saved under {Path(args.out) / day}")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

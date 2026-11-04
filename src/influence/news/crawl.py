"""Polite, robots-respecting article collector.

Two ways to get article URLs:
  1. sitemaps listed in each outlet's robots.txt (good for recent articles), or
  2. a URL list you already have, e.g. from GDELT (see docs/gdelt_urls.sql),
     which is the practical route to 2021-2025 history.

Fetched HTML is stored gzipped under data/raw/news/<domain>/ so extraction can
be re-run without re-crawling. Extracted articles go to data/processed/articles.parquet.

Usage (on your own machine; this workspace has no general internet):
  python -m influence.news.crawl sitemaps --outlet detik.com --since 2025-01-01 --max 500
  python -m influence.news.crawl urls --file gdelt_urls.csv --max 5000
  python -m influence.news.crawl extract
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import os
import random
import sys
import time
import xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, Iterator, Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

from .outlets import OUTLETS, USER_AGENT

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data" / "raw" / "news"
PROC = ROOT / "data" / "processed"
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def outlet_of(url: str) -> Optional[str]:
    host = urlparse(url).netloc.lower()
    for dom in OUTLETS:
        if host == dom or host.endswith("." + dom):
            return dom
    return None


class PoliteClient:
    """One request at a time per domain, with a randomised delay and robots checks."""

    def __init__(self, client: Optional[httpx.Client] = None, min_delay: float = 2.0,
                 max_delay: float = 5.0):
        ua = USER_AGENT.replace("set CONTACT_EMAIL env var", os.environ.get("CONTACT_EMAIL", "unset"))
        self.client = client or httpx.Client(headers={"User-Agent": ua}, timeout=20,
                                             follow_redirects=True)
        self.ua = ua
        self.min_delay, self.max_delay = min_delay, max_delay
        self._robots: dict[str, RobotFileParser] = {}
        self._last: dict[str, float] = {}

    def robots(self, domain: str) -> RobotFileParser:
        if domain not in self._robots:
            rp = RobotFileParser()
            try:
                r = self.client.get(f"https://www.{domain}/robots.txt")
                rp.parse(r.text.splitlines() if r.status_code == 200 else [])
            except httpx.HTTPError:
                rp.parse([])
            self._robots[domain] = rp
        return self._robots[domain]

    def allowed(self, url: str) -> bool:
        dom = outlet_of(url)
        return bool(dom) and OUTLETS[dom]["crawl"] and self.robots(dom).can_fetch(self.ua, url)

    def get(self, url: str) -> Optional[httpx.Response]:
        if not self.allowed(url):
            return None
        dom = outlet_of(url)
        wait = self._last.get(dom, 0) + random.uniform(self.min_delay, self.max_delay) - time.time()
        if wait > 0:
            time.sleep(wait)
        for attempt in range(3):
            try:
                r = self.client.get(url)
                self._last[dom] = time.time()
                if r.status_code == 429 or r.status_code >= 500:
                    time.sleep(10 * (attempt + 1))
                    continue
                return r
            except httpx.HTTPError:
                time.sleep(5 * (attempt + 1))
        return None


def parse_sitemap(xml_text: str) -> tuple[list[str], list[tuple[str, Optional[str]]]]:
    """Return (child_sitemaps, [(url, lastmod)])."""
    root = ET.fromstring(xml_text.encode("utf-8") if isinstance(xml_text, str) else xml_text)
    tag = root.tag.split("}")[-1]
    if tag == "sitemapindex":
        return [e.text.strip() for e in root.findall("sm:sitemap/sm:loc", NS) if e.text], []
    urls = []
    for u in root.findall("sm:url", NS):
        loc = u.find("sm:loc", NS)
        lm = u.find("sm:lastmod", NS)
        if loc is not None and loc.text:
            urls.append((loc.text.strip(), lm.text.strip() if lm is not None and lm.text else None))
    return [], urls


def sitemap_urls(pc: PoliteClient, domain: str, since: Optional[date],
                 limit: int) -> Iterator[str]:
    queue = list(pc.robots(domain).site_maps() or [])
    seen = set()
    n = 0
    while queue and n < limit:
        sm = queue.pop(0)
        if sm in seen:
            continue
        seen.add(sm)
        r = pc.get(sm) if pc.allowed(sm) else None
        if r is None or r.status_code != 200:
            continue
        body = gzip.decompress(r.content).decode("utf-8", "replace") if sm.endswith(".gz") else r.text
        try:
            children, urls = parse_sitemap(body)
        except ET.ParseError:
            continue
        queue.extend(children)
        for u, lm in urls:
            if since and lm:
                try:
                    if datetime.fromisoformat(lm.replace("Z", "+00:00")).date() < since:
                        continue
                except ValueError:
                    pass
            yield u
            n += 1
            if n >= limit:
                return


def raw_path(url: str) -> Path:
    dom = outlet_of(url) or "other"
    h = hashlib.sha1(url.encode()).hexdigest()
    return RAW / dom / f"{h}.html.gz"


def fetch_all(pc: PoliteClient, urls: Iterable[str]) -> int:
    got = 0
    for url in urls:
        p = raw_path(url)
        if p.exists():
            continue
        r = pc.get(url)
        if r is None or r.status_code != 200 or "html" not in r.headers.get("content-type", "html"):
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(p, "wt", encoding="utf-8") as f:
            f.write(url + "\n" + r.text)
        got += 1
    return got


def extract_one(stored: str) -> Optional[dict]:
    """stored = first line URL, rest HTML (as written by fetch_all)."""
    import trafilatura

    url, _, html = stored.partition("\n")
    doc = trafilatura.bare_extraction(html, url=url, with_metadata=True,
                                      include_comments=False, favor_precision=True)
    if not doc:
        return None
    d = doc if isinstance(doc, dict) else doc.as_dict()
    text = d.get("text") or ""
    if len(text) < 300:      # nav pages, galleries, video-only stubs
        return None
    return {
        "url": url,
        "outlet": outlet_of(url),
        "group": OUTLETS.get(outlet_of(url) or "", {}).get("group"),
        "published": d.get("date"),
        "title": d.get("title"),
        "author": d.get("author"),
        "text": text,
        "text_sha1": hashlib.sha1(text.encode()).hexdigest(),
    }


def extract_all() -> int:
    import pandas as pd

    rows = []
    for p in RAW.glob("*/*.html.gz"):
        with gzip.open(p, "rt", encoding="utf-8") as f:
            row = extract_one(f.read())
        if row:
            rows.append(row)
    if not rows:
        return 0
    df = pd.DataFrame(rows)
    # Syndicated copies (same text on sister sites) would inflate counts.
    df["duplicate_of_group_copy"] = df.duplicated(subset=["group", "text_sha1"], keep="first")
    PROC.mkdir(parents=True, exist_ok=True)
    df.to_parquet(PROC / "articles.parquet", index=False)
    return len(df)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sitemaps")
    s.add_argument("--outlet", required=True, choices=sorted(OUTLETS))
    s.add_argument("--since", type=date.fromisoformat)
    s.add_argument("--max", type=int, default=500)
    u = sub.add_parser("urls")
    u.add_argument("--file", required=True, help="CSV/TXT with a 'url' column or one URL per line")
    u.add_argument("--max", type=int, default=5000)
    sub.add_parser("extract")
    a = ap.parse_args(argv[1:])

    if a.cmd == "extract":
        print(f"extracted {extract_all()} articles")
        return 0
    pc = PoliteClient()
    if a.cmd == "sitemaps":
        urls = list(sitemap_urls(pc, a.outlet, a.since, a.max))
    else:
        text = Path(a.file).read_text(encoding="utf-8").splitlines()
        if text and text[0].strip().lower().startswith("url"):
            import csv
            urls = [r["url"] for r in csv.DictReader(text)]
        else:
            urls = [t.strip() for t in text if t.strip()]
        urls = [x for x in urls if outlet_of(x)][: a.max]
    print(f"{len(urls)} candidate URLs; fetching (this is deliberately slow)")
    print(f"fetched {fetch_all(pc, urls)} new pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

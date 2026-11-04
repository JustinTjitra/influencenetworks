import gzip

import httpx
import pandas as pd

from influence.news import crawl
from influence.news.crawl import PoliteClient, extract_one, outlet_of, parse_sitemap
from influence.news.tag_entities import build_patterns, tag

ROBOTS = "User-agent: *\nDisallow: /search\nSitemap: https://www.detik.com/sitemap.xml\n"
INDEX = """<?xml version="1.0"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<sitemap><loc>https://www.detik.com/sm-2025.xml</loc></sitemap></sitemapindex>"""
URLSET = """<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>https://news.detik.com/berita/d-1/a</loc><lastmod>2025-03-01T10:00:00+07:00</lastmod></url>
<url><loc>https://news.detik.com/berita/d-2/b</loc><lastmod>2020-01-01</lastmod></url>
</urlset>"""


def handler(req: httpx.Request) -> httpx.Response:
    path = req.url.path
    if path == "/robots.txt":
        return httpx.Response(200, text=ROBOTS)
    if path == "/sitemap.xml":
        return httpx.Response(200, text=INDEX)
    if path == "/sm-2025.xml":
        return httpx.Response(200, text=URLSET)
    return httpx.Response(200, text="<html></html>", headers={"content-type": "text/html"})


def client():
    return PoliteClient(httpx.Client(transport=httpx.MockTransport(handler)), 0, 0)


def test_outlet_of_handles_subdomains():
    assert outlet_of("https://news.detik.com/x") == "detik.com"
    assert outlet_of("https://example.com/x") is None


def test_robots_disallow_respected():
    pc = client()
    assert pc.allowed("https://www.detik.com/berita/x")
    assert not pc.allowed("https://www.detik.com/search?q=x")
    assert not pc.allowed("https://example.com/x")


def test_sitemap_walk_filters_by_date():
    from datetime import date
    urls = list(crawl.sitemap_urls(client(), "detik.com", date(2024, 1, 1), 10))
    assert urls == ["https://news.detik.com/berita/d-1/a"]


def test_parse_sitemap_index():
    children, urls = parse_sitemap(INDEX)
    assert children == ["https://www.detik.com/sm-2025.xml"] and urls == []


def test_extract_skips_stubs_and_keeps_articles():
    body = "Bank Rakyat Indonesia (BRI) melaporkan laba. " * 20
    html = f"<html><head><title>BRI laba naik</title></head><body><article><h1>BRI laba naik</h1><p>{body}</p></article></body></html>"
    row = extract_one("https://news.detik.com/berita/d-1/a\n" + html)
    assert row and row["outlet"] == "detik.com" and "BRI" in row["text"]
    assert extract_one("https://news.detik.com/x\n<html><body><p>short</p></body></html>") is None


def test_tagger_case_rules():
    nodes = pd.DataFrame({"id": ["p_x"], "type": ["person"], "name": ["Budi Santoso"], "aliases": [""]})
    aliases = pd.DataFrame({"node_id": ["bank_bri", "party_pkb"], "alias": ["BRI", "PKB"]})
    arts = pd.DataFrame({"url": ["u1"], "title": ["BRI dan budi santoso"],
                         "text": ["Kata bri tidak dihitung. BRI dihitung. pkb tidak."]})
    m = tag(arts, build_patterns(nodes, aliases)).set_index("node_id")
    assert m.loc["bank_bri", "count"] == 2        # title + body, uppercase only
    assert m.loc["p_x", "count"] == 1             # long name, case-insensitive
    assert "party_pkb" not in m.index

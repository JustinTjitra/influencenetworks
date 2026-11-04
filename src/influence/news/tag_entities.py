"""Tag articles with mentions of graph entities, using an explicit alias list.

Alias matching is deliberately simple and auditable: every alias is listed in
data/mappings/entity_aliases.csv (plus each node's own name). Short acronyms
(<= 5 characters, e.g. BRI, PKB) match case-sensitively on word boundaries;
longer names match case-insensitively.

Run:  python -m influence.news.tag_entities
Writes data/processed/mentions.parquet: one row per (article, entity) with a count.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
PROC = ROOT / "data" / "processed"
MAPS = ROOT / "data" / "mappings"
TAG_TYPES = {"person", "bank", "business_group", "party", "company"}


def build_patterns(nodes: pd.DataFrame, aliases: pd.DataFrame) -> list[tuple[str, re.Pattern]]:
    terms: dict[str, set[str]] = {}
    for r in nodes.itertuples():
        if r.type == "person":
            terms.setdefault(r.id, set()).add(r.name)
    for r in aliases.itertuples():
        terms.setdefault(r.node_id, set()).add(r.alias)
    pats = []
    for nid, ts in terms.items():
        cs = [re.escape(t) for t in ts if len(t) <= 5]
        ci = [re.escape(t) for t in ts if len(t) > 5]
        parts = []
        if cs:
            parts.append(r"(?-i:\b(?:" + "|".join(cs) + r")\b)")
        if ci:
            parts.append(r"\b(?:" + "|".join(ci) + r")\b")
        pats.append((nid, re.compile("|".join(parts), re.IGNORECASE)))
    return pats


def tag(articles: pd.DataFrame, pats: list[tuple[str, re.Pattern]]) -> pd.DataFrame:
    rows = []
    for a in articles.itertuples():
        text = f"{a.title or ''}\n{a.text}"
        for nid, p in pats:
            n = len(p.findall(text))
            if n:
                in_title = bool(p.search(a.title or ""))
                rows.append({"url": a.url, "node_id": nid, "count": n, "in_title": in_title})
    return pd.DataFrame(rows, columns=["url", "node_id", "count", "in_title"])


def main() -> int:
    nodes = pd.read_csv(PROC / "nodes.csv", dtype=str).fillna("")
    aliases = pd.read_csv(MAPS / "entity_aliases.csv", dtype=str).fillna("")
    articles = pd.read_parquet(PROC / "articles.parquet")
    m = tag(articles, build_patterns(nodes, aliases))
    m.to_parquet(PROC / "mentions.parquet", index=False)
    print(f"{len(m)} mentions across {m.url.nunique() if len(m) else 0} articles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

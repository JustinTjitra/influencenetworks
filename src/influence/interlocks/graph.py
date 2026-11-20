"""Company-to-company graph of shared board members on a given date.

An interlock is a derived relationship (two companies list the same person on their
boards on that date), not a statement about conduct by anyone.
"""
from __future__ import annotations

import datetime as dt
from itertools import combinations

import networkx as nx
import pandas as pd

LINK_COLUMNS = ["company_a", "company_b", "n_shared", "shared_people", "kind"]
KINDS = ("intra_group", "horizontal", "other")


def _clean(value) -> str:
    """Empty, None and NaN all mean 'not given'."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def active(seats: pd.DataFrame, on: dt.date) -> pd.DataFrame:
    """Seats in effect on `on`; start and end are inclusive, None means open-ended."""
    keep = [
        (pd.isna(s) or s is None or s <= on) and (pd.isna(e) or e is None or e >= on)
        for s, e in zip(seats["start"], seats["end"])
    ]
    return seats[pd.Series(keep, index=seats.index, dtype=bool)].copy()


def _kind(a: str, b: str, info: dict) -> str:
    ga, sa = info.get(a, ("", ""))
    gb, sb = info.get(b, ("", ""))
    if ga and ga == gb:
        return "intra_group"
    if sa and sa == sb:
        return "horizontal"
    return "other"


def interlocks(seats: pd.DataFrame, companies: pd.DataFrame, on: dt.date) -> pd.DataFrame:
    """One row per unordered company pair sharing at least one person on `on`."""
    info = {
        row.company: (_clean(row.group), _clean(row.sub_industry))
        for row in companies.itertuples(index=False)
    }
    now = active(seats, on)
    boards: dict[str, set[str]] = {}
    for row in now.itertuples(index=False):
        boards.setdefault(row.person_key, set()).add(row.company)

    shared: dict[tuple[str, str], set[str]] = {}
    for person, cos in boards.items():
        for a, b in combinations(sorted(cos), 2):
            shared.setdefault((a, b), set()).add(person)

    rows = []
    for (a, b), people in sorted(shared.items()):
        rows.append(
            {
                "company_a": a,
                "company_b": b,
                "n_shared": len(people),
                "shared_people": ";".join(sorted(people)),
                "kind": _kind(a, b, info),
            }
        )
    return pd.DataFrame(rows, columns=LINK_COLUMNS)


def summary(links: pd.DataFrame, companies: pd.DataFrame) -> dict:
    """Counts of companies, linked companies, links by kind, and density."""
    n = int(companies["company"].nunique())
    linked = set(links["company_a"]) | set(links["company_b"])
    by_kind = {k: int((links["kind"] == k).sum()) for k in KINDS}
    possible = n * (n - 1) / 2
    return {
        "n_companies": n,
        "n_linked_companies": len(linked),
        "n_links": int(len(links)),
        "by_kind": by_kind,
        "density": (len(links) / possible) if possible else 0.0,
    }


def to_networkx(links: pd.DataFrame) -> nx.Graph:
    """Undirected graph with `n_shared` and `kind` on each edge."""
    g = nx.Graph()
    for row in links.itertuples(index=False):
        g.add_edge(row.company_a, row.company_b, n_shared=int(row.n_shared), kind=row.kind)
    return g

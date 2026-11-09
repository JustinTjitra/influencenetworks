"""Load validated nodes/edges into a NetworkX graph and answer basic questions."""

from __future__ import annotations

import calendar
import csv
from datetime import date
from pathlib import Path
from typing import Iterable, Optional

import networkx as nx

from .schema import (
    Confidence, Edge, EdgeType, Node, NodeType, SchemaError, SourceType, validate_edge,
)


def _parse_date(s: str, end: bool = False) -> Optional[date]:
    """Parse YYYY, YYYY-MM or YYYY-MM-DD.

    A start date given only to the year or month is read as the first day of that
    period; an end date (end=True) as the last day. Both are the generous reading:
    an edge "2019 to 2024" is active throughout 2024, and a financing edge dated
    2015 to 2015 is active for the whole of 2015 rather than for one day.
    """
    s = (s or "").strip()
    if not s:
        return None
    parts = s.split("-")
    y = int(parts[0])
    if len(parts) == 1:
        return date(y, 12, 31) if end else date(y, 1, 1)
    m = int(parts[1])
    if len(parts) == 2:
        return date(y, m, calendar.monthrange(y, m)[1]) if end else date(y, m, 1)
    return date(y, m, int(parts[2]))


def _opt_float(s: str) -> Optional[float]:
    s = (s or "").strip()
    return float(s) if s else None


def load_nodes(path: Path) -> dict[str, Node]:
    nodes: dict[str, Node] = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            nid = row["id"].strip()
            if nid in nodes:
                raise SchemaError(f"duplicate node id {nid!r}")
            nodes[nid] = Node(
                id=nid,
                type=NodeType(row["type"].strip()),
                name=row["name"].strip(),
                aliases=[a.strip() for a in (row.get("aliases") or "").split(";") if a.strip()],
            )
    return nodes


def load_doc_registry(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with open(path, newline="", encoding="utf-8") as f:
        return {row["doc_id"].strip() for row in csv.DictReader(f)}


def load_edges(path: Path, nodes: dict[str, Node],
               doc_ids: Optional[set[str]] = None) -> tuple[list[Edge], list[str]]:
    """Return (valid_edges, errors). Invalid rows are reported, not silently dropped.

    If doc_ids is given, doc: sources must refer to a registered document.
    """
    edges, errors = [], []
    with open(path, newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            try:
                e = Edge(
                    source_id=row["source_id"].strip(),
                    target_id=row["target_id"].strip(),
                    type=EdgeType(row["type"].strip()),
                    source_url=row["source_url"].strip(),
                    source_type=SourceType(row["source_type"].strip()),
                    confidence=Confidence(row["confidence"].strip()),
                    role=(row.get("role") or "").strip() or None,
                    start_date=_parse_date(row.get("start_date", "")),
                    end_date=_parse_date(row.get("end_date", ""), end=True),
                    pct=_opt_float(row.get("pct", "")),
                    amount_usd=_opt_float(row.get("amount_usd", "")),
                    note=(row.get("note") or "").strip() or None,
                )
                validate_edge(e, nodes)
                if doc_ids is not None and e.source_url.startswith("doc:"):
                    did = e.source_url[4:].split("#")[0]
                    if did not in doc_ids:
                        raise SchemaError(f"unregistered document {did!r}")
                edges.append(e)
            except (SchemaError, ValueError, KeyError) as exc:
                errors.append(f"{path.name}:{i}: {exc}")
    return edges, errors


def build_graph(nodes: dict[str, Node], edges: Iterable[Edge]) -> nx.MultiDiGraph:
    g = nx.MultiDiGraph()
    for n in nodes.values():
        g.add_node(n.id, type=n.type.value, name=n.name, aliases=n.aliases)
    for e in edges:
        g.add_edge(
            e.source_id, e.target_id, key=e.type.value + (f":{e.role}" if e.role else ""),
            type=e.type.value, role=e.role, source_url=e.source_url,
            confidence=e.confidence.value, start=e.start_date, end=e.end_date, obj=e,
        )
    return g


def snapshot(g: nx.MultiDiGraph, on: date) -> nx.MultiDiGraph:
    """Subgraph of edges active on a given date (for 'linked at publication time')."""
    h = nx.MultiDiGraph()
    h.add_nodes_from(g.nodes(data=True))
    for u, v, k, d in g.edges(keys=True, data=True):
        if d["obj"].active_on(on):
            h.add_edge(u, v, key=k, **d)
    return h


def linked_entities(g: nx.MultiDiGraph, start: str, max_hops: int = 2) -> dict[str, int]:
    """Entities within max_hops of `start`, ignoring edge direction.

    This is how the media analysis defines an outlet's 'owner network':
    outlet -> media group -> owner -> (companies, party, family) within N hops.
    Returns {node_id: hop_distance}.
    """
    und = g.to_undirected(as_view=True)
    return dict(nx.single_source_shortest_path_length(und, start, cutoff=max_hops))


def paths_between(g: nx.MultiDiGraph, a: str, b: str, max_len: int = 4) -> list[list[str]]:
    """All simple paths up to max_len edges, with the evidence on each hop."""
    und = nx.Graph(g.to_undirected())
    return [p for p in nx.all_simple_paths(und, a, b, cutoff=max_len)]

"""Pure functions that load the project's data once and answer the monitor's questions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from typing import Any

import networkx as nx
import pandas as pd

from ..connections.build_measures import PROC, load_graph
from ..events import eventset
from ..graph import snapshot

MEASURES_PATH = PROC / "connection_measures.parquet"
EXCLUDED_EDGE_TYPES = frozenset({"finances", "publishes"})
START_DATE = date(2021, 1, 1)
OTHER_GROUP = "Other"
STAKEHOLDER_GROUPS = {
    "person": "People",
    "party": "Parties",
    "govt_body": "State",
    "bank": "Companies and groups",
    "company": "Companies and groups",
    "business_group": "Companies and groups",
    "media_group": "Media",
    "outlet": "Media",
}
NODE_COLUMNS = ["id", "name", "type", "hop", "stakeholder_group"]
EDGE_COLUMNS = ["source", "target", "type", "role", "start", "end", "pct",
                "source_url", "confidence"]


@dataclass(frozen=True)
class Bundle:
    graph: nx.MultiDiGraph
    tickers: pd.DataFrame
    events: pd.DataFrame
    measures: pd.DataFrame


@lru_cache(maxsize=1)
def load() -> Bundle:
    return Bundle(
        graph=load_graph(),
        tickers=eventset.load_tickers(),
        events=eventset.load_events(),
        measures=pd.read_parquet(MEASURES_PATH),
    )


def _ticker_row(bundle: Bundle, ticker: str) -> pd.Series:
    rows = bundle.tickers[bundle.tickers.ticker == ticker]
    if rows.empty:
        raise KeyError(f"unknown ticker {ticker!r}")
    return rows.iloc[0]


def firm_node(bundle: Bundle, ticker: str) -> str:
    return str(_ticker_row(bundle, ticker).node_id)


def firm_label(bundle: Bundle, ticker: str) -> str:
    return str(_ticker_row(bundle, ticker).listed_name)


def stakeholder_group(node_type: str) -> str:
    return STAKEHOLDER_GROUPS.get(node_type, OTHER_GROUP)


def _clean(value: Any) -> Any:
    return None if value is None or (isinstance(value, float) and pd.isna(value)) else value


def network(bundle: Bundle, ticker: str, on: date, hops: int = 2) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The firm's undirected neighbourhood within `hops` on the date `on`.

    `finances` and `publishes` edges are left out before distances are taken. Edges
    returned are those active on `on` that join two nodes of the neighbourhood.
    """
    root = firm_node(bundle, ticker)
    snap = snapshot(bundle.graph, on)
    drop = [(u, v, k) for u, v, k, d in snap.edges(keys=True, data=True)
            if d["type"] in EXCLUDED_EDGE_TYPES]
    snap.remove_edges_from(drop)
    dist = nx.single_source_shortest_path_length(snap.to_undirected(as_view=True), root, cutoff=hops)

    node_rows = []
    for nid, hop in sorted(dist.items(), key=lambda kv: (kv[1], kv[0])):
        attrs = snap.nodes[nid]
        node_rows.append({"id": nid, "name": attrs["name"], "type": attrs["type"], "hop": hop,
                          "stakeholder_group": stakeholder_group(attrs["type"])})

    edge_rows = []
    for u, v, _k, d in snap.edges(keys=True, data=True):
        if u not in dist or v not in dist:
            continue
        if not d.get("source_url"):
            raise ValueError(f"edge {u} -> {v} ({d['type']}) has no source_url")
        edge_rows.append({"source": u, "target": v, "type": d["type"], "role": d["role"],
                          "start": d["start"], "end": d["end"], "pct": d["obj"].pct,
                          "source_url": d["source_url"], "confidence": d["confidence"]})
    nodes_df = pd.DataFrame(node_rows, columns=NODE_COLUMNS)
    edges_df = pd.DataFrame(edge_rows, columns=EDGE_COLUMNS)
    if len(edges_df):
        edges_df = edges_df.sort_values(["source", "target", "type", "role"],
                                        kind="stable", na_position="last").reset_index(drop=True)
    return nodes_df, edges_df


def date_bounds(bundle: Bundle) -> tuple[date, date]:
    """2021-01-01 to the latest event date."""
    return START_DATE, bundle.events["date"].max().date()

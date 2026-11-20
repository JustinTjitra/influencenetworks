"""Banks recorded as financing a palm oil firm's group, by year and amount."""

from __future__ import annotations

from functools import lru_cache

import pandas as pd

from ..connections.build_measures import PROC, ROOT
from ..graph import load_doc_registry, load_edges, load_nodes
from .data import Bundle, firm_node

COLUMNS = ["bank", "year", "kind", "detail", "amount_usd_m", "source_url", "confidence"]
KINDS = ("credit", "holding")


def licence_note() -> str:
    return ("Financing data: Forests & Finance, personal-use licence. Not for republication "
            "without permission from Rainforest Action Network.")


@lru_cache(maxsize=1)
def _finance_edges() -> tuple:
    """All validated `finances` edges from the edge list (the graph merges parallel edges)."""
    nodes = load_nodes(PROC / "nodes.csv")
    docs = load_doc_registry(ROOT / "data" / "raw" / "documents.csv")
    edges, errors = load_edges(PROC / "edges.csv", nodes, doc_ids=docs)
    if errors:
        raise ValueError("edge list has rejected edges:\n" + "\n".join(errors))
    return tuple(e for e in edges if e.type.value == "finances")


def _targets(graph, node: str) -> set[str]:
    """The firm's node plus every group it is a `member_of_group` of."""
    targets = {node}
    for _u, v, d in graph.out_edges(node, data=True):
        if d["type"] == "member_of_group":
            targets.add(v)
    return targets


def _split_role(role: str | None) -> tuple[str, str]:
    prefix, sep, rest = (role or "").partition(":")
    prefix = prefix.strip().lower()
    if not sep or prefix not in KINDS:
        return "other", (role or "").strip()
    return prefix, rest.strip()


def lenders(bundle: Bundle, ticker: str) -> pd.DataFrame:
    graph = bundle.graph
    targets = _targets(graph, firm_node(bundle, ticker))
    rows = []
    for e in _finance_edges():
        if e.target_id not in targets:
            continue
        if not e.source_url:
            raise ValueError(f"finances edge {e.source_id} -> {e.target_id} has no source_url")
        kind, detail = _split_role(e.role)
        amount = e.amount_usd
        rows.append({
            "bank": graph.nodes[e.source_id]["name"] if e.source_id in graph else e.source_id,
            "year": e.start_date.year,
            "kind": kind,
            "detail": detail,
            "amount_usd_m": None if amount is None else round(amount / 1e6, 1),
            "source_url": e.source_url,
            "confidence": getattr(e.confidence, "value", e.confidence),
        })
    df = pd.DataFrame(rows, columns=COLUMNS)
    if len(df):
        df = df.sort_values(["kind", "year", "bank", "detail"], ascending=[True, False, True, True],
                            kind="stable").reset_index(drop=True)
    return df


def credit_by_bank(df: pd.DataFrame) -> pd.DataFrame:
    """Credit rows only, summed per bank, largest first. Holdings are never included."""
    credit = df[df["kind"] == "credit"]
    out = (credit.groupby("bank", as_index=False)["amount_usd_m"].sum()
           .sort_values(["amount_usd_m", "bank"], ascending=[False, True], kind="stable")
           .reset_index(drop=True))
    out["amount_usd_m"] = out["amount_usd_m"].round(1)
    return out

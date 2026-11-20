"""Exposure profile tables for the monitor: measures for one firm on one date, and the
sourced relationships behind each number. No composite score is computed here."""

from __future__ import annotations

import math
import re
from datetime import date
from functools import lru_cache

import pandas as pd

from ..connections.build_measures import coverage, load_rosters
from ..connections.measures import compute_all, edge_ref
from ..graph import snapshot
from .data import Bundle, firm_node

MEASURE_LABELS = {
    "state_own": "State shareholding",
    "board_party": "Board members with a governing-party role",
    "board_office": "Board members holding government office",
    "board_former": "Board members who left office in the last five years",
    "board_family": "Board members related to a party chair or minister",
    "group_conn": "Owner holds office or a party role",
    "dist_gov": "Steps to the state or a governing party",
}
PROFILE_COLUMNS = ["measure", "label", "value", "display", "n_edges"]
EVIDENCE_COLUMNS = ["from_name", "relation", "to_name", "start", "end", "source_url"]

_REF = re.compile(r"^(?P<src>[^>]+)>(?P<tgt>[^:]+):(?P<rel>[^\[]+)\[(?P<start>[^.]*)\.\.(?P<end>[^\]]*)\]<(?P<url>.*)>$")


def _compute(bundle: Bundle, ticker: str, on: date) -> dict:
    return compute_all(bundle.graph, firm_node(bundle, ticker), on)


def _display(measure: str, value: float) -> str:
    if measure == "state_own":
        return f"{value * 100:.1f}%"
    if measure == "group_conn":
        return "yes" if value else "no"
    if measure == "dist_gov" and math.isinf(value):
        return "no path"
    return str(int(value))


def _dist_edges(bundle: Bundle, row: dict, on: date) -> list[str]:
    """Edge references along the shortest path to the state or a governing party."""
    path = [n for n in row["dist_gov_path"].split(">") if n]
    if len(path) < 2:
        return []
    snap = snapshot(bundle.graph, on)
    refs = set()
    for a, b in zip(path, path[1:]):
        for u, v in ((a, b), (b, a)):
            for _k, d in (snap.get_edge_data(u, v) or {}).items():
                refs.add(edge_ref(d["obj"]))
    return sorted(refs)


def _refs(bundle: Bundle, row: dict, on: date, measure: str) -> list[str]:
    if measure == "dist_gov":
        return _dist_edges(bundle, row, on)
    if measure not in MEASURE_LABELS:
        raise KeyError(f"unknown measure {measure!r}")
    return list(row["evidence"].get(measure, []))


def profile(bundle: Bundle, ticker: str, on: date) -> pd.DataFrame:
    row = _compute(bundle, ticker, on)
    rows = []
    for measure, label in MEASURE_LABELS.items():
        value = float(row[measure])
        rows.append({"measure": measure, "label": label, "value": value,
                     "display": _display(measure, value),
                     "n_edges": len(_refs(bundle, row, on, measure))})
    return pd.DataFrame(rows, columns=PROFILE_COLUMNS)


def evidence(bundle: Bundle, ticker: str, on: date, measure: str) -> pd.DataFrame:
    row = _compute(bundle, ticker, on)
    out = []
    for ref in _refs(bundle, row, on, measure):
        m = _REF.match(ref)
        if not m:
            raise ValueError(f"cannot parse evidence string {ref!r}")
        names = bundle.graph.nodes
        out.append({"from_name": names[m["src"]].get("name", m["src"]),
                    "relation": m["rel"],
                    "to_name": names[m["tgt"]].get("name", m["tgt"]),
                    "start": m["start"], "end": m["end"],
                    "source_url": m["url"]})
    df = pd.DataFrame(out, columns=EVIDENCE_COLUMNS)
    df[["start", "end"]] = df[["start", "end"]].astype(str)
    return df


@lru_cache(maxsize=1)
def _rosters() -> pd.DataFrame:
    return load_rosters()


def data_note(bundle: Bundle, ticker: str, on: date) -> str:
    row = _compute(bundle, ticker, on)
    n = int(row["n_board_known"])
    cov = coverage(_rosters(), firm_node(bundle, ticker), on)
    people = "board member is" if n == 1 else "board members are"
    text = f"{n} {people} recorded for this firm on {on.isoformat()}."
    if cov < 1:
        text += (" No complete board roster is on file for this firm on that date, so a count"
                 " of zero means \"none recorded\", not \"none exist\".")
    return text

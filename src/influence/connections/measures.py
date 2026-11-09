"""Connection measures for a listed firm on a date (DESIGN.md section 4).

Every measure is computed on `graph.snapshot(date)`, so only relationships in effect
on that date count. Each public function has the signature

    measure(graph, firm_node_id, date, ...) -> value

and `compute_all` returns all of them at once together with the edges that produced
each number, so a reader can click from a value back to its sources.

Definitions (kept here and in docs/paper/prereg.md; change both or neither):

firm entities   The firm's own node plus every group it has an active
                `member_of_group` edge to. Seeds record some board seats and all
                family control at group level, so the measures look at both.
party set       The parties counted by the party-based measures: the governing
                parties on the date (connections.coalition), or one named party when
                `party_filter` is given (used for events about a single party).
state_own       Sum of `pct` on active `owns`/`controls` edges into the firm from
                state nodes (type govt_body, or a state holding vehicle), plus the
                `pct` held by corporate shareholders that are themselves majority
                state-owned. Share between 0 and 1, capped at 1.
board_party     Board members (active `board_seat`) with an active `party_role` in
                the party set.
board_office    Board members with an active `held_office` at a government body.
board_former    Board members with no active office whose last office ended within
                the previous five years.
board_family    Board members with an active `family_of` edge to a person who is the
                general chair of a party in the party set, or a sitting minister or
                president (deputy and vice posts are not counted here).
group_conn      1 if a person who owns or controls the firm or its group has an
                active party role in the party set, an active government office, or
                a family tie to someone who has either; else 0. With `party_filter`
                only party ties to that party count.
dist_gov        Shortest undirected path, over all active edges, from the firm to a
                government body, a state holding vehicle or a party in the party
                set. `inf` when there is no path.

Nothing here says anything about conduct. The measures count documented positions,
shareholdings and family relationships.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

import networkx as nx
import numpy as np
import pandas as pd

from ..graph import snapshot
from . import coalition

# Companies that hold shares on behalf of the state. Listed here, not inferred.
STATE_VEHICLES = frozenset({"co_danantara_am"})
OWNER_EDGE_TYPES = frozenset({"owns", "controls", "owns_media"})
CORPORATE_TYPES = frozenset({"company", "bank", "business_group", "media_group"})
SOE_CONTROL_THRESHOLD = 50.0     # pct of direct state ownership that makes a holder an SOE
FORMER_OFFICE_YEARS = 5

_PARTY_CHAIR = re.compile(r"\bgeneral chair(man|woman|person)?\b", re.I)
_SENIOR_OFFICE = re.compile(r"\b(minister|president)\b", re.I)
_NOT_PRINCIPAL = re.compile(r"\b(deputy|vice|former|division|staff)\b", re.I)

TIE_MEASURES = ("state_own", "board_party", "board_office", "board_former",
                "board_family", "group_conn")
PCA_COLUMNS = TIE_MEASURES + ("gov_proximity",)
_RANK = {"low": 0, "medium": 1, "high": 2}


@dataclass
class Measure:
    value: float
    edges: list = field(default_factory=list)   # schema.Edge objects behind the value


@dataclass
class Context:
    g: nx.MultiDiGraph            # full graph (needed for ended offices)
    h: nx.MultiDiGraph            # snapshot on `on`
    on: date
    firm: str
    entities: tuple[str, ...]
    parties: frozenset[str]
    party_filter: Optional[str]


def make_context(g: nx.MultiDiGraph, firm: str, on: date, party_filter: Optional[str] = None,
                 count_flagged: bool = True, coalition_path: Optional[Path] = None,
                 h: Optional[nx.MultiDiGraph] = None) -> Context:
    if firm not in g:
        raise KeyError(f"firm node {firm!r} is not in the graph")
    h = snapshot(g, on) if h is None else h
    groups = sorted({v for _, v, d in h.out_edges(firm, data=True)
                     if d["type"] == "member_of_group"})
    if party_filter:
        parties = frozenset({party_filter})
    else:
        kw = {"path": coalition_path} if coalition_path else {}
        parties = frozenset(coalition.governing_parties(on, count_flagged, **kw))
    return Context(g=g, h=h, on=on, firm=firm, entities=(firm, *groups),
                   parties=parties, party_filter=party_filter)


# ---------------------------------------------------------------- graph helpers

def _out(h, u, etype):
    return [(v, d["obj"]) for _, v, d in h.out_edges(u, data=True) if d["type"] == etype]


def _in(h, v, etypes):
    etypes = {etypes} if isinstance(etypes, str) else etypes
    return [(u, d["obj"]) for u, _, d in h.in_edges(v, data=True) if d["type"] in etypes]


def _ntype(h, n) -> str:
    return h.nodes[n].get("type", "")


def _is_state(h, n) -> bool:
    return _ntype(h, n) == "govt_body" or n in STATE_VEHICLES


def _board(ctx: Context) -> dict[str, list]:
    """person -> active board_seat edges on the firm or its group."""
    seats: dict[str, list] = {}
    for ent in ctx.entities:
        for p, obj in _in(ctx.h, ent, "board_seat"):
            if _ntype(ctx.h, p) == "person":
                seats.setdefault(p, []).append(obj)
    return seats


def _party_roles(ctx: Context, person: str) -> list:
    return [obj for t, obj in _out(ctx.h, person, "party_role") if t in ctx.parties]


def _offices(ctx: Context, person: str) -> list:
    return [obj for t, obj in _out(ctx.h, person, "held_office")
            if _ntype(ctx.h, t) == "govt_body"]


def _relatives(ctx: Context, person: str) -> list[tuple[str, object]]:
    rel = [(v, obj) for v, obj in _out(ctx.h, person, "family_of")]
    rel += [(u, obj) for u, obj in _in(ctx.h, person, "family_of")]
    return [(q, obj) for q, obj in rel if _ntype(ctx.h, q) == "person"]


def _years_before(d: date, years: int) -> date:
    try:
        return d.replace(year=d.year - years)
    except ValueError:                      # 29 February
        return d.replace(year=d.year - years, day=28)


# ---------------------------------------------------------------- the measures

def _state_own(ctx: Context) -> Measure:
    total, ev = 0.0, []
    for ent in ctx.entities:
        for src, obj in _in(ctx.h, ent, {"owns", "controls"}):
            if obj.pct is None:
                continue
            if _is_state(ctx.h, src):
                total += obj.pct
                ev.append(obj)
            elif _ntype(ctx.h, src) in CORPORATE_TYPES:
                up = [o for s, o in _in(ctx.h, src, {"owns", "controls"})
                      if o.pct is not None and _is_state(ctx.h, s)]
                if sum(o.pct for o in up) >= SOE_CONTROL_THRESHOLD:
                    total += obj.pct
                    ev += [obj, *up]
    return Measure(min(1.0, total / 100.0), ev)


def _board_party(ctx: Context) -> Measure:
    n, ev = 0, []
    for p, seats in _board(ctx).items():
        roles = _party_roles(ctx, p)
        if roles:
            n += 1
            ev += seats + roles
    return Measure(float(n), ev)


def _board_office(ctx: Context) -> Measure:
    n, ev = 0, []
    for p, seats in _board(ctx).items():
        offices = _offices(ctx, p)
        if offices:
            n += 1
            ev += seats + offices
    return Measure(float(n), ev)


def _board_former(ctx: Context) -> Measure:
    floor = _years_before(ctx.on, FORMER_OFFICE_YEARS)
    n, ev = 0, []
    for p, seats in _board(ctx).items():
        if _offices(ctx, p):
            continue                        # counted by board_office
        ended = [d["obj"] for _, t, d in ctx.g.out_edges(p, data=True)
                 if d["type"] == "held_office" and _ntype(ctx.g, t) == "govt_body"
                 and d["obj"].end_date is not None and floor <= d["obj"].end_date < ctx.on]
        if ended:
            n += 1
            ev += seats + ended
    return Measure(float(n), ev)


def _principal_ties(ctx: Context, person: str) -> list:
    """Edges that make `person` a party general chair, minister or president."""
    out = [obj for obj in _party_roles(ctx, person)
           if _PARTY_CHAIR.search(obj.role or "") and not _NOT_PRINCIPAL.search(obj.role or "")]
    if not ctx.party_filter:
        out += [obj for obj in _offices(ctx, person)
                if _SENIOR_OFFICE.search(obj.role or "")
                and not _NOT_PRINCIPAL.search(obj.role or "")]
    return out


def _board_family(ctx: Context) -> Measure:
    n, ev = 0, []
    for p, seats in _board(ctx).items():
        hits = []
        for q, fam in _relatives(ctx, p):
            ties = _principal_ties(ctx, q)
            if ties:
                hits += [fam, *ties]
        if hits:
            n += 1
            ev += seats + hits
    return Measure(float(n), ev)


def _own_ties(ctx: Context, person: str) -> list:
    ties = _party_roles(ctx, person)
    if not ctx.party_filter:
        ties += _offices(ctx, person)
    return ties


def _group_conn(ctx: Context) -> Measure:
    ev = []
    for ent in ctx.entities:
        for owner, own_edge in _in(ctx.h, ent, OWNER_EDGE_TYPES):
            if _ntype(ctx.h, owner) != "person":
                continue
            ties = _own_ties(ctx, owner)
            for q, fam in _relatives(ctx, owner):
                rel_ties = _own_ties(ctx, q)
                if rel_ties:
                    ties += [fam, *rel_ties]
            if ties:
                ev += [own_edge, *ties]
    return Measure(1.0 if ev else 0.0, ev)


def _dist_gov(ctx: Context) -> tuple[float, list[str]]:
    targets = {n for n in ctx.h.nodes if _is_state(ctx.h, n)} | set(ctx.parties)
    targets.discard(ctx.firm)
    und = ctx.h.to_undirected(as_view=True)
    paths = nx.single_source_shortest_path(und, ctx.firm)
    reachable = [(len(paths[t]) - 1, t) for t in targets if t in paths]
    if not reachable:
        return math.inf, []
    dist, nearest = min(reachable)
    return float(dist), paths[nearest]


_MEASURES = {
    "state_own": _state_own, "board_party": _board_party, "board_office": _board_office,
    "board_former": _board_former, "board_family": _board_family, "group_conn": _group_conn,
}


def _public(name):
    def fn(g, firm_node_id, on, party_filter=None, count_flagged=True) -> float:
        return _MEASURES[name](make_context(g, firm_node_id, on, party_filter, count_flagged)).value
    fn.__name__ = name
    fn.__doc__ = f"{name} for a firm on a date; see the module docstring."
    return fn


state_own = _public("state_own")
board_party = _public("board_party")
board_office = _public("board_office")
board_former = _public("board_former")
board_family = _public("board_family")
group_conn = _public("group_conn")


def dist_gov(g, firm_node_id, on, party_filter=None, count_flagged=True) -> float:
    """Undirected shortest path length from the firm to the state or the party set."""
    return _dist_gov(make_context(g, firm_node_id, on, party_filter, count_flagged))[0]


def gov_proximity(dist: float) -> float:
    """1 / (1 + dist_gov), and 0 when there is no path. Bounded form used in the PCA."""
    return 0.0 if math.isinf(dist) else 1.0 / (1.0 + dist)


def edge_ref(e) -> str:
    """Compact, stable description of an edge for evidence columns."""
    span = f"{e.start_date or ''}..{e.end_date or ''}"
    return f"{e.source_id}>{e.target_id}:{e.type.value}[{span}]<{e.source_url}>"


def compute_all(g: nx.MultiDiGraph, firm: str, on: date, party_filter: Optional[str] = None,
                count_flagged: bool = True, h: Optional[nx.MultiDiGraph] = None,
                coalition_path: Optional[Path] = None) -> dict:
    """All measures for one firm-date, with evidence and data-quality fields."""
    ctx = make_context(g, firm, on, party_filter, count_flagged, coalition_path, h=h)
    row: dict = {}
    evidence: dict[str, list[str]] = {}
    tiers: dict[str, str] = {}
    used = []
    for name, fn in _MEASURES.items():
        m = fn(ctx)
        row[name] = m.value
        if m.value:
            evidence[name] = sorted({edge_ref(e) for e in m.edges})
            tiers[name] = min((e.confidence.value for e in m.edges), key=_RANK.__getitem__)
            used += m.edges
    dist, path = _dist_gov(ctx)
    row["dist_gov"] = dist
    row["gov_proximity"] = gov_proximity(dist)
    row["dist_gov_path"] = ">".join(path)
    row["n_board_known"] = len(_board(ctx))
    row["node_level"] = "firm+group" if len(ctx.entities) > 1 else "firm"
    row["confidence_tier"] = (min((e.confidence.value for e in used), key=_RANK.__getitem__)
                              if used else "none")
    # Edges with no start date are assumed to be in effect (schema.Edge.active_on).
    row["n_open_ended_edges"] = len({edge_ref(e) for e in used if e.start_date is None})
    row["evidence"] = evidence
    row["tiers"] = tiers          # lowest confidence among the edges behind each non-zero measure
    return row


def lowest_tier(tiers: dict, names) -> str:
    found = [tiers[n] for n in names if n in tiers]
    return min(found, key=_RANK.__getitem__) if found else "none"


def composite_index(df: pd.DataFrame, columns=PCA_COLUMNS) -> tuple[pd.Series, pd.Series, float]:
    """First principal component of the standardised measures across firms.

    Returns (scores, loadings, share of variance explained). Columns with no
    variation across the firms are left out and get a NaN loading. The component is
    oriented so that its loadings sum to a positive number: higher means more ties.
    """
    x = df[list(columns)].astype(float)
    sd = x.std(ddof=0)
    keep = [c for c in columns if sd[c] > 0 and np.isfinite(sd[c])]
    loadings = pd.Series(np.nan, index=list(columns), name="loading")
    if not keep or len(df) < 2:
        return pd.Series(0.0, index=df.index, name="composite_pc1"), loadings, float("nan")
    z = (x[keep] - x[keep].mean()) / sd[keep]
    _, s, vt = np.linalg.svd(z.to_numpy(), full_matrices=False)
    v = vt[0]
    if v.sum() < 0:
        v = -v
    loadings[keep] = v
    scores = pd.Series(z.to_numpy() @ v, index=df.index, name="composite_pc1")
    return scores, loadings, float(s[0] ** 2 / (s ** 2).sum())

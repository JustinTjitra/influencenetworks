"""Connection measures for every (ticker, event) pair.

Reads the processed graph, data/mappings/tickers.csv and data/events/events.csv and
writes

    data/processed/connection_measures.parquet     one row per (ticker, event)
    data/processed/connection_pca_loadings.csv     PC1 loadings per event date
    data/processed/connection_event_summary.csv    treated / untreated counts per event

No price data is used or needed. Run:  python -m influence.connections.build_measures

Snapshot date. The measures are taken on the last weekday before the first day the
market could react to the event (the event date, or the next weekday for news after
the close or on a weekend). Exchange holidays are not modelled here: edges are dated
to the day at best and usually to the month, so a one-day shift cannot matter unless
an edge starts on the event itself, and the snapshot is deliberately before that.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd

from ..events import eventset
from ..graph import _parse_date, build_graph, load_doc_registry, load_edges, load_nodes, snapshot
from . import measures as M

ROOT = Path(__file__).resolve().parents[3]
PROC = ROOT / "data" / "processed"
ROSTERS_PATH = ROOT / "data" / "mappings" / "board_rosters.csv"
BOARD_ORGANS = ("commissioners", "directors")
PARTY_MEASURES = ("board_party", "board_family", "group_conn")
MIN_CLUSTERS = 3     # treated and untreated clusters an event needs for the main test


def load_graph(proc: Path = PROC):
    nodes = load_nodes(proc / "nodes.csv")
    docs = load_doc_registry(ROOT / "data" / "raw" / "documents.csv")
    edges, errors = load_edges(proc / "edges.csv", nodes, doc_ids=docs)
    if errors:
        raise SystemExit("graph has rejected edges; run influence.validate:\n" + "\n".join(errors))
    return build_graph(nodes, edges)


def load_rosters(path: Path = ROSTERS_PATH) -> pd.DataFrame:
    """Firm-organ-period rows for which a complete, primary-source roster exists."""
    cols = ["node_id", "organ", "valid_from", "valid_to", "source", "note"]
    if not path.exists():
        return pd.DataFrame(columns=cols)
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    bad = set(df.organ) - set(BOARD_ORGANS)
    if bad:
        raise ValueError(f"{path.name}: bad organ {bad}")
    df["valid_from"] = df.valid_from.map(_parse_date)
    df["valid_to"] = df.valid_to.map(lambda s: _parse_date(s, end=True))
    return df


def coverage(rosters: pd.DataFrame, node_id: str, on: date) -> float:
    """Share of the firm's two board organs (commissioners, directors) for which a
    complete primary-source roster covers the date. 0 means that a board measure of
    zero is zero by absence of data, not zero by evidence."""
    r = rosters[rosters.node_id == node_id]
    covered = {o for o, a, b in zip(r.organ, r.valid_from, r.valid_to)
               if (a is None or a <= on) and (b is None or on <= b)}
    return len(covered) / len(BOARD_ORGANS)


def cluster_id(g, node_id: str) -> str:
    """The unit that counts once when treated firms are counted.

    Firms controlled by the same person are one cluster (the first person, by id, with
    a `controls` or `owns_media` edge into the firm or its group, whatever its dates);
    otherwise the firm's group; otherwise the firm itself. Minority `owns` edges do
    not define a cluster.
    """
    groups = sorted({v for _, v, d in g.out_edges(node_id, data=True)
                     if d["type"] == "member_of_group"})
    controllers = sorted({u for ent in (node_id, *groups) for u, _, d in g.in_edges(ent, data=True)
                          if d["type"] in ("controls", "owns_media")
                          and g.nodes[u].get("type") == "person"})
    if controllers:
        return controllers[0]
    return groups[0] if groups else node_id


def build(g, tickers: pd.DataFrame, events: pd.DataFrame,
          rosters: Optional[pd.DataFrame] = None, count_flagged: bool = True,
          coalition_path: Optional[Path] = None
          ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rosters = load_rosters() if rosters is None else rosters
    rows, loadings = [], []
    for ev in events.itertuples(index=False):
        day0 = eventset.effective_weekday(ev.date.date(), ev.after_close)
        snap_date = eventset.previous_weekday(day0)
        h = snapshot(g, snap_date)
        ts0 = pd.Timestamp(day0)
        listed = tickers[(tickers.listing_date <= ts0)
                         & (tickers.delisting_date.isna() | (tickers.delisting_date > ts0))]
        ev_rows = []
        for t in listed.itertuples(index=False):
            base = M.compute_all(g, t.node_id, snap_date, count_flagged=count_flagged, h=h,
                                 coalition_path=coalition_path)
            tested = base
            if ev.target_party:
                tested = M.compute_all(g, t.node_id, snap_date, party_filter=ev.target_party,
                                       h=h, coalition_path=coalition_path)
            evidence = base.pop("evidence")
            base_tiers = base.pop("tiers")
            tested_tiers = tested["tiers"] if ev.target_party else base_tiers
            row = dict(event_id=ev.event_id, event_date=ev.date.date(), day0_weekday=day0,
                       snapshot_date=snap_date, ticker=t.ticker, node_id=t.node_id,
                       sector_bucket=t.sector_bucket, cluster=cluster_id(g, t.node_id),
                       in_event_sample=(ev.scope == "market" or ev.sector in ("all", t.sector_bucket)),
                       **base)
            row["soe"] = int(row["state_own"] >= M.SOE_CONTROL_THRESHOLD / 100.0)
            row["coverage"] = coverage(rosters, t.node_id, snap_date)
            row["tested_measure"] = ev.connection_measure_tested
            row["target_party"] = ev.target_party
            if ev.connection_measure_tested == "all":
                names = PARTY_MEASURES if ev.target_party else M.TIE_MEASURES
                row["tested_binary"] = int(any(tested[n] > 0 for n in names))
                row["tested_value"] = float("nan")      # composite, filled below
                tev = {n: tested["evidence"].get(n, []) for n in names} if ev.target_party else evidence
            else:
                row["tested_value"] = float(tested[ev.connection_measure_tested])
                row["tested_binary"] = int(row["tested_value"] > 0)
                tev = {ev.connection_measure_tested:
                       (tested["evidence"] if ev.target_party else evidence)
                       .get(ev.connection_measure_tested, [])}
            tested_names = names if ev.connection_measure_tested == "all" else (ev.connection_measure_tested,)
            # lowest confidence among the edges behind the measure this event tests
            row["tested_tier"] = M.lowest_tier(tested_tiers, tested_names)
            row["evidence"] = json.dumps(evidence, sort_keys=True)
            row["tested_evidence"] = json.dumps({k: v for k, v in tev.items() if v}, sort_keys=True)
            ev_rows.append(row)
        block = pd.DataFrame(ev_rows)
        if len(block):
            scores, load, explained = M.composite_index(block)
            block["composite_pc1"] = scores.to_numpy()
            if ev.connection_measure_tested == "all":
                block["tested_value"] = (block.tested_binary.astype(float) if ev.target_party
                                         else block.composite_pc1)
            for name, val in load.items():
                loadings.append(dict(event_id=ev.event_id, snapshot_date=snap_date, measure=name,
                                     loading=val, explained_variance=explained, n_firms=len(block)))
        rows.append(block)
    out = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    return out, pd.DataFrame(loadings), summarise(out, events)


def summarise(measures: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """Per event: how many firms and clusters have a non-zero tested measure.

    `enough_clusters` is the mechanical rule from the pre-registration: at least
    MIN_CLUSTERS treated and MIN_CLUSTERS untreated clusters in the event sample.
    """
    out = []
    for ev in events.itertuples(index=False):
        s = measures[(measures.event_id == ev.event_id) & measures.in_event_sample]
        treated = s[s.tested_binary == 1]
        untreated = s[s.tested_binary == 0]
        out.append(dict(
            event_id=ev.event_id, date=ev.date.date(), type=ev.type,
            tested_measure=ev.connection_measure_tested, target_party=ev.target_party,
            sign=ev.expected_sign_connected, anticipation_flag=ev.anticipation_flag,
            confounder_flag=ev.confounder_flag, n_firms=len(s),
            n_treated=len(treated), n_treated_clusters=treated.cluster.nunique(),
            n_untreated=len(untreated), n_untreated_clusters=untreated.cluster.nunique(),
            treated_tickers=" ".join(sorted(treated.ticker)),
            enough_clusters=int(treated.cluster.nunique() >= MIN_CLUSTERS
                                and untreated.cluster.nunique() >= MIN_CLUSTERS),
        ))
    df = pd.DataFrame(out)
    if len(df):
        df["main_test"] = ((df.anticipation_flag == 0) & (df.confounder_flag == 0)
                           & df.sign.isin(["+", "-"]) & (df.enough_clusters == 1)).astype(int)
    return df


def main() -> int:
    g = load_graph()
    tickers = eventset.load_tickers()
    events = eventset.load_events()
    missing = sorted(set(tickers.node_id) - set(g.nodes))
    if missing:
        raise SystemExit(f"tickers.csv refers to nodes that are not in the graph: {missing}")
    measures, loadings, summary = build(g, tickers, events)
    PROC.mkdir(parents=True, exist_ok=True)
    measures.to_parquet(PROC / "connection_measures.parquet", index=False)
    loadings.to_csv(PROC / "connection_pca_loadings.csv", index=False)
    summary.to_csv(PROC / "connection_event_summary.csv", index=False)
    print(f"wrote {len(measures)} rows for {measures.ticker.nunique()} tickers x "
          f"{measures.event_id.nunique()} events")
    print(summary[["event_id", "tested_measure", "n_firms", "n_treated", "n_treated_clusters",
                   "main_test"]].to_string(index=False))
    zero_cov = (measures.coverage == 0).mean()
    print(f"firm-events with no primary-source board roster (coverage 0): {zero_cov:.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from datetime import date
from pathlib import Path

import pytest

from influence.graph import build_graph, linked_entities, load_edges, load_nodes, snapshot
from influence.schema import (
    Confidence, Edge, EdgeType, Node, NodeType, SchemaError, SourceType, validate_edge,
)

# Fictional fixture entities only.
NODES = {
    "p_a": Node("p_a", NodeType.PERSON, "Person A"),
    "p_b": Node("p_b", NodeType.PERSON, "Person B"),
    "co_x": Node("co_x", NodeType.COMPANY, "PT X"),
    "mg_m": Node("mg_m", NodeType.MEDIA_GROUP, "Media M"),
    "out_m": Node("out_m", NodeType.OUTLET, "m.example"),
}
URL = "https://example.org/report.pdf"


def edge(**kw):
    base = dict(source_id="p_a", target_id="co_x", type=EdgeType.BOARD_SEAT,
                source_url=URL, source_type=SourceType.ANNUAL_REPORT,
                confidence=Confidence.HIGH)
    base.update(kw)
    return Edge(**base)


def test_valid_edge_passes():
    validate_edge(edge(), NODES)


def test_missing_source_rejected():
    with pytest.raises(SchemaError):
        validate_edge(edge(source_url=""), NODES)


def test_unknown_node_rejected():
    with pytest.raises(SchemaError):
        validate_edge(edge(target_id="nope"), NODES)


def test_low_confidence_family_tie_rejected():
    with pytest.raises(SchemaError):
        validate_edge(edge(type=EdgeType.FAMILY_OF, target_id="p_b",
                           confidence=Confidence.LOW, source_type=SourceType.NEWS), NODES)


def test_conviction_needs_court_record():
    with pytest.raises(SchemaError):
        validate_edge(edge(type=EdgeType.CONVICTED_IN, source_type=SourceType.NEWS), NODES)


def test_end_before_start_rejected():
    with pytest.raises(SchemaError):
        validate_edge(edge(start_date=date(2022, 1, 1), end_date=date(2021, 1, 1)), NODES)


def test_snapshot_respects_dates():
    e1 = edge(start_date=date(2020, 1, 1), end_date=date(2022, 12, 31))
    g = build_graph(NODES, [e1])
    assert snapshot(g, date(2021, 6, 1)).number_of_edges() == 1
    assert snapshot(g, date(2023, 6, 1)).number_of_edges() == 0


def test_owner_network_hops():
    es = [
        edge(source_id="mg_m", target_id="out_m", type=EdgeType.PUBLISHES),
        edge(source_id="p_a", target_id="mg_m", type=EdgeType.OWNS_MEDIA),
        edge(source_id="p_a", target_id="co_x", type=EdgeType.BOARD_SEAT),
    ]
    g = build_graph(NODES, es)
    net = linked_entities(g, "out_m", max_hops=3)
    assert net["co_x"] == 3
    assert "p_b" not in net


def test_csv_loader_reports_bad_rows(tmp_path: Path):
    (tmp_path / "nodes.csv").write_text(
        "id,type,name,aliases\np_a,person,Person A,\nco_x,company,PT X,X\n", encoding="utf-8")
    (tmp_path / "edges.csv").write_text(
        "source_id,target_id,type,source_url,source_type,confidence,role,start_date,end_date,pct,amount_usd,note\n"
        f"p_a,co_x,board_seat,{URL},annual_report,high,commissioner,2021,,,,\n"
        "p_a,co_x,board_seat,,annual_report,high,director,,,,,\n",
        encoding="utf-8")
    nodes = load_nodes(tmp_path / "nodes.csv")
    edges, errors = load_edges(tmp_path / "edges.csv", nodes)
    assert len(edges) == 1 and len(errors) == 1


def test_doc_source_must_be_registered(tmp_path: Path):
    (tmp_path / "nodes.csv").write_text(
        "id,type,name,aliases\np_a,person,Person A,\nco_x,company,PT X,\n", encoding="utf-8")
    (tmp_path / "edges.csv").write_text(
        "source_id,target_id,type,source_url,source_type,confidence,role,start_date,end_date,pct,amount_usd,note\n"
        "p_a,co_x,board_seat,doc:ar_2025#p10,annual_report,high,,,,,,\n"
        "p_a,co_x,owns,doc:unknown_doc#p1,annual_report,high,,,,,,\n",
        encoding="utf-8")
    nodes = load_nodes(tmp_path / "nodes.csv")
    edges, errors = load_edges(tmp_path / "edges.csv", nodes, doc_ids={"ar_2025"})
    assert len(edges) == 1 and "unregistered" in errors[0]

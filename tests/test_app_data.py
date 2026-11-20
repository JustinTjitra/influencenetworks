from datetime import date

import pytest

from influence.app import data

BBRI_NODE = "bank_bri"


@pytest.fixture(scope="module")
def bundle():
    return data.load()


def test_load_is_cached_and_complete(bundle):
    assert data.load() is bundle
    assert BBRI_NODE in bundle.graph
    assert "BBRI" in set(bundle.tickers.ticker)
    assert len(bundle.events) > 0
    assert len(bundle.measures) > 0


def test_firm_node_and_label(bundle):
    assert data.firm_node(bundle, "BBRI") == BBRI_NODE
    assert "Bank Rakyat Indonesia" in data.firm_label(bundle, "BBRI")


def test_bbri_2025_has_state_node_and_person(bundle):
    nodes, _ = data.network(bundle, "BBRI", date(2025, 6, 30))
    state = nodes[(nodes.stakeholder_group == "State") & (nodes.hop == 1)]
    assert len(state) >= 1
    assert "gov_danantara" in set(state.id)
    assert (nodes.type == "person").sum() >= 1
    assert set(nodes.columns) == set(data.NODE_COLUMNS)


def test_bbri_2022_state_node_is_republic(bundle):
    nodes, _ = data.network(bundle, "BBRI", date(2022, 6, 30))
    state = nodes[(nodes.type == "govt_body") & (nodes.hop == 1)]
    assert list(state.id) == ["gov_republic"]


def test_hop_limits_respected(bundle):
    on = date(2025, 6, 30)
    n1, e1 = data.network(bundle, "BBRI", on, hops=1)
    n2, e2 = data.network(bundle, "BBRI", on, hops=2)
    assert n1.hop.max() == 1
    assert n2.hop.max() == 2
    assert set(n1.id) < set(n2.id)
    assert len(e1) < len(e2)
    assert (n2[n2.hop == 0].id == BBRI_NODE).all() and len(n2[n2.hop == 0]) == 1
    ids = set(n2.id)
    assert set(e2.source) <= ids and set(e2.target) <= ids
    n0, _ = data.network(bundle, "BBRI", on, hops=0)
    assert list(n0.id) == [BBRI_NODE]


def test_finances_and_publishes_never_appear(bundle):
    for on in (date(2022, 6, 30), date(2025, 6, 30)):
        for tk in ("BBRI", "BMRI"):
            _, edges = data.network(bundle, tk, on, hops=3)
            assert len(edges) > 0
            assert not set(edges.type) & {"finances", "publishes"}


def test_every_edge_row_has_a_source(bundle):
    _, edges = data.network(bundle, "BBRI", date(2025, 6, 30), hops=3)
    assert len(edges) > 0
    assert (edges.source_url.str.len() > 0).all()
    assert list(edges.columns) == data.EDGE_COLUMNS


def test_edge_without_source_raises(bundle):
    g = bundle.graph.copy()
    for _u, _v, _k, d in g.edges(BBRI_NODE, keys=True, data=True):
        d["source_url"] = ""
    broken = data.Bundle(g, bundle.tickers, bundle.events, bundle.measures)
    with pytest.raises(ValueError):
        data.network(broken, "BBRI", date(2025, 6, 30))


def test_unknown_ticker_raises_keyerror(bundle):
    with pytest.raises(KeyError):
        data.firm_node(bundle, "ZZZZ")
    with pytest.raises(KeyError):
        data.firm_label(bundle, "ZZZZ")
    with pytest.raises(KeyError):
        data.network(bundle, "ZZZZ", date(2025, 6, 30))


def test_stakeholder_groups():
    expected = {"person": "People", "party": "Parties", "govt_body": "State",
                "bank": "Companies and groups", "company": "Companies and groups",
                "business_group": "Companies and groups", "media_group": "Media",
                "outlet": "Media"}
    for t, g in expected.items():
        assert data.stakeholder_group(t) == g


def test_date_bounds(bundle):
    lo, hi = data.date_bounds(bundle)
    assert lo == date(2021, 1, 1)
    assert hi == bundle.events["date"].max().date()
    assert hi > lo

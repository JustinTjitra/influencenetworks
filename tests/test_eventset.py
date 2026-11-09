"""Checks on the registered data files themselves (no prices involved)."""
import pandas as pd
import pytest

from influence.connections import build_measures as B
from influence.connections.coalition import party_status
from influence.events import eventset as E
from influence.events.prices import PREREG


@pytest.fixture(scope="module")
def data():
    g = B.load_graph()
    tickers, events = E.load_tickers(), E.load_events()
    measures, loadings, summary = B.build(g, tickers, events)
    return g, tickers, events, measures, summary


def test_every_ticker_maps_to_a_graph_node_with_a_source(data):
    g, tickers, *_ = data
    assert set(tickers.node_id) <= set(g.nodes)
    assert tickers.node_id.is_unique and len(tickers) == 34
    assert tickers.sector_bucket.value_counts().to_dict() == {"bank": 12, "palm": 11, "media": 11}
    # a listed company that is not itself a group or bank node has a sourced membership edge
    for nid in tickers.node_id[tickers.node_id.str.startswith("co_")]:
        kinds = {d["type"] for _, _, d in g.out_edges(nid, data=True)}
        assert "member_of_group" in kinds, nid
    assert (tickers.listing_date < "2022-01-01").all()


def test_event_file_obeys_its_own_rules(data):
    _, _, events, _, _ = data
    assert 15 <= len(events) <= 25
    assert events.date.min() >= pd.Timestamp("2021-01-01") and events.date.max() <= pd.Timestamp("2026-11-01")
    # an event within five trading days of another with an overlapping sample must be flagged
    for eid, near in E.neighbours_within(events).items():
        if near:
            assert events.set_index("event_id").loc[eid, "confounder_flag"] == 1, (eid, near)
    # ambiguous and zero-sign events are never in the main subset
    assert set(E.main_test_subset(events).expected_sign_connected) <= {"+", "-"}


def test_danantara_launch_sign_is_the_confirmed_one(data):
    _, _, events, _, _ = data
    launch = events.set_index("event_id").loc["ev_danantara_launch"]
    assert launch.date == pd.Timestamp("2025-02-24")
    assert launch.expected_sign_connected == "-" and launch.connection_measure_tested == "state_own"
    assert "Rejected alternative" in launch.notes


def test_state_banks_are_state_owned_before_and_after_the_transfer(data):
    _, _, _, measures, _ = data
    m = measures.set_index(["event_id", "ticker"])
    for ev in ("ev_cpo_export_ban", "ev_danantara_date_announced", "ev_soe_ministry_to_agency"):
        own = m.loc[ev].state_own
        assert own[["BMRI", "BBRI", "BBNI", "BBTN", "BRIS"]].between(0.5, 1.0).all(), ev
        assert (own.drop(["BMRI", "BBRI", "BBNI", "BBTN", "BRIS"]) == 0).all(), ev
    assert m.loc[("ev_cpo_export_ban", "BBRI"), "state_own"] == pytest.approx(0.5319)
    assert m.loc[("ev_danantara_date_announced", "BBTN"), "state_own"] == pytest.approx(0.60)   # no double count


def test_registered_main_test_subset(data):
    _, _, _, _, summary = data
    assert set(summary.loc[summary.main_test == 1, "event_id"]) == {
        "ev_danantara_date_announced", "ev_mk_wamen_signal"}
    s = summary.set_index("event_id")
    assert s.loc["ev_perindo_joins_prabowo", "n_treated_clusters"] == 1      # four tickers, one owner
    assert s.loc["ev_golkar_pan_prabowo", "enough_clusters"] == 0


def test_nasdem_status_path():
    from datetime import date
    assert party_status("party_nasdem", date(2022, 10, 2)) == "governing"
    assert party_status("party_nasdem", date(2022, 10, 3)) == "unknown"
    assert party_status("party_nasdem", date(2024, 6, 1)) == "outside"
    assert party_status("party_nasdem", date(2024, 10, 20)) == "governing"
    assert party_status("party_nasdem", date(2024, 10, 20), count_flagged=False) == "outside"


def test_prereg_lists_the_main_subset(data):
    _, _, _, _, summary = data
    text = PREREG.read_text(encoding="utf-8")
    for eid in summary.loc[summary.main_test == 1, "event_id"]:
        assert f"- `{eid}`" in text
    assert "Registration commit:" in text

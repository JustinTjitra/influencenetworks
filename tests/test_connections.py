import math
from datetime import date

import pandas as pd
import pytest

from influence.connections import build_measures as B
from influence.connections import coalition
from influence.connections import measures as M
from influence.graph import _parse_date, build_graph
from influence.schema import Confidence, Edge, EdgeType, Node, NodeType, SourceType

# Fictional fixture entities only.
URL = "https://example.org/filing.pdf"


def E(src, tgt, etype, start=None, end=None, role=None, pct=None, conf=Confidence.HIGH):
    return Edge(source_id=src, target_id=tgt, type=EdgeType(etype), source_url=URL,
                source_type=SourceType.ANNUAL_REPORT, confidence=conf, role=role,
                start_date=start, end_date=end, pct=pct)


def N(i, t, name=None):
    return Node(i, NodeType(t), name or i)


@pytest.fixture
def cpath(tmp_path):
    p = tmp_path / "coalition_events.csv"
    p.write_text(
        "event_id,date,party,event_description,source_url,confidence,party_id,status_after,status_flag\n"
        "a1,2019-10-23,Alpha,in cabinet,https://example.org/a,high,party_alpha,governing,\n"
        "a2,2022-10-03,Alpha,names a rival candidate,https://example.org/b,high,party_alpha,unknown,contested\n"
        "a3,2023-09-02,Alpha,runs against the government ticket,https://example.org/c,high,party_alpha,outside,\n"
        "a4,2024-04-25,Alpha,recorded but no change,https://example.org/d,high,party_alpha,,\n"
        "a5,2024-10-20,Alpha,supports without ministers,https://example.org/e,high,party_alpha,governing,no_ministers\n"
        "b1,2019-10-23,Beta,in cabinet,https://example.org/f,high,party_beta,governing,\n",
        encoding="utf-8")
    coalition.load_status_changes.cache_clear()
    return p


@pytest.fixture
def toy():
    nodes = {n.id: n for n in [
        N("co_f", "company"), N("pg_g", "business_group"), N("bank_s", "bank"),
        N("bank_sub", "bank"), N("co_far", "company"), N("co_iso", "company"),
        N("gov_state", "govt_body"), N("gov_cab", "govt_body"),
        N("party_alpha", "party"), N("party_beta", "party"),
        N("p_left", "person"), N("p_stays", "person"), N("p_owner", "person"),
        N("p_chair", "person"), N("p_kin", "person"), N("p_exmin", "person"),
    ]}
    edges = [
        E("co_f", "pg_g", "member_of_group"),
        E("p_owner", "pg_g", "controls"),
        E("co_far", "co_f", "owns", pct=10.0),               # owner chain for dist_gov
        # a board member who leaves before the test date
        E("p_left", "co_f", "board_seat", date(2021, 1, 1), date(2024, 3, 31)),
        E("p_left", "party_beta", "party_role", role="member"),
        E("p_stays", "co_f", "board_seat", date(2021, 1, 1)),
        E("p_stays", "party_alpha", "party_role", role="member"),
        # family tie from a board member to a party general chair
        E("p_kin", "co_f", "board_seat", date(2022, 1, 1)),
        E("p_kin", "p_chair", "family_of", role="child"),
        E("p_chair", "party_beta", "party_role", role="general chairman"),
        # a former minister on the board
        E("p_exmin", "co_f", "board_seat", date(2023, 1, 1)),
        E("p_exmin", "gov_cab", "held_office", date(2019, 1, 1), date(2022, 6, 30), role="Minister"),
        # state ownership, direct and through a majority state-owned parent
        E("gov_state", "bank_s", "owns", date(2010, 1, 1), pct=60.0),
        E("bank_s", "bank_sub", "owns", date(2021, 2, 1), pct=51.0),
        E("p_owner", "bank_sub", "owns", pct=5.0),
    ]
    return build_graph(nodes, edges)


# ------------------------------------------------------------------ coalition

def test_party_status_flips_on_the_right_date(cpath):
    st = lambda d, **kw: coalition.party_status("party_alpha", d, path=cpath, **kw)
    assert st(date(2019, 10, 22)) == "unknown"            # before the first sourced row
    assert st(date(2022, 10, 2)) == "governing"
    assert st(date(2022, 10, 3)) == "unknown"             # contested from the day itself
    assert st(date(2023, 9, 1)) == "unknown"
    assert st(date(2023, 9, 2)) == "outside"
    assert st(date(2024, 10, 19)) == "outside"            # the 2024-04-25 row changes nothing
    assert st(date(2024, 10, 20)) == "governing"
    assert st(date(2024, 10, 20), count_flagged=False) == "outside"
    assert coalition.party_status("party_nowhere", date(2024, 1, 1), path=cpath) == "unknown"


def test_governing_parties_set(cpath):
    assert coalition.governing_parties(date(2023, 12, 1), path=cpath) == {"party_beta"}
    assert coalition.governing_parties(date(2025, 1, 1), path=cpath) == {"party_alpha", "party_beta"}


# ------------------------------------------------------------------ measures

def ctx_all(toy, cpath, on, **kw):
    return M.compute_all(toy, "co_f", on, coalition_path=cpath, **kw)


def test_board_member_who_left_does_not_count(toy, cpath):
    before = ctx_all(toy, cpath, date(2024, 3, 31))
    after = ctx_all(toy, cpath, date(2024, 4, 1))
    # p_left (Beta, governing) counts until the last day of the seat, then drops out;
    # p_stays is tied to Alpha, which is outside the government in early 2024.
    assert before["board_party"] == 1
    assert after["board_party"] == 0
    assert before["n_board_known"] == 4 and after["n_board_known"] == 3


def test_board_party_follows_party_status(toy, cpath):
    assert ctx_all(toy, cpath, date(2022, 6, 1))["board_party"] == 2      # Alpha and Beta governing
    assert ctx_all(toy, cpath, date(2023, 10, 1))["board_party"] == 1     # Alpha outside
    assert ctx_all(toy, cpath, date(2025, 1, 1))["board_party"] == 1      # p_left gone, Alpha back
    assert ctx_all(toy, cpath, date(2025, 1, 1), count_flagged=False)["board_party"] == 0


def test_party_filter_ignores_governing_status(toy, cpath):
    row = ctx_all(toy, cpath, date(2023, 10, 1), party_filter="party_alpha")
    assert row["board_party"] == 1 and row["board_family"] == 0


def test_board_family_and_former_office(toy, cpath):
    row = ctx_all(toy, cpath, date(2024, 6, 1))
    assert row["board_family"] == 1          # p_kin -> p_chair, general chair of governing Beta
    assert row["board_office"] == 0
    assert row["board_former"] == 1          # office ended 2022-06-30, inside five years
    assert ctx_all(toy, cpath, date(2027, 7, 1))["board_former"] == 0
    assert "board_family" in row["evidence"] and row["confidence_tier"] == "high"


def test_group_conn_through_group_owner(toy, cpath):
    assert ctx_all(toy, cpath, date(2024, 6, 1))["group_conn"] == 0
    g2 = toy.copy()
    e = E("p_owner", "party_beta", "party_role", role="member", conf=Confidence.MEDIUM)
    g2.add_edge("p_owner", "party_beta", key="party_role:member", type="party_role", role="member",
                source_url=URL, confidence="medium", start=None, end=None, obj=e)
    row = M.compute_all(g2, "co_f", date(2024, 6, 1), coalition_path=cpath)
    assert row["group_conn"] == 1
    assert row["confidence_tier"] == "medium" and row["n_open_ended_edges"] >= 1


def test_state_own_direct_and_through_state_parent(toy, cpath):
    assert M.compute_all(toy, "bank_s", date(2024, 1, 1), coalition_path=cpath)["state_own"] == pytest.approx(0.60)
    sub = M.compute_all(toy, "bank_sub", date(2024, 1, 1), coalition_path=cpath)
    assert sub["state_own"] == pytest.approx(0.51)        # the private 5% is not state
    assert M.compute_all(toy, "bank_sub", date(2021, 1, 1), coalition_path=cpath)["state_own"] == 0
    assert M.compute_all(toy, "co_f", date(2024, 1, 1), coalition_path=cpath)["state_own"] == 0


def test_dist_gov_through_an_owner_chain(toy, cpath):
    on = date(2024, 6, 1)
    assert M.compute_all(toy, "bank_s", on, coalition_path=cpath)["dist_gov"] == 1
    assert M.compute_all(toy, "bank_sub", on, coalition_path=cpath)["dist_gov"] == 2
    # co_far -> co_f -> p_kin -> p_chair -> party_beta (governing): four hops
    far = M.compute_all(toy, "co_far", on, coalition_path=cpath)
    assert far["dist_gov"] == 4 and far["dist_gov_path"] == "co_far>co_f>p_kin>p_chair>party_beta"
    # while p_left (a Beta member) still holds a seat the path is one hop shorter
    assert M.compute_all(toy, "co_far", date(2024, 3, 1), coalition_path=cpath)["dist_gov"] == 3
    iso = M.compute_all(toy, "co_iso", on, coalition_path=cpath)
    assert math.isinf(iso["dist_gov"]) and iso["gov_proximity"] == 0


def test_pca_runs_on_five_firm_toy():
    df = pd.DataFrame({
        "state_own": [0.6, 0.52, 0.0, 0.0, 0.0],
        "board_party": [2, 1, 0, 0, 0],
        "board_office": [3, 2, 0, 1, 0],
        "board_former": [0, 0, 0, 0, 0],          # no variation: left out
        "board_family": [1, 0, 0, 0, 0],
        "group_conn": [0, 0, 1, 0, 0],
        "gov_proximity": [0.5, 0.5, 0.25, 0.2, 0.0],
    })
    scores, loadings, explained = M.composite_index(df)
    assert len(scores) == 5 and abs(scores.mean()) < 1e-9
    assert math.isnan(loadings["board_former"])
    assert loadings.dropna().sum() > 0 and 0 < explained <= 1
    assert scores.idxmax() == 0 and scores.iloc[0] > scores.iloc[4]
    assert abs((loadings.dropna() ** 2).sum() - 1) < 1e-9


# ------------------------------------------------------------------ builder

def test_build_measures_table(toy, cpath):
    tickers = pd.DataFrame({
        "node_id": ["co_f", "bank_s", "bank_sub", "co_iso", "co_far"],
        "ticker": ["FFFF", "SSSS", "SUBB", "ISOO", "FARR"],
        "sector_bucket": ["palm", "bank", "bank", "media", "palm"],
        "listing_date": pd.to_datetime(["2010-01-01"] * 4 + ["2030-01-01"]),
        "delisting_date": pd.to_datetime([None] * 5),
    })
    events = pd.DataFrame({
        "event_id": ["ev_state", "ev_party"],
        "date": pd.to_datetime(["2024-06-03", "2023-10-07"]),      # Monday; Saturday
        "type": ["state_governance", "coalition"],
        "expected_sign_connected": ["-", "+"],
        "connection_measure_tested": ["state_own", "board_party"],
        "scope": ["sector", "market"], "sector": ["bank", "all"],
        "anticipation_flag": [0, 0], "confounder_flag": [0, 0],
        "target_party": ["", "party_alpha"], "after_close": [0, 0],
    })
    rosters = pd.DataFrame({"node_id": ["co_f"], "organ": ["commissioners"],
                            "valid_from": [date(2024, 1, 1)], "valid_to": [date(2024, 12, 31)],
                            "source": ["doc:x#p1"], "note": [""]})
    out, loadings, summary = B.build(toy, tickers, events, rosters=rosters, coalition_path=cpath)
    assert len(out) == 8                                   # FARR not yet listed
    st = out[out.event_id == "ev_state"].set_index("ticker")
    assert st.loc["SSSS", "snapshot_date"] == date(2024, 5, 31)
    assert st.loc["SSSS", "tested_binary"] == 1 and st.loc["SUBB", "soe"] == 1
    assert bool(st.loc["FFFF", "in_event_sample"]) is False
    assert st.loc["FFFF", "coverage"] == 0.5 and st.loc["SSSS", "coverage"] == 0.0
    pt = out[out.event_id == "ev_party"].set_index("ticker")
    assert pt.loc["FFFF", "day0_weekday"] == date(2023, 10, 9)     # Saturday news -> Monday
    assert pt.loc["FFFF", "tested_value"] == 1            # tie to Alpha, whatever its status
    assert pt.loc["FFFF", "board_party"] == 1             # governing-based count sees only Beta
    s = summary.set_index("event_id")
    assert s.loc["ev_state", "n_firms"] == 2 and s.loc["ev_state", "n_treated"] == 2
    assert s.loc["ev_state", "main_test"] == 0            # too few clusters
    assert set(loadings.event_id) == {"ev_state", "ev_party"}


def test_end_dates_are_read_generously():
    assert _parse_date("2015", end=True) == date(2015, 12, 31)
    assert _parse_date("2024-02", end=True) == date(2024, 2, 29)
    assert _parse_date("2015") == date(2015, 1, 1)
    assert _parse_date("2025-03-22", end=True) == date(2025, 3, 22)

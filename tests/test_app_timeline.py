import numpy as np
import pandas as pd
import pytest

from influence.app import data, sector, timeline as tl
from influence.events import eventset

DANANTARA = {"ev_danantara_postponed", "ev_danantara_date_announced", "ev_danantara_launch"}


@pytest.fixture(scope="module")
def bundle():
    return data.load()


@pytest.fixture
def no_results(tmp_path):
    return tmp_path / "absent"


def test_default_results_dir_is_real_results():
    assert tl.DEFAULT_RESULTS_DIR == data.PROC / "results"
    assert tl.DEFAULT_RESULTS_DIR.name == "results"
    assert "synthetic" not in str(tl.DEFAULT_RESULTS_DIR)


def test_bbri_has_danantara_events_connected(bundle, no_results):
    t = tl.timeline(bundle, "BBRI", no_results)
    assert list(t.columns) == tl.COLUMNS
    d = t[t.event_id.isin(DANANTARA)]
    assert set(d.event_id) == DANANTARA
    assert (d.firm_connected == "yes").all()
    assert t.date.is_monotonic_increasing
    assert t.event_id.is_unique


def test_palm_ticker_has_no_bank_event(bundle, no_results):
    t = tl.timeline(bundle, "AALI", no_results)
    assert len(t) > 0
    bank_events = set(bundle.events[bundle.events.sector == "bank"].event_id)
    assert bank_events
    assert not (set(t.event_id) & bank_events)
    assert "ev_cpo_export_ban" in set(t.event_id)


def test_event_rule_flag(bundle, no_results):
    t = tl.timeline(bundle, "BBRI", no_results).set_index("event_id")
    assert t.loc["ev_danantara_date_announced", "event_rule"] == "yes"  # signed, flags 0
    assert t.loc["ev_danantara_launch", "event_rule"] == "no"           # confounder_flag 1
    assert t.loc["ev_kopdes_himbara", "event_rule"] == "no"   # sign "ambiguous"


def test_event_rule_matches_eventset_rule(bundle, no_results):
    t = tl.timeline(bundle, "BBRI", no_results)
    flagged = set(t[t.event_rule == "yes"].event_id)
    expected = set(t.event_id) & set(eventset.main_test_subset(bundle.events).event_id)
    assert flagged == expected
    assert flagged  # not vacuous


def test_columns_order_event_rule_before_main_test(bundle, no_results):
    t = tl.timeline(bundle, "BBRI", no_results)
    cols = list(t.columns)
    assert cols.index("main_test") == cols.index("event_rule") + 1
    assert cols.index("firm_connected") + 1 == cols.index("event_rule")


def test_main_test_matches_registered_summary(bundle, no_results):
    t = tl.timeline(bundle, "BBRI", no_results)
    summ = pd.read_csv(tl.SUMMARY_PATH).set_index("event_id")["main_test"]
    yes = set(t[t.main_test == "yes"].event_id)
    assert yes == {e for e in t.event_id if summ[e] == 1}
    assert set(t.main_test) <= {"yes", "no"}


def test_main_test_implies_event_rule_and_differs_somewhere(bundle, no_results):
    t = tl.timeline(bundle, "BBRI", no_results)
    assert (t[t.main_test == "yes"].event_rule == "yes").all()
    assert ((t.event_rule == "yes") & (t.main_test == "no")).any()


def test_main_test_equals_sector_page(bundle, no_results):
    t = tl.timeline(bundle, "BBRI", no_results).set_index("event_id")
    page = sector.event_table(bundle, "bank").set_index("event_id")
    assert len(t) > 0
    for eid in t.index:
        assert t.loc[eid, "main_test"] == page.loc[eid, "main_test"], eid


def test_event_missing_from_summary_raises_keyerror(bundle, no_results, tmp_path):
    summ = pd.read_csv(tl.SUMMARY_PATH)
    full = tl.timeline(bundle, "BBRI", no_results)
    missing = "ev_danantara_launch"
    assert missing in set(full.event_id)
    path = tmp_path / "summary.csv"
    summ[summ.event_id != missing].to_csv(path, index=False)
    with pytest.raises(KeyError, match=missing):
        tl.timeline(bundle, "BBRI", no_results, summary_path=path)


def test_no_results_dir_gives_nan_car(bundle, no_results):
    assert not tl.has_results(no_results)
    t = tl.timeline(bundle, "BBRI", no_results)
    assert t.car.isna().all()
    assert t.sector_median_car.isna().all()


def test_fake_cars_fill_car_and_sector_median(bundle, tmp_path):
    ev = "ev_danantara_launch"
    bank = bundle.measures[(bundle.measures.event_id == ev) & bundle.measures.in_event_sample
                           & (bundle.measures.sector_bucket == "bank")].ticker.tolist()
    assert "BBRI" in bank and len(bank) >= 3
    others = [x for x in bank if x != "BBRI"]
    rows = [dict(event_id=ev, ticker="BBRI", model="market", window="[-1,+1]", car=0.02)]
    vals = [0.10, -0.04, 0.06, 0.0, 0.01, 0.03, 0.05]
    for x, v in zip(others, vals):
        rows.append(dict(event_id=ev, ticker=x, model="market", window="[-1,+1]", car=v))
    used = vals[:len(others)]
    # a different model and window must be ignored
    rows.append(dict(event_id=ev, ticker="BBRI", model="dimson", window="[-1,+1]", car=9.0))
    rows.append(dict(event_id=ev, ticker="BBRI", model="market", window="[0,+2]", car=8.0))
    pd.DataFrame(rows).to_csv(tmp_path / "cars.csv", index=False)

    assert tl.has_results(tmp_path)
    t = tl.timeline(bundle, "BBRI", tmp_path).set_index("event_id")
    assert t.loc[ev, "car"] == pytest.approx(0.02)
    assert t.loc[ev, "sector_median_car"] == pytest.approx(np.median([0.02] + used))
    other = t.drop(index=ev)
    assert other.car.isna().all() and other.sector_median_car.isna().all()

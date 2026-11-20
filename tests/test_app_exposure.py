import math
import re
from datetime import date
from pathlib import Path

import pytest

from influence.app import data, exposure

ON = date(2025, 6, 30)
ORDER = ["state_own", "board_party", "board_office", "board_former", "board_family",
         "group_conn", "dist_gov"]
BANNED = ["risk", "risky", "captured", "corrupt", "favoured", "crony"]


@pytest.fixture(scope="module")
def bundle():
    return data.load()


def test_profile_shape_order_and_labels(bundle):
    p = exposure.profile(bundle, "BBTN", ON)
    assert list(p.columns) == ["measure", "label", "value", "display", "n_edges"]
    assert list(p.measure) == ORDER
    labels = dict(zip(p.measure, p.label))
    assert labels["state_own"] == "State shareholding"
    assert labels["dist_gov"] == "Steps to the state or a governing party"
    assert "composite" not in " ".join(p.columns).lower()


def test_bbtn_board_office_with_annual_report_evidence(bundle):
    p = exposure.profile(bundle, "BBTN", ON).set_index("measure")
    assert p.loc["board_office", "value"] >= 1
    ev = exposure.evidence(bundle, "BBTN", ON, "board_office")
    assert len(ev) >= 1
    assert list(ev.columns) == ["from_name", "relation", "to_name", "start", "end", "source_url"]
    assert ev.source_url.str.startswith("doc:btn_ar_2025").any()
    assert "held_office" in set(ev.relation)
    assert not ev.from_name.str.startswith("p_").any()   # names, not node ids
    assert p.loc["board_office", "n_edges"] == len(ev)


def test_evidence_dates_are_strings_with_empty_for_open_ended(bundle):
    ev = exposure.evidence(bundle, "BBTN", ON, "board_office")
    for col in ("start", "end"):
        assert all(isinstance(v, str) for v in ev[col])
    assert "" in set(ev.end)
    assert "2026-02-25" in set(ev.end)


def test_bbca_state_own_zero_and_group_conn_no(bundle):
    p = exposure.profile(bundle, "BBCA", ON).set_index("measure")
    assert p.loc["state_own", "value"] == 0
    assert p.loc["state_own", "display"] == "0.0%"
    assert p.loc["group_conn", "display"] == "no"
    assert len(exposure.evidence(bundle, "BBCA", ON, "state_own")) == 0


def test_display_formats(bundle):
    p = exposure.profile(bundle, "BBTN", ON).set_index("measure")
    assert re.fullmatch(r"\d+(\.\d)?%", p.loc["state_own", "display"])
    assert p.loc["state_own", "display"] == "60.0%"
    assert p.loc["board_office", "display"] == str(int(p.loc["board_office", "value"]))
    assert p.loc["dist_gov", "display"] == "1"
    assert exposure._display("dist_gov", math.inf) == "no path"
    assert exposure._display("group_conn", 1.0) == "yes"
    assert exposure._display("group_conn", 0.0) == "no"
    assert exposure._display("board_party", 3.0) == "3"


def test_every_evidence_row_has_a_source(bundle):
    for ticker in ("BBTN", "BBCA", "BBRI"):
        for m in ORDER:
            ev = exposure.evidence(bundle, ticker, ON, m)
            assert ev.source_url.notna().all()
            assert (ev.source_url.str.len() > 0).all()


def test_evidence_count_matches_profile(bundle):
    p = exposure.profile(bundle, "BBTN", ON).set_index("measure")
    for m in ORDER:
        assert p.loc[m, "n_edges"] == len(exposure.evidence(bundle, "BBTN", ON, m))
    assert p.loc["dist_gov", "n_edges"] >= 1


def test_unknown_measure_raises(bundle):
    with pytest.raises(KeyError):
        exposure.evidence(bundle, "BBTN", ON, "composite")


def test_data_note(bundle):
    note = exposure.data_note(bundle, "BBTN", ON)
    assert "7 board members" in note
    note_bca = exposure.data_note(bundle, "BBCA", ON)
    assert note_bca.startswith("0 board members")
    assert "none recorded" in note_bca and "none exist" in note_bca


def test_data_note_no_roster_caveat_absent_when_complete(bundle, monkeypatch):
    monkeypatch.setattr(exposure, "coverage", lambda *a, **k: 1.0)
    assert "none recorded" not in exposure.data_note(bundle, "BBTN", ON)


def test_module_source_has_no_banned_words():
    src = Path(exposure.__file__).read_text(encoding="utf-8").lower()
    for word in BANNED:
        assert word not in src, word

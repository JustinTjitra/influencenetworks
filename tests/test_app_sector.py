import re
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from influence.app import data, sector

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "src" / "influence" / "app" / "sector.py"
PAGE = ROOT / "src" / "influence" / "app" / "pages" / "1_Sector.py"
BANNED = ["ri" + "sk", "ri" + "sky", "cap" + "tured", "cor" + "rupt", "favou" + "red", "cro" + "ny"]
STATE_BANKS = ["BBRI", "BMRI", "BBNI", "BBTN", "BRIS"]
ON = date(2025, 6, 30)
# Column names of stacked.csv as written by influence/events/run.py (`group, model, window,
# conn` at the dict in the "# ---- stacked" block, then crosssection.stacked()'s result keys).
STACKED_ROW = dict(spec="sector_event_fe", n=40, n_firms=10, n_events=4, n_treated=8,
                   identified=True, d=0.5, se=0.1, t=5.0, p=0.01, ci_low=0.3, ci_high=0.7,
                   controls="", dropped_controls="", note="")


@pytest.fixture(scope="module")
def bundle():
    return data.load()


def test_bank_table_has_12_rows_and_state_banks_owned(bundle):
    t = sector.measures_table(bundle, "bank", ON)
    assert len(t) == 12
    own = t.set_index("ticker")["state_own"]
    for tk in STATE_BANKS:
        assert tk in own.index
        assert own[tk] >= 0.5, tk


def test_measures_table_columns_are_registered_measures_only(bundle):
    t = sector.measures_table(bundle, "palm", ON)
    assert list(t.columns) == ["ticker", "firm", "state_own", "board_party", "board_office",
                               "board_former", "board_family", "group_conn", "dist_gov",
                               "n_board_known"]
    assert set(t.ticker) == set(bundle.tickers[bundle.tickers.sector_bucket == "palm"].ticker)


def test_palm_event_table_lists_export_ban(bundle):
    t = sector.event_table(bundle, "palm")
    assert "ev_cpo_export_ban" in set(t.event_id)
    row = t[t.event_id == "ev_cpo_export_ban"].iloc[0]
    assert row.main_test == "no"
    assert row.n_connected_firms == 0


def test_event_table_scopes_by_sector(bundle):
    ev = bundle.events.set_index("event_id")
    bank = sector.event_table(bundle, "bank")
    palm = sector.event_table(bundle, "palm")
    assert "ev_cpo_export_ban" not in set(bank.event_id)
    assert len(bank) == 14 + 2 and len(palm) == 14 + 6
    for tbl, name in ((bank, "bank"), (palm, "palm")):
        assert set(ev.loc[tbl.event_id, "sector"]) <= {name, "all"}
    assert bank.main_test.isin(["yes", "no"]).all()
    assert "yes" in set(bank.main_test)


def test_stacked_results_none_without_results_dir(tmp_path):
    assert sector.stacked_results(tmp_path / "missing") is None
    assert sector.stacked_results(tmp_path) is None


def test_stacked_results_none_for_synthetic_dir(tmp_path):
    d = tmp_path / "results_synthetic"
    d.mkdir()
    pd.DataFrame([dict(group="main: all", model="market", window="[-1,+1]", conn="binary",
                       **STACKED_ROW)]).to_csv(d / "stacked.csv", index=False)
    assert sector.stacked_results(d) is None


def test_stacked_results_filters_window_and_conn(tmp_path):
    rows = [dict(group="main: all", model="market", window=w, conn=c, **STACKED_ROW)
            for w in ("[-1,+1]", "[0,+5]") for c in ("binary", "value")]
    pd.DataFrame(rows).to_csv(tmp_path / "stacked.csv", index=False)
    out = sector.stacked_results(tmp_path)
    assert len(out) == 1
    assert out.iloc[0]["d"] == 0.5
    assert {"group", "model", "spec", "d", "se", "p"} <= set(out.columns)


def test_new_sources_use_neutral_wording():
    for path in (MODULE, PAGE):
        text = path.read_text(encoding="utf-8").lower()
        for word in BANNED:
            assert not re.search(word, text), f"{word!r} found in {path.name}"
        assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
        assert "composite" not in text and "gov_proximity" not in text


def _page():
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest
    return AppTest.from_file(str(PAGE), default_timeout=180)


def test_page_renders_tables_and_no_results_text(monkeypatch, tmp_path):
    monkeypatch.setattr(sector, "DEFAULT_RESULTS_DIR", tmp_path / "none")
    at = _page()
    at.secrets["app_password"] = "pw"
    at.run()
    at.text_input[0].set_value("pw").run()
    assert not at.exception
    assert len(at.dataframe) == 2
    assert any("Results appear here after the event study has been run." in m.value
               for m in at.markdown)
    assert any("Every item links to its source. Report an error:" in m.value for m in at.markdown)


def test_page_refuses_without_password_secret():
    at = _page()
    at.run()
    assert not at.exception
    assert any("app_password" in e.value for e in at.error)
    assert len(at.dataframe) == 0
    assert not any("Results appear here" in m.value for m in at.markdown)

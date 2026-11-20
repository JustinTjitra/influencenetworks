import re
from pathlib import Path

import pytest

from influence.app import auth

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "src" / "influence" / "app" / "streamlit_app.py"
AUTH = ROOT / "src" / "influence" / "app" / "auth.py"
SECTIONS = ["Stakeholder map", "Exposure profile", "Event timeline", "Lenders"]
BANNED = ["ri" + "sk", "ri" + "sky", "cap" + "tured", "cor" + "rupt", "favou" + "red", "cro" + "ny"]


def test_check_password_true_and_false():
    assert auth.check_password("s3cret", "s3cret") is True
    assert auth.check_password("wrong", "s3cret") is False
    assert auth.check_password("", "s3cret") is False


def test_new_modules_use_neutral_wording():
    for path in (APP, AUTH):
        text = path.read_text(encoding="utf-8").lower()
        for word in BANNED:
            assert not re.search(word, text), f"{word!r} found in {path.name}"


def test_no_hardcoded_email_address():
    for path in (APP, AUTH):
        assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", path.read_text(encoding="utf-8"))


def _headers(at):
    return [h.value for h in at.header]


def _app():
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest
    return AppTest.from_file(str(APP), default_timeout=120)


def test_app_renders_four_sections_with_password():
    at = _app()
    at.secrets["app_password"] = "pw"
    at.run()
    at.text_input[0].set_value("pw").run()
    assert not at.exception
    assert _headers(at) == SECTIONS
    assert any("Every item links to its source. Report an error:" in m.value
               and "contact the project owner" in m.value for m in at.markdown)


def test_footer_mailto_uses_secret():
    at = _app()
    at.secrets["app_password"] = "pw"
    at.secrets["contact_email"] = "someone@example.org"
    at.run()
    at.text_input[0].set_value("pw").run()
    assert not at.exception
    assert any("mailto:someone@example.org" in m.value for m in at.markdown)


def test_app_refuses_to_start_without_password_secret():
    at = _app()
    at.run()
    assert not at.exception
    assert any("app_password" in e.value for e in at.error)
    assert _headers(at) == []


def test_wrong_password_shows_no_sections():
    at = _app()
    at.secrets["app_password"] = "pw"
    at.run()
    assert _headers(at) == []
    at.text_input[0].set_value("nope").run()
    assert not at.exception
    assert any("Wrong password" in e.value for e in at.error)
    assert _headers(at) == []


def test_timeline_blank_firm_value_for_composite_and_no_car_columns(tmp_path):
    pytest.importorskip("streamlit")
    from influence.app import data, streamlit_app
    bundle = data.load()
    m = bundle.measures
    tickers = m[m.in_event_sample & (m.tested_measure == "all")].ticker.unique()
    assert len(tickers) > 0
    others = m[m.in_event_sample & (m.tested_measure != "all") & m.tested_value.notna()]
    assert len(others) > 0
    shown = {}
    for tk in list(tickers[:1]) + list(others.ticker.unique()[:1]):
        tl = streamlit_app.timeline_view(bundle, tk, tmp_path)[0]
        shown[tk] = tl
    comp = shown[tickers[0]]
    assert (comp.tested_measure == "all").any()
    assert comp.loc[comp.tested_measure == "all", "firm_value"].isna().all()
    tl, has = streamlit_app.timeline_view(bundle, tickers[0], tmp_path)
    assert has is False
    assert "car" not in tl.columns and "sector_median_car" not in tl.columns
    other = shown[others.ticker.unique()[0]]
    assert other.loc[other.tested_measure != "all", "firm_value"].notna().any()

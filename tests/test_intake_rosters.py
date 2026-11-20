import io

import pandas as pd

from influence.intake import rosters as R

TICKERS = ["BBRI", "BMRI"]


def _row(**kw):
    base = {c: "" for c in R.COLUMNS}
    base.update(doc_id="d1", ticker="BBRI", organ="directors",
                person_name="Ann Lee", role="Director", start_date="2024-01-02",
                page="10")
    base.update(kw)
    return base


def _df(*rows):
    return pd.DataFrame(list(rows), columns=R.COLUMNS)


def _has(problems, text):
    return any(text in p for p in problems)


def test_template_header_and_examples():
    lines = R.template("d1", "BBRI").splitlines()
    assert lines[0] == ",".join(R.COLUMNS)
    assert len(lines) == 3 and all(l.startswith("# d1,BBRI,") for l in lines[1:])
    # commented rows are skipped when read back
    tf = io.StringIO(R.template("d1", "BBRI"))
    df = R.read_roster(tf)
    assert list(df.columns) == R.COLUMNS and len(df) == 0


def test_valid_row_passes():
    assert R.validate(_df(_row()), TICKERS) == []


def test_required_fields():
    assert _has(R.validate(_df(_row(person_name="")), TICKERS), "person_name is required")


def test_organ_and_ticker():
    assert _has(R.validate(_df(_row(organ="board")), TICKERS), "organ")
    assert _has(R.validate(_df(_row(ticker="ZZZZ")), TICKERS), "unknown ticker")


def test_dates():
    assert _has(R.validate(_df(_row(start_date="2024-13")), TICKERS), "start_date")
    assert _has(R.validate(_df(_row(start_date="2024-02-30")), TICKERS), "start_date")
    assert _has(R.validate(_df(_row(end_date="2023-12-31")), TICKERS), "before")
    assert R.validate(_df(_row(start_date="2024", end_date="2024-06")), TICKERS) == []


def test_pages_positive():
    assert _has(R.validate(_df(_row(page="0")), TICKERS), "page")
    assert _has(R.validate(_df(_row(page="x")), TICKERS), "page")


def test_government_post_needs_body_and_page():
    p = R.validate(_df(_row(government_post="Minister")), TICKERS)
    assert _has(p, "government_body") and _has(p, "post_page")
    ok = _row(government_post="Minister", government_body="Ministry X", post_page="5")
    assert R.validate(_df(ok), TICKERS) == []


def test_duplicates_and_spaces():
    assert _has(R.validate(_df(_row(), _row()), TICKERS), "duplicate")
    assert _has(R.validate(_df(_row(person_name=" Ann Lee")), TICKERS), "spaces")


def test_person_id():
    assert R.person_id("Dr. H. Ann  Lee, S.E.") == "p_dr_h_ann_lee_s_e"


def test_to_edges():
    df = _df(
        _row(organ="commissioners", person_name="Ann Lee", role="President Commissioner", page="10"),
        _row(person_name="Bob Tan", page="12", note="n1", government_post="Deputy Minister",
             government_body="Ministry X", post_start="2020", post_page="40"),
        _row(ticker="BMRI", person_name="Cy O'Neil", page="7", end_date="2025"),
    )
    e = R.to_edges(df)
    assert len(e) == 4
    assert list(e["type"]) == ["board_seat", "board_seat", "held_office", "board_seat"]
    assert list(e["source_id"]) == ["p_ann_lee", "p_bob_tan", "p_bob_tan", "p_cy_o_neil"]
    assert list(e["source_url"]) == ["doc:d1#p10", "doc:d1#p12", "doc:d1#p40", "doc:d1#p7"]
    assert set(e["source_type"]) == {"annual_report"} and set(e["confidence"]) == {"high"}
    assert list(e["ticker"]) == ["BBRI", "BBRI", "", "BMRI"]
    assert set(e["target_id"]) == {""}
    assert e.loc[2, "note"] == "Ministry X" and e.loc[2, "role"] == "Deputy Minister"
    assert e.loc[3, "end_date"] == "2025"
    for c in R.EDGE_COLUMNS:
        assert c in e.columns


def _write(tmp_path, *rows):
    p = tmp_path / "r.csv"
    body = R.template("d1", "BBRI")
    for r in rows:
        body += ",".join(r[c] for c in R.COLUMNS) + "\n"
    p.write_text(body, encoding="utf-8")
    return p


def test_read_roster_keeps_hash_inside_fields(tmp_path):
    p = _write(tmp_path, _row(note="see item #3"))
    df = R.read_roster(p)
    assert len(df) == 1
    assert df.loc[0, "note"] == "see item #3"
    assert df.loc[0, "page"] == "10"


def test_read_roster_keeps_hash_in_quoted_note(tmp_path):
    p = _write(tmp_path)
    p.write_text(p.read_text() + 'd1,BBRI,directors,Ann Lee,Director,2024,,10,,"see item #3, p. 4",,,,,\n')
    df = R.read_roster(p)
    assert len(df) == 1
    assert df.loc[0, "note"] == "see item #3, p. 4"
    assert df.loc[0, "post_page"] == ""


def test_cli_validate(tmp_path, capsys):
    good = _write(tmp_path, _row())
    assert R.main(["validate", str(good)]) == 0
    bad = tmp_path / "bad.csv"
    bad.write_text(good.read_text() + ",".join(_row(organ="board", person_name="Bo")[c] for c in R.COLUMNS) + "\n")
    assert R.main(["validate", str(bad)]) == 1
    assert "organ" in capsys.readouterr().out

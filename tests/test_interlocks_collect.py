import pytest

from influence.interlocks import collect_profiles as cp


def test_profile_url():
    u = cp.profile_url("bmri", base="https://example.test/")
    assert u == ("https://example.test/primary/ListedCompany/GetCompanyProfilesDetail"
                 "?KodeEmiten=BMRI&language=en-us")


def test_out_path(tmp_path):
    assert cp.out_path(tmp_path, "2026-11-20", "BBRI") == tmp_path / "2026-11-20" / "BBRI.json"


def test_load_tickers(tmp_path):
    f = tmp_path / "t.csv"
    f.write_text("node_id,ticker,x\na,BMRI,1\nb,,2\nc,bbri,3\nd,BMRI,4\n", encoding="utf-8")
    assert cp.load_tickers(f) == ["BMRI", "BBRI"]


def test_plan_skips_existing_nonempty(tmp_path):
    day = "2026-11-20"
    p = cp.out_path(tmp_path, day, "AAA")
    p.parent.mkdir(parents=True)
    p.write_bytes(b"{}")
    cp.out_path(tmp_path, day, "BBB").write_bytes(b"")
    assert cp.plan(["AAA", "BBB", "CCC"], tmp_path, day) == ["BBB", "CCC"]


def test_fetch_all_preserves_raw_bytes_and_sleeps_between(tmp_path):
    body = b'{"a": 1,\r\n "b": "\xc3\xa9"}  '
    calls, sleeps = [], []

    def fetch(url):
        calls.append(url)
        return 200, body

    res = cp.fetch_all(["AAA", "BBB", "CCC"], tmp_path, "d", fetch, sleeps.append, 3.0, 6.0)
    assert res == [("AAA", 200, len(body)), ("BBB", 200, len(body)), ("CCC", 200, len(body))]
    assert cp.out_path(tmp_path, "d", "BBB").read_bytes() == body
    assert len(calls) == 3 and "KodeEmiten=AAA" in calls[0]
    assert len(sleeps) == 2 and all(3.0 <= s <= 6.0 for s in sleeps)


def test_fetch_all_skips_existing(tmp_path):
    p = cp.out_path(tmp_path, "d", "AAA")
    p.parent.mkdir(parents=True)
    p.write_bytes(b"old")
    calls = []
    res = cp.fetch_all(["AAA", "BBB"], tmp_path, "d", lambda u: (calls.append(u), (200, b"{}"))[1], lambda s: None)
    assert [r[0] for r in res] == ["BBB"]
    assert p.read_bytes() == b"old"


def test_stops_after_three_consecutive_failures(tmp_path):
    calls = []

    def fetch(url):
        calls.append(url)
        return 403, b"blocked"

    res = cp.fetch_all(list("ABCDE"), tmp_path, "d", fetch, lambda s: None)
    assert len(calls) == 3
    assert res == [("A", 403, 0), ("B", 403, 0), ("C", 403, 0)]
    assert not cp.out_path(tmp_path, "d", "A").exists()


def test_success_resets_failure_count(tmp_path):
    statuses = iter([500, 500, 200, 500, 500, 200])
    res = cp.fetch_all(list("ABCDEF"), tmp_path, "d", lambda u: (next(statuses), b"{}"), lambda s: None)
    assert len(res) == 6


def test_exception_counts_as_failure(tmp_path):
    def fetch(url):
        raise RuntimeError("boom")

    res = cp.fetch_all(list("ABCD"), tmp_path, "d", fetch, lambda s: None)
    assert res == [("A", 0, 0), ("B", 0, 0), ("C", 0, 0)]


def test_http_mode_requires_contact_email(monkeypatch):
    monkeypatch.delenv("CONTACT_EMAIL", raising=False)
    with pytest.raises(SystemExit) as e:
        cp.make_http_fetch()
    assert "CONTACT_EMAIL" in str(e.value)


def test_html_body_with_status_200_is_a_failure(tmp_path):
    res = cp.fetch_all(["A"], tmp_path, "d", lambda u: (200, b"<html>Just a moment</html>"), lambda s: None)
    assert res == [("A", 200, 0)]
    assert not cp.out_path(tmp_path, "d", "A").exists()


def test_three_html_bodies_in_a_row_stop_the_run(tmp_path):
    calls = []

    def fetch(url):
        calls.append(url)
        return 200, b"  \n<!DOCTYPE html><html></html>"

    res = cp.fetch_all(list("ABCDE"), tmp_path, "d", fetch, lambda s: None)
    assert len(calls) == 3
    assert res == [("A", 200, 0), ("B", 200, 0), ("C", 200, 0)]


def test_json_with_leading_whitespace_and_bom_saved_unchanged(tmp_path):
    b1 = b' \r\n\t{"a": 1}\n'
    b2 = b'\xef\xbb\xbf  [1, 2]'
    bodies = iter([b1, b2])
    res = cp.fetch_all(["A", "B"], tmp_path, "d", lambda u: (200, next(bodies)), lambda s: None)
    assert res == [("A", 200, len(b1)), ("B", 200, len(b2))]
    assert cp.out_path(tmp_path, "d", "A").read_bytes() == b1
    assert cp.out_path(tmp_path, "d", "B").read_bytes() == b2

import datetime as dt
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from influence.app import data, lenders


@pytest.fixture(scope="module")
def bundle():
    return data.load()


def test_smar_has_credit_from_two_banks(bundle):
    df = lenders.lenders(bundle, "SMAR")
    assert list(df.columns) == lenders.COLUMNS
    credit = df[df.kind == "credit"]
    assert credit.bank.nunique() >= 2
    assert (credit.amount_usd_m > 0).all()
    assert df.source_url.str.startswith("http").all()
    assert df.confidence.notna().all()
    assert df.year.between(2000, 2030).all()
    assert set(df.kind) <= {"credit", "holding"}


def test_bank_returns_empty_frame_with_columns(bundle):
    df = lenders.lenders(bundle, "BBCA")
    assert df.empty
    assert list(df.columns) == lenders.COLUMNS


EDGES_CSV = Path(__file__).resolve().parents[1] / "data" / "processed" / "edges.csv"


def _file_rows(targets):
    f = pd.read_csv(EDGES_CSV, dtype={"start_date": str})
    f = f[(f.type == "finances") & f.target_id.isin(targets)].copy()
    f["m"] = (f.amount_usd / 1e6).round(1)
    f["kind"] = f.role.str.split(":").str[0].str.strip()
    return f


def test_smar_rows_match_edge_file(bundle):
    df = lenders.lenders(bundle, "SMAR")
    f = _file_rows({"pg_sinarmas"})
    assert len(df) == len(f) > 17
    assert df.amount_usd_m.sum() == pytest.approx(f.m.sum(), abs=0.1 * len(f))


def test_credit_by_bank_matches_file_per_bank(bundle):
    df = lenders.lenders(bundle, "SMAR")
    out = lenders.credit_by_bank(df)
    f = _file_rows({"pg_sinarmas"})
    f = f[f.kind == "credit"]
    names = {n: d["name"] for n, d in bundle.graph.nodes(data=True)}
    per_bank = f.groupby(f.source_id.map(names)).agg(total=("m", "sum"), n=("m", "size"))
    assert set(out.bank) == set(per_bank.index)
    for bank, amt in zip(out.bank, out.amount_usd_m):
        assert amt == pytest.approx(per_bank.loc[bank, "total"], abs=0.1 * per_bank.loc[bank, "n"])


def test_palm_rows_not_fewer_than_graph(bundle):
    g = bundle.graph
    total = graph_total = 0
    seen = set()
    for t in bundle.tickers[bundle.tickers.sector_bucket == "palm"].ticker:
        node = data.firm_node(bundle, t)
        targets = {node} | {v for _, v, d in g.out_edges(node, data=True) if d["type"] == "member_of_group"}
        total += len(lenders.lenders(bundle, t))
        graph_total += sum(1 for _, _, d in g.in_edges(targets, data=True) if d["type"] == "finances")
    assert total >= graph_total > 0
    assert total > graph_total


def test_credit_by_bank_sums_credit_only_sorted(bundle):
    df = lenders.lenders(bundle, "SMAR")
    out = lenders.credit_by_bank(df)
    credit = df[df.kind == "credit"]
    assert list(out.columns) == ["bank", "amount_usd_m"]
    assert out.amount_usd_m.is_monotonic_decreasing
    assert out.amount_usd_m.sum() == pytest.approx(credit.amount_usd_m.sum(), abs=0.2)
    for bank, amt in zip(out.bank, out.amount_usd_m):
        assert amt == pytest.approx(credit[credit.bank == bank].amount_usd_m.sum(), abs=0.1)


def test_credit_and_holdings_never_added_together():
    df = pd.DataFrame([
        {"bank": "A", "year": 2020, "kind": "credit", "detail": "Loan", "amount_usd_m": 10.0,
         "source_url": "u", "confidence": "medium"},
        {"bank": "A", "year": 2026, "kind": "holding", "detail": "Shareholding", "amount_usd_m": 500.0,
         "source_url": "u", "confidence": "medium"},
        {"bank": "B", "year": 2021, "kind": "holding", "detail": "Bondholding", "amount_usd_m": 900.0,
         "source_url": "u", "confidence": "medium"},
        {"bank": "C", "year": 2021, "kind": "credit", "detail": "Loan", "amount_usd_m": 30.0,
         "source_url": "u", "confidence": "medium"},
    ])
    out = lenders.credit_by_bank(df)
    assert list(out.bank) == ["C", "A"]
    assert list(out.amount_usd_m) == [30.0, 10.0]


def test_credit_by_bank_real_data_excludes_holdings(bundle):
    for t in ("SMAR", "AALI", "LSIP"):
        df = lenders.lenders(bundle, t)
        out = lenders.credit_by_bank(df)
        holding_only = set(df[df.kind == "holding"].bank) - set(df[df.kind == "credit"].bank)
        assert not holding_only & set(out.bank)
        assert out.amount_usd_m.sum() == pytest.approx(df[df.kind == "credit"].amount_usd_m.sum(), abs=0.5)


def test_credit_by_bank_empty():
    empty = pd.DataFrame(columns=lenders.COLUMNS)
    out = lenders.credit_by_bank(empty)
    assert out.empty and list(out.columns) == ["bank", "amount_usd_m"]


def test_missing_source_url_raises(bundle, monkeypatch):
    real = lenders._finance_edges()
    bad = SimpleNamespace(source_id=real[0].source_id, target_id="pg_sinarmas", role="credit: Loan",
                          source_url="", start_date=dt.date(2020, 1, 1), amount_usd=1e6,
                          confidence="medium")
    monkeypatch.setattr(lenders, "_finance_edges", lambda: (bad,))
    with pytest.raises(ValueError, match="source_url"):
        lenders.lenders(bundle, "SMAR")


def test_licence_note_and_neutral_wording():
    note = lenders.licence_note()
    assert note.startswith("Financing data: Forests & Finance, personal-use licence.")
    assert "Rainforest Action Network" in note
    src = open(lenders.__file__).read().lower()
    for word in ["captured", "crony", "corrupt", "favoured", "risky"]:
        assert word not in src

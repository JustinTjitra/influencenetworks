import pandas as pd
import pytest

from influence.intake import fundamentals as fu

TICKERS = ["BMRI", "BBCA"]
GOOD = dict(ticker="BMRI", fiscal_year_end="2023-12-31", shares_outstanding=100,
            total_assets=10, total_liabilities=5, currency="IDR", unit="1e6",
            source_url="https://example.org/ar.pdf", note="")


def frame(*rows):
    return pd.DataFrame([{**GOOD, **r} for r in rows], columns=fu.COLUMNS)


def test_empty_file_is_valid(tmp_path):
    p = tmp_path / "f.csv"
    p.write_text(",".join(fu.COLUMNS) + "\n")
    assert fu.validate(pd.read_csv(p), TICKERS) == []
    assert len(fu.load(p, TICKERS)) == 0


def test_good_row_valid():
    assert fu.validate(frame({}), TICKERS) == []
    assert fu.validate(frame({"source_url": "doc:ar2023#p12"}), TICKERS) == []


@pytest.mark.parametrize("bad", [
    {"ticker": "XXXX"},
    {"fiscal_year_end": "31/12/2023"},
    {"shares_outstanding": 0},
    {"total_assets": -1},
    {"total_liabilities": -1},
    {"total_liabilities": 16},
    {"currency": "USD"},
    {"unit": "1e4"},
    {"source_url": "ftp://x"},
    {"source_url": "doc:abc"},
])
def test_each_rule_triggers(bad):
    assert len(fu.validate(frame(bad), TICKERS)) == 1


def test_duplicate():
    assert len(fu.validate(frame({}, {}), TICKERS)) == 1


def test_scaling(tmp_path):
    p = tmp_path / "f.csv"
    frame({}).to_csv(p, index=False)
    out = fu.load(p, TICKERS)
    assert out.total_assets[0] == 10e6 and out.total_liabilities[0] == 5e6
    assert out.shares_outstanding[0] == 100


def test_load_raises_listing_problems(tmp_path):
    p = tmp_path / "f.csv"
    frame({"currency": "USD"}, {"ticker": "ZZZ", "fiscal_year_end": "2022-12-31"}).to_csv(p, index=False)
    with pytest.raises(ValueError) as e:
        fu.load(p, TICKERS)
    assert "currency" in str(e.value) and "ZZZ" in str(e.value)


def test_coverage_shape():
    cov = fu.coverage(frame({}), TICKERS, [2022, 2023])
    assert cov.shape == (2, 3)
    assert list(cov.columns) == ["ticker", 2022, 2023]
    assert bool(cov.loc[cov.ticker == "BMRI", 2023].iloc[0]) is True
    assert not cov[[2022, 2023]].loc[cov.ticker == "BBCA"].any().any()

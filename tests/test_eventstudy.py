import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from influence.events import controls as C
from influence.events import crosssection as X
from influence.events import eventstudy as es
from influence.events import prices, synthetic

# Everything here is simulated. No market data is used in the tests.


def panel_from_returns(cal, rm, firm_returns: dict, volume=None):
    frames = [pd.DataFrame(dict(date=cal, ticker=es.MARKET, close=1000 * np.cumprod(1 + rm),
                                adj_close=1000 * np.cumprod(1 + rm), volume=1e9))]
    for t, r in firm_returns.items():
        px = 500 * np.cumprod(1 + r)
        v = np.full(len(cal), 1e6) if volume is None else volume.get(t, np.full(len(cal), 1e6))
        frames.append(pd.DataFrame(dict(date=cal, ticker=t, close=px, adj_close=px, volume=v)))
    return pd.concat(frames, ignore_index=True)


@pytest.fixture(scope="module")
def toy():
    cal = synthetic.calendar("2022-01-03", "2023-12-29")
    rng = np.random.default_rng(7)
    rm = rng.normal(0.0002, 0.01, len(cal))
    i0 = 400
    r = 0.001 + 1.5 * rm                       # exact one-factor returns
    r[i0 - 1] += 0.02
    r[i0] += -0.01
    r[i0 + 1] += 0.03
    rp = es.prepare(panel_from_returns(cal, rm, {"AAAA": r}))
    return rp, cal, rm, i0


def test_car_reproduces_hand_computed_numbers(toy):
    rp, cal, rm, i0 = toy
    event = cal[i0]
    est = es.estimate(rp, "AAAA", event, "market")
    assert est.ok and est.alpha == pytest.approx(0.001, abs=1e-9)
    assert est.beta == pytest.approx(1.5, abs=1e-9)
    assert est.n_obs == 221 and est.n_valid == 221
    # market model: the planted abnormal returns, 0.02 - 0.01 + 0.03
    assert es.car(rp, "AAAA", event, (-1, 1), "market") == pytest.approx(0.04, abs=1e-9)
    assert es.car(rp, "AAAA", event, (0, 0), "market") == pytest.approx(-0.01, abs=1e-9)
    # market-adjusted: R_i - R_m = 0.001 + 0.5 R_m + planted, summed over three days
    by_hand = 0.04 + 3 * 0.001 + 0.5 * rm[i0 - 1:i0 + 2].sum()
    assert es.car(rp, "AAAA", event, (-1, 1), "market_adjusted") == pytest.approx(by_hand, abs=1e-9)
    # Dimson: lead and lag betas are zero in exact data, so it matches the market model
    d = es.estimate(rp, "AAAA", event, "dimson")
    assert d.betas == pytest.approx((0.0, 1.5, 0.0), abs=1e-8)
    assert es.car(rp, "AAAA", event, (-1, 1), "dimson") == pytest.approx(0.04, abs=1e-8)
    # the pre-event leakage window holds nothing
    assert es.car(rp, "AAAA", event, (-5, -2), "market") == pytest.approx(0.0, abs=1e-9)
    ar = es.abnormal_returns(rp, "AAAA", event, "market", span=(-1, 1))
    assert ar.tolist() == pytest.approx([0.02, -0.01, 0.03], abs=1e-9)


def test_trading_day_windows_skip_holidays_and_weekends(toy):
    rp, cal, rm, _ = toy
    # the invented calendar is closed 8-12 April; 2023-04-10 is inside that week
    assert pd.Timestamp("2023-04-10") not in cal
    i = rp.day0("2023-04-10")
    assert pd.Timestamp(rp.dates[i]) == pd.Timestamp("2023-04-13")
    assert pd.Timestamp(rp.dates[i - 1]) == pd.Timestamp("2023-04-07")       # day -1 is the Friday before
    # a Saturday event reacts on Monday; after-close news on a Friday also moves to Monday
    assert pd.Timestamp(rp.dates[rp.day0("2023-06-10")]) == pd.Timestamp("2023-06-12")
    assert pd.Timestamp(rp.dates[rp.day0("2023-06-09")]) == pd.Timestamp("2023-06-09")
    assert pd.Timestamp(rp.dates[rp.day0("2023-06-09", after_close=True)]) == pd.Timestamp("2023-06-12")
    # the CAR over [-1,+1] of the holiday event is the sum over 7, 13 and 14 April
    idx = [i - 1, i, i + 1]
    est = es.estimate(rp, "AAAA", "2023-04-10", "market")
    by_hand = sum(rp.ret[k, 0] - est.alpha - est.beta * rp.mkt[k] for k in idx)
    assert es.car(rp, "AAAA", "2023-04-10", (-1, 1), "market") == pytest.approx(by_hand, abs=1e-12)
    assert rp.day0("2030-01-01") is None


def test_firm_event_needs_enough_traded_days(toy):
    rp, cal, rm, i0 = toy
    assert not es.estimate(rp, "AAAA", cal[100], "market").ok            # too little history
    vol = {"BBBB": np.where(np.arange(len(cal)) % 2 == 0, 0.0, 1e6)}      # trades every other day
    rp2 = es.prepare(panel_from_returns(cal, rm, {"BBBB": 0.5 * rm}, vol))
    est = es.estimate(rp2, "BBBB", cal[i0], "market")
    assert est.n_obs == 221 and est.n_valid < es.MIN_VALID and not est.ok
    assert np.isnan(es.car(rp2, "BBBB", cal[i0], (-1, 1), "market"))
    assert es.estimate(rp2, "BBBB", cal[i0], "market", min_valid=100).ok


def test_three_models_agree_without_thin_trading():
    tickers = [f"T{i:03d}" for i in range(8)]
    panel = synthetic.make_panel(tickers, seed=3, betas={t: 1.0 for t in tickers},
                                 alphas={t: 0.0 for t in tickers})
    rp = es.prepare(panel)
    event = "2024-09-03"
    cars = np.array([[es.car(rp, t, event, (-1, 1), m) for m in es.MODELS] for t in tickers])
    assert (cars.max(axis=1) - cars.min(axis=1)).max() < 0.02     # same story firm by firm
    assert np.corrcoef(cars.T).min() > 0.95                       # and the same ranking of firms


def test_dimson_beta_corrects_thin_trading():
    tickers = [f"T{i:03d}" for i in range(12)]
    panel = synthetic.make_panel(tickers, seed=5, thin=tickers, thin_share=0.5,
                                 betas={t: 1.2 for t in tickers})
    rp = es.prepare(panel)
    mk = np.mean([es.estimate(rp, t, "2024-09-03", "market", min_valid=60).beta for t in tickers])
    dm = np.mean([es.estimate(rp, t, "2024-09-03", "dimson", min_valid=60).beta for t in tickers])
    assert mk < 1.0 < dm + 0.25 and dm > mk + 0.15       # stale prices bias the plain beta down


def test_abnormal_volume():
    cal = synthetic.calendar("2022-01-03", "2023-12-29")
    rng = np.random.default_rng(1)
    rm = rng.normal(0, 0.01, len(cal))
    v = np.full(len(cal), 1000.0)
    v[400] = 1000.0 * np.e ** 2
    rp = es.prepare(panel_from_returns(cal, rm, {"AAAA": rm.copy()}, {"AAAA": v}))
    assert es.abnormal_volume(rp, "AAAA", cal[400], (0, 0)) == pytest.approx(2.0)
    assert es.abnormal_volume(rp, "AAAA", cal[400], (-1, 1)) == pytest.approx(2.0 / 3)


# ------------------------------------------------------------------ cross-section

def make_study(effect, seed=11, n_firms=24, constant_sign=False):
    tickers = [f"F{i:03d}" for i in range(n_firms)]
    dates = pd.to_datetime(["2021-03-02", "2021-09-14", "2022-02-08", "2022-07-19", "2022-11-22",
                            "2023-03-07", "2023-08-15", "2024-01-23", "2024-06-11", "2024-11-05",
                            "2025-04-22", "2025-09-09"])
    signs = ["-"] * len(dates) if constant_sign else ["+", "-"] * (len(dates) // 2)
    events = pd.DataFrame(dict(
        event_id=[f"e{i:02d}" for i in range(len(dates))], date=dates, after_close=0,
        type=["coalition", "state_governance"] * (len(dates) // 2),
        expected_sign_connected=signs, anticipation_flag=0, confounder_flag=0,
        connection_measure_tested="state_own"))
    treated = set(tickers[::3])
    measures = pd.DataFrame([dict(
        event_id=e, ticker=t, sector_bucket=["bank", "palm", "media"][i % 3 if i % 3 else (i // 3) % 3],
        cluster=t, tested_binary=int(t in treated), tested_value=0.6 if t in treated else 0.0,
        soe=int(t in treated), coverage=0.0, confidence_tier="high",
        state_own=0.6 if t in treated else 0.0, in_event_sample=True)
        for e in events.event_id for i, t in enumerate(tickers)])
    panel = synthetic.make_panel(tickers, start="2019-06-03", end="2025-12-30", seed=seed,
                                 events=events, measures=measures, effect=effect)
    return es.prepare(panel), events, measures


def test_stacked_estimator_recovers_planted_effect():
    rp, events, measures = make_study(effect=0.03)
    cars = es.event_cars(rp, events)
    assert len(cars) == 12 * 24 * 3 * 4 and cars.est_ok.all()
    for model in es.MODELS:
        df = X.regression_frame(cars, measures, events, model)
        for spec in X.SPECS:
            fit = X.stacked(df, spec)
            assert fit["identified"] and fit["n"] == 288
            assert fit["d"] == pytest.approx(0.03, abs=0.01)
            assert fit["p"] < 0.01 and fit["ci_low"] < 0.03 < fit["ci_high"]
            assert X.fe_point_estimate(df, spec) == pytest.approx(fit["d"], abs=1e-10)
    # nothing in the leakage window, where no effect was planted
    lead = X.stacked(X.regression_frame(cars, measures, events, "market", es.LEAKAGE_WINDOW),
                     "sector_event_fe")
    assert abs(lead["d"]) < 0.012


def test_firm_fe_is_reported_as_not_identified_when_sign_never_varies():
    rp, events, measures = make_study(effect=0.03, constant_sign=True)
    df = X.regression_frame(es.event_cars(rp, events, models=("market",), windows=((-1, 1),)),
                            measures, events, "market")
    fe = X.stacked(df, "firm_fe")
    assert not fe["identified"] and np.isnan(fe["d"]) and "not identified" in fe["note"]
    within = X.stacked(df, "sector_event_fe")
    assert within["identified"] and within["d"] == pytest.approx(0.03, abs=0.01)


def test_per_event_ols_and_controls_rule():
    rp, events, measures = make_study(effect=0.05)
    cars = es.event_cars(rp, events, models=("market",), windows=((-1, 1),))
    ctl = C.build_controls(rp, events, measures, synthetic.make_fundamentals(rp.tickers))
    df = X.regression_frame(cars, measures, events, "market", controls=ctl)
    chosen, why = X.choose_controls(df)
    assert chosen == list(X.PRIMARY_CONTROLS) and why == "primary controls"
    # twelve events carry every control; a single event carries one; fifteen firms carry none
    assert 200 < X.identifying_obs(df) <= 288 and X.limit_controls(df, chosen) == chosen
    assert X.limit_controls(df[df.event_id == "e00"], chosen) == ["log_mcap"]
    assert X.limit_controls(df[df.event_id == "e00"].head(15), chosen) == []
    one = X.per_event_ols(df, "e00", chosen)
    assert one["n"] == 24 and one["n_treated"] == 8 and np.isfinite(one["se"])
    assert "soe" not in one["controls"].split()           # collinear with the connection here
    ds = [X.per_event_ols(df, e)["d"] * (1 if s == "+" else -1)
          for e, s in zip(events.event_id, events.expected_sign_connected)]
    assert np.mean(ds) == pytest.approx(0.05, abs=0.012)
    # without fundamentals the pre-registered fallback applies
    bare = X.regression_frame(cars, measures, events, "market",
                              controls=C.build_controls(rp, events, measures, pd.DataFrame(columns=C.FUND_COLUMNS)))
    assert X.choose_controls(bare)[0] == list(X.FALLBACK_CONTROLS)
    flat = df.assign(conn=0.0)
    assert "no variation" in X.per_event_ols(flat, "e00")["note"]


def test_placebo_is_centred_without_an_effect_and_rejects_with_one():
    rp, events, measures = make_study(effect=0.0, seed=21)
    null = X.placebo(rp, events, measures, "market", n=40, seed=1)
    draws = null["draws"][np.isfinite(null["draws"])]
    assert len(draws) == 40
    assert abs(draws.mean()) < 3 * draws.std(ddof=1) / np.sqrt(len(draws))
    assert null["p_empirical"] > 0.05
    rp2, events2, measures2 = make_study(effect=0.04, seed=21)
    hit = X.placebo(rp2, events2, measures2, "market", n=40, seed=1)
    assert hit["d_true"] == pytest.approx(0.04, abs=0.012)
    assert hit["p_empirical"] == pytest.approx(1 / 41)
    per_firm = X.placebo(rp, events, measures, "market", n=10, seed=1, mode="per_firm")
    assert per_firm["n_draws"] == 10


def test_placebo_days_avoid_real_events():
    rp, events, measures = make_study(effect=0.0)
    days = X.eligible_days(rp, events, exclude=10)
    real = np.array([rp.day0(d) for d in events.date])
    assert np.abs(days[:, None] - real[None, :]).min() > 10
    assert days.min() >= 251 and days.max() + 5 < len(rp.dates)


# ------------------------------------------------------------------ prices

def test_price_download_is_blocked_until_registration(tmp_path):
    missing = tmp_path / "prereg.md"
    with pytest.raises(prices.PreregistrationError):
        prices.registration_commit(missing)
    missing.write_text("# Pre-registration\n\nRegistration commit: pending\n", encoding="utf-8")
    with pytest.raises(prices.PreregistrationError):
        prices.registration_commit(missing)
    with pytest.raises(prices.PreregistrationError):
        prices.download(["BBCA"], prereg=missing, out_root=tmp_path / "prices")
    assert not (tmp_path / "prices").exists()
    missing.write_text("Registration commit: `0123456789abcdef0123456789abcdef01234567`\n", encoding="utf-8")
    with pytest.raises(prices.PreregistrationError):          # hash is not a commit here
        prices.registration_commit(missing)
    head = subprocess.run(["git", "-C", str(prices.ROOT), "rev-parse", "HEAD"],
                          capture_output=True, text=True)
    if head.returncode == 0:
        missing.write_text(f"Registration commit: `{head.stdout.strip()}`\n", encoding="utf-8")
        assert prices.registration_commit(missing) == head.stdout.strip()


def test_load_and_coverage_report(tmp_path):
    cal = synthetic.calendar("2023-01-02", "2023-03-31")
    rng = np.random.default_rng(2)
    panel = panel_from_returns(cal, rng.normal(0, 0.01, len(cal)),
                               {"AAAA": rng.normal(0, 0.02, len(cal))})
    a = panel[panel.ticker == "AAAA"].reset_index(drop=True)
    a.loc[10:12, "volume"] = 0
    a = a.drop(index=[20, 21, 22, 23])                     # a four-day gap
    d = tmp_path / "2026-11-10"
    d.mkdir()
    a.to_parquet(d / "AAAA.parquet", index=False)
    panel[panel.ticker == es.MARKET].to_parquet(d / "IDX_JKSE.parquet", index=False)
    (d / "manifest.json").write_text("{}", encoding="utf-8")
    assert prices.latest_dir(tmp_path) == d
    loaded, cov = prices.load(d)
    assert set(loaded.columns) == set(prices.PANEL_COLUMNS)
    row = cov.set_index("ticker").loc["AAAA"]
    assert row.missing_days == 4 and row.longest_gap_days == 4 and row.zero_volume_days == 3
    rp = es.prepare(loaded)
    assert np.isnan(rp.ret[20:25, 0]).all() and np.isfinite(rp.ret[25, 0])
    assert prices.yahoo_symbol("BBCA") == "BBCA.JK" and prices.yahoo_symbol("^JKSE") == "^JKSE"

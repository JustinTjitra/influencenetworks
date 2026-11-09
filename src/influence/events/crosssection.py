"""Cross-sectional and stacked regressions of CARs on connection (DESIGN.md 6.2), and
the placebo test.

Per event e:      CAR_ie = g_e + d_e * Conn_i(t_e) + X_i'k + sector FE + u_ie
Stacked:          CAR_ie = g_e + d * (Conn_i(t_e) x Sign_e) + X_ie'k + FE + u_ie

`Conn` is the event's pre-registered connection measure (a 0/1 indicator in the main
specification), `Sign_e` is +1 or -1 from `expected_sign_connected`, so d > 0 always
means "connected firms moved in the pre-registered direction".

Two stacked specifications are always reported:

    firm_fe          event FE + firm FE (DESIGN.md 6.2 as written; sector FE and any
                     firm-constant control are absorbed by the firm FE)
    sector_event_fe  event x sector FE, no firm FE (comparison within sector within
                     event)

With firm FE, d is identified only from within-firm variation in Conn x Sign: the
connection must change over time, or the firm must face events of both signs. When
that variation is absent the specification is reported as not identified instead of
returning an arbitrary number.

Estimation is OLS with statsmodels. Per-event standard errors are HC3 (HC1 when a
leverage point makes HC3 undefined). Stacked standard errors are clustered two ways,
by firm and by event, with t inference on min(clusters) - 1 degrees of freedom.
"""

from __future__ import annotations

from typing import Iterable, Optional, Sequence

import numpy as np
import pandas as pd
import statsmodels.api as sm

from . import eventstudy as es
from .eventset import sign_value

TOL = 1e-10
# In order of priority: when the sample cannot carry all of them, the last go first.
PRIMARY_CONTROLS = ("log_mcap", "soe", "leverage", "turnover")
FALLBACK_CONTROLS = ("log_traded_value", "soe", "zero_volume_share")
OBS_PER_COEFFICIENT = 10
SPECS = ("firm_fe", "sector_event_fe")


# ------------------------------------------------------------------ frames

def regression_frame(cars: pd.DataFrame, measures: pd.DataFrame, events: pd.DataFrame,
                     model: str, window: Sequence[int] = es.PRIMARY_WINDOW,
                     controls: Optional[pd.DataFrame] = None, conn: str = "binary") -> pd.DataFrame:
    """One row per usable firm-event for a model and window.

    conn="binary" uses the 0/1 indicator of the tested measure; conn="value" uses the
    measure itself, scaled within each event to unit standard deviation so events
    with different measures can be stacked. Firm-events with no CAR, or with no trade
    on any day of the window, are dropped.
    """
    c = cars[(cars.model == model) & (cars.window == es.window_label(window))]
    m = measures[measures.in_event_sample.astype(bool)]
    keep = ["event_id", "ticker", "sector_bucket", "cluster", "tested_value", "tested_binary",
            "soe", "coverage", "confidence_tier", "tested_tier", "state_own"]
    df = c.merge(m[[k for k in keep if k in m.columns]], on=["event_id", "ticker"], how="inner")
    ev = events[["event_id", "type", "expected_sign_connected", "anticipation_flag",
                 "confounder_flag", "connection_measure_tested"]]
    df = df.merge(ev, on="event_id", how="inner")
    df["sign"] = df.expected_sign_connected.map(sign_value)
    if conn == "binary":
        df["conn"] = df.tested_binary.astype(float)
    else:
        sd = df.groupby("event_id").tested_value.transform(lambda s: s.std(ddof=0))
        df["conn"] = np.where(sd > 0, df.tested_value / sd.where(sd > 0, 1.0), 0.0)
    df["x"] = df.conn * df.sign
    if controls is not None:
        df = df.merge(controls, on=["event_id", "ticker"], how="left", suffixes=("", "_ctl"))
    df = df[df.car.notna() & ~df.no_trade.astype(bool)]
    return df.reset_index(drop=True)


def choose_controls(df: pd.DataFrame, primary: Sequence[str] = PRIMARY_CONTROLS,
                    fallback: Sequence[str] = FALLBACK_CONTROLS,
                    max_missing: float = 0.20) -> tuple[list[str], str]:
    """Apply the pre-registered rule: the primary control set if each control is
    present for at least 80% of firm-events, otherwise the price-based fallback."""
    def missing(cols):
        return max((df[c].isna().mean() if c in df.columns else 1.0) for c in cols)
    if missing(primary) <= max_missing:
        return list(primary), "primary controls"
    if missing(fallback) <= max_missing:
        return list(fallback), "fallback controls (fundamentals missing for more than 20% of firm-events)"
    return [c for c in ("soe",) if c in df.columns], "soe only (no usable controls)"


def identifying_obs(df: pd.DataFrame) -> int:
    """Firm-events in event x sector cells where the connection varies: the only
    observations that can move the estimate once comparisons are within sector."""
    varies = df.groupby(["event_id", "sector_bucket"]).conn.transform("nunique") > 1
    return int(varies.sum())


def limit_controls(df: pd.DataFrame, controls: Sequence[str],
                   per_coef: int = OBS_PER_COEFFICIENT) -> list[str]:
    """Keep as many controls, in priority order, as the sample can carry: at least
    `per_coef` identifying firm-events for the connection coefficient and for each
    control. With 24 identifying firm-events that is one control."""
    k = max(0, identifying_obs(df) // per_coef - 1)
    return list(controls)[:k]


# ------------------------------------------------------------------ linear algebra

def _dummies(*keys: pd.Series) -> np.ndarray:
    codes = pd.factorize(pd.Series(list(zip(*[k.astype(str) for k in keys]))))[0]
    out = np.zeros((len(codes), codes.max() + 1))
    out[np.arange(len(codes)), codes] = 1.0
    return out


def _fe_matrix(df: pd.DataFrame, spec: str) -> np.ndarray:
    if spec == "firm_fe":
        return np.column_stack([_dummies(df.event_id), _dummies(df.ticker)[:, 1:]])
    if spec == "sector_event_fe":
        return _dummies(df.event_id, df.sector_bucket)
    if spec == "event_fe":
        return _dummies(df.event_id)
    raise ValueError(f"unknown spec {spec!r}")


def _resid(v: np.ndarray, z: np.ndarray) -> np.ndarray:
    if z.shape[1] == 0:
        return v
    return v - z @ np.linalg.lstsq(z, v, rcond=None)[0]


def _independent_columns(z: np.ndarray) -> np.ndarray:
    """Greedy full-column-rank subset of z (keeps the earliest columns)."""
    keep, basis = [], np.zeros((z.shape[0], 0))
    for k in range(z.shape[1]):
        r = _resid(z[:, k], basis)
        if r @ r > TOL * max(z[:, k] @ z[:, k], 1.0):
            keep.append(k)
            basis = np.column_stack([basis, z[:, k]])
    return z[:, keep]


def _usable_controls(df: pd.DataFrame, controls: Iterable[str], fe: np.ndarray,
                     x: Optional[np.ndarray] = None) -> tuple[list[str], list[str]]:
    """Controls that still vary after the fixed effects, the connection variable and
    the controls before them. A control that is collinear with the connection (the
    SOE dummy in an event whose measure is state ownership) is dropped, not the
    connection."""
    kept, dropped = [], []
    z = fe if x is None else np.column_stack([fe, x])
    for c in controls:
        v = df[c].to_numpy(float)
        r = _resid(v, z)
        if r @ r > TOL * max(v @ v, 1.0):
            kept.append(c)
            z = np.column_stack([z, v])
        else:
            dropped.append(c)
    return kept, dropped


def fe_point_estimate(df: pd.DataFrame, spec: str, controls: Sequence[str] = (),
                      xcol: str = "x") -> float:
    """Coefficient on xcol after partialling out the fixed effects and controls;
    NaN when it is not identified. Fast path used by the placebo."""
    fe = _fe_matrix(df, spec)
    x = df[xcol].to_numpy(float)
    kept, _ = _usable_controls(df, controls, fe, x)
    z = np.column_stack([fe, df[kept].to_numpy(float)]) if kept else fe
    xr = _resid(x, z)
    if xr @ xr <= TOL * max(x @ x, 1.0):
        return float("nan")
    return float(xr @ _resid(df.car.to_numpy(float), z) / (xr @ xr))


# ------------------------------------------------------------------ estimators

def per_event_ols(df: pd.DataFrame, event_id: str, controls: Sequence[str] = ()) -> dict:
    """d_e for one event, with sector FE where the sample spans more than one sector."""
    s = df[df.event_id == event_id].dropna(subset=["car", "conn", *controls])
    out = dict(event_id=event_id, n=len(s), n_treated=int((s.conn > 0).sum()) if len(s) else 0,
               d=np.nan, se=np.nan, t=np.nan, p=np.nan, ci_low=np.nan, ci_high=np.nan,
               controls="", note="")
    if len(s) < 4 or s.conn.nunique() < 2:
        out["note"] = "no variation in the connection measure" if len(s) else "no firm-events"
        return out
    fe = _dummies(s.sector_bucket) if s.sector_bucket.nunique() > 1 else np.ones((len(s), 1))
    x = s.conn.to_numpy(float)
    kept, _ = _usable_controls(s, controls, fe, x)
    while kept and len(s) - (1 + len(kept) + fe.shape[1]) < 3:
        kept = kept[:-1]                               # too few firms for every control
    z = np.column_stack([fe, s[kept].to_numpy(float)]) if kept else fe
    xr = _resid(x, z)
    if xr @ xr <= TOL * max(x @ x, 1.0) or len(s) - (z.shape[1] + 1) < 2:
        out["note"] = "connection is collinear with sector or controls"
        return out
    design = np.column_stack([x, z])
    fit = sm.OLS(s.car.to_numpy(float), design).fit(cov_type="HC3")
    if not np.isfinite(fit.bse[0]):
        fit = sm.OLS(s.car.to_numpy(float), design).fit(cov_type="HC1")
        out["note"] = "HC1 standard error (HC3 undefined)"
    lo, hi = fit.conf_int()[0]
    out.update(d=float(fit.params[0]), se=float(fit.bse[0]), t=float(fit.tvalues[0]),
               p=float(fit.pvalues[0]), ci_low=float(lo), ci_high=float(hi),
               controls=" ".join(kept))
    return out


def stacked(df: pd.DataFrame, spec: str = "firm_fe", controls: Sequence[str] = (),
            xcol: str = "x") -> dict:
    """The stacked estimate d with two-way clustered standard errors."""
    df = df.dropna(subset=["car", xcol, *controls]).reset_index(drop=True)
    out = dict(spec=spec, n=len(df), n_firms=df.ticker.nunique(), n_events=df.event_id.nunique(),
               n_treated=int((df.conn > 0).sum()) if "conn" in df else np.nan,
               identified=False, d=np.nan, se=np.nan, t=np.nan, p=np.nan,
               ci_low=np.nan, ci_high=np.nan, controls="", dropped_controls="", note="")
    if len(df) < 5:
        out["note"] = "too few firm-events"
        return out
    fe = _independent_columns(_fe_matrix(df, spec))
    x = df[xcol].to_numpy(float)
    kept, dropped = _usable_controls(df, controls, fe, x)
    z = np.column_stack([fe, df[kept].to_numpy(float)]) if kept else fe
    xr = _resid(x, z)
    out.update(controls=" ".join(kept), dropped_controls=" ".join(dropped))
    if xr @ xr <= TOL * max(x @ x, 1.0) or len(df) <= z.shape[1] + 1:
        out["note"] = ("not identified: connection x sign does not vary within "
                       + ("firm" if spec == "firm_fe" else "event-sector cell"))
        return out
    # Frisch-Waugh: partial the fixed effects and controls out of both sides, then
    # regress residual on residual. Only the coefficient of interest gets a variance,
    # and absorbed fixed effects do not enter the small-sample factor (the reghdfe
    # convention for fixed effects nested in the clusters).
    yr = _resid(df.car.to_numpy(float), z)
    firm, event = pd.factorize(df.ticker)[0], pd.factorize(df.event_id)[0]
    if min(firm.max(), event.max()) < 1:
        fit = sm.OLS(yr, xr).fit(cov_type="HC1")
        out["note"] = "one cluster on a dimension: HC1 standard error"
    else:
        fit = sm.OLS(yr, xr).fit(cov_type="cluster", use_t=True,
                                 cov_kwds={"groups": np.column_stack([firm, event])})
        with np.errstate(invalid="ignore"):
            two_way_ok = bool(np.isfinite(fit.bse[0]) and fit.bse[0] > 0)
        if not two_way_ok:
            # the two-way variance (firm + event - intersection) can come out negative
            one_way = [sm.OLS(yr, xr).fit(cov_type="cluster", use_t=True, cov_kwds={"groups": g})
                       for g in (firm, event)]
            fit = max(one_way, key=lambda f: f.bse[0])
            out["note"] = "two-way variance not positive: larger one-way clustered standard error"
    lo, hi = fit.conf_int()[0]
    out.update(identified=True, d=float(fit.params[0]), se=float(fit.bse[0]),
               t=float(fit.tvalues[0]), p=float(fit.pvalues[0]),
               ci_low=float(lo), ci_high=float(hi))
    return out


# ------------------------------------------------------------------ placebo

def eligible_days(rp: es.ReturnPanel, events: pd.DataFrame, exclude: int = 10,
                  windows: Sequence[Sequence[int]] = es.WINDOWS) -> np.ndarray:
    """Trading-day indices usable as pseudo-events: enough history for the estimation
    window, room for the longest event window, and more than `exclude` trading days
    away from every real event."""
    hi = max(w[1] for w in windows)
    idx = np.arange(1 - es.EST_START, len(rp.dates) - hi - 1)
    real = [rp.day0(d, a) for d, a in zip(events.date, events.after_close)]
    real = np.array([r for r in real if r is not None])
    if len(real):
        idx = idx[np.abs(idx[:, None] - real[None, :]).min(axis=1) > exclude]
    return idx


def placebo(rp: es.ReturnPanel, events: pd.DataFrame, measures: pd.DataFrame, model: str,
            window: Sequence[int] = es.PRIMARY_WINDOW, spec: str = "sector_event_fe",
            controls_frame: Optional[pd.DataFrame] = None, controls: Sequence[str] = (),
            conn: str = "binary", n: int = 200, seed: int = 20261109,
            mode: str = "common_date", all_events: Optional[pd.DataFrame] = None) -> dict:
    """Re-run the stacked estimate on pseudo-event dates.

    mode="common_date": in each of the n draws every event is moved to one random
    non-event trading day shared by all firms. This keeps the same-day correlation
    of returns across firms, which is the main threat to inference when all firms
    share an event date. mode="per_firm" draws a separate day for every firm-event;
    it breaks that correlation and so gives a narrower, optimistic null.

    The connection measures, signs, sample and controls stay as at the real events;
    only the return dates change. Returns the real estimate, the draws and the
    empirical two-sided p-value (1 + #{|d_b| >= |d|}) / (B + 1).
    """
    if mode not in ("common_date", "per_firm"):
        raise ValueError(mode)
    rng = np.random.default_rng(seed)
    days = eligible_days(rp, events if all_events is None else all_events)
    if len(days) < len(events):
        raise ValueError("not enough non-event trading days for the placebo")
    real = es.event_cars(rp, events, models=(model,), windows=(window,))
    base = regression_frame(real, measures, events, model, window, controls_frame, conn)
    d_true = fe_point_estimate(base, spec, controls)
    skeleton = base.drop(columns=["car", "no_trade"])
    draws = np.full(n, np.nan)
    for b in range(n):
        if mode == "common_date":
            pick = dict(zip(events.event_id, rng.choice(days, size=len(events), replace=False)))
            i0 = skeleton.event_id.map(pick).to_numpy()
        else:
            i0 = rng.choice(days, size=len(skeleton), replace=True)
        cars_b, notrade = np.full(len(skeleton), np.nan), np.zeros(len(skeleton), bool)
        for r, (t, i) in enumerate(zip(skeleton.ticker, i0)):
            row = es.firm_event_cars(rp, rp.col[t], int(i), (model,), (window,))[0]
            cars_b[r], notrade[r] = row["car"], row["no_trade"]
        frame = skeleton.assign(car=cars_b)[np.isfinite(cars_b) & ~notrade]
        if len(frame) > 5:
            draws[b] = fe_point_estimate(frame, spec, controls)
    ok = draws[np.isfinite(draws)]
    p = (1 + int((np.abs(ok) >= abs(d_true)).sum())) / (len(ok) + 1) if np.isfinite(d_true) and len(ok) else np.nan
    return dict(model=model, window=es.window_label(window), spec=spec, mode=mode, n_draws=len(ok),
                d_true=d_true, placebo_mean=float(ok.mean()) if len(ok) else np.nan,
                placebo_sd=float(ok.std(ddof=1)) if len(ok) > 1 else np.nan,
                p_empirical=p, draws=draws)

"""Abnormal returns and volume around events (DESIGN.md 6.1).

Returns are simple daily returns on adjusted close. All day counting is in trading
days on the exchange calendar, which is the set of dates on which the market index
(^JKSE) has a price. Day 0 of an event is the first trading day on or after the
event date, or the first trading day strictly after it for news that came after the
close.

Three models of the normal return, estimated on trading days [-250, -30]:

    market           R_it = a_i + b_i R_mt + e_it
    market_adjusted  a_i = 0, b_i = 1 (nothing estimated)
    dimson           R_it = a_i + b1 R_m,t-1 + b2 R_mt + b3 R_m,t+1 + e_it and the
                     abnormal return uses the summed beta: AR_it = R_it - a_i - (b1+b2+b3) R_mt

A firm-event is used only if the estimation window has at least `min_valid` days on
which the stock has a return and traded (volume > 0). Days with a return but no
trade stay in the regression (dropping them would misalign multi-day returns); they
are what the Dimson betas are there to correct for.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Union

import numpy as np
import pandas as pd

MARKET = "^JKSE"
MODELS = ("market", "market_adjusted", "dimson")
EST_START, EST_END = -250, -30
MIN_VALID = 120
WINDOWS = ((-1, 1), (0, 2), (0, 5), (-5, -2))
PRIMARY_WINDOW = (-1, 1)
LEAKAGE_WINDOW = (-5, -2)
VOL_BASE = (-60, -11)


def window_label(w: Sequence[int]) -> str:
    return f"[{w[0]:+d},{w[1]:+d}]".replace("+0", "0")


@dataclass
class ReturnPanel:
    """Prices reshaped for event-time arithmetic. Build with `prepare`."""
    dates: np.ndarray            # datetime64[D], sorted: the exchange calendar
    tickers: list[str]
    ret: np.ndarray              # (T, N) simple returns, NaN where unavailable
    vol: np.ndarray              # (T, N) volume, NaN where unavailable
    close: np.ndarray            # (T, N) unadjusted close, NaN where unavailable
    mkt: np.ndarray              # (T,) market return
    off_calendar_rows: int = 0

    def __post_init__(self):
        self.col = {t: j for j, t in enumerate(self.tickers)}

    def day0(self, event_date, after_close: Union[bool, int] = False) -> Optional[int]:
        """Row index of day 0, or None if the event is past the end of the calendar."""
        d = np.datetime64(pd.Timestamp(event_date).date(), "D")
        i = int(np.searchsorted(self.dates, d, side="right" if after_close else "left"))
        return i if i < len(self.dates) else None

    def trading_days_between(self, a, b) -> int:
        """Signed number of trading days from day 0 of a to day 0 of b."""
        return self.day0(b) - self.day0(a)


def prepare(panel: pd.DataFrame, market: str = MARKET) -> ReturnPanel:
    """Tidy (date, ticker, adj_close, volume[, close]) -> ReturnPanel."""
    if market not in set(panel.ticker):
        raise ValueError(f"the panel has no market series {market!r}")
    df = panel.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    cal = pd.DatetimeIndex(sorted(df.loc[df.ticker == market, "date"].unique()))
    off = int((~df["date"].isin(cal)).sum())
    px = df.pivot(index="date", columns="ticker", values="adj_close").reindex(cal)
    ret = px.pct_change(fill_method=None)
    tickers = [t for t in px.columns if t != market]
    vol = (df.pivot(index="date", columns="ticker", values="volume").reindex(cal)
           if "volume" in df else pd.DataFrame(np.nan, index=cal, columns=px.columns))
    raw = (df.pivot(index="date", columns="ticker", values="close").reindex(cal)
           if "close" in df else px)
    return ReturnPanel(
        dates=cal.values.astype("datetime64[D]"), tickers=tickers,
        ret=ret[tickers].to_numpy(float), vol=vol.reindex(columns=tickers).to_numpy(float),
        close=raw.reindex(columns=tickers).to_numpy(float),
        mkt=ret[market].to_numpy(float), off_calendar_rows=off)


def _as_panel(panel) -> ReturnPanel:
    return panel if isinstance(panel, ReturnPanel) else prepare(panel)


@dataclass
class Estimate:
    model: str
    ok: bool
    alpha: float = float("nan")
    beta: float = float("nan")          # summed beta for dimson; 1 for market_adjusted
    betas: tuple = ()
    sigma: float = float("nan")         # sd of estimation-window abnormal returns
    n_obs: int = 0                      # days in the regression
    n_valid: int = 0                    # of those, days with a trade
    r2: float = float("nan")


def _fit(rp: ReturnPanel, j: int, i0: int, model: str, min_valid: int = MIN_VALID) -> Estimate:
    a, b = i0 + EST_START, i0 + EST_END
    if a < 1 or b + 1 >= len(rp.dates):
        return Estimate(model, False)
    sl = slice(a, b + 1)
    y, m = rp.ret[sl, j], rp.mkt[sl]
    mask = np.isfinite(y) & np.isfinite(m)
    if model == "dimson":
        lag, lead = rp.mkt[a - 1:b], rp.mkt[a + 1:b + 2]
        mask &= np.isfinite(lag) & np.isfinite(lead)
    v = rp.vol[sl, j]
    n_obs = int(mask.sum())
    n_valid = int((mask & ~(v == 0)).sum())          # unknown volume counts as traded
    if n_valid < min_valid or n_obs < 10:
        return Estimate(model, False, n_obs=n_obs, n_valid=n_valid)
    y, m = y[mask], m[mask]
    if model == "market_adjusted":
        ar = y - m
        return Estimate(model, True, 0.0, 1.0, (), float(ar.std(ddof=1)), n_obs, n_valid)
    if model == "market":
        x = np.column_stack([np.ones(n_obs), m])
    elif model == "dimson":
        x = np.column_stack([np.ones(n_obs), lag[mask], m, lead[mask]])
    else:
        raise ValueError(f"unknown model {model!r}")
    coef, *_ = np.linalg.lstsq(x, y, rcond=None)
    alpha, betas = float(coef[0]), tuple(float(c) for c in coef[1:])
    beta = float(sum(betas))
    ar = y - alpha - beta * m
    fitted_resid = y - x @ coef
    tss = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - float((fitted_resid ** 2).sum()) / tss if tss > 0 else float("nan")
    return Estimate(model, True, alpha, beta, betas, float(ar.std(ddof=len(coef))),
                    n_obs, n_valid, r2)


def estimate(panel, ticker: str, event_date, model: str = "market", after_close=False,
             min_valid: int = MIN_VALID) -> Estimate:
    """Normal-return parameters for one firm-event."""
    rp = _as_panel(panel)
    i0 = rp.day0(event_date, after_close)
    if i0 is None:
        return Estimate(model, False)
    return _fit(rp, rp.col[ticker], i0, model, min_valid)


def _ar_block(rp: ReturnPanel, j: int, i0: int, est: Estimate, lo: int, hi: int) -> np.ndarray:
    """Abnormal returns for relative days lo..hi (NaN outside the calendar)."""
    out = np.full(hi - lo + 1, np.nan)
    if not est.ok:
        return out
    idx = np.arange(i0 + lo, i0 + hi + 1)
    ok = (idx >= 0) & (idx < len(rp.dates))
    out[ok] = rp.ret[idx[ok], j] - est.alpha - est.beta * rp.mkt[idx[ok]]
    return out


def abnormal_returns(panel, ticker: str, event_date, model: str = "market", after_close=False,
                     span: Sequence[int] = (-5, 5), min_valid: int = MIN_VALID) -> pd.Series:
    """Abnormal returns indexed by relative trading day."""
    rp = _as_panel(panel)
    i0 = rp.day0(event_date, after_close)
    rel = np.arange(span[0], span[1] + 1)
    if i0 is None:
        return pd.Series(np.nan, index=rel, name="ar")
    est = _fit(rp, rp.col[ticker], i0, model, min_valid)
    return pd.Series(_ar_block(rp, rp.col[ticker], i0, est, span[0], span[1]), index=rel, name="ar")


def car(panel, ticker: str, event_date, window: Sequence[int] = PRIMARY_WINDOW,
        model: str = "market", after_close=False, min_valid: int = MIN_VALID) -> float:
    """Cumulative abnormal return over a window; NaN if any day in it is missing."""
    ar = abnormal_returns(panel, ticker, event_date, model, after_close, window, min_valid)
    return float(ar.sum()) if ar.notna().all() else float("nan")


def _avol(rp: ReturnPanel, j: int, i0: int, window: Sequence[int]) -> float:
    a, b = i0 + VOL_BASE[0], i0 + VOL_BASE[1]
    if a < 0 or i0 + window[1] >= len(rp.dates):
        return float("nan")
    base = np.nanmean(rp.vol[a:b + 1, j]) if np.isfinite(rp.vol[a:b + 1, j]).any() else np.nan
    v = rp.vol[i0 + window[0]:i0 + window[1] + 1, j]
    v = v[np.isfinite(v) & (v > 0)]
    if not np.isfinite(base) or base <= 0 or len(v) == 0:
        return float("nan")
    return float(np.mean(np.log(v / base)))


def abnormal_volume(panel, ticker: str, event_date, window: Sequence[int] = PRIMARY_WINDOW,
                    after_close=False) -> float:
    """Mean over the window of log(V_t / mean V[-60,-11]); days with no trade are skipped."""
    rp = _as_panel(panel)
    i0 = rp.day0(event_date, after_close)
    return float("nan") if i0 is None else _avol(rp, rp.col[ticker], i0, window)


def firm_event_cars(rp: ReturnPanel, j: int, i0: int, models: Iterable[str] = MODELS,
                    windows: Iterable[Sequence[int]] = WINDOWS,
                    min_valid: int = MIN_VALID) -> list[dict]:
    """All model x window CARs for one firm at one day-0 index."""
    windows = list(windows)
    lo, hi = min(w[0] for w in windows), max(w[1] for w in windows)
    rows = []
    for model in models:
        est = _fit(rp, j, i0, model, min_valid)
        ar = _ar_block(rp, j, i0, est, lo, hi)
        for w in windows:
            seg = ar[w[0] - lo:w[1] - lo + 1]
            n = len(seg)
            ok = est.ok and np.isfinite(seg).all()
            idx = np.arange(i0 + w[0], i0 + w[1] + 1)
            inside = idx[(idx >= 0) & (idx < len(rp.dates))]
            zero = int((rp.vol[inside, j] == 0).sum())
            c = float(seg.sum()) if ok else float("nan")
            rows.append(dict(
                model=model, window=window_label(w), car=c,
                car_t=c / (est.sigma * np.sqrt(n)) if ok and est.sigma > 0 else float("nan"),
                alpha=est.alpha, beta=est.beta, sigma=est.sigma, n_obs=est.n_obs,
                n_valid=est.n_valid, est_ok=est.ok, zero_volume_days=zero,
                no_trade=bool(len(inside) and zero == len(inside)),
                avol=_avol(rp, j, i0, w)))
    return rows


def event_cars(panel, events: pd.DataFrame, tickers: Optional[Iterable[str]] = None,
               models: Iterable[str] = MODELS, windows: Iterable[Sequence[int]] = WINDOWS,
               min_valid: int = MIN_VALID, day0_override: Optional[dict] = None) -> pd.DataFrame:
    """Long table of CARs: one row per (event, ticker, model, window).

    `events` needs event_id, date and after_close. `day0_override` maps event_id to a
    row index (used by the placebo). Firm-events that fail the estimation rule are
    kept with car = NaN and est_ok = False so that drops can be counted.
    """
    rp = _as_panel(panel)
    tickers = [t for t in (tickers or rp.tickers) if t in rp.col]
    out = []
    for ev in events.itertuples(index=False):
        i0 = (day0_override or {}).get(ev.event_id)
        if i0 is None:
            i0 = rp.day0(ev.date, getattr(ev, "after_close", 0))
        if i0 is None:
            continue
        for t in tickers:
            for row in firm_event_cars(rp, rp.col[t], i0, models, windows, min_valid):
                out.append(dict(event_id=ev.event_id, ticker=t,
                                day0=pd.Timestamp(rp.dates[i0]).date(), **row))
    return pd.DataFrame(out)

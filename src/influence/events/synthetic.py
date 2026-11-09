"""Synthetic price panels for testing the engine. Nothing here is market data.

`make_panel` simulates a market index and firm prices from a one-factor model on a
weekday calendar with invented holidays. Options add thin trading (days with no
trade and a stale price) and plant a known effect on event days, so the tests can
check that the pipeline recovers it and that the placebo is centred when nothing is
planted.
"""

from __future__ import annotations

from typing import Iterable, Optional

import numpy as np
import pandas as pd

MARKET = "^JKSE"
# Invented fixed holidays (month, day) plus one closed week a year.
_HOLIDAYS = {(1, 1), (5, 1), (8, 17), (12, 25), (12, 26)}
_CLOSED_WEEK = (4, 8, 12)        # month, first day, last day


def calendar(start: str, end: str) -> pd.DatetimeIndex:
    days = pd.bdate_range(start, end)
    m, a, b = _CLOSED_WEEK
    keep = [d for d in days if (d.month, d.day) not in _HOLIDAYS
            and not (d.month == m and a <= d.day <= b)]
    return pd.DatetimeIndex(keep)


def make_panel(tickers: Iterable[str], start: str = "2018-06-01", end: str = "2026-11-06",
               seed: int = 0, listing: Optional[dict] = None, thin: Iterable[str] = (),
               thin_share: float = 0.35, events: Optional[pd.DataFrame] = None,
               measures: Optional[pd.DataFrame] = None, effect: float = 0.0,
               betas: Optional[dict] = None, alphas: Optional[dict] = None,
               idio_sd: Optional[dict] = None, market_sd: float = 0.011) -> pd.DataFrame:
    """Tidy panel (date, ticker, close, adj_close, volume) including the market.

    effect: abnormal return added on day 0 of each signed event to firms whose
    tested_binary is 1, times the event's sign. `events` needs event_id, date,
    after_close, expected_sign_connected; `measures` needs event_id, ticker,
    tested_binary, in_event_sample.
    """
    rng = np.random.default_rng(seed)
    tickers = list(tickers)
    cal = calendar(start, end)
    T = len(cal)
    rm = rng.normal(0.0003, market_sd, T)
    shock = pd.DataFrame(0.0, index=cal, columns=tickers)
    if events is not None and measures is not None and effect:
        sign = {"+": 1.0, "-": -1.0}
        for ev in events.itertuples(index=False):
            s = sign.get(ev.expected_sign_connected)
            if s is None:
                continue
            i = cal.searchsorted(pd.Timestamp(ev.date), side="right" if ev.after_close else "left")
            if i >= T:
                continue
            m = measures[(measures.event_id == ev.event_id) & measures.in_event_sample.astype(bool)
                         & (measures.tested_binary == 1)]
            for t in m.ticker:
                if t in shock.columns:
                    shock.iloc[i, shock.columns.get_loc(t)] += effect * s
    frames = [pd.DataFrame(dict(date=cal, ticker=MARKET, close=6000 * np.cumprod(1 + rm),
                                adj_close=6000 * np.cumprod(1 + rm), volume=1e9))]
    thin = set(thin)
    for t in tickers:
        beta = (betas or {}).get(t, rng.uniform(0.6, 1.4))
        alpha = (alphas or {}).get(t, rng.normal(0.0, 0.0002))
        sd = (idio_sd or {}).get(t, rng.uniform(0.012, 0.028))
        r = alpha + beta * rm + rng.normal(0.0, sd, T) + shock[t].to_numpy()
        latent = rng.uniform(200, 5000) * np.cumprod(1 + r)
        volume = np.round(rng.lognormal(15, 0.8, T))
        if t in thin:
            idle = rng.random(T) < thin_share
            idle[0] = False
            volume[idle] = 0
            last = np.maximum.accumulate(np.where(~idle, np.arange(T), 0))
            price = latent[last]                 # stale price on days with no trade
        else:
            price = latent
        df = pd.DataFrame(dict(date=cal, ticker=t, close=price, adj_close=price, volume=volume))
        first = (listing or {}).get(t)
        if first is not None and pd.notna(first):
            df = df[df.date >= pd.Timestamp(first)]
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def make_fundamentals(tickers: Iterable[str], years: Iterable[int] = range(2017, 2027),
                      seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 1)
    rows = []
    for t in tickers:
        shares = float(np.round(rng.uniform(1e9, 5e10)))
        assets = rng.uniform(5e12, 2e15)
        lev = rng.uniform(0.3, 0.9)
        for y in years:
            assets *= rng.uniform(0.98, 1.12)
            rows.append(dict(ticker=t, fiscal_year_end=pd.Timestamp(y, 12, 31),
                             shares_outstanding=shares, total_assets=assets,
                             total_liabilities=assets * lev, source_url="synthetic"))
    return pd.DataFrame(rows)

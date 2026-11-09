"""Firm-event control variables (DESIGN.md 6.2).

Primary set, as pre-registered:
    log_mcap   log(close x shares outstanding) on trading day -30
    leverage   total liabilities / total assets at the latest fiscal year-end that is
               at least 90 days before the event (so the figure was public)
    turnover   mean daily volume / shares outstanding over days [-250, -30]
    soe        1 if state_own >= 0.5 on the snapshot date

Shares, assets and liabilities come from data/mappings/fundamentals.csv, which is
collected after registration from annual reports (columns: ticker, fiscal_year_end,
shares_outstanding, total_assets, total_liabilities, source_url). It holds no prices.

Fallback set, used only under the rule in crosssection.choose_controls, needs prices
alone:
    log_traded_value    log of mean daily close x volume over [-250, -30]
    zero_volume_share   share of days in [-250, -30] with no trade
    soe
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from . import eventstudy as es

ROOT = Path(__file__).resolve().parents[3]
FUNDAMENTALS_PATH = ROOT / "data" / "mappings" / "fundamentals.csv"
PUBLICATION_LAG_DAYS = 90
FUND_COLUMNS = ["ticker", "fiscal_year_end", "shares_outstanding", "total_assets",
                "total_liabilities", "source_url"]


def load_fundamentals(path: Path = FUNDAMENTALS_PATH) -> pd.DataFrame:
    if not Path(path).exists():
        return pd.DataFrame(columns=FUND_COLUMNS)
    df = pd.read_csv(path)
    df["fiscal_year_end"] = pd.to_datetime(df["fiscal_year_end"])
    return df


def build_controls(rp: es.ReturnPanel, events: pd.DataFrame, measures: pd.DataFrame,
                   fundamentals: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    fund = load_fundamentals() if fundamentals is None else fundamentals.copy()
    if len(fund):
        fund["fiscal_year_end"] = pd.to_datetime(fund["fiscal_year_end"])
    by_ticker = {t: g.sort_values("fiscal_year_end") for t, g in fund.groupby("ticker")}
    soe = measures.set_index(["event_id", "ticker"]).soe
    rows = []
    for ev in events.itertuples(index=False):
        i0 = rp.day0(ev.date, ev.after_close)
        if i0 is None or i0 + es.EST_START < 0:
            continue
        a, b = i0 + es.EST_START, i0 + es.EST_END
        cutoff = pd.Timestamp(rp.dates[i0]) - pd.Timedelta(days=PUBLICATION_LAG_DAYS)
        for t in measures.loc[measures.event_id == ev.event_id, "ticker"]:
            if t not in rp.col:
                continue
            j = rp.col[t]
            close, vol = rp.close[a:b + 1, j], rp.vol[a:b + 1, j]
            traded = close * vol
            have = np.isfinite(vol)
            row = dict(event_id=ev.event_id, ticker=t,
                       soe=float(soe.get((ev.event_id, t), np.nan)),
                       log_traded_value=_safe_log(np.nanmean(traded)) if np.isfinite(traded).any() else np.nan,
                       zero_volume_share=float((vol[have] == 0).mean()) if have.any() else np.nan,
                       log_mcap=np.nan, leverage=np.nan, turnover=np.nan)
            f = by_ticker.get(t)
            f = f[f.fiscal_year_end <= cutoff] if f is not None else None
            if f is not None and len(f):
                last = f.iloc[-1]
                px = close[np.isfinite(close)]
                if len(px) and last.shares_outstanding > 0:
                    row["log_mcap"] = _safe_log(px[-1] * last.shares_outstanding)
                    row["turnover"] = (float(np.nanmean(vol)) / last.shares_outstanding
                                       if have.any() else np.nan)
                if last.total_assets > 0:
                    row["leverage"] = float(last.total_liabilities / last.total_assets)
            rows.append(row)
    return pd.DataFrame(rows)


def _safe_log(x: float) -> float:
    return float(np.log(x)) if np.isfinite(x) and x > 0 else float("nan")

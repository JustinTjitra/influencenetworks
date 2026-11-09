"""What size of effect could the registered main test detect? A simulation on
synthetic prices, run before any real price is seen.

    python -m influence.events.power

It plants a known gap on the main-test events, repeats over many simulated price
histories and reports the spread of the stacked estimate. The simulated firms have
daily idiosyncratic volatility between 1.2% and 2.8% (synthetic.make_panel); real
volatility will differ, so read the output as an order of magnitude.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from ..connections.build_measures import summarise
from . import controls as C
from . import crosssection as X
from . import eventset, synthetic
from . import eventstudy as es

ROOT = Path(__file__).resolve().parents[3]


def simulate(n: int = 200, effect: float = 0.02, seed: int = 0) -> pd.DataFrame:
    events = eventset.load_events()
    tickers = eventset.load_tickers()
    measures = pd.read_parquet(ROOT / "data" / "processed" / "connection_measures.parquet")
    summary = summarise(measures, events)
    main = events[events.event_id.isin(summary.loc[summary.main_test == 1, "event_id"])]
    if main.empty:
        raise SystemExit("no event passes the main-test rules")
    rows = []
    for b in range(n):
        panel = synthetic.make_panel(tickers.ticker, seed=seed + b, events=events, measures=measures,
                                     effect=effect, listing=dict(zip(tickers.ticker, tickers.listing_date)))
        rp = es.prepare(panel)
        cars = es.event_cars(rp, main, models=("market",), windows=(es.PRIMARY_WINDOW,))
        ctl = C.build_controls(rp, main, measures, synthetic.make_fundamentals(tickers.ticker, seed=seed + b))
        df = X.regression_frame(cars, measures, main, "market", controls=ctl)
        used = X.limit_controls(df, X.PRIMARY_CONTROLS)
        fit = X.stacked(df, "sector_event_fe", used)
        rows.append(dict(draw=b, d=fit["d"], se=fit["se"], p=fit["p"], n=fit["n"],
                         n_treated=fit["n_treated"], controls=" ".join(used)))
    return pd.DataFrame(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--draws", type=int, default=200)
    ap.add_argument("--effect", type=float, default=0.02)
    args = ap.parse_args(argv)
    null = simulate(args.draws, 0.0)
    alt = simulate(args.draws, args.effect)
    sd = null.d.std(ddof=1)
    print(f"main-test events: firm-events {int(null.n.iloc[0])}, treated {int(null.n_treated.iloc[0])}, "
          f"controls kept: {null.controls.iloc[0] or 'none'}")
    print(f"no effect planted:  mean d {null.d.mean() * 100:+.2f} pp, sd {sd * 100:.2f} pp, "
          f"share with clustered p < 0.05: {(null.p < 0.05).mean():.0%}")
    print(f"{args.effect * 100:.1f} pp planted:     mean d {alt.d.mean() * 100:+.2f} pp, sd {alt.d.std(ddof=1) * 100:.2f} pp, "
          f"share with clustered p < 0.05: {(alt.p < 0.05).mean():.0%}")
    big = simulate(args.draws, 4 * args.effect)
    print(f"{4 * args.effect * 100:.1f} pp planted:     share with clustered p < 0.05: {(big.p < 0.05).mean():.0%}")
    print(f"smallest gap detectable with 80% power at the 5% level, given that spread: "
          f"about {2.8 * sd * 100:.1f} pp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

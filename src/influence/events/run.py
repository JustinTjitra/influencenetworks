"""One command from prices + events.csv + connection_measures.parquet to results.

    python -m influence.events.run                      # real prices (latest download)
    python -m influence.events.run --synthetic          # simulated prices, engine check

Real runs refuse to start until the pre-registration records its commit (see
prices.registration_commit). Outputs go to data/processed/results/ (real) or
data/processed/results_synthetic/ (simulated): tables as CSV, figures as PNG and SVG,
and results_summary.md, which applies the decision rules of docs/paper/prereg.md
mechanically. Nothing in the summary is written by hand.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from ..connections.build_measures import summarise
from . import controls as C
from . import crosssection as X
from . import eventset
from . import eventstudy as es
from . import plots, prices, synthetic

ROOT = Path(__file__).resolve().parents[3]
PROC = ROOT / "data" / "processed"
ALPHA = 0.05
PLACEBO_DRAWS = 200
PLACEBO_SEED = 20261109
PEOPLE_MEASURES = ("board_party", "board_office", "board_family", "group_conn")
PRIMARY_SPEC = "sector_event_fe"      # prereg.md section 7; firm_fe is reported beside it


def event_groups(events: pd.DataFrame, summary: pd.DataFrame) -> dict[str, list[str]]:
    """Named sets of events. The first block is the pre-registered main test."""
    s = summary.set_index("event_id")
    ev = events.set_index("event_id")
    main = [e for e in ev.index if s.loc[e, "main_test"] == 1]
    signed = [e for e in ev.index if ev.loc[e, "expected_sign_connected"] in ("+", "-")]
    groups = {"main: all": main}
    for t in sorted(set(ev.loc[main, "type"])) if main else []:
        groups[f"main: {t}"] = [e for e in main if ev.loc[e, "type"] == t]
    groups["main: ownership ties (H2)"] = [e for e in main if ev.loc[e, "connection_measure_tested"] == "state_own"]
    groups["main: people ties (H2)"] = [e for e in main if ev.loc[e, "connection_measure_tested"] in PEOPLE_MEASURES]
    groups["robustness: anticipated"] = [e for e in signed if ev.loc[e, "anticipation_flag"] == 1]
    groups["robustness: confounded"] = [e for e in signed if ev.loc[e, "confounder_flag"] == 1]
    groups["robustness: too few clusters"] = [e for e in signed if s.loc[e, "enough_clusters"] == 0]
    groups["robustness: all signed events"] = signed
    return {k: v for k, v in groups.items() if v}


def _subset(df: pd.DataFrame, ids: list[str]) -> pd.DataFrame:
    return df[df.event_id.isin(ids)].reset_index(drop=True)


def run(rp: es.ReturnPanel, events: pd.DataFrame, measures: pd.DataFrame, out: Path,
        fundamentals: Optional[pd.DataFrame] = None, n_placebo: int = PLACEBO_DRAWS,
        seed: int = PLACEBO_SEED, banner: str = "", price_coverage: Optional[pd.DataFrame] = None
        ) -> dict:
    out = Path(out)
    (out / "figures").mkdir(parents=True, exist_ok=True)
    summary = summarise(measures, events)
    tickers = sorted(set(measures.ticker) & set(rp.tickers))
    missing_prices = sorted(set(measures.ticker) - set(rp.tickers))

    cars = es.event_cars(rp, events, tickers)
    ctl = C.build_controls(rp, events, measures, fundamentals)
    frames = {(m, w, c): X.regression_frame(cars, measures, events, m, w, ctl, c)
              for m in es.MODELS for w in es.WINDOWS for c in ("binary", "value")}
    primary = {m: frames[(m, es.PRIMARY_WINDOW, "binary")] for m in es.MODELS}
    controls, controls_note = X.choose_controls(primary["market"])

    # ---- per event
    pe = []
    for m in es.MODELS:
        for ev in events.itertuples(index=False):
            one = primary[m][primary[m].event_id == ev.event_id]
            row = X.per_event_ols(primary[m], ev.event_id, X.limit_controls(one, controls))
            sgn = eventset.sign_value(ev.expected_sign_connected)
            flip = sgn if np.isfinite(sgn) else 1.0
            lo, hi = sorted([row["ci_low"] * flip, row["ci_high"] * flip]) if np.isfinite(row["d"]) else (np.nan, np.nan)
            pe.append(dict(model=m, date=ev.date.date(), type=ev.type,
                           expected_sign=ev.expected_sign_connected,
                           measure=ev.connection_measure_tested, **row,
                           d_signed=row["d"] * flip, ci_low_signed=lo, ci_high_signed=hi))
    per_event = pd.DataFrame(pe).merge(summary[["event_id", "main_test", "enough_clusters"]], on="event_id")

    # ---- stacked
    groups = event_groups(events, summary)
    st = []
    for g, ids in groups.items():
        for (m, w, c), df in frames.items():
            if c == "value" and w != es.PRIMARY_WINDOW:
                continue
            sub = _subset(df, ids)
            for spec in X.SPECS:
                st.append(dict(group=g, model=m, window=es.window_label(w), conn=c,
                               **X.stacked(sub, spec, X.limit_controls(sub, controls))))
    stacked = pd.DataFrame(st)

    # ---- quality splits on the main test (treated firms restricted by evidence tier)
    sp = []
    main_ids = groups.get("main: all", [])
    for m in es.MODELS:
        df = _subset(primary[m], main_ids)
        treated = df.conn > 0
        tier = df.tested_tier if "tested_tier" in df else df.confidence_tier
        for name, keep in (("treated ties all high confidence", ~treated | (tier == "high")),
                           ("treated ties medium or low confidence", ~treated | (tier != "high")),
                           ("firms with a primary-source board roster", df.coverage > 0)):
            part = df[keep].reset_index(drop=True)
            for spec in X.SPECS:
                sp.append(dict(split=name, model=m, **X.stacked(part, spec, X.limit_controls(part, controls))))
    splits = pd.DataFrame(sp)

    # ---- falsification: events pre-registered as "no differential"
    zero_ids = events.loc[events.expected_sign_connected == "0", "event_id"].tolist()
    fz = []
    for m in (es.MODELS if zero_ids else ()):
        z = _subset(primary[m], zero_ids).assign(x=lambda d: d.conn)
        fz.append(dict(model=m, **X.stacked(z, PRIMARY_SPEC, X.limit_controls(z, controls))))
    falsification = pd.DataFrame(fz)

    # ---- decision rule and placebo, main-test groups only
    prim = stacked[(stacked.window == es.window_label(es.PRIMARY_WINDOW)) & (stacked.conn == "binary")]
    decisions, pl_rows, pl_draws = [], [], {}
    for g, ids in groups.items():
        if not g.startswith("main:"):
            continue
        sub = prim[prim.group == g]
        spec = PRIMARY_SPEC
        rows = sub[sub.spec == spec].set_index("model")
        ev_g = events[events.event_id.isin(ids)]
        placebo_p = {}
        for m in es.MODELS:
            if not rows.loc[m, "identified"] or n_placebo <= 0:
                placebo_p[m] = np.nan
                continue
            used = X.limit_controls(_subset(primary[m], ids), controls)
            res = X.placebo(rp, ev_g, measures, m, es.PRIMARY_WINDOW, spec, ctl, used,
                            n=n_placebo, seed=seed, all_events=events)
            placebo_p[m] = res["p_empirical"]
            pl_draws[(g, m)] = res
            pl_rows.append(dict(group=g, **{k: v for k, v in res.items() if k != "draws"}))
        sign_ok = bool((rows.d > 0).all())
        p_ok = bool((rows.p < ALPHA).all())
        pl_ok = bool(all(np.isfinite(v) and v < ALPHA for v in placebo_p.values()))
        decisions.append(dict(
            group=g, spec=spec, n_events=len(ids), n=int(rows.n.max()),
            n_treated=int(rows.n_treated.max()),
            **{f"d_{m}": rows.loc[m, "d"] for m in es.MODELS},
            **{f"p_{m}": rows.loc[m, "p"] for m in es.MODELS},
            **{f"placebo_p_{m}": placebo_p[m] for m in es.MODELS},
            sign_as_registered=sign_ok, p_below_alpha=p_ok, survives_placebo=pl_ok,
            holds=bool(rows.identified.all() and sign_ok and p_ok and pl_ok)))
    decisions = pd.DataFrame(decisions)
    placebo_tbl = pd.DataFrame(pl_rows)

    # ---- confounder re-check on the exchange calendar
    day0 = {e: rp.day0(d, a) for e, d, a in zip(events.event_id, events.date, events.after_close)}
    unflagged = []
    for a in events.itertuples(index=False):
        near = [b for b in events.event_id if b != a.event_id and day0[a.event_id] is not None
                and day0[b] is not None
                and abs(day0[a.event_id] - day0[b]) <= eventset.CONFOUNDER_TRADING_DAYS]
        if near and a.confounder_flag == 0:
            unflagged.append((a.event_id, near))

    # ---- write
    cars.to_csv(out / "cars.csv", index=False)
    ctl.to_csv(out / "controls.csv", index=False)
    per_event.to_csv(out / "per_event.csv", index=False)
    stacked.to_csv(out / "stacked.csv", index=False)
    splits.to_csv(out / "splits.csv", index=False)
    falsification.to_csv(out / "falsification.csv", index=False)
    decisions.to_csv(out / "decisions.csv", index=False)
    placebo_tbl.to_csv(out / "placebo.csv", index=False)
    summary.to_csv(out / "event_sample.csv", index=False)
    if pl_draws:
        pd.DataFrame({f"{g} | {m}": r["draws"] for (g, m), r in pl_draws.items()}).to_csv(
            out / "placebo_draws.csv", index=False)
    if price_coverage is not None:
        price_coverage.to_csv(out / "price_coverage.csv", index=False)

    note = f"{banner}. " if banner else ""
    f = per_event[per_event.model == "market"].copy()
    f["label"] = f.date.astype(str) + "  " + f.event_id
    plots.forest(f[f.expected_sign.isin(["+", "-"])], out / "figures" / "forest_per_event",
                 subtitle=f"{note}Market model, CAR[-1,+1], 95% intervals (HC3)")
    main_st = prim[prim.group.str.startswith("main:")]
    spec_of = dict(zip(decisions.group, decisions.spec)) if len(decisions) else {}
    main_st = main_st[[spec_of.get(g) == s for g, s in zip(main_st.group, main_st.spec)]]
    plots.stacked_by_type(main_st, out / "figures" / "stacked_by_type",
                          subtitle=f"{note}CAR[-1,+1], 95% intervals, two-way clustered")
    if ("main: all", "market") in pl_draws:
        r = pl_draws[("main: all", "market")]
        plots.placebo_hist(r["draws"], r["d_true"], out / "figures" / "placebo_main",
                           r["p_empirical"], subtitle=f"{note}Main test, market model, "
                           f"{r['n_draws']} draws of common pseudo-event dates")

    text = _summary_md(banner, events, summary, cars, controls, controls_note, decisions,
                       stacked, per_event, falsification, splits, missing_prices, unflagged,
                       n_placebo, rp)
    (out / "results_summary.md").write_text(text, encoding="utf-8")
    return dict(cars=cars, per_event=per_event, stacked=stacked, decisions=decisions,
                placebo=placebo_tbl, summary=summary, controls=controls, text=text)


def _fmt(v, pct=False, nd=3):
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "n/a"
    return f"{v * 100:+.2f}" if pct else f"{v:.{nd}f}"


def _summary_md(banner, events, summary, cars, controls, controls_note, decisions, stacked,
                per_event, falsification, splits, missing_prices, unflagged, n_placebo, rp) -> str:
    L = ["# Event-study results summary", ""]
    if banner:
        L += [f"> **{banner}.** These numbers say nothing about any real firm.", ""]
    L += ["Generated by `python -m influence.events.run`; do not edit by hand. Rules are those of "
          "`docs/paper/prereg.md`. Estimates are in percentage points of CAR[-1,+1]: the gap between "
          "connected and unconnected firms, signed so that a positive number is the "
          "pre-registered direction.", ""]
    usable = cars[(cars.model == "market") & (cars.window == es.window_label(es.PRIMARY_WINDOW))]
    L += ["## Sample", "",
          f"- Calendar: {pd.Timestamp(rp.dates[0]).date()} to {pd.Timestamp(rp.dates[-1]).date()}, "
          f"{len(rp.dates)} trading days; {len(rp.tickers)} tickers with prices.",
          f"- Events: {len(events)} listed; {int(summary.main_test.sum())} in the main test.",
          f"- Firm-events: {len(usable)}; dropped by the estimation rule (fewer than {es.MIN_VALID} "
          f"traded days in [-250,-30], or a missing return in the window): {int(usable.car.isna().sum())}; "
          f"no trade on any day of the window: {int(usable.no_trade.sum())}.",
          f"- Controls, in priority order: {', '.join(controls) or 'none'} ({controls_note}). Each regression "
          f"keeps as many as its sample carries ({X.OBS_PER_COEFFICIENT} identifying firm-events per coefficient); "
          "the `controls` column of `stacked.csv` shows which.", ""]
    if missing_prices:
        L += [f"- Tickers in the mapping without prices: {', '.join(missing_prices)}.", ""]
    L += ["## Decision rule, applied mechanically", "",
          "A result holds only if the stacked estimate has the registered sign with p < 0.05 "
          "under all three return models, and the placebo p-value is below 0.05 under all three.", ""]
    if len(decisions):
        L += ["| Event set | Spec | Events | Firm-events | Treated | d market | d mkt-adj | d Dimson | "
              "p (m / ma / D) | placebo p (m / ma / D) | Holds |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in decisions.itertuples(index=False):
            L.append(f"| {r.group} | {r.spec} | {r.n_events} | {r.n} | {r.n_treated} | "
                     f"{_fmt(r.d_market, True)} | {_fmt(r.d_market_adjusted, True)} | {_fmt(r.d_dimson, True)} | "
                     f"{_fmt(r.p_market)} / {_fmt(r.p_market_adjusted)} / {_fmt(r.p_dimson)} | "
                     f"{_fmt(r.placebo_p_market)} / {_fmt(r.placebo_p_market_adjusted)} / {_fmt(r.placebo_p_dimson)} | "
                     f"{'yes' if r.holds else 'no'} |")
        L.append("")
        if not n_placebo:
            L += ["Placebo was skipped in this run, so nothing can hold.", ""]
    else:
        L += ["No event passes the main-test rules, so there is no main result to report.", ""]
    L += ["## Both specifications, primary window, 0/1 connection", "",
          "| Event set | Model | Spec | d (pp) | se (pp) | p | n | Note |", "|---|---|---|---|---|---|---|---|"]
    p0 = stacked[(stacked.window == es.window_label(es.PRIMARY_WINDOW)) & (stacked.conn == "binary")]
    for r in p0.itertuples(index=False):
        L.append(f"| {r.group} | {r.model} | {r.spec} | {_fmt(r.d, True)} | {_fmt(r.se, True)} | "
                 f"{_fmt(r.p)} | {r.n} | {r.note} |")
    L += ["", "## Leakage check, window [-5,-2], main test", "",
          "| Model | Spec | d (pp) | p |", "|---|---|---|---|"]
    lk = stacked[(stacked.window == es.window_label(es.LEAKAGE_WINDOW)) & (stacked.group == "main: all")]
    for r in lk.itertuples(index=False):
        L.append(f"| {r.model} | {r.spec} | {_fmt(r.d, True)} | {_fmt(r.p)} |")
    L += ["", "## Per event (market model)", "",
          "| Date | Event | Measure | Sign | Main test | n | Treated | d signed (pp) | p | Note |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for r in per_event[per_event.model == "market"].itertuples(index=False):
        L.append(f"| {r.date} | {r.event_id} | {r.measure} | {r.expected_sign} | "
                 f"{'yes' if r.main_test else 'no'} | {r.n} | {r.n_treated} | {_fmt(r.d_signed, True)} | "
                 f"{_fmt(r.p)} | {r.note} |")
    if len(falsification):
        L += ["", "## Falsification: events registered as no differential", "",
              "| Model | d (pp) | p | n |", "|---|---|---|---|"]
        for r in falsification.itertuples(index=False):
            L.append(f"| {r.model} | {_fmt(r.d, True)} | {_fmt(r.p)} | {r.n} |")
    if len(splits):
        L += ["", "## Main test split by evidence quality", "",
              "| Split | Model | Spec | d (pp) | p | n | Note |", "|---|---|---|---|---|---|---|"]
        for r in splits.itertuples(index=False):
            L.append(f"| {r.split} | {r.model} | {r.spec} | {_fmt(r.d, True)} | {_fmt(r.p)} | {r.n} | {r.note} |")
    if unflagged:
        L += ["", "## Check: events within 5 trading days of another listed event but not flagged", ""]
        L += [f"- {e}: near {', '.join(n)}" for e, n in unflagged]
    L += ["", "Files: `cars.csv`, `controls.csv`, `per_event.csv`, `stacked.csv`, `splits.csv`, "
          "`falsification.csv`, `decisions.csv`, `placebo.csv`, `placebo_draws.csv`, "
          "`event_sample.csv`, `figures/`.", ""]
    return "\n".join(L)


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--synthetic", action="store_true", help="simulate prices instead of loading them")
    ap.add_argument("--effect", type=float, default=0.02, help="planted effect for --synthetic")
    ap.add_argument("--prices", default=None, help="price download folder (default: latest)")
    ap.add_argument("--placebo", type=int, default=PLACEBO_DRAWS)
    ap.add_argument("--seed", type=int, default=PLACEBO_SEED)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    events = eventset.load_events()
    tickers = eventset.load_tickers()
    mpath = PROC / "connection_measures.parquet"
    if not mpath.exists():
        raise SystemExit("run `python -m influence.connections.build_measures` first")
    measures = pd.read_parquet(mpath)

    if args.synthetic:
        panel = synthetic.make_panel(
            tickers.ticker, seed=args.seed, events=events, measures=measures, effect=args.effect,
            listing=dict(zip(tickers.ticker, tickers.listing_date)), thin=tickers.ticker[::6])
        out = Path(args.out) if args.out else PROC / "results_synthetic"
        res = run(es.prepare(panel), events, measures, out,
                  fundamentals=synthetic.make_fundamentals(tickers.ticker, seed=args.seed),
                  n_placebo=args.placebo, seed=args.seed,
                  banner=f"SYNTHETIC PRICES with a planted effect of {args.effect * 100:.1f} pp",
                  price_coverage=prices.coverage_report(panel))
    else:
        sha = prices.registration_commit()
        panel, cov = prices.load(args.prices)
        out = Path(args.out) if args.out else PROC / "results"
        res = run(es.prepare(panel), events, measures, out, n_placebo=args.placebo, seed=args.seed,
                  banner="", price_coverage=cov)
        print(f"pre-registration commit {sha}")
    print(f"wrote {out}")
    if len(res["decisions"]):
        print(res["decisions"][["group", "spec", "n_events", "holds"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

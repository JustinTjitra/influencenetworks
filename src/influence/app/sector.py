"""Pure functions for the sector page: firms side by side, events, stacked estimates."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from ..connections.build_measures import PROC
from ..connections.measures import compute_all
from ..events import eventstudy as es
from .data import Bundle, firm_node

MEASURES = ("state_own", "board_party", "board_office", "board_former", "board_family",
            "group_conn", "dist_gov")
MEASURE_COLUMNS = ["ticker", "firm", *MEASURES, "n_board_known"]
EVENT_COLUMNS = ["date", "event_id", "description", "type", "scope", "tested_measure",
                 "expected_sign", "n_firms", "n_connected_firms", "main_test",
                 "source_url_1", "source_url_2"]
SUMMARY_PATH = PROC / "connection_event_summary.csv"
DEFAULT_RESULTS_DIR = PROC / "results"
STACKED_FILE = "stacked.csv"
STACKED_WINDOW = es.window_label(es.PRIMARY_WINDOW)   # "[-1,+1]"
STACKED_CONN = "binary"                               # the 0/1 connection indicator
STACKED_COLUMNS = ["group", "model", "spec", "n", "n_firms", "n_events", "n_treated",
                   "identified", "d", "se", "t", "p", "ci_low", "ci_high", "note"]


def measures_table(bundle: Bundle, sector: str, on: date) -> pd.DataFrame:
    """One row per firm in `sector`: the seven registered measures on `on`, and n_board_known."""
    firms = bundle.tickers[bundle.tickers.sector_bucket == sector].sort_values("ticker")
    rows = []
    for r in firms.itertuples(index=False):
        res = compute_all(bundle.graph, firm_node(bundle, r.ticker), on)
        rows.append({"ticker": r.ticker, "firm": r.listed_name,
                     **{m: res[m] for m in MEASURES}, "n_board_known": res["n_board_known"]})
    return pd.DataFrame(rows, columns=MEASURE_COLUMNS)


def event_table(bundle: Bundle, sector: str, summary_path: Path | str = SUMMARY_PATH) -> pd.DataFrame:
    """Events whose sample includes `sector` (market-wide events and its own sector events)."""
    ev = bundle.events
    ev = ev[(ev["scope"] == "market") | (ev["sector"] == sector) | (ev["sector"] == "all")]
    summ = pd.read_csv(summary_path)[["event_id", "n_firms", "n_treated", "main_test"]]
    df = ev.merge(summ, on="event_id", how="left")
    df = df.rename(columns={"expected_sign_connected": "expected_sign",
                            "connection_measure_tested": "tested_measure",
                            "n_treated": "n_connected_firms"})
    df["main_test"] = df["main_test"].map({1: "yes", 0: "no"})
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return (df[EVENT_COLUMNS].sort_values(["date", "event_id"], kind="stable")
            .reset_index(drop=True))


def stacked_results(results_dir: str | Path | None = None) -> pd.DataFrame | None:
    """Primary-window, 0/1-connection rows of stacked.csv; None if the file does not exist."""
    folder = Path(results_dir) if results_dir is not None else DEFAULT_RESULTS_DIR
    if "synthetic" in folder.name:
        return None
    path = folder / STACKED_FILE
    if not path.is_file():
        return None
    df = pd.read_csv(path)
    df = df[(df["window"] == STACKED_WINDOW) & (df["conn"] == STACKED_CONN)]
    return df[STACKED_COLUMNS].reset_index(drop=True)

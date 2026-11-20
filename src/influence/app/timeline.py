"""Event timeline for one firm: the registered events whose sample includes it."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..connections.build_measures import PROC
from ..events import eventset
from ..events import eventstudy as es
from .data import Bundle

DEFAULT_RESULTS_DIR = PROC / "results"
CARS_FILE = "cars.csv"
CAR_MODEL = "market"
CAR_WINDOW = es.window_label(es.PRIMARY_WINDOW)   # "[-1,+1]"
COLUMNS = ["date", "event_id", "description", "type", "expected_sign", "tested_measure",
           "firm_value", "firm_connected", "main_test", "source_url_1", "source_url_2",
           "car", "sector_median_car"]


def _results_path(results_dir: str | Path | None) -> Path:
    return Path(results_dir) if results_dir is not None else DEFAULT_RESULTS_DIR


def has_results(results_dir: str | Path | None = None) -> bool:
    return (_results_path(results_dir) / CARS_FILE).is_file()


def _load_cars(results_dir: str | Path | None) -> pd.DataFrame | None:
    path = _results_path(results_dir) / CARS_FILE
    if not path.is_file():
        return None
    cars = pd.read_csv(path)
    cars = cars[(cars["model"] == CAR_MODEL) & (cars["window"] == CAR_WINDOW)]
    return cars[["event_id", "ticker", "car"]]


def timeline(bundle: Bundle, ticker: str, results_dir: str | Path | None = None) -> pd.DataFrame:
    m = bundle.measures
    firm = m[(m.ticker == ticker) & m.in_event_sample]
    ev = bundle.events.set_index("event_id")
    main_ids = set(eventset.main_test_subset(bundle.events).event_id)
    rows = []
    for r in firm.itertuples(index=False):
        e = ev.loc[r.event_id]
        rows.append({
            "date": e.date, "event_id": r.event_id, "description": e.description,
            "type": e.type, "expected_sign": e.expected_sign_connected,
            "tested_measure": r.tested_measure, "firm_value": r.tested_value,
            "firm_connected": "yes" if r.tested_binary == 1 else "no",
            "main_test": "yes" if r.event_id in main_ids else "no",
            "source_url_1": e.source_url_1, "source_url_2": e.source_url_2,
            "car": np.nan, "sector_median_car": np.nan,
            "_sector": r.sector_bucket,
        })
    out = pd.DataFrame(rows, columns=COLUMNS + ["_sector"])

    cars = _load_cars(results_dir)
    if cars is not None and len(out):
        cars = cars.dropna(subset=["car"])
        sector_of = m[m.in_event_sample][["event_id", "ticker", "sector_bucket"]]
        cars = cars.merge(sector_of, on=["event_id", "ticker"])
        own = cars[cars.ticker == ticker].set_index("event_id")["car"]
        med = cars.groupby(["event_id", "sector_bucket"])["car"].median()
        out["car"] = out.event_id.map(own).astype(float)
        out["sector_median_car"] = [med.get((eid, sec), np.nan)
                                    for eid, sec in zip(out.event_id, out._sector)]
        out["sector_median_car"] = out["sector_median_car"].astype(float)

    out = out.drop(columns="_sector")
    return out.sort_values(["date", "event_id"], kind="stable").reset_index(drop=True)

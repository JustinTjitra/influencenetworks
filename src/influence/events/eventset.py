"""Load and validate the ticker mapping and the event set.

Both files are fixed by the pre-registration (docs/paper/prereg.md), so the loaders
are strict: an unknown value, a missing source or a bad date is an error, not a
warning.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
TICKERS_PATH = ROOT / "data" / "mappings" / "tickers.csv"
EVENTS_PATH = ROOT / "data" / "events" / "events.csv"

TICKER_COLUMNS = ["node_id", "ticker", "exchange", "listed_name", "sector_bucket",
                  "listing_date", "delisting_date", "source_url", "source_url_2", "note"]
EVENT_COLUMNS = ["event_id", "date", "type", "subtype", "description",
                 "expected_sign_connected", "connection_measure_tested", "scope", "sector",
                 "anticipation_flag", "confounder_flag", "source_url_1", "source_url_2",
                 "confidence", "notes", "target_party", "after_close"]

SECTORS = {"bank", "palm", "media"}
EVENT_TYPES = {"coalition", "state_governance", "sector_policy", "governance"}
SIGNS = {"+", "-", "0", "ambiguous"}
MEASURES_TESTED = {"state_own", "board_party", "board_office", "board_family",
                   "group_conn", "all"}
SCOPES = {"market", "sector"}
EVENT_SECTORS = SECTORS | {"all"}
CONFIDENCE = {"high", "medium", "low"}
CONFOUNDER_TRADING_DAYS = 5


class EventSetError(ValueError):
    pass


def _read(path: Path, columns: list[str]) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise EventSetError(f"{path.name}: missing columns {missing}")
    return df[columns].apply(lambda s: s.str.strip())


def _dates(df: pd.DataFrame, col: str, name: str, required: bool) -> pd.Series:
    out = pd.to_datetime(df[col].where(df[col] != "", None), format="%Y-%m-%d", errors="coerce")
    bad = df[(df[col] != "") & out.isna()]
    if len(bad):
        raise EventSetError(f"{name}: unparseable {col}: {bad[col].tolist()}")
    if required and out.isna().any():
        raise EventSetError(f"{name}: {col} is required on every row")
    return out


def _is_url(s: pd.Series) -> pd.Series:
    return s.str.match(r"^https?://\S+$")


def load_tickers(path: Path = TICKERS_PATH) -> pd.DataFrame:
    df = _read(path, TICKER_COLUMNS)
    name = path.name
    if df.ticker.duplicated().any():
        raise EventSetError(f"{name}: duplicate tickers {df.ticker[df.ticker.duplicated()].tolist()}")
    if not df.ticker.str.match(r"^[A-Z]{4}$").all():
        raise EventSetError(f"{name}: IDX tickers are four capital letters")
    if set(df.exchange) - {"IDX"}:
        raise EventSetError(f"{name}: Phase 1 is IDX only")
    if set(df.sector_bucket) - SECTORS:
        raise EventSetError(f"{name}: bad sector_bucket {set(df.sector_bucket) - SECTORS}")
    if not _is_url(df.source_url).all():
        raise EventSetError(f"{name}: every ticker needs a source_url")
    if not (_is_url(df.source_url_2) | (df.source_url_2 == "")).all():
        raise EventSetError(f"{name}: source_url_2 must be a URL or empty")
    df["listing_date"] = _dates(df, "listing_date", name, required=True)
    df["delisting_date"] = _dates(df, "delisting_date", name, required=False)
    return df


def load_events(path: Path = EVENTS_PATH) -> pd.DataFrame:
    df = _read(path, EVENT_COLUMNS)
    name = path.name
    if df.event_id.duplicated().any():
        raise EventSetError(f"{name}: duplicate event_id")
    checks = [("type", EVENT_TYPES), ("expected_sign_connected", SIGNS),
              ("connection_measure_tested", MEASURES_TESTED), ("scope", SCOPES),
              ("sector", EVENT_SECTORS), ("confidence", CONFIDENCE),
              ("anticipation_flag", {"0", "1"}), ("confounder_flag", {"0", "1"}),
              ("after_close", {"0", "1"})]
    for col, allowed in checks:
        bad = set(df[col]) - allowed
        if bad:
            raise EventSetError(f"{name}: bad {col} {sorted(bad)}")
    if not (_is_url(df.source_url_1) & _is_url(df.source_url_2)).all():
        raise EventSetError(f"{name}: every event needs two source URLs")
    if (df.source_url_1 == df.source_url_2).any():
        raise EventSetError(f"{name}: the two sources of an event must differ")
    if (df.notes == "").any() or (df.description == "").any():
        raise EventSetError(f"{name}: description and notes (the sign argument) are required")
    if not (df.target_party.str.match(r"^party_[a-z_]+$") | (df.target_party == "")).all():
        raise EventSetError(f"{name}: target_party must be a party node id or empty")
    if ((df.scope == "sector") & (df.sector == "all")).any():
        raise EventSetError(f"{name}: a sector-scope event must name its sector")
    df["date"] = _dates(df, "date", name, required=True)
    for col in ("anticipation_flag", "confounder_flag", "after_close"):
        df[col] = df[col].astype(int)
    return df.sort_values("date", kind="stable").reset_index(drop=True)


def sign_value(sign: str) -> float:
    """+1 / -1 for a signed event; NaN for "0" and "ambiguous"."""
    return {"+": 1.0, "-": -1.0}.get(sign, float("nan"))


def main_test_subset(events: pd.DataFrame) -> pd.DataFrame:
    """Unanticipated, unconfounded events with a pre-registered direction."""
    keep = ((events.anticipation_flag == 0) & (events.confounder_flag == 0)
            & events.expected_sign_connected.isin(["+", "-"]))
    return events[keep]


def previous_weekday(d: date) -> date:
    """The last Monday-to-Friday day strictly before d (exchange holidays not modelled)."""
    d = d - timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def effective_weekday(d: date, after_close: int = 0) -> date:
    """First weekday on which the market could react: the date itself, or the next
    weekday when the news came after the close or on a weekend."""
    if after_close:
        d = d + timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def samples_overlap(scope_a: str, sector_a: str, scope_b: str, sector_b: str) -> bool:
    """Two events share firms unless both are sector events about different sectors."""
    if "market" in (scope_a, scope_b) or "all" in (sector_a, sector_b):
        return True
    return sector_a == sector_b


def neighbours_within(events: pd.DataFrame, days: int = CONFOUNDER_TRADING_DAYS) -> dict[str, list[str]]:
    """For each event, the other listed events with an overlapping sample whose first
    reaction day falls within `days` weekdays of its own. Weekdays stand in for
    trading days here; the engine re-checks with the exchange calendar once prices
    exist. Every event with a neighbour must carry confounder_flag = 1."""
    eff = [np.datetime64(effective_weekday(d.date(), a), "D")
           for d, a in zip(events.date, events.after_close)]
    ids = events.event_id.tolist()
    scope, sector = events.scope.tolist(), events.sector.tolist()
    out: dict[str, list[str]] = {}
    for i, a in enumerate(eff):
        out[ids[i]] = [ids[j] for j, b in enumerate(eff)
                       if j != i and abs(int(np.busday_count(a, b))) <= days
                       and samples_overlap(scope[i], sector[i], scope[j], sector[j])]
    return out

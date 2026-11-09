"""Time-varying party status relative to the sitting government.

Status comes from `data/seed/coalition_events.csv`. A row changes a party's status
when its `status_after` column is filled; rows with an empty `status_after` are
events that are recorded but do not change the coding. A party's status on a date is
the `status_after` of its latest status-changing row on or before that date, and
"unknown" when there is none.

`status_flag` marks a coding that a reasonable reader could dispute (for example a
party that supports the government without holding a minister post). With
`count_flagged=False` a flagged "governing" status is read as "outside", which is the
sensitivity check the design asks for.

The coding rule, applied to every party:
    governing = holds at least one minister or vice-minister post in the sitting
                cabinet, or has formally declared support for the sitting government;
    outside   = neither;
    unknown   = no sourced row yet, or the party's position is contested in the
                sources (recorded with the flag "contested").
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Optional

from ..graph import _parse_date

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PATH = ROOT / "data" / "seed" / "coalition_events.csv"

STATUSES = ("governing", "outside", "unknown")


@dataclass(frozen=True)
class StatusChange:
    party_id: str
    on: date
    status: str
    flag: str
    event_id: str
    source_url: str


@lru_cache(maxsize=8)
def load_status_changes(path: Path = DEFAULT_PATH) -> dict[str, tuple[StatusChange, ...]]:
    """Read the status-changing rows, grouped by party and sorted by date."""
    by_party: dict[str, list[StatusChange]] = {}
    with open(path, newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            status = (row.get("status_after") or "").strip()
            if not status:
                continue
            if status not in STATUSES:
                raise ValueError(f"{Path(path).name}:{i}: bad status_after {status!r}")
            pid = (row.get("party_id") or "").strip()
            on = _parse_date(row.get("date", ""))
            if not pid or on is None:
                raise ValueError(f"{Path(path).name}:{i}: status row needs party_id and date")
            by_party.setdefault(pid, []).append(StatusChange(
                party_id=pid, on=on, status=status,
                flag=(row.get("status_flag") or "").strip(),
                event_id=row["event_id"].strip(), source_url=row["source_url"].strip(),
            ))
    return {p: tuple(sorted(v, key=lambda c: c.on)) for p, v in by_party.items()}


def status_record(party_id: str, on: date, path: Path = DEFAULT_PATH) -> Optional[StatusChange]:
    """The row that determines a party's status on a date, or None."""
    current = None
    for change in load_status_changes(path).get(party_id, ()):
        if change.on <= on:
            current = change
        else:
            break
    return current


def party_status(party_id: str, on: date, count_flagged: bool = True,
                 path: Path = DEFAULT_PATH) -> str:
    """Return "governing", "outside" or "unknown" for a party on a date."""
    rec = status_record(party_id, on, path)
    if rec is None:
        return "unknown"
    if rec.status == "governing" and rec.flag and not count_flagged:
        return "outside"
    return rec.status


def governing_parties(on: date, count_flagged: bool = True,
                      path: Path = DEFAULT_PATH) -> set[str]:
    return {p for p in load_status_changes(path)
            if party_status(p, on, count_flagged, path) == "governing"}

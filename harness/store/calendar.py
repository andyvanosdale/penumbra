"""Lane trading calendars (spec/02 Trading calendars).

Calendars are rows in the `calendar` table, built once per snapshot at load time and
never inferred from price rows at read time:

- `nyse`: the dates on which the snapshot's equity daily bars (SEP) carry any bar.
  Built only from `market = 'us_equity'`, so crypto rows never add a date.
- `utc`: every UTC calendar day in a range.

A calendar row dated D has `available_at` = D.
"""

from __future__ import annotations

import datetime as dt
import sqlite3

import pandas as pd

from harness.store.schema import LANE_CALENDAR
from harness.store.writer import upsert


class CalendarError(ValueError):
    pass


def calendar_for_lane(lane: str) -> str:
    try:
        return LANE_CALENDAR[lane]
    except KeyError:
        raise CalendarError(f"unknown lane {lane!r}; lanes are {sorted(LANE_CALENDAR)}")


def build_nyse_calendar(conn: sqlite3.Connection, snapshot_id: str) -> int:
    """Write the `nyse` calendar for `snapshot_id` from its equity daily bars.

    Loaders call this after the SEP rows are written. A weekend date among the
    equity bars is a data error and is refused. Returns the number of sessions.
    """
    dates = [r[0] for r in conn.execute(
        "SELECT DISTINCT date FROM bars_daily WHERE snapshot_id = ? AND market = 'us_equity' "
        "ORDER BY date", (snapshot_id,))]
    weekend = [d for d in dates if dt.date.fromisoformat(d).weekday() >= 5]
    if weekend:
        raise CalendarError(f"equity bars on weekend dates {weekend[:5]} "
                            f"({len(weekend)} total) in snapshot {snapshot_id}")
    upsert(conn, "calendar", snapshot_id,
           [{"calendar": "nyse", "date": d, "available_at": d} for d in dates])
    return len(dates)


def build_utc_calendar(conn: sqlite3.Connection, snapshot_id: str,
                       start: str, end: str) -> int:
    """Write the `utc` calendar (every calendar day in [start, end])."""
    days = pd.date_range(start, end, freq="D").strftime("%Y-%m-%d")
    upsert(conn, "calendar", snapshot_id,
           [{"calendar": "utc", "date": d, "available_at": d} for d in days])
    return len(days)


def next_session(conn: sqlite3.Connection, snapshot_id: str, calendar: str,
                 date: str) -> str | None:
    """The first session of `calendar` strictly after `date`, or None past the end.

    Loaders use it for the EVENTS `available_at` (spec/04 `filing_2d`).
    """
    row = conn.execute(
        "SELECT MIN(date) FROM calendar WHERE snapshot_id = ? AND calendar = ? AND date > ?",
        (snapshot_id, calendar, date)).fetchone()
    return row[0]

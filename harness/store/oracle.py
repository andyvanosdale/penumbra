"""Bounded future-aware reader, for the labeler only (spec/04 Labels; spec/03 Era
boundaries).

Only `harness/labels.py` and `harness/backtest.py` may import this module
(docs/architecture.md import rules; tests/test_architecture.py).

The oracle reads rows dated after an as-of date, so it has no `available_at`
filter. It is bounded instead:

- it refuses any read whose end is after `last_date` (the last trading day of the
  run's era), and
- unless `unlocked`, it refuses any read whose end is on or after `holdout_start`.

The era bounds and the unlock are parameters, supplied by the run (config/eras.py
and the run record are issue 17's). The SQL also caps every read at the effective
bound, so a caller cannot widen it.
"""

from __future__ import annotations

import datetime as dt
import sqlite3

import pandas as pd

from harness.store import adjust as _adjust
from harness.store.reader import _in, _market, _symbols_arg, end_of_day, iso_date
from harness.store.schema import CALENDARS


class OracleBoundError(PermissionError):
    """A read past the era's last trading day."""


class HoldoutLockedError(PermissionError):
    """A read into the holdout without the logged unlock."""


class OracleReader:
    def __init__(self, conn: sqlite3.Connection, snapshot_id: str, last_date,
                 holdout_start, unlocked: bool = False):
        if conn.execute("SELECT 1 FROM snapshots WHERE snapshot_id = ?",
                        (snapshot_id,)).fetchone() is None:
            raise KeyError(f"snapshot {snapshot_id!r} is not in the store")
        self.conn = conn
        self.snapshot_id = snapshot_id
        self.last_date = iso_date(last_date)
        self.holdout_start = iso_date(holdout_start)
        self.unlocked = bool(unlocked)
        bound = self.last_date
        if not self.unlocked:
            day_before = (dt.date.fromisoformat(self.holdout_start)
                          - dt.timedelta(days=1)).isoformat()
            bound = min(bound, day_before)
        self.bound = bound

    def _check(self, end: str) -> str:
        if end > self.last_date:
            raise OracleBoundError(f"read to {end} is past the era's last trading day "
                                   f"{self.last_date}")
        if not self.unlocked and end >= self.holdout_start:
            raise HoldoutLockedError(f"read to {end} reaches the holdout (from "
                                     f"{self.holdout_start}) and the holdout is not unlocked")
        return end

    def _frame(self, sql: str, params: list) -> pd.DataFrame:
        return pd.read_sql_query(sql, self.conn, params=params)

    def bars(self, market: str, symbols, start, end, adjust: str = "none",
             basis=None) -> pd.DataFrame:
        """Daily bars dated in [start, end].

        With `adjust` other than 'none', prices are expressed in the basis of date
        `basis` (the entry's as-of date D): bars after D are divided by the factors
        of actions in (D, t], bars before D multiplied by those in (t, D].
        """
        s, e = iso_date(start), self._check(iso_date(end))
        kinds = _adjust.adjusting_actions(adjust)
        params: list = [self.snapshot_id, _market(market), s, e, self.bound]
        syms = _symbols_arg(symbols)
        bars = self._frame(
            "SELECT market, symbol, date, open, high, low, close, volume, dollar_volume, "
            "available_at FROM bars_daily WHERE snapshot_id = ? AND market = ? "
            "AND date >= ? AND date <= ? AND date <= ?" + _in("symbol", syms, params)
            + " ORDER BY symbol, date", params)
        if not kinds or bars.empty:
            return bars
        if basis is None:
            raise ValueError("an adjusted oracle read needs `basis` (the as-of date)")
        b = self._check(iso_date(basis))
        params = [self.snapshot_id, market, self.bound]
        sql = ("SELECT a.symbol, a.date, a.action, a.value, "
               " (SELECT b.close FROM bars_daily b WHERE b.snapshot_id = a.snapshot_id "
               "  AND b.market = a.market AND b.symbol = a.symbol AND b.date < a.date "
               "  ORDER BY b.date DESC LIMIT 1) AS prev_close "
               "FROM actions a WHERE a.snapshot_id = ? AND a.market = ? AND a.date <= ?"
               + _in("a.action", kinds, params)
               + _in("a.symbol", sorted(bars["symbol"].unique()), params))
        factors = _adjust.action_factors(self._frame(sql, params))
        return _adjust.apply(bars, factors, b)

    def hourly(self, market: str, symbols, start, end) -> pd.DataFrame:
        """Hourly klines opening on UTC dates [start, end]."""
        s, e = iso_date(start), self._check(iso_date(end))
        params: list = [self.snapshot_id, _market(market), f"{s}T", end_of_day(e),
                        end_of_day(self.bound)]
        return self._frame(
            "SELECT market, symbol, ts, open, high, low, close, volume, quote_volume, "
            "available_at FROM bars_hourly WHERE snapshot_id = ? AND market = ? "
            "AND ts >= ? AND ts <= ? AND ts <= ?"
            + _in("symbol", _symbols_arg(symbols), params) + " ORDER BY symbol, ts", params)

    def actions(self, market: str, symbols, start, end) -> pd.DataFrame:
        s, e = iso_date(start), self._check(iso_date(end))
        params: list = [self.snapshot_id, _market(market), s, e, self.bound]
        return self._frame(
            "SELECT market, symbol, date, action, value, ticker, contraticker, contraname, "
            "available_at FROM actions WHERE snapshot_id = ? AND market = ? AND date >= ? "
            "AND date <= ? AND date <= ?" + _in("symbol", _symbols_arg(symbols), params)
            + " ORDER BY symbol, date, action", params)

    def listing(self, market: str, symbols, start, end) -> pd.DataFrame:
        s, e = iso_date(start), self._check(iso_date(end))
        params: list = [self.snapshot_id, _market(market), s, e, self.bound]
        return self._frame(
            "SELECT market, symbol, event, date, reason, exchange, source, available_at "
            "FROM listing WHERE snapshot_id = ? AND market = ? AND date >= ? AND date <= ? "
            "AND date <= ?" + _in("symbol", _symbols_arg(symbols), params)
            + " ORDER BY symbol, date, event", params)

    def events(self, market: str, symbols, start, end) -> pd.DataFrame:
        """EVENTS rows by filing date in [start, end] (the ex-post bucket, spec/04)."""
        s, e = iso_date(start), self._check(iso_date(end))
        params: list = [self.snapshot_id, _market(market), s, e, self.bound]
        return self._frame(
            "SELECT market, symbol, filing_date, eventcodes, available_at FROM events "
            "WHERE snapshot_id = ? AND market = ? AND filing_date >= ? AND filing_date <= ? "
            "AND filing_date <= ?" + _in("symbol", _symbols_arg(symbols), params)
            + " ORDER BY symbol, filing_date", params)

    def calendar(self, calendar_name: str, start, end) -> pd.DataFrame:
        if calendar_name not in CALENDARS:
            raise ValueError(f"calendar must be one of {CALENDARS}, got {calendar_name!r}")
        s, e = iso_date(start), self._check(iso_date(end))
        return self._frame(
            "SELECT calendar, date, available_at FROM calendar WHERE snapshot_id = ? "
            "AND calendar = ? AND date >= ? AND date <= ? AND date <= ? ORDER BY date",
            [self.snapshot_id, calendar_name, s, e, self.bound])

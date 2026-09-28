"""As-of reader: the only store read path for the universe, features and costs.

Every public method takes `as_of` (an ISO date: "after the close of D"), and the SQL
itself filters `available_at <= :as_of`. For hourly klines, whose `available_at` is a
UTC close time, as-of D means the end of UTC day D. Every read is scoped to one
snapshot. Every returned frame includes `available_at`, so the store leakage test
(tests/store/test_leakage.py, spec/02 Leakage tests) can check each row.

Future-aware reads for the labeler live in `harness.store.oracle`, never here.
"""

from __future__ import annotations

import datetime as dt
import sqlite3
from typing import Sequence

import pandas as pd

from harness.store import adjust as _adjust
from harness.store.schema import CALENDARS, MARKETS

# spec/04 Features: "Sector is Sharadar TICKERS `sector`, a current classification
# with no history. It is the one input the store leakage test allowlists, and the
# allowlist entry cites this line." `symbols.sector` is served as-is at every as-of
# date. spec/01 Eligibility extends this to `category` (also a current TICKERS value
# with no vendor history) and, only as the fallback `exchange_on` takes when ACTIONS
# carries no listing/exchange-change event for a name, to `symbols.exchange` too --
# the primary, point-in-time answer for exchange is `exchange_on`, below, not
# `symbols.exchange` directly.
NON_PIT_ALLOWLIST = {
    ("symbols", "sector"): "spec/04 Features (Sector is Sharadar TICKERS `sector`)",
    ("symbols", "category"): "spec/01 Eligibility (category is a current value with no "
                             "history, allowlisted like sector)",
    ("symbols", "exchange"): "spec/01 Eligibility (TICKERS exchange, only as exchange_on's "
                             "fallback when ACTIONS carries no listing/exchange-change event)",
}

SYMBOL_ATTRIBUTES = ("market", "symbol", "ticker", "name", "category", "exchange",
                     "sector", "base", "quote", "available_at")
BAR_COLUMNS = ("market", "symbol", "date", "open", "high", "low", "close", "volume",
               "dollar_volume", "available_at")


def iso_date(d) -> str:
    if isinstance(d, str):
        dt.date.fromisoformat(d[:10])
        if len(d) != 10:
            raise ValueError(f"expected an ISO date, got {d!r}")
        return d
    if isinstance(d, dt.datetime):  # includes pd.Timestamp
        if d.time() != dt.time(0) or d.tzinfo is not None:
            raise ValueError(f"expected a date, got an intraday or tz-aware time {d!r}")
        return d.date().isoformat()
    if isinstance(d, dt.date):
        return d.isoformat()
    return pd.Timestamp(d).strftime("%Y-%m-%d")


def end_of_day(d: str) -> str:
    """The last millisecond of UTC day `d`, in the hourly `available_at` format."""
    return f"{d}T23:59:59.999Z"


def _market(m: str) -> str:
    if m not in MARKETS:
        raise ValueError(f"market must be one of {MARKETS}, got {m!r}")
    return m


def _in(column: str, values: Sequence[str] | None, params: list) -> str:
    if values is None:
        return ""
    values = [str(v) for v in values]
    if not values:
        return " AND 0"
    params.extend(values)
    return f" AND {column} IN ({', '.join('?' for _ in values)})"


def _symbols_arg(symbols) -> list[str] | None:
    if symbols is None:
        return None
    if isinstance(symbols, str):
        return [symbols]
    return list(symbols)


class AsOfReader:
    """As-of reads of one snapshot."""

    def __init__(self, conn: sqlite3.Connection, snapshot_id: str):
        if conn.execute("SELECT 1 FROM snapshots WHERE snapshot_id = ?",
                        (snapshot_id,)).fetchone() is None:
            raise KeyError(f"snapshot {snapshot_id!r} is not in the store")
        self.conn = conn
        self.snapshot_id = snapshot_id

    def _frame(self, sql: str, params: list) -> pd.DataFrame:
        return pd.read_sql_query(sql, self.conn, params=params)

    # ------------------------------------------------------------------ bars
    def bars(self, market: str, symbols, date, as_of, adjust: str = "none") -> pd.DataFrame:
        """Daily bars dated `date` (a single-date read), in the as-of basis."""
        d = iso_date(date)
        return self.panel(market, symbols, d, d, as_of, adjust)

    def panel(self, market: str, symbols, start, end, as_of,
              adjust: str = "none") -> pd.DataFrame:
        """Daily bars dated in [start, end] for `symbols` (None = all), known as-of.

        The one windowed read per (lane, era). `adjust` in {none, split, split_div};
        the adjusted series is in the as-of basis (spec/02 Store). `dollar_volume`
        is always unadjusted.
        """
        kinds = _adjust.adjusting_actions(adjust)
        a = iso_date(as_of)
        params: list = [self.snapshot_id, _market(market), iso_date(start), iso_date(end), a]
        syms = _symbols_arg(symbols)
        sql = (f"SELECT {', '.join(BAR_COLUMNS)} FROM bars_daily "
               "WHERE snapshot_id = ? AND market = ? AND date >= ? AND date <= ? "
               "AND available_at <= ?" + _in("symbol", syms, params)
               + " ORDER BY symbol, date")
        bars = self._frame(sql, params)
        if not kinds or bars.empty:
            return bars
        factors = self._factors(market, sorted(bars["symbol"].unique()),
                                bars["date"].min(), a, kinds)
        return _adjust.apply(bars, factors, a)

    def _factors(self, market: str, symbols: list[str], after: str, as_of: str,
                 kinds: tuple[str, ...]) -> pd.DataFrame:
        """Factors of adjusting actions dated in (after, as_of], known as-of."""
        params: list = [as_of, self.snapshot_id, market, after, as_of, as_of]
        sql = ("SELECT a.symbol, a.date, a.action, a.value, "
               " (SELECT b.close FROM bars_daily b WHERE b.snapshot_id = a.snapshot_id "
               "  AND b.market = a.market AND b.symbol = a.symbol AND b.date < a.date "
               "  AND b.available_at <= ? ORDER BY b.date DESC LIMIT 1) AS prev_close "
               "FROM actions a WHERE a.snapshot_id = ? AND a.market = ? "
               "AND a.date > ? AND a.date <= ? AND a.available_at <= ?"
               + _in("a.action", kinds, params) + _in("a.symbol", symbols, params))
        return _adjust.action_factors(self._frame(sql, params))

    def hourly(self, market: str, symbols, start, end, as_of) -> pd.DataFrame:
        """Hourly klines opening on UTC dates [start, end], closed by the end of as_of.

        A single-date read is start = end. Unadjusted (Binance has no actions).
        """
        params: list = [self.snapshot_id, _market(market), f"{iso_date(start)}T",
                        end_of_day(iso_date(end)), end_of_day(iso_date(as_of))]
        sql = ("SELECT market, symbol, ts, open, high, low, close, volume, quote_volume, "
               "available_at FROM bars_hourly WHERE snapshot_id = ? AND market = ? "
               "AND ts >= ? AND ts <= ? AND available_at <= ?"
               + _in("symbol", _symbols_arg(symbols), params) + " ORDER BY symbol, ts")
        return self._frame(sql, params)

    # ------------------------------------------------------- reference data
    def symbols(self, market: str, symbols, as_of) -> pd.DataFrame:
        """Symbol attributes for symbols known as-of (available_at = first listing).

        Attributes are the vendor's current values. `sector` is the one
        allowlisted non-point-in-time input (spec/04; NON_PIT_ALLOWLIST).
        """
        params: list = [self.snapshot_id, _market(market), iso_date(as_of)]
        sql = (f"SELECT {', '.join(SYMBOL_ATTRIBUTES)} FROM symbols "
               "WHERE snapshot_id = ? AND market = ? AND available_at <= ?"
               + _in("symbol", _symbols_arg(symbols), params) + " ORDER BY symbol")
        return self._frame(sql, params)

    def actions(self, market: str, symbols, start, end, as_of,
                kinds: Sequence[str] | None = None) -> pd.DataFrame:
        params: list = [self.snapshot_id, _market(market), iso_date(start), iso_date(end),
                        iso_date(as_of)]
        sql = ("SELECT market, symbol, date, action, value, ticker, contraticker, "
               "contraname, available_at FROM actions WHERE snapshot_id = ? AND market = ? "
               "AND date >= ? AND date <= ? AND available_at <= ?"
               + _in("action", kinds, params) + _in("symbol", _symbols_arg(symbols), params)
               + " ORDER BY symbol, date, action")
        return self._frame(sql, params)

    def listing(self, market: str, symbols, start, end, as_of) -> pd.DataFrame:
        """Listing events dated in [start, end], known as-of."""
        params: list = [self.snapshot_id, _market(market), iso_date(start), iso_date(end),
                        iso_date(as_of)]
        sql = ("SELECT market, symbol, event, date, reason, exchange, source, available_at "
               "FROM listing WHERE snapshot_id = ? AND market = ? AND date >= ? "
               "AND date <= ? AND available_at <= ?"
               + _in("symbol", _symbols_arg(symbols), params) + " ORDER BY symbol, date, event")
        return self._frame(sql, params)

    def listed(self, market: str, date, as_of) -> pd.DataFrame:
        """Symbols listed on `date`, from the listing events known as-of.

        spec/02 Store: listed on D = a `listed` event on or before D and no
        `delisted` event on or before D. One row per symbol: its latest listing
        event on or before D.
        """
        d, a = iso_date(date), iso_date(as_of)
        params = [self.snapshot_id, _market(market), d, a, d, a]
        sql = ("SELECT l.market, l.symbol, MAX(l.date) AS date, MAX(l.available_at) AS available_at "
               "FROM listing l WHERE l.snapshot_id = ? AND l.market = ? AND l.event = 'listed' "
               "AND l.date <= ? AND l.available_at <= ? AND NOT EXISTS ("
               " SELECT 1 FROM listing x WHERE x.snapshot_id = l.snapshot_id "
               " AND x.market = l.market AND x.symbol = l.symbol AND x.event = 'delisted' "
               " AND x.date <= ? AND x.available_at <= ?) "
               "GROUP BY l.market, l.symbol ORDER BY l.symbol")
        return self._frame(sql, params)

    def exchange_on(self, market: str, symbols, date, as_of) -> pd.DataFrame:
        """Point-in-time exchange for eligibility (spec/01 Eligibility: "the
        exchange on D is taken from the most recent ACTIONS listing or
        exchange-change event dated on or before D, and from TICKERS `exchange`
        where ACTIONS carries none").

        One row per symbol known as-of `as_of`: `exchange`, `source` (`actions`
        when a `listing` row (`listed` or `delisted`, both carry the exchange in
        effect at that event) dated on or before `date` is known as-of `as_of`,
        else `tickers_fallback` for `symbols.exchange`, the allowlisted current
        value), and `available_at` (that event's, or the symbol's first-listing
        date for the fallback).
        """
        d, a = iso_date(date), iso_date(as_of)
        m = _market(market)
        syms = _symbols_arg(symbols)

        params: list = [self.snapshot_id, m, a, d]
        events = self._frame(
            "SELECT symbol, date, exchange, available_at FROM listing "
            "WHERE snapshot_id = ? AND market = ? AND available_at <= ? AND date <= ? "
            "AND source = 'actions' AND exchange IS NOT NULL"
            + _in("symbol", syms, params) + " ORDER BY symbol, date", params)
        latest = (events.sort_values("date").groupby("symbol", as_index=False).last()
                 if not events.empty else events)

        base_params: list = [self.snapshot_id, m, a]
        base = self._frame(
            "SELECT market, symbol, exchange, available_at FROM symbols "
            "WHERE snapshot_id = ? AND market = ? AND available_at <= ?"
            + _in("symbol", syms, base_params) + " ORDER BY symbol", base_params)

        if latest.empty:
            out = base.copy()
            out["source"] = "tickers_fallback"
            return out[["market", "symbol", "exchange", "source", "available_at"]]

        merged = base.merge(latest[["symbol", "exchange", "available_at"]], on="symbol",
                            how="left", suffixes=("_fallback", "_actions"))
        has_event = merged["exchange_actions"].notna()
        merged["exchange"] = merged["exchange_actions"].where(has_event, merged["exchange_fallback"])
        merged["available_at"] = merged["available_at_actions"].where(
            has_event, merged["available_at_fallback"])
        merged["source"] = pd.Series("actions", index=merged.index).where(has_event, "tickers_fallback")
        return merged[["market", "symbol", "exchange", "source", "available_at"]]

    def marketcap(self, market: str, symbols, start, end, as_of) -> pd.DataFrame:
        params: list = [self.snapshot_id, _market(market), iso_date(start), iso_date(end),
                        iso_date(as_of)]
        sql = ("SELECT market, symbol, date, marketcap, available_at FROM marketcap "
               "WHERE snapshot_id = ? AND market = ? AND date >= ? AND date <= ? "
               "AND available_at <= ?"
               + _in("symbol", _symbols_arg(symbols), params) + " ORDER BY symbol, date")
        return self._frame(sql, params)

    def events(self, market: str, symbols, start, end, as_of) -> pd.DataFrame:
        """EVENTS rows with filing_date in [start, end], known as-of.

        `available_at` is the next NYSE session after the filing date, or the filing
        date when acceptance was before 16:00 ET (spec/04 `filing_2d`).
        """
        params: list = [self.snapshot_id, _market(market), iso_date(start), iso_date(end),
                        iso_date(as_of)]
        sql = ("SELECT market, symbol, filing_date, eventcodes, available_at FROM events "
               "WHERE snapshot_id = ? AND market = ? AND filing_date >= ? "
               "AND filing_date <= ? AND available_at <= ?"
               + _in("symbol", _symbols_arg(symbols), params) + " ORDER BY symbol, filing_date")
        return self._frame(sql, params)

    def calendar(self, calendar_name: str, start, end, as_of) -> pd.DataFrame:
        """Sessions of `calendar_name` ('nyse' or 'utc') in [start, end], known as-of.

        Lanes map to calendars through `harness.store.calendar.calendar_for_lane`.
        """
        if calendar_name not in CALENDARS:
            raise ValueError(f"calendar must be one of {CALENDARS}, got {calendar_name!r}")
        params = [self.snapshot_id, calendar_name, iso_date(start), iso_date(end),
                  iso_date(as_of)]
        return self._frame(
            "SELECT calendar, date, available_at FROM calendar WHERE snapshot_id = ? "
            "AND calendar = ? AND date >= ? AND date <= ? AND available_at <= ? "
            "ORDER BY date", params)

    def lane_membership(self, lane: str, start, end, as_of) -> pd.DataFrame:
        params = [self.snapshot_id, lane, iso_date(start), iso_date(end), iso_date(as_of)]
        return self._frame(
            "SELECT lane, market, symbol, date, screen_values, available_at "
            "FROM lane_membership WHERE snapshot_id = ? AND lane = ? AND date >= ? "
            "AND date <= ? AND available_at <= ? ORDER BY date, symbol", params)

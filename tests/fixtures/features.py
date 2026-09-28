"""Synthetic panels for the feature-builder tests (issue 8; spec/04).

Each builder writes a small, self-contained store — no dependency on
`tests/fixtures/store.py`, per the issue brief ("extend `tests/fixtures/store.py`
only through a new fixture module"). Bars are handed in explicitly so a test's
expected values can be computed by direct arithmetic in the test itself, not by
calling `harness.features`.
"""

from __future__ import annotations

import sqlite3

import pandas as pd

from harness.store import (build_nyse_calendar, build_utc_calendar, connect,
                           register_snapshot, upsert)

EQ = "us_equity"
CX = "binance_spot"
SNAPSHOT = "feat-a"


def nyse_sessions(n: int, end: str = "2021-12-31") -> list[str]:
    """`n` consecutive NYSE (weekday) sessions ending on `end`."""
    return [d.strftime("%Y-%m-%d") for d in pd.bdate_range(end=end, periods=n)]


def utc_sessions(n: int, end: str = "2021-12-31") -> list[str]:
    """`n` consecutive UTC calendar days ending on `end`."""
    return [d.strftime("%Y-%m-%d") for d in pd.date_range(end=end, periods=n, freq="D")]


def _bar_row(market: str, symbol: str, date: str, b: dict) -> dict:
    dollar_volume = b.get("dollar_volume", b["close"] * b["volume"])
    return dict(market=market, symbol=symbol, date=date, open=b["open"], high=b["high"],
               low=b["low"], close=b["close"], volume=b["volume"],
               dollar_volume=dollar_volume, available_at=date)


def build_equity_store(bars: dict[str, dict[str, dict]], sectors: dict[str, str] | None = None,
                       events: list[dict] | None = None, snapshot_id: str = SNAPSHOT,
                       conn: sqlite3.Connection | None = None) -> sqlite3.Connection:
    """A store with one or more `us_equity` symbols and the `nyse` calendar.

    `bars`: symbol -> {date -> {open, high, low, close, volume[, dollar_volume]}}.
    `events`: rows of dict(symbol, filing_date, available_at, eventcodes).
    The `nyse` calendar is built from exactly the union of dates in `bars`, so a
    test's session count is exactly what it wrote (no implicit holidays).
    """
    sectors = sectors or {}
    conn = conn if conn is not None else connect(":memory:")
    register_snapshot(conn, snapshot_id, "2021-12-31T00:00:00Z", 1, {"synthetic": True})
    all_dates = sorted({d for sym_bars in bars.values() for d in sym_bars})
    upsert(conn, "symbols", snapshot_id, [
        dict(market=EQ, symbol=sym, ticker=sym, name=sym, category="Domestic Common Stock",
            exchange="NYSE", sector=sectors.get(sym, "Industrials"), available_at=all_dates[0])
        for sym in bars])
    rows = [_bar_row(EQ, sym, d, b) for sym, sym_bars in bars.items() for d, b in sym_bars.items()]
    upsert(conn, "bars_daily", snapshot_id, rows)
    build_nyse_calendar(conn, snapshot_id)
    if events:
        upsert(conn, "events", snapshot_id,
              [dict(market=EQ, eventcodes="99", **e) if "eventcodes" not in e
               else dict(market=EQ, **e) for e in events])
    return conn


def build_crypto_store(bars: dict[str, dict[str, dict]], snapshot_id: str = SNAPSHOT,
                       conn: sqlite3.Connection | None = None) -> sqlite3.Connection:
    """A store with one or more `binance_spot` symbols and the `utc` calendar."""
    conn = conn if conn is not None else connect(":memory:")
    register_snapshot(conn, snapshot_id, "2021-12-31T00:00:00Z", 1, {"synthetic": True})
    all_dates = sorted({d for sym_bars in bars.values() for d in sym_bars})
    upsert(conn, "symbols", snapshot_id, [
        dict(market=CX, symbol=sym, base=sym[:-4], quote="USDT", available_at=all_dates[0])
        for sym in bars])
    rows = [_bar_row(CX, sym, d, b) for sym, sym_bars in bars.items() for d, b in sym_bars.items()]
    upsert(conn, "bars_daily", snapshot_id, rows)
    build_utc_calendar(conn, snapshot_id, all_dates[0], all_dates[-1])
    return conn


def flat_bar(close: float, half_range: float = 1.0, volume: float = 1_000.0) -> dict:
    """A bar with `close` at the midpoint of [close - half_range, close + half_range]."""
    return dict(open=close, high=close + half_range, low=close - half_range, close=close,
               volume=volume)


def all_eligible(symbols, dates) -> pd.DataFrame:
    """An `eligible` frame naming every symbol eligible on every date.

    `build_features` requires `eligible` for equity lanes (spec/01); most
    feature tests aren't exercising `sector_rel_ret_1`'s eligibility screen at
    all, so this is the "everyone is eligible" frame for them to pass through.
    """
    if isinstance(symbols, str):
        symbols = [symbols]
    return pd.DataFrame([(d, s) for d in dates for s in symbols], columns=["date", "symbol"])

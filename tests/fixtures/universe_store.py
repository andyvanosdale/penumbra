"""Synthetic point-in-time store for `harness.universe` tests (issue 6).

Extends the patterns in `tests/fixtures/store.py` (calendar, symbols, bars,
actions, listing, marketcap) without editing that shared fixture: these tests
need several years of continuous daily bars per symbol to exercise the 250-day
completeness rule and the 20-day windows, which the shared fixture's one month
of data can't cover. Every helper takes an explicit `snapshot_id` so a test can
build more than one store (e.g. the invariance test's perturbed copy).
"""

from __future__ import annotations

import math
import sqlite3

import pandas as pd

from harness.store import build_nyse_calendar, connect, register_snapshot, upsert

EQ = "us_equity"
SNAPSHOT = "universe-snap"

# Four and a half years of weekdays: room for a 250-session lookback plus a
# wide buffer on both sides of any date a test picks.
CAL_START, CAL_END = "2017-01-02", "2021-06-30"

DEFAULT_ANNUAL_VOL = 0.60             # comfortably above the 40% vol floor
DEFAULT_DOLLAR_VOLUME = 2_000_000.0   # comfortably above the $500k liquidity floor
DEFAULT_MARKETCAP = 500_000_000.0     # comfortably below the $2B smallcap ceiling
DEFAULT_LISTED = "2010-01-04"         # well before CAL_START


def trading_days(start: str = CAL_START, end: str = CAL_END) -> list[str]:
    return [d.strftime("%Y-%m-%d") for d in pd.bdate_range(start, end)]


TRADING_DAYS = trading_days()
# A date comfortably past the 250-session lookback, with hundreds of sessions
# to spare on both sides for delisting, invariance and windowing tests.
D = TRADING_DAYS[300]


def new_store(snapshot_id: str = SNAPSHOT) -> sqlite3.Connection:
    conn = connect(":memory:")
    register_snapshot(conn, snapshot_id, "2021-07-01T00:00:00Z", 0,
                      {"snapshot_id": snapshot_id, "synthetic": True})
    return conn


def finalize(conn: sqlite3.Connection, snapshot_id: str = SNAPSHOT) -> sqlite3.Connection:
    """Build the nyse calendar; call once every symbol's bars are written."""
    build_nyse_calendar(conn, snapshot_id)
    return conn


def add_symbol(conn, symbol: str, *, category: str = "Domestic Common Stock",
               exchange: str = "NASDAQ", sector: str = "Technology",
               listed: str = DEFAULT_LISTED, delisted: str | None = None,
               delist_reason: str = "voluntarydelisting",
               snapshot_id: str = SNAPSHOT) -> None:
    upsert(conn, "symbols", snapshot_id, [dict(
        market=EQ, symbol=symbol, ticker=symbol, name=f"{symbol} Inc", category=category,
        exchange=exchange, sector=sector, available_at=listed)])
    events = [dict(market=EQ, symbol=symbol, event="listed", date=listed, source="tickers",
                   available_at=listed)]
    if delisted:
        events.append(dict(market=EQ, symbol=symbol, event="delisted", date=delisted,
                           reason=delist_reason, exchange=exchange, source="actions",
                           available_at=delisted))
        upsert(conn, "actions", snapshot_id, [dict(
            market=EQ, symbol=symbol, date=delisted, action=delist_reason, ticker=symbol,
            available_at=delisted)])
    upsert(conn, "listing", snapshot_id, events)


def price_path(start_price: float, n: int, daily_log_vol: float) -> list[float]:
    """A price series alternating +/-`daily_log_vol` log returns from `start_price`.

    Its trailing sample std of log returns over any window is close to
    `daily_log_vol` (exact for an even-length window), which makes the
    annualized realized-vol screen deterministic and controllable in tests.
    """
    prices = [start_price]
    for i in range(n - 1):
        r = daily_log_vol if i % 2 == 0 else -daily_log_vol
        prices.append(prices[-1] * math.exp(r))
    return prices


def add_bars(conn, symbol: str, dates: list[str], closes: list[float],
            dollar_volumes: list[float] | None = None, snapshot_id: str = SNAPSHOT) -> None:
    if dollar_volumes is None:
        dollar_volumes = [DEFAULT_DOLLAR_VOLUME] * len(dates)
    rows = []
    for d, c, dv in zip(dates, closes, dollar_volumes):
        v = dv / c
        rows.append(dict(market=EQ, symbol=symbol, date=d, open=c, high=c, low=c, close=c,
                         volume=v, dollar_volume=dv, available_at=d))
    upsert(conn, "bars_daily", snapshot_id, rows)


def add_marketcap(conn, symbol: str, dates: list[str], values: list[float | None],
                  snapshot_id: str = SNAPSHOT) -> None:
    rows = [dict(market=EQ, symbol=symbol, date=d, marketcap=v, available_at=d)
           for d, v in zip(dates, values) if v is not None]
    if rows:
        upsert(conn, "marketcap", snapshot_id, rows)


def add_split(conn, symbol: str, date: str, ratio: float, snapshot_id: str = SNAPSHOT) -> None:
    upsert(conn, "actions", snapshot_id, [dict(
        market=EQ, symbol=symbol, date=date, action="split", value=ratio, ticker=symbol,
        available_at=date)])


def add_eligible_equity(conn, symbol: str, *, start: str = CAL_START, end: str = CAL_END,
                        start_price: float = 50.0, annual_vol: float = DEFAULT_ANNUAL_VOL,
                        dollar_volume: float = DEFAULT_DOLLAR_VOLUME,
                        marketcap: float | None = DEFAULT_MARKETCAP,
                        listed: str = DEFAULT_LISTED, delisted: str | None = None,
                        category: str = "Domestic Common Stock", exchange: str = "NASDAQ",
                        snapshot_id: str = SNAPSHOT) -> list[str]:
    """A fully eligible candidate: full history, high vol, ample liquidity, a
    price well above the floor, and a market cap under the smallcap ceiling.

    Returns the symbol's trading-day dates (truncated at `delisted`, if given),
    so a caller can index into them.
    """
    dates = trading_days(start, end)
    if delisted:
        dates = [d for d in dates if d <= delisted]
    daily_log_vol = annual_vol / math.sqrt(252)
    closes = price_path(start_price, len(dates), daily_log_vol)
    add_symbol(conn, symbol, category=category, exchange=exchange, listed=listed,
              delisted=delisted, snapshot_id=snapshot_id)
    add_bars(conn, symbol, dates, closes, [dollar_volume] * len(dates), snapshot_id=snapshot_id)
    if marketcap is not None:
        add_marketcap(conn, symbol, dates, [marketcap] * len(dates), snapshot_id=snapshot_id)
    return dates

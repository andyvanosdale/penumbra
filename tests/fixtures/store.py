"""Reusable synthetic point-in-time store (issue 16).

March 2021, one snapshot per call. Weekdays are NYSE sessions (no holidays in the
synthetic calendar). Contents:

- us_equity 100001: ticker AAA, renamed AAB on 2021-03-15 (one permaticker);
  2-for-1 split with ex-date 2021-03-17.
- us_equity 100002: ticker BBB, cash dividend of 1.00 with ex-date 2021-03-10; an
  EVENTS row filed after the close on Friday 2021-03-12 (available Monday 03-15)
  and one filed on 2021-03-22 before 16:00 ET (available the same day).
- us_equity 100003: ticker CCC on NASDAQ, listed 2021-03-03, delisted 2021-03-24
  with reason `bankruptcyliquidation`.
- DAILY market cap on every equity bar.
- binance_spot BTCUSDT and ETHUSDT: 1d klines on every UTC day, 1h klines
  2021-03-05 (Fri) to 2021-03-08 (Mon), weekends included.
- lane_membership rows for smallcap and crypto; nyse and utc calendars.

Prices are unadjusted. `price_scale` multiplies every price so a second snapshot
can be told apart from the first.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3

import pandas as pd

from harness.store import (build_nyse_calendar, build_utc_calendar, connect,
                           next_session, register_snapshot, upsert)

SNAPSHOT = "snap-a"
START, END = "2021-03-01", "2021-03-31"
HOURLY_START, HOURLY_END = "2021-03-05", "2021-03-08"

SPLIT_SYM, SPLIT_DATE, SPLIT_RATIO = "100001", "2021-03-17", 2.0
TICKER_CHANGE_DATE = "2021-03-15"
DIV_SYM, DIV_DATE, DIV_AMOUNT = "100002", "2021-03-10", 1.0
DELIST_SYM, DELIST_LISTED, DELIST_DATE = "100003", "2021-03-03", "2021-03-24"
EVENT_AFTER_CLOSE = ("100002", "2021-03-12", "2021-03-15")   # symbol, filed, available
EVENT_BEFORE_CLOSE = ("100001", "2021-03-22", "2021-03-22")
CRYPTO = ("BTCUSDT", "ETHUSDT")


def weekdays(start: str = START, end: str = END) -> list[str]:
    return [d.strftime("%Y-%m-%d") for d in pd.bdate_range(start, end)]


def days(start: str = START, end: str = END) -> list[str]:
    return [d.strftime("%Y-%m-%d") for d in pd.date_range(start, end, freq="D")]


def unadjusted_close(symbol: str, date: str, price_scale: float = 1.0) -> float:
    i = weekdays().index(date)
    if symbol == SPLIT_SYM:
        c = 100.0 + i
        return price_scale * (c / SPLIT_RATIO if date >= SPLIT_DATE else c)
    if symbol == DIV_SYM:
        return price_scale * (40.0 + 0.1 * i)
    if symbol == DELIST_SYM:
        return price_scale * (5.0 - 0.1 * i)
    raise KeyError(symbol)


def _equity_bars(price_scale: float) -> list[dict]:
    rows = []
    for sym in (SPLIT_SYM, DIV_SYM, DELIST_SYM):
        for d in weekdays():
            if sym == DELIST_SYM and not DELIST_LISTED <= d <= DELIST_DATE:
                continue
            c = unadjusted_close(sym, d, price_scale)
            vol = 1_000_000.0 * (SPLIT_RATIO if sym == SPLIT_SYM and d >= SPLIT_DATE else 1.0)
            # Vendor close is split-adjusted as of the download (after the split).
            vendor = c / SPLIT_RATIO if sym == SPLIT_SYM and d < SPLIT_DATE else c
            rows.append(dict(market="us_equity", symbol=sym, date=d, open=c - 0.5,
                             high=c + 1.0, low=c - 1.0, close=c, volume=vol,
                             dollar_volume=c * vol, close_vendor=vendor,
                             closeadj_vendor=vendor, lastupdated="2021-04-30",
                             available_at=d))
    return rows


def _crypto_daily(price_scale: float) -> list[dict]:
    rows = []
    for k, sym in enumerate(CRYPTO):
        for i, d in enumerate(days()):
            c = price_scale * (50_000.0 if k == 0 else 1_500.0) * (1 + 0.01 * i)
            rows.append(dict(market="binance_spot", symbol=sym, date=d, open=c * 0.99,
                             high=c * 1.02, low=c * 0.97, close=c, volume=1_000.0,
                             dollar_volume=c * 1_000.0, available_at=d))
    return rows


def _crypto_hourly(price_scale: float) -> list[dict]:
    rows = []
    for k, sym in enumerate(CRYPTO):
        base = price_scale * (50_000.0 if k == 0 else 1_500.0)
        for h, ts in enumerate(pd.date_range(HOURLY_START, f"{HOURLY_END} 23:00", freq="h")):
            close_time = ts + pd.Timedelta(hours=1) - pd.Timedelta(milliseconds=1)
            c = base * (1 + 0.001 * h)
            rows.append(dict(market="binance_spot", symbol=sym,
                             ts=ts.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                             open=c, high=c * 1.001, low=c * 0.999, close=c, volume=10.0,
                             quote_volume=c * 10.0,
                             available_at=close_time.strftime("%Y-%m-%dT%H:%M:%S.")
                             + f"{close_time.microsecond // 1000:03d}Z"))
    return rows


def build_store(conn: sqlite3.Connection | None = None, snapshot_id: str = SNAPSHOT,
                price_scale: float = 1.0) -> sqlite3.Connection:
    """Write the synthetic snapshot into `conn` (a new in-memory store if None)."""
    conn = conn if conn is not None else connect(":memory:")
    register_snapshot(conn, snapshot_id, "2021-04-30T00:00:00Z", 7,
                      {"snapshot_id": snapshot_id, "files": [], "synthetic": True})

    upsert(conn, "symbols", snapshot_id, [
        dict(market="us_equity", symbol=SPLIT_SYM, ticker="AAB", name="Alpha Corp",
             category="Domestic Common Stock", exchange="NYSE", sector="Industrials",
             available_at="2015-01-02"),
        dict(market="us_equity", symbol=DIV_SYM, ticker="BBB", name="Beta Inc",
             category="Domestic Common Stock", exchange="NASDAQ", sector="Utilities",
             available_at="2015-01-02"),
        dict(market="us_equity", symbol=DELIST_SYM, ticker="CCC", name="Gamma Ltd",
             category="Domestic Common Stock", exchange="NASDAQ", sector="Energy",
             available_at=DELIST_LISTED),
        *[dict(market="binance_spot", symbol=s, base=s[:-4], quote="USDT",
               available_at=START) for s in CRYPTO],
    ])

    upsert(conn, "bars_daily", snapshot_id, _equity_bars(price_scale) + _crypto_daily(price_scale))
    upsert(conn, "bars_hourly", snapshot_id, _crypto_hourly(price_scale))
    build_nyse_calendar(conn, snapshot_id)
    build_utc_calendar(conn, snapshot_id, START, END)

    upsert(conn, "actions", snapshot_id, [
        dict(market="us_equity", symbol=SPLIT_SYM, date=SPLIT_DATE, action="split",
             value=SPLIT_RATIO, ticker="AAB", available_at=SPLIT_DATE),
        dict(market="us_equity", symbol=SPLIT_SYM, date=TICKER_CHANGE_DATE,
             action="tickerchangeto", ticker="AAB", contraticker="AAA",
             available_at=TICKER_CHANGE_DATE),
        dict(market="us_equity", symbol=DIV_SYM, date=DIV_DATE, action="dividend",
             value=DIV_AMOUNT, ticker="BBB", available_at=DIV_DATE),
        dict(market="us_equity", symbol=DELIST_SYM, date=DELIST_DATE,
             action="bankruptcyliquidation", ticker="CCC", available_at=DELIST_DATE),
    ])

    upsert(conn, "listing", snapshot_id, [
        dict(market="us_equity", symbol=SPLIT_SYM, event="listed", date="2015-01-02",
             source="tickers", available_at="2015-01-02"),
        dict(market="us_equity", symbol=DIV_SYM, event="listed", date="2015-01-02",
             source="tickers", available_at="2015-01-02"),
        dict(market="us_equity", symbol=DELIST_SYM, event="listed", date=DELIST_LISTED,
             source="actions", available_at=DELIST_LISTED),
        dict(market="us_equity", symbol=DELIST_SYM, event="delisted", date=DELIST_DATE,
             reason="bankruptcyliquidation", exchange="NASDAQ", source="actions",
             available_at=DELIST_DATE),
        *[dict(market="binance_spot", symbol=s, event="listed", date=START,
               source="klines", available_at=START) for s in CRYPTO],
    ])

    upsert(conn, "marketcap", snapshot_id, [
        dict(market="us_equity", symbol=b["symbol"], date=b["date"],
             marketcap=b["close"] * 10_000_000.0, lastupdated="2021-04-30",
             available_at=b["date"]) for b in _equity_bars(price_scale)])

    events = []
    for (sym, filed, _), codes in ((EVENT_AFTER_CLOSE, "13|81"), (EVENT_BEFORE_CLOSE, "22")):
        # After-close filings (and unknown acceptance time) are available the next
        # NYSE session; known pre-16:00 filings the same day (spec/04 filing_2d).
        available = (filed if (sym, filed) == EVENT_BEFORE_CLOSE[:2]
                     else next_session(conn, snapshot_id, "nyse", filed))
        events.append(dict(market="us_equity", symbol=sym, filing_date=filed,
                           eventcodes=codes, available_at=available))
    upsert(conn, "events", snapshot_id, events)

    membership = [dict(lane="smallcap", market="us_equity", symbol=s, date=d,
                       screen_values=json.dumps({"marketcap": 1e8}), available_at=d)
                  for s in (DIV_SYM, DELIST_SYM) for d in weekdays("2021-03-15", "2021-03-19")]
    membership += [dict(lane="crypto", market="binance_spot", symbol="BTCUSDT", date=d,
                        screen_values=json.dumps({"rank": 1}), available_at=d)
                   for d in days("2021-03-13", "2021-03-19")]
    upsert(conn, "lane_membership", snapshot_id, membership)
    return conn


def as_of_dates() -> list[str]:
    """Every calendar day in the fixture range plus a day either side."""
    before = (dt.date.fromisoformat(START) - dt.timedelta(days=1)).isoformat()
    after = (dt.date.fromisoformat(END) + dt.timedelta(days=1)).isoformat()
    return [before, *days(), after]

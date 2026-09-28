"""Scenario stores for the labeler tests (issue 9), built on `tests/fixtures/store.py`.

`tests/fixtures/store.py` is the canonical synthetic store (a split, a dividend, a
NASDAQ bankruptcy, EVENTS rows, crypto klines); the labeler's corporate-action,
bucket and crypto tests run on it directly. The exit-path tests need precise,
per-session control of one name's bars, which `scenario_store` gives:

- `sessions`: the equity sessions. An anchor symbol carries a bar on every one,
  so the `nyse` calendar (built from any SEP bar, spec/02) has every session even
  when the name under test has none.
- `bars`: {symbol: {date: (open, high, low, close)}}, unadjusted.
- `actions`, `listing`, `events`: rows in the store's shape (docs/store.md).
"""

from __future__ import annotations

import pandas as pd

from harness.store import build_nyse_calendar, connect, register_snapshot, upsert

SNAPSHOT = "snap-labels"
ANCHOR = "999999"
EQ = "us_equity"


def flat(sessions: list[str], price: float = 100.0, half_range: float = 0.5
         ) -> dict[str, tuple[float, float, float, float]]:
    """A bar at `price` on every session: open = close = price, range 2 x half_range."""
    return {d: (price, price + half_range, price - half_range, price) for d in sessions}


def scenario_store(sessions: list[str], bars: dict[str, dict], actions=(), listing=(),
                   events=(), snapshot: str = SNAPSHOT):
    conn = connect(":memory:")
    register_snapshot(conn, snapshot, "2024-12-31T00:00:00Z", 0,
                      {"snapshot_id": snapshot, "files": [], "synthetic": True})
    rows = []
    for sym, by_date in {ANCHOR: flat(sessions, 50.0), **bars}.items():
        for d, (o, h, lo, c) in sorted(by_date.items()):
            rows.append(dict(market=EQ, symbol=sym, date=d, open=o, high=h, low=lo, close=c,
                             volume=100_000.0, dollar_volume=c * 100_000.0, available_at=d))
    upsert(conn, "bars_daily", snapshot, rows)
    build_nyse_calendar(conn, snapshot)
    first = min(sessions)
    listed = [dict(market=EQ, symbol=s, event="listed", date=first, source="tickers",
                   available_at=first) for s in bars]
    upsert(conn, "listing", snapshot, listed + [dict(available_at=r["date"], **r) for r in listing])
    if actions:
        upsert(conn, "actions", snapshot, [dict(available_at=r["date"], **r) for r in actions])
    if events:
        upsert(conn, "events", snapshot, list(events))
    return conn


def sessions_between(start: str, end: str) -> list[str]:
    return [d.strftime("%Y-%m-%d") for d in pd.bdate_range(start, end)]

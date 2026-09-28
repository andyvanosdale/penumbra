"""Synthetic panel for the invariance tests.

This is a small, self-contained generator: GBM closes, an OHLC envelope
consistent with them, volumes, a sparse events frame and a trading calendar
with holidays. Issue 16 (`tests/fixtures/store.py`) is building the real
fixture panel in parallel; this module does not depend on it, and is not
meant to be vendor-shaped the way that one will be.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import numpy as np
import pandas as pd

# A handful of NYSE-shaped holidays across the synthetic date range, so the
# trading calendar has real gaps rather than being a plain weekday range.
HOLIDAYS = frozenset(
    {
        dt.date(2020, 1, 1),
        dt.date(2020, 1, 20),
        dt.date(2020, 2, 17),
        dt.date(2020, 5, 25),
        dt.date(2020, 7, 3),
        dt.date(2020, 9, 7),
        dt.date(2020, 11, 26),
        dt.date(2020, 12, 25),
        dt.date(2021, 1, 1),
        dt.date(2021, 1, 18),
        dt.date(2021, 2, 15),
        dt.date(2021, 5, 31),
        dt.date(2021, 7, 5),
        dt.date(2021, 9, 6),
        dt.date(2021, 11, 25),
        dt.date(2021, 12, 24),
    }
)


def trading_calendar(start: dt.date, end: dt.date, holidays: frozenset[dt.date] = HOLIDAYS) -> list[dt.date]:
    """Weekdays in [start, end] minus `holidays` — a small stand-in for the
    lane's NYSE calendar (spec/02 Trading calendars)."""

    days = []
    d = start
    one = dt.timedelta(days=1)
    while d <= end:
        if d.weekday() < 5 and d not in holidays:
            days.append(d)
        d += one
    return days


def gbm_bars(dates: list[dt.date], *, seed: int, start_price: float = 50.0, mu: float = 0.0002, sigma: float = 0.02) -> pd.DataFrame:
    """OHLCV bars consistent with a GBM close series: high/low/open form a
    plausible envelope around each day's close, volume is independent noise,
    and `dollar_volume` is unadjusted close x volume (spec/04)."""

    rng = np.random.default_rng(seed)
    n = len(dates)
    log_rets = rng.normal(mu, sigma, n)
    close = start_price * np.exp(np.cumsum(log_rets))
    prev_close = np.concatenate([[start_price], close[:-1]])
    open_ = prev_close * np.exp(rng.normal(0.0, sigma * 0.3, n))
    intraday = np.abs(rng.normal(0.0, sigma * 0.5, n))
    high = np.maximum(open_, close) * (1.0 + intraday)
    low = np.minimum(open_, close) * (1.0 - intraday)
    volume = rng.integers(100_000, 5_000_000, n).astype(float)
    return pd.DataFrame(
        {
            "date": dates,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "dollar_volume": close * volume,
        }
    )


def sparse_events(dates: list[dt.date], *, seed: int, rate: float = 0.03) -> pd.DataFrame:
    """A sparse 8-K-style events frame. `available_at` follows spec/02: the
    next lane trading day after the filing date, or the filing date itself
    when a coin flip stands in for "acceptance known to be before 16:00 ET".
    """

    rng = np.random.default_rng(seed)
    rows = []
    for i, d in enumerate(dates):
        if rng.random() < rate:
            before_close = rng.random() < 0.5
            if before_close or i + 1 >= len(dates):
                available_at = d
            else:
                available_at = dates[i + 1]
            rows.append(
                {
                    "filing_date": d,
                    "available_at": available_at,
                    "eventcodes": str(int(rng.integers(1, 99))),
                }
            )
    return pd.DataFrame(rows, columns=["filing_date", "available_at", "eventcodes"])


@dataclass(frozen=True)
class Name:
    lane: str
    symbol: str
    bars: pd.DataFrame
    events: pd.DataFrame


def build_panel(
    *,
    lanes: tuple[str, ...] = ("smallcap", "crypto"),
    names_per_lane: int = 2,
    start: dt.date = dt.date(2020, 1, 1),
    end: dt.date = dt.date(2021, 6, 30),
    seed: int = 0,
) -> list[Name]:
    """A small multi-lane, multi-name synthetic panel sharing one calendar."""

    dates = trading_calendar(start, end)
    names: list[Name] = []
    seed_i = seed
    for lane in lanes:
        for k in range(names_per_lane):
            symbol = f"{lane[:2].upper()}{k}"
            bars = gbm_bars(dates, seed=seed_i)
            events = sparse_events(dates, seed=seed_i + 10_000)
            names.append(Name(lane=lane, symbol=symbol, bars=bars, events=events))
            seed_i += 1
    return names

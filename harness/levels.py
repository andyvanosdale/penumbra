"""Entry levels from as-of data: the target and the signal day's range (spec/05).

spec/05 "Parameters (locked)":

- target level: the mean of the 20 closes ending at the signal day D, fixed for
  the life of the position;
- hard stop level: the entry fill price minus 1.5 x D's (high - low), fixed at
  entry.

Both are known at D's close except the fill price, so this module computes the
target and D's range (`stop_range`) from the as-of-D store and nothing else, and
`hard_stop_level` combines the range with the fill once the labeler has it.

Quarantine: this module reads through `harness.store.reader.AsOfReader` only. It
may not import the oracle or the labeler (tests/test_architecture.py). The exit
invariance test (spec/02 Leakage tests) targets `entry_levels` through a real
store, so a level that read any bar dated after D would fail it.

Prices are in the as-of-D split-and-dividend-adjusted basis (spec/02 Store: fills
and features use that series). The labeler converts later bars into the same
basis (docs/architecture.md "Adjustment", consequence 2), so the levels never
move after entry.
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from config.params import SPEC05
from harness.store.calendar import calendar_for_lane
from harness.store.reader import AsOfReader, iso_date

LANE_MARKET = {"smallcap": "us_equity", "discovered": "us_equity", "crypto": "binance_spot"}

TARGET_WINDOW = SPEC05.target_window_days
STOP_MULTIPLIER = float(SPEC05.hard_stop_range_multiplier)

# Calendar days read back to find the last TARGET_WINDOW sessions: 20 NYSE
# sessions span at most ~30 calendar days, so 60 leaves room for holidays.
_LOOKBACK_CALENDAR_DAYS = 3 * TARGET_WINDOW

LEVEL_COLUMNS = ("symbol", "signal_date", "target_level", "stop_range")


def market_for_lane(lane: str) -> str:
    try:
        return LANE_MARKET[lane]
    except KeyError:
        raise ValueError(f"unknown lane {lane!r}; lanes are {sorted(LANE_MARKET)}") from None


def compute_levels(window: pd.DataFrame, sessions: list[str], signal_date: str
                   ) -> tuple[float, float]:
    """(target_level, stop_range) for one name from its as-of-D bars.

    `window` holds the name's bars in the as-of-D basis dated in `sessions`, the
    last TARGET_WINDOW lane sessions ending at D. A missing bar in the window, or
    no bar on D, gives NaN: the name is ineligible on D (spec/02 Trading
    calendars: no forward fill), so it is never a candidate.
    """
    w = window[window["date"].isin(sessions)].sort_values("date")
    if len(sessions) < TARGET_WINDOW or len(w) != len(sessions) or w["date"].iloc[-1] != signal_date:
        return float("nan"), float("nan")
    target = float(w["close"].mean())
    d = w.iloc[-1]
    return target, float(d["high"] - d["low"])


def hard_stop_level(fill_price: float, stop_range: float) -> float:
    """Entry fill price minus 1.5 x the signal day's range (spec/05), fixed at entry."""
    return float(fill_price) - STOP_MULTIPLIER * float(stop_range)


def entry_levels(reader: AsOfReader, lane: str, symbols, signal_date) -> pd.DataFrame:
    """Target level and signal-day range for `symbols` on D, from as-of-D data only.

    One row per symbol: LEVEL_COLUMNS. Every read is as-of D, so nothing dated
    after D can reach the levels.
    """
    D = iso_date(signal_date)
    market = market_for_lane(lane)
    start = (dt.date.fromisoformat(D) - dt.timedelta(days=_LOOKBACK_CALENDAR_DAYS)).isoformat()
    cal = reader.calendar(calendar_for_lane(lane), start, D, as_of=D)["date"].tolist()
    sessions = cal[-TARGET_WINDOW:]
    syms = [symbols] if isinstance(symbols, str) else [str(s) for s in symbols]
    if sessions:
        bars = reader.panel(market, syms, sessions[0], D, as_of=D, adjust="split_div")
    else:
        bars = pd.DataFrame(columns=["symbol", "date", "open", "high", "low", "close"])
    rows = []
    for s in syms:
        target, rng = compute_levels(bars[bars["symbol"] == s], sessions, D)
        rows.append({"symbol": s, "signal_date": D, "target_level": target, "stop_range": rng})
    out = pd.DataFrame(rows, columns=list(LEVEL_COLUMNS))
    out[["target_level", "stop_range"]] = out[["target_level", "stop_range"]].astype(np.float64)
    return out

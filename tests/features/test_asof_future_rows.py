"""The as-of read (spec/02 Leakage tests, first bullet; issue 8 Acceptance):
no feature reads a row with `available_at` after D.

Proven directly with a store fixture holding future bars and a future EVENTS
row alongside the historical data: `build_features` at D must be unchanged
from a store that never had the future rows at all. See
`test_feature_invariance.py` for the general-purpose invariance check
(`harness.testing.assert_feature_invariance`, issue 18).
"""

from __future__ import annotations

import math

import pandas as pd
import pytest

from harness.features import build_features
from harness.store import AsOfReader
from tests.fixtures.features import all_eligible, build_equity_store, nyse_sessions

pytestmark = pytest.mark.leakage

N_BEFORE_D = 260
N_AFTER_D = 5


def _wave_bar(i: int) -> dict:
    close = 100.0 + 5.0 * math.sin(i / 6.0) + 0.05 * i
    return dict(open=close * 0.999, high=close * 1.01 + 0.3, low=close * 0.99 - 0.3,
               close=close, volume=1_000.0 + i, dollar_volume=close * (1_000.0 + i))


def _build(dates: list[str], d: str, events: list[dict], include_future: bool):
    cutoff_dates = dates if include_future else [x for x in dates if x <= d]
    bars = {"A": {x: _wave_bar(i) for i, x in enumerate(dates) if x in cutoff_dates},
           "B": {x: _wave_bar(i + 3) for i, x in enumerate(dates) if x in cutoff_dates}}
    cutoff_events = events if include_future else [e for e in events if e["available_at"] <= d]
    conn = build_equity_store(bars, sectors={"A": "Tech", "B": "Tech"}, events=cutoff_events)
    return AsOfReader(conn, "feat-a")


def test_features_at_D_are_unchanged_by_future_bars_and_events():
    dates = nyse_sessions(N_BEFORE_D + N_AFTER_D)
    d = dates[N_BEFORE_D - 1]                 # D: leaves N_AFTER_D future sessions
    d_plus_1, d_plus_2 = dates[N_BEFORE_D], dates[N_BEFORE_D + 1]

    events = [
        dict(symbol="A", filing_date=dates[N_BEFORE_D - 2], available_at=dates[N_BEFORE_D - 2]),
        # Future events: filed after D, and one whose availability lands on D+1/D+2.
        dict(symbol="A", filing_date=d_plus_1, available_at=d_plus_1),
        dict(symbol="B", filing_date=d_plus_2, available_at=d_plus_2),
    ]

    eligible = all_eligible(["A", "B"], [d])
    with_future = build_features(_build(dates, d, events, include_future=True), "smallcap", [d],
                                 eligible=eligible)
    without_future = build_features(_build(dates, d, events, include_future=False), "smallcap",
                                    [d], eligible=eligible)

    pd.testing.assert_frame_equal(with_future.reset_index(drop=True),
                                  without_future.reset_index(drop=True))

    # The fixture must actually exercise the guard: real, non-NaN feature values.
    assert with_future.drop(columns=["lane", "market", "symbol", "date"]).notna().to_numpy().any()

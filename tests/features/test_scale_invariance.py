"""Scale invariance (docs/architecture.md "Adjustment", consequence 1).

For any D inside the panel, the panel-end-adjusted series equals the as-of-D
series times a constant on every bar t <= D. Every spec/04 feature is a ratio,
a log return, or a rank, so multiplying every price (and its dollar volume) by
a constant must leave every feature at D unchanged. This is the test issue 8
requires: "multiply every bar before D by a constant, and show every feature at
D is unchanged."
"""

from __future__ import annotations

import math

import pandas as pd

from harness.features import FEATURE_COLUMNS, build_features
from harness.store import AsOfReader
from tests.fixtures.features import all_eligible, build_equity_store, nyse_sessions

N_SESSIONS = 260


def _wave_bar(i: int, scale: float = 1.0) -> dict:
    close = scale * (100.0 + 5.0 * math.sin(i / 6.0) + 0.05 * i)
    high = close * 1.01 + 0.3 * scale
    low = close * 0.99 - 0.3 * scale
    open_ = scale * (100.0 + 5.0 * math.sin((i - 0.5) / 6.0) + 0.05 * (i - 0.5))
    volume = 1_000.0 + i  # unadjusted volume: not scaled by price
    return dict(open=open_, high=high, low=low, close=close, volume=volume,
               dollar_volume=close * volume)


def _panel(dates: list[str], symbol_phase: float, scale: float) -> dict[str, dict]:
    return {d: _wave_bar(i + symbol_phase, scale) for i, d in enumerate(dates)}


def _build(scale: float, dates: list[str]):
    bars = {
        "A": _panel(dates, 0.0, scale),
        "B": _panel(dates, 3.0, scale),
    }
    sectors = {"A": "Tech", "B": "Tech"}
    conn = build_equity_store(
        bars, sectors=sectors, snapshot_id="feat-a",
        events=[dict(symbol="A", filing_date=dates[-2], available_at=dates[-2])])
    return AsOfReader(conn, "feat-a")


def test_scale_invariance_of_every_feature():
    dates = nyse_sessions(N_SESSIONS)
    eval_dates = dates[-5:]

    eligible = all_eligible(["A", "B"], eval_dates)
    reader_1x = _build(1.0, dates)
    out_1x = build_features(reader_1x, "smallcap", eval_dates, eligible=eligible)

    reader_scaled = _build(3.7, dates)
    out_scaled = build_features(reader_scaled, "smallcap", eval_dates, eligible=eligible)

    pd.testing.assert_frame_equal(
        out_1x.drop(columns=["ret_per_vol"]).reset_index(drop=True),
        out_scaled.drop(columns=["ret_per_vol"]).reset_index(drop=True),
        check_exact=False, rtol=1e-9, atol=1e-12)
    # ret_per_vol divides by (vol_pctl_250 + 0.01); vol_pctl_250 itself is exactly
    # scale-invariant (checked above), so ret_per_vol is too.
    pd.testing.assert_series_equal(
        out_1x["ret_per_vol"].reset_index(drop=True),
        out_scaled["ret_per_vol"].reset_index(drop=True),
        check_exact=False, rtol=1e-9, atol=1e-12)

    # Sanity: the fixture actually produced real (non-NaN) values for every
    # feature, or the invariance check above would be vacuous.
    for col in FEATURE_COLUMNS:
        assert out_1x[col].notna().any(), f"{col} was NaN everywhere; fixture too short"

"""cost_report: per-lane, per-year cost reporting helpers (spec/06 Costs,
"Acceptance")."""

from __future__ import annotations

import math

import pandas as pd

from harness.costs import cost_report


def _trades() -> pd.DataFrame:
    return pd.DataFrame(
        [
            dict(lane="smallcap", symbol="A", entry_date="2024-01-10", leg="entry",
                 notional=10_000.0, spread=0.0025, slippage=0.001, fee=0.0, floor_bound=True),
            dict(lane="smallcap", symbol="A", entry_date="2024-01-10", leg="exit_target",
                 notional=10_000.0, spread=0.002, slippage=0.0015, fee=0.0, floor_bound=False),
            dict(lane="smallcap", symbol="B", entry_date="2024-06-01", leg="entry",
                 notional=10_000.0, spread=0.003, slippage=0.0005, fee=0.0, floor_bound=True),
            dict(lane="smallcap", symbol="B", entry_date="2024-06-01", leg="exit_stop",
                 notional=10_000.0, spread=0.0025, slippage=0.002, fee=0.0, floor_bound=True),
            dict(lane="crypto", symbol="BTCUSDT", entry_date="2024-03-01", leg="entry",
                 notional=10_000.0, spread=0.001, slippage=0.001, fee=0.001, floor_bound=False),
            dict(lane="crypto", symbol="BTCUSDT", entry_date="2024-03-01", leg="exit_time",
                 notional=10_000.0, spread=0.0005, slippage=0.0008, fee=0.001, floor_bound=True),
        ]
    )


def test_floor_bound_share_per_lane_year():
    report = cost_report(_trades())
    share = report["floor_bound_share"].set_index(["lane", "year"])["floor_bound_share"]
    assert math.isclose(share.loc[("smallcap", 2024)], 0.75, rel_tol=1e-9)  # 3 of 4 legs
    assert math.isclose(share.loc[("crypto", 2024)], 0.5, rel_tol=1e-9)


def test_mean_cost_bps_by_leg_label():
    report = cost_report(_trades())
    by_leg = report["mean_cost_bps_by_leg"].set_index(["lane", "year", "leg_label"])["mean_cost_bps"]
    expected_entry_bps = (0.0025 + 0.001) * 10_000.0
    assert math.isclose(by_leg.loc[("smallcap", 2024, "entry")], expected_entry_bps, rel_tol=1e-9)
    assert ("smallcap", 2024, "stop") in by_leg.index
    assert ("crypto", 2024, "time_stop") in by_leg.index


def test_component_sums_are_currency():
    report = cost_report(_trades())
    sums = report["component_sums"].set_index(["lane", "year"])
    # All four smallcap legs (symbol A's two, symbol B's two) fall in 2024.
    expected_spread_cost = (0.0025 + 0.002 + 0.003 + 0.0025) * 10_000.0
    assert math.isclose(sums.loc[("smallcap", 2024), "spread_cost"], expected_spread_cost, rel_tol=1e-9)


def test_missing_column_rejected():
    import pytest

    bad = _trades().drop(columns=["notional"])
    with pytest.raises(ValueError):
        cost_report(bad)

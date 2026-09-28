"""`dist_52w_low`, `dd_from_20d_high`, `close_loc`, `gap`, `range_rel_20`,
`ret_per_vol`, `close_loc_chg_2` (spec/04 Features)."""

from __future__ import annotations

import statistics

import pytest

from harness.features import build_features
from harness.store import AsOfReader
from tests.fixtures.features import build_equity_store, nyse_sessions


def _bars(rows: list[dict]) -> dict[str, dict]:
    dates = nyse_sessions(len(rows))
    return {d: r for d, r in zip(dates, rows)}


def test_dist_52w_low():
    # 250 sessions: a known low on day 100 (index), a higher low elsewhere, D's
    # close known.
    rows = [dict(open=100.0, high=101.0, low=90.0, close=100.0, volume=1.0) for _ in range(250)]
    rows[100]["low"] = 50.0          # the minimum of the 250-day window
    rows[-1]["close"] = 80.0         # D's close
    conn = build_equity_store({"900001": _bars(rows)})
    reader = AsOfReader(conn, "feat-a")
    dates = nyse_sessions(250)

    out = build_features(reader, "smallcap", [dates[-1]])
    assert out.loc[0, "dist_52w_low"] == pytest.approx(80.0 / 50.0 - 1.0)


def test_dd_from_20d_high():
    rows = [dict(open=100.0, high=100.0, low=90.0, close=95.0, volume=1.0) for _ in range(20)]
    rows[5]["high"] = 130.0          # the max of the 20-day window
    rows[-1]["close"] = 100.0        # D's close
    conn = build_equity_store({"900001": _bars(rows)})
    reader = AsOfReader(conn, "feat-a")
    dates = nyse_sessions(20)

    out = build_features(reader, "smallcap", [dates[-1]])
    assert out.loc[0, "dd_from_20d_high"] == pytest.approx(100.0 / 130.0 - 1.0)


def test_close_loc_normal_and_flat_bar():
    rows = [
        dict(open=100.0, high=110.0, low=90.0, close=104.0, volume=1.0),  # normal
        dict(open=100.0, high=100.0, low=100.0, close=100.0, volume=1.0),  # high == low
    ]
    conn = build_equity_store({"900001": _bars(rows)})
    reader = AsOfReader(conn, "feat-a")
    dates = nyse_sessions(2)

    out = build_features(reader, "smallcap", dates)
    assert out.loc[0, "close_loc"] == pytest.approx((104.0 - 90.0) / (110.0 - 90.0))
    assert out.loc[1, "close_loc"] == pytest.approx(0.5)


def test_gap():
    rows = [
        dict(open=100.0, high=101.0, low=99.0, close=100.0, volume=1.0),
        dict(open=103.0, high=105.0, low=102.0, close=104.0, volume=1.0),
    ]
    conn = build_equity_store({"900001": _bars(rows)})
    reader = AsOfReader(conn, "feat-a")
    dates = nyse_sessions(2)

    out = build_features(reader, "smallcap", [dates[-1]])
    assert out.loc[0, "gap"] == pytest.approx(103.0 / 100.0 - 1.0)


def test_range_rel_20():
    ranges = [2.0] * 19 + [8.0]  # 19 days of range 2, D's range is 8
    rows = [dict(open=100.0, high=100.0 + r / 2, low=100.0 - r / 2, close=100.0, volume=1.0)
           for r in ranges]
    conn = build_equity_store({"900001": _bars(rows)})
    reader = AsOfReader(conn, "feat-a")
    dates = nyse_sessions(20)

    out = build_features(reader, "smallcap", [dates[-1]])
    expected = ranges[-1] / statistics.mean(ranges)
    assert out.loc[0, "range_rel_20"] == pytest.approx(expected)


def test_ret_per_vol():
    # 250 sessions of flat dollar volume except D, which is the strict max
    # (vol_pctl_250 = 1.0); D's simple return is known.
    rows = [dict(open=100.0, high=101.0, low=99.0, close=100.0, volume=1.0,
                dollar_volume=1.0) for _ in range(249)]
    rows.append(dict(open=100.0, high=112.0, low=99.0, close=110.0, volume=1.0,
                     dollar_volume=2.0))
    conn = build_equity_store({"900001": _bars(rows)})
    reader = AsOfReader(conn, "feat-a")
    dates = nyse_sessions(250)

    out = build_features(reader, "smallcap", [dates[-1]])
    simple_ret = 110.0 / 100.0 - 1.0
    vol_pctl = 1.0  # strict max of the window, no ties
    assert out.loc[0, "vol_pctl_250"] == pytest.approx(vol_pctl)
    assert out.loc[0, "ret_per_vol"] == pytest.approx(simple_ret / (vol_pctl + 0.01))


def test_close_loc_chg_2():
    rows = [
        dict(open=100.0, high=110.0, low=90.0, close=100.0, volume=1.0),  # D-2: loc = 0.5
        dict(open=100.0, high=101.0, low=99.0, close=100.0, volume=1.0),  # D-1: irrelevant
        dict(open=100.0, high=120.0, low=80.0, close=116.0, volume=1.0),  # D: loc = 0.9
    ]
    conn = build_equity_store({"900001": _bars(rows)})
    reader = AsOfReader(conn, "feat-a")
    dates = nyse_sessions(3)

    out = build_features(reader, "smallcap", [dates[-1]])
    loc_d2 = (100.0 - 90.0) / (110.0 - 90.0)
    loc_d = (116.0 - 80.0) / (120.0 - 80.0)
    assert out.loc[0, "close_loc_chg_2"] == pytest.approx(loc_d - loc_d2)

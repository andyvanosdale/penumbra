"""`ret_1`, `rvol_20`, `rvol_20_prev`, `shock` (spec/04 Features).

Expected values are computed here with `math.log` and `statistics.stdev` directly
on the fixture's closing prices, independent of `harness.features`'s rolling
implementation.
"""

from __future__ import annotations

import math
import statistics

import pytest

from harness.features import build_features
from harness.store import AsOfReader
from tests.fixtures.features import all_eligible, build_equity_store, flat_bar, nyse_sessions

ANN = math.sqrt(252.0)


def _panel(closes: list[float]) -> dict[str, dict]:
    return {d: flat_bar(c) for d, c in zip(nyse_sessions(len(closes)), closes)}


def test_ret_1_is_the_one_day_log_return():
    closes = [100.0, 110.0]
    dates = nyse_sessions(2)
    conn = build_equity_store({"900001": _panel(closes)})
    reader = AsOfReader(conn, "feat-a")

    out = build_features(reader, "smallcap", [dates[-1]],
                        eligible=all_eligible("900001", [dates[-1]]))
    expected = math.log(110.0 / 100.0)
    assert out.loc[0, "ret_1"] == pytest.approx(expected)


def test_rvol_20_and_rvol_20_prev():
    # 20 alternating +a/-a log returns (days s1..s20, i.e. D-20..D-1), then a
    # distinct 21st return on D. Sessions: s0 (base) .. s20 (=D-1), s21 (=D).
    a = 0.02
    r_last = -0.03
    n_alt = 20
    log_rets = [a if k % 2 == 1 else -a for k in range(1, n_alt + 1)] + [r_last]
    closes = [100.0]
    for r in log_rets:
        closes.append(closes[-1] * math.exp(r))
    dates = nyse_sessions(len(closes))
    conn = build_equity_store({"900001": _panel(closes)})
    reader = AsOfReader(conn, "feat-a")

    out = build_features(reader, "smallcap", [dates[-1]],
                        eligible=all_eligible("900001", [dates[-1]]))
    row = out.iloc[0]

    expected_rvol_20_prev = statistics.stdev(log_rets[:20]) * ANN
    expected_rvol_20 = statistics.stdev(log_rets[1:21]) * ANN
    assert row["rvol_20_prev"] == pytest.approx(expected_rvol_20_prev)
    assert row["rvol_20"] == pytest.approx(expected_rvol_20)


def test_rvol_windows_are_nan_until_full():
    # Only 19 prior returns: rvol_20_prev needs 20, so it (and rvol_20, and shock)
    # must be NaN, not silently computed over a short window.
    closes = [100.0 * (1.01 ** i) for i in range(20)]  # 19 returns
    dates = nyse_sessions(len(closes))
    conn = build_equity_store({"900001": _panel(closes)})
    reader = AsOfReader(conn, "feat-a")

    out = build_features(reader, "smallcap", [dates[-1]],
                        eligible=all_eligible("900001", [dates[-1]]))
    row = out.iloc[0]
    assert math.isnan(row["rvol_20_prev"])
    assert math.isnan(row["rvol_20"])
    assert math.isnan(row["shock"])


def test_shock_uses_the_window_ending_D_minus_1_not_D():
    """The fixture the issue requires: a shock day that would inflate its own vol
    denominator if `shock` mistakenly used `rvol_20` (ending D) rather than
    `rvol_20_prev` (ending D-1).

    Baseline: 20 small alternating returns (genuine, non-zero prior volatility).
    D: one large drop. `shock` must be `ret_1` divided by the *prior* daily vol
    (excluding D), not the vol including D's own outsized move.
    """
    a = 0.005                       # small baseline daily moves
    r_shock = -0.15                 # a large one-day drop on D
    baseline = [a if k % 2 == 1 else -a for k in range(1, 21)]
    closes = [100.0]
    for r in baseline:
        closes.append(closes[-1] * math.exp(r))
    closes.append(closes[-1] * math.exp(r_shock))
    dates = nyse_sessions(len(closes))
    conn = build_equity_store({"900001": _panel(closes)})
    reader = AsOfReader(conn, "feat-a")

    out = build_features(reader, "smallcap", [dates[-1]],
                        eligible=all_eligible("900001", [dates[-1]]))
    row = out.iloc[0]

    daily_vol_prev = statistics.stdev(baseline)              # excludes D, correct
    daily_vol_including_D = statistics.stdev(baseline[-19:] + [r_shock])  # wrong window

    correct_shock = r_shock / daily_vol_prev
    wrong_shock = r_shock / daily_vol_including_D

    assert row["shock"] == pytest.approx(correct_shock)
    # The two denominators must differ meaningfully, or the fixture doesn't
    # actually exercise the bug this test is guarding against.
    assert abs(daily_vol_prev - daily_vol_including_D) / daily_vol_prev > 0.5
    assert row["shock"] != pytest.approx(wrong_shock, rel=1e-6)

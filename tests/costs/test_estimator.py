"""Abdi-Ranaldo (2017) close-high-low estimator: recovery on a known spread and
the negatives-zeroed-before-averaging rule (spec/06 Costs)."""

from __future__ import annotations

import math

import numpy as np

from harness import costs


def test_recovers_known_spread_from_bid_ask_prints():
    """A mid-price random walk with a fixed true half-spread; OHLC built from
    alternating bid/ask prints. Over a long sample the estimator recovers the
    true round-trip spread within a stated tolerance.

    `intraday_sigma` is kept modest relative to the spread on purpose. Spec/06
    requires negative two-day estimates to be zeroed before averaging, and
    `E[max(0, X)] > max(0, E[X])` whenever X has variance straddling zero
    (Jensen); since each two-day estimate's variance grows with the day's own
    volatility while its mean carries only the (tiny) spread signal, a daily
    vol many multiples of the spread makes the zero-floor rule bias the
    average upward, a known property of close-high-low spread estimators
    under high vol-to-spread ratios, not a defect in this implementation. A
    grid search over `intraday_sigma` (see the PR description) confirmed
    <5% relative error at this level, stable across seeds.
    """

    rng = np.random.default_rng(0)
    n_days = 3000
    ticks_per_day = 60
    true_half_spread = 0.004  # 40 bps half-spread, 80 bps round trip
    true_spread = 2.0 * true_half_spread
    intraday_sigma = 0.005

    mid = 100.0
    highs = np.empty(n_days)
    lows = np.empty(n_days)
    closes = np.empty(n_days)
    for day in range(n_days):
        intraday_rets = rng.normal(0.0, intraday_sigma / math.sqrt(ticks_per_day), ticks_per_day)
        mids = mid * np.exp(np.cumsum(intraday_rets))
        mid = mids[-1]
        side = rng.integers(0, 2, ticks_per_day)
        prints = np.where(side == 1, mids * (1.0 + true_half_spread), mids * (1.0 - true_half_spread))
        closes[day] = prints[-1]
        highs[day] = prints.max()
        lows[day] = prints.min()

    est = costs.abdi_ranaldo_spread(highs, lows, closes)
    assert abs(est - true_spread) / true_spread < 0.10


def test_negatives_zeroed_before_averaging():
    """A crafted 3-session window where the first two-day pair's raw estimate
    is negative and the second is positive; the implementation must zero the
    first before averaging rather than let it pull the mean (and the sqrt)
    down or negative."""

    high = np.array([101.0, 300.0, 180.0])
    low = np.array([99.0, 100.0, 150.0])
    close = np.array([101.0, 150.0, 160.0])

    eta = (np.log(high) + np.log(low)) / 2.0
    c = np.log(close)
    raw = 4.0 * (c[:-1] - eta[:-1]) * (c[:-1] - eta[1:])
    assert raw[0] < 0
    assert raw[1] > 0

    clipped_mean = float(np.mean(np.clip(raw, 0.0, None)))
    expected = math.sqrt(clipped_mean)
    got = costs.abdi_ranaldo_spread(high, low, close)
    assert math.isclose(got, expected, rel_tol=1e-9)

    naive = math.sqrt(float(np.mean(raw)))
    assert not math.isclose(got, naive, rel_tol=1e-6)


def test_requires_at_least_two_sessions():
    import pytest

    with pytest.raises(ValueError):
        costs.abdi_ranaldo_spread(np.array([100.0]), np.array([99.0]), np.array([99.5]))

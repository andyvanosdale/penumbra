"""Tests for the labeler (plan §3.3). Verifies the excess-return / threshold
arithmetic and that incomplete forward windows are left unlabeled (never guessed).
"""

import numpy as np
import pandas as pd

from harness.store import PITStore
from harness.labels import Labeler


def _store_with(ticker_path, etf_path, dates):
    """Build a store where AAPL maps to XLK (see config.universe)."""
    rows = []
    for sym, closes in (("AAPL", ticker_path), ("XLK", etf_path)):
        for d, c in zip(dates, closes):
            rows.append({"ticker": sym, "date": d, "open": c, "high": c,
                         "low": c, "close": c, "adj_close": c, "volume": 1e6})
    store = PITStore(":memory:")
    store.write_prices(pd.DataFrame(rows))
    return store


def test_excess_return_and_positive_label():
    dates = ["2020-01-02", "2020-01-03", "2020-01-06", "2020-01-07",
             "2020-01-08", "2020-01-09"]
    # AAPL +10% over 5 days; XLK +2% over 5 days -> excess ~ +8% > 2% threshold.
    aapl = [100, 100, 100, 100, 100, 110.0]
    xlk = [100, 100, 100, 100, 100, 102.0]
    store = _store_with(aapl, xlk, dates)
    lab = Labeler(store, horizon=5, threshold=0.02).label("AAPL", "2020-01-02")
    assert lab.label == 1
    assert abs(lab.ticker_return - 0.10) < 1e-9
    assert abs(lab.benchmark_return - 0.02) < 1e-9
    assert abs(lab.excess_return - 0.08) < 1e-9


def test_negative_label_when_below_threshold():
    dates = ["2020-01-02", "2020-01-03", "2020-01-06", "2020-01-07",
             "2020-01-08", "2020-01-09"]
    aapl = [100, 100, 100, 100, 100, 101.0]   # +1%
    xlk = [100, 100, 100, 100, 100, 100.5]    # +0.5% -> excess 0.5% < 2%
    store = _store_with(aapl, xlk, dates)
    lab = Labeler(store, horizon=5, threshold=0.02).label("AAPL", "2020-01-02")
    assert lab.label == 0


def test_incomplete_forward_window_is_unlabeled():
    dates = ["2020-01-02", "2020-01-03", "2020-01-06"]  # only 3 days, horizon 5
    store = _store_with([100, 101, 102], [100, 100, 100], dates)
    lab = Labeler(store, horizon=5, threshold=0.02).label("AAPL", "2020-01-02")
    assert lab.label is None
    assert lab.excess_return is None

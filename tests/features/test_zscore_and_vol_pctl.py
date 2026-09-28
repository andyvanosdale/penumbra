"""`zscore_20` and `vol_pctl_250` (spec/04 Features).

`vol_pctl_250`'s tie handling: ties share the mean ("midrank") of the tied
group — rank(x) = count(v < x) + (count(v == x) + 1) / 2, divided by 250 — the
same convention `pandas.Series.rank(method="average")` uses. Documented in
`docs/features.md`.
"""

from __future__ import annotations

import statistics

import pytest

from harness.features import build_features
from harness.store import AsOfReader
from tests.fixtures.features import build_equity_store, flat_bar, nyse_sessions


def test_zscore_20():
    closes = [100.0 + i for i in range(20)]  # 100..119, D = 119
    dates = nyse_sessions(len(closes))
    conn = build_equity_store({"900001": {d: flat_bar(c) for d, c in zip(dates, closes)}})
    reader = AsOfReader(conn, "feat-a")

    out = build_features(reader, "smallcap", [dates[-1]])
    mean_20 = statistics.mean(closes)
    std_20 = statistics.stdev(closes)
    expected = (closes[-1] - mean_20) / std_20
    assert out.loc[0, "zscore_20"] == pytest.approx(expected)


def _dollar_volume_panel(volumes: list[float]) -> dict[str, dict]:
    dates = nyse_sessions(len(volumes))
    return {d: dict(open=100.0, high=101.0, low=99.0, close=100.0, volume=1.0,
                   dollar_volume=v) for d, v in zip(dates, volumes)}


def test_vol_pctl_250_no_ties():
    volumes = [float(i) for i in range(1, 251)]  # D's own value (250) is the max
    conn = build_equity_store({"900001": _dollar_volume_panel(volumes)})
    reader = AsOfReader(conn, "feat-a")
    dates = nyse_sessions(250)

    out = build_features(reader, "smallcap", [dates[-1]])
    # D is the strict maximum of the 250-window: rank 250 of 250.
    assert out.loc[0, "vol_pctl_250"] == pytest.approx(1.0)


def test_vol_pctl_250_ties_use_the_midrank():
    volumes = [1.0] * 250  # every value in the window, including D's, ties
    conn = build_equity_store({"900001": _dollar_volume_panel(volumes)})
    reader = AsOfReader(conn, "feat-a")
    dates = nyse_sessions(250)

    out = build_features(reader, "smallcap", [dates[-1]])
    # All 250 tie: midrank = (0 + (250 + 1) / 2) / 250.
    expected = (0 + (250 + 1) / 2) / 250
    assert out.loc[0, "vol_pctl_250"] == pytest.approx(expected)


def test_vol_pctl_250_is_nan_with_fewer_than_250_sessions():
    volumes = [float(i) for i in range(1, 250)]  # only 249
    conn = build_equity_store({"900001": _dollar_volume_panel(volumes)})
    reader = AsOfReader(conn, "feat-a")
    dates = nyse_sessions(249)

    out = build_features(reader, "smallcap", [dates[-1]])
    assert out.loc[0, "vol_pctl_250"] != out.loc[0, "vol_pctl_250"]  # NaN

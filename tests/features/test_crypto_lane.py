"""Crypto lane: the `utc` calendar (every day is a session) and annualization by
sqrt(365) (spec/02 Trading calendars)."""

from __future__ import annotations

import math
import statistics

import pytest

from harness.features import build_features
from harness.store import AsOfReader
from tests.fixtures.features import build_crypto_store, utc_sessions

ANN = math.sqrt(365.0)


def _panel(closes: list[float], dates: list[str]) -> dict[str, dict]:
    return {d: dict(open=c, high=c + 1.0, low=c - 1.0, close=c, volume=10.0,
                    dollar_volume=c * 10.0) for d, c in zip(dates, closes)}


def test_ret_1_and_rvol_20_prev_use_the_utc_calendar_and_sqrt_365():
    a = 0.03
    log_rets = [a if k % 2 == 1 else -a for k in range(1, 21)]
    closes = [1_000.0]
    for r in log_rets:
        closes.append(closes[-1] * math.exp(r))
    closes.append(closes[-1] * math.exp(-0.02))  # D's own return
    dates = utc_sessions(len(closes))

    conn = build_crypto_store({"BTCUSDT": _panel(closes, dates)})
    reader = AsOfReader(conn, "feat-a")

    out = build_features(reader, "crypto", [dates[-1]])
    row = out.iloc[0]

    assert row["ret_1"] == pytest.approx(math.log(closes[-1] / closes[-2]))
    expected_rvol_20_prev = statistics.stdev(log_rets) * ANN
    assert row["rvol_20_prev"] == pytest.approx(expected_rvol_20_prev)

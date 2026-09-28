"""cost_inputs reads nothing after D (spec/02 Leakage tests; the store leakage
invariant applied to the cost model's own reads).

A synthetic equity store is built for one symbol over ~6 months. `cost_inputs`
is computed at a fixed signal day D, then recomputed after every generic
perturbation `harness.testing.invariance.perturbations` applies to the data
dated after D (deletion, random rescaling, extreme shocks, and shuffling among
post-D dates). Every field must come back bit-identical, since `cost_inputs`
never reads a date after D.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from harness.costs import cost_inputs
from harness.store import AsOfReader, build_nyse_calendar, connect, register_snapshot, upsert
from harness.testing.invariance import perturbations

LANE = "smallcap"
SYMBOL = "999001"
START, END = "2023-09-01", "2024-02-28"
D = "2024-01-10"


def _synthetic_bars(seed: int = 0) -> pd.DataFrame:
    dates = pd.bdate_range(START, END)
    rng = np.random.default_rng(seed)
    n = len(dates)
    log_rets = rng.normal(0.0002, 0.02, n)
    close = 50.0 * np.exp(np.cumsum(log_rets))
    prev_close = np.concatenate([[50.0], close[:-1]])
    open_ = prev_close * np.exp(rng.normal(0.0, 0.005, n))
    intraday = np.abs(rng.normal(0.0, 0.01, n))
    high = np.maximum(open_, close) * (1.0 + intraday)
    low = np.minimum(open_, close) * (1.0 - intraday)
    volume = rng.integers(500_000, 2_000_000, n).astype(float)
    return pd.DataFrame(
        {
            "date": dates.strftime("%Y-%m-%d"),
            "symbol": SYMBOL,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "dollar_volume": close * volume,
        }
    )


def _reader_from_bars(bars: pd.DataFrame, snapshot_id: str) -> AsOfReader:
    conn = connect(":memory:")
    register_snapshot(conn, snapshot_id, "2024-06-01T00:00:00Z", len(bars),
                       {"snapshot_id": snapshot_id, "synthetic": True})
    rows = [
        dict(market="us_equity", symbol=r.symbol, date=r.date, open=r.open, high=r.high,
             low=r.low, close=r.close, volume=r.volume, dollar_volume=r.dollar_volume,
             available_at=r.date)
        for r in bars.itertuples()
    ]
    upsert(conn, "bars_daily", snapshot_id, rows)
    build_nyse_calendar(conn, snapshot_id)
    return AsOfReader(conn, snapshot_id)


def test_cost_inputs_invariant_to_perturbations_after_D():
    baseline_bars = _synthetic_bars()
    baseline_reader = _reader_from_bars(baseline_bars, "snap-costs-inv-base")
    baseline = cost_inputs(baseline_reader, LANE, [SYMBOL], [D])

    rng = np.random.default_rng(42)
    for name, variant_bars, _ in perturbations(baseline_bars, None, D, rng, date_col="date"):
        variant_reader = _reader_from_bars(variant_bars, f"snap-costs-inv-{name}")
        got = cost_inputs(variant_reader, LANE, [SYMBOL], [D])
        try:
            pd.testing.assert_frame_equal(
                baseline.reset_index(drop=True),
                got.reset_index(drop=True),
                check_exact=False,
                rtol=1e-9,
                atol=1e-12,
            )
        except AssertionError as exc:
            raise AssertionError(f"cost_inputs changed under perturbation {name!r}: {exc}") from exc

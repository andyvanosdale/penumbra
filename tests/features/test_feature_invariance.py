"""Feature invariance (spec/02 Leakage tests, second bullet), on the real
feature builder.

Issue 18's `harness.testing.invariance.assert_feature_invariance` (PR #27) is
merged; this calls it directly against `harness.features.build_features` over
a synthetic store built from `tests/invariance/_synth.py`'s panel generator
(the same one `tests/invariance/test_feature_invariance.py` uses for its
reference implementation), replacing the minimal in-test version this PR
carried before #27 merged.

Each sampled D is driven through a fresh in-memory store built from that D's
own (possibly perturbed) bars/events, so the check exercises the real read
path — the windowed `panel` read, the `calendar` and `events` reads, and the
per-symbol rolling computation — not just in-memory arithmetic.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from harness.features import FEATURE_COLUMNS, FLAG_COLUMNS, LANE_MARKET, build_features
from harness.store import connect, register_snapshot, upsert
from harness.store.calendar import calendar_for_lane
from harness.store.reader import AsOfReader, iso_date
from harness.testing import assert_feature_invariance, sample_dates
from tests.invariance._synth import build_panel

pytestmark = pytest.mark.leakage

# Edges of the 20- and 250-day windows the real features use: an off-by-one
# leak is most likely to show up right at a window boundary.
_WINDOW_EDGE_INDICES = (19, 20, 21, 249, 250, 251)


def _build_store(lane: str, symbol: str, bars: pd.DataFrame,
                 events: pd.DataFrame | None, snapshot_id: str) -> AsOfReader:
    market = LANE_MARKET[lane]
    conn = connect(":memory:")
    register_snapshot(conn, snapshot_id, "2021-12-31T00:00:00Z", 1, {"synthetic": True})
    upsert(conn, "symbols", snapshot_id, [dict(
        market=market, symbol=symbol, ticker=symbol, name=symbol,
        category="Domestic Common Stock", exchange="NYSE", sector="Synthetic",
        base=symbol if market == "binance_spot" else None,
        quote="USDT" if market == "binance_spot" else None,
        available_at=iso_date(bars["date"].min()))])

    upsert(conn, "bars_daily", snapshot_id, [
        dict(market=market, symbol=symbol, date=iso_date(row.date), open=float(row.open),
            high=float(row.high), low=float(row.low), close=float(row.close),
            volume=float(row.volume), dollar_volume=float(row.dollar_volume),
            available_at=iso_date(row.date))
        for row in bars.itertuples(index=False)])

    # Calendar rows track exactly the dates this (possibly perturbed) frame
    # carries, so a store leakage test artifact (a "trading day" with no bar)
    # never masquerades as a missing-bar case.
    cal_name = calendar_for_lane(lane)
    upsert(conn, "calendar", snapshot_id, [
        dict(calendar=cal_name, date=iso_date(d), available_at=iso_date(d))
        for d in bars["date"]])

    if events is not None and not events.empty:
        # The `shuffled` perturbation reassigns filing_date/eventcodes among
        # rows independently of available_at (which it never moves), so it
        # can produce a row with available_at < filing_date — a combination
        # the store's writer refuses outright (spec/02: "a row cannot be
        # known before it happened"). Every such row necessarily has
        # available_at > D (perturbations never touch dated <= D rows), so it
        # can never affect D's features either way; drop it rather than
        # letting a generic, domain-unaware perturbation crash the store.
        rows = [dict(market=market, symbol=symbol, filing_date=iso_date(row.filing_date),
                    available_at=iso_date(row.available_at), eventcodes=str(row.eventcodes))
               for row in events.itertuples(index=False)]
        rows = [r for r in rows if r["available_at"] >= r["filing_date"]]
        if rows:
            upsert(conn, "events", snapshot_id, rows)
    return AsOfReader(conn, snapshot_id)


def _compute(lane: str, symbol: str):
    def compute(bars: pd.DataFrame, events: pd.DataFrame | None, D) -> dict:
        reader = _build_store(lane, symbol, bars, events, snapshot_id="inv")
        out = build_features(reader, lane, [iso_date(D)], symbols=[symbol])
        row = out.iloc[0]
        return {col: row[col] for col in (*FEATURE_COLUMNS, *FLAG_COLUMNS)}
    return compute


def _samples_for(bars: pd.DataFrame, rng: np.random.Generator) -> list:
    dates = bars["date"].tolist()
    samples = set(sample_dates(dates, 6, rng))
    samples.update(dates[i] for i in _WINDOW_EDGE_INDICES if 0 <= i < len(dates))
    return sorted(samples)


@pytest.fixture(scope="module")
def panel():
    return build_panel(lanes=("smallcap", "crypto"), names_per_lane=1, seed=7)


def test_build_features_is_invariant_to_data_after_D(panel):
    for name in panel:
        rng = np.random.default_rng(hash((name.lane, name.symbol)) % (2**32))
        samples = _samples_for(name.bars, rng)
        assert_feature_invariance(_compute(name.lane, name.symbol), name.bars, name.events,
                                  samples, rng)

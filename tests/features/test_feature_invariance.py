"""Feature invariance (spec/02 Leakage tests, second bullet), on the real
feature builder.

Issue 18's `harness.testing.invariance.assert_feature_invariance` (PR #27) is
merged; this calls it directly against `harness.features.build_features` over
a synthetic store built from `tests/invariance/_synth.py`'s panel generator
(the same one `tests/invariance/test_feature_invariance.py` uses for its
reference implementation).

`compute(bars, events, D)` calls `build_features` over a date range that
extends *past* D (`D-5 .. D+10`, clamped to what the perturbed frame still
has), not just `[D]`. Calling it with `dates=[D]` alone would make the panel
read's own `date <= D` SQL filter the only thing keeping future bars out of
memory — exactly the shape of a real run, where `build_features` is called
once per era with `dates = [D_1 .. D_n]` and the panel is read as of `D_n`, so
bars after every earlier `D_i` are already in memory. `test_windowing.py`
(the `center=True` mutant, below) is what proves this range actually matters:
called with `dates=[D]` alone, that mutant would pass invariance trivially,
because there would be no future data in memory for a leaky window to reach.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from harness.features import EQUITY_LANES, FEATURE_COLUMNS, FLAG_COLUMNS, LANE_MARKET, build_features
from harness.store import connect, register_snapshot, upsert
from harness.store.calendar import calendar_for_lane
from harness.store.reader import AsOfReader, iso_date
from harness.testing import assert_feature_invariance, sample_dates
from tests.invariance._synth import build_panel

pytestmark = pytest.mark.leakage

# Edges of the 20- and 250-day windows the real features use: an off-by-one
# leak is most likely to show up right at a window boundary.
_WINDOW_EDGE_INDICES = (19, 20, 21, 249, 250, 251)

# How far past (and before) D each `compute` call asks build_features for, so
# the in-memory panel actually holds bars after D, the way a real run's
# multi-date call would.
_DATES_BEFORE, _DATES_AFTER = 5, 10


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


def _dates_window(bars: pd.DataFrame, D) -> list[str]:
    """`D-5 .. D+10` (clamped), in whatever dates `bars` still has after a
    perturbation — so the panel `build_features` reads genuinely extends past
    D, the way a real multi-date call's does."""

    dates = sorted(bars["date"].unique())
    idx = dates.index(D)
    lo = max(0, idx - _DATES_BEFORE)
    hi = min(len(dates), idx + _DATES_AFTER + 1)
    return [iso_date(d) for d in dates[lo:hi]]


def _compute(lane: str, symbol: str):
    def compute(bars: pd.DataFrame, events: pd.DataFrame | None, D) -> dict:
        reader = _build_store(lane, symbol, bars, events, snapshot_id="inv")
        window_dates = _dates_window(bars, D)
        eligible = (pd.DataFrame({"date": window_dates, "symbol": [symbol] * len(window_dates)})
                   if lane in EQUITY_LANES else None)
        out = build_features(reader, lane, window_dates, symbols=[symbol], eligible=eligible)
        row = out.loc[out["date"] == iso_date(D)].iloc[0]
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


def _center_roll(s: pd.Series, window: int, how: str, ddof: int = 1) -> pd.Series:
    """A `_roll` mutant using a centered window — the acceptance-criteria bug
    this invariance check must catch: a centered window at D reaches into
    bars dated after D."""

    r = s.rolling(window, center=True)
    if how == "mean":
        val = r.mean()
    elif how == "std":
        val = r.std(ddof=ddof)
    elif how == "min":
        val = r.min()
    elif how == "max":
        val = r.max()
    else:
        raise ValueError(how)
    return val.where(r.count() == window)


def test_center_window_mutant_fails_invariance(panel, monkeypatch):
    name = next(n for n in panel if n.lane == "smallcap")
    monkeypatch.setattr("harness.features._roll", _center_roll)
    rng = np.random.default_rng(123)
    samples = _samples_for(name.bars, rng)
    with pytest.raises(AssertionError, match="perturbation"):
        assert_feature_invariance(_compute(name.lane, name.symbol), name.bars, name.events,
                                  samples, rng)

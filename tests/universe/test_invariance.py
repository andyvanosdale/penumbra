"""Invariance: perturbing every bar after D leaves D's membership unchanged.

This is the universe-builder analogue of the feature-invariance test spec/02
Leakage tests calls for (issue 8 owns the feature version). It is stronger than
the store's own leakage test: it checks that `harness.universe`'s own rolling
computations, done from one windowed panel read spanning many requested dates,
never let a later date's data leak backward into an earlier date's screen
values -- not just that the store's as-of filter excludes rows dated after D.
"""

from __future__ import annotations

import pandas as pd
import pytest

from harness import universe
from harness.store import AsOfReader
from tests.fixtures.universe_store import D, SNAPSHOT, TRADING_DAYS, add_eligible_equity, finalize, new_store


def _row(frame, symbol, date):
    match = frame[(frame["symbol"] == symbol) & (frame["date"] == date)]
    assert len(match) == 1, (symbol, date, frame)
    return match.iloc[0]


@pytest.fixture()
def conn():
    c = new_store()
    add_eligible_equity(c, "CTRL")
    finalize(c)
    return c


def test_screen_values_at_d_are_unchanged_by_a_later_request_date(conn):
    d_idx = TRADING_DAYS.index(D)
    later = TRADING_DAYS[d_idx + 60]
    reader = AsOfReader(conn, SNAPSHOT)

    alone = universe._equity_screen_frame(reader, [D])
    with_later = universe._equity_screen_frame(reader, [D, later])

    row_alone = _row(alone, "CTRL", D)
    row_with_later = _row(with_later, "CTRL", D)
    for col in ("close", "marketcap", "dv_median_20_prev", "rvol_20", "eligible",
               "smallcap_cap_ok", "liquidity_ok", "vol_ok", "price_ok"):
        assert row_alone[col] == pytest.approx(row_with_later[col]) if isinstance(
            row_alone[col], float) else row_alone[col] == row_with_later[col]


def test_perturbing_every_bar_after_d_leaves_d_membership_unchanged(conn):
    d_idx = TRADING_DAYS.index(D)
    later = TRADING_DAYS[d_idx + 60]

    reader = AsOfReader(conn, SNAPSHOT)
    before = universe.SmallcapBuilder().build(reader, "smallcap", [D])

    # Perturb every bar, market cap and listing row dated after D: extreme price
    # and volume changes, and a spurious future delisting.
    conn.execute("UPDATE bars_daily SET close = close * 11.0, volume = volume * 7.0, "
                "dollar_volume = dollar_volume * 7.0 WHERE symbol = 'CTRL' AND date > ?", (D,))
    conn.execute("UPDATE marketcap SET marketcap = marketcap * 0.001 "
                "WHERE symbol = 'CTRL' AND date > ?", (D,))
    conn.execute(
        "INSERT INTO listing (market, symbol, event, date, snapshot_id, reason, exchange, "
        "source, available_at) VALUES ('us_equity', 'CTRL', 'delisted', ?, ?, "
        "'voluntarydelisting', 'NASDAQ', 'actions', ?)", (later, SNAPSHOT, later))
    conn.commit()

    after = universe.SmallcapBuilder().build(reader, "smallcap", [D, later])
    after_d = after[after["date"] == D].reset_index(drop=True)

    pd.testing.assert_frame_equal(before.reset_index(drop=True), after_d)

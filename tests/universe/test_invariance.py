"""Invariance: perturbing every bar after D leaves D's membership unchanged.

This is the universe-builder analogue of the feature-invariance test spec/02
Leakage tests calls for (issue 8 owns the feature version, using the same
`harness.testing.invariance` machinery). The first test below is stronger than
the store's own leakage test: it checks that `harness.universe`'s own rolling
computations, done from one windowed panel read spanning many requested dates,
never let a later date's data leak backward into an earlier date's screen
values -- not just that the store's as-of filter excludes rows dated after D.
"""

from __future__ import annotations

import sqlite3

import numpy as np
import pandas as pd
import pytest

from harness import universe
from harness.store import AsOfReader, connect, register_snapshot, upsert
from harness.store.writer import StoreWriteError
from harness.testing import perturbations
from tests.fixtures.universe_store import D, SNAPSHOT, TRADING_DAYS, add_eligible_equity, finalize, new_store


def _row(frame, symbol, date):
    match = frame[(frame["symbol"] == symbol) & (frame["date"] == date)]
    assert len(match) == 1, (symbol, date, frame)
    return match.iloc[0]


def _copy_store(conn: sqlite3.Connection) -> sqlite3.Connection:
    copy = sqlite3.connect(":memory:")
    conn.backup(copy)
    return copy


def _bars_frame(conn: sqlite3.Connection, symbol: str) -> pd.DataFrame:
    """bars_daily as a plain (symbol, date, ...) frame, `available_at` dropped:
    for this table `available_at` always equals `date`, and `perturbations`
    would otherwise be free to shuffle it away from its row's own date, which
    the store's writer refuses (`available_at` before the date it dates).
    `_replace_bars` reconstructs it from `date` on the way back in.
    """
    return pd.read_sql_query(
        "SELECT symbol, date, open, high, low, close, volume, dollar_volume "
        "FROM bars_daily WHERE symbol = ? ORDER BY date", conn, params=(symbol,))


def _replace_bars(conn: sqlite3.Connection, symbol: str, frame: pd.DataFrame) -> None:
    conn.execute("DELETE FROM bars_daily WHERE symbol = ?", (symbol,))
    conn.commit()
    if frame.empty:
        return
    rows = frame.assign(market=universe.EQUITY_MARKET,
                        available_at=frame["date"]).to_dict("records")
    upsert(conn, "bars_daily", SNAPSHOT, rows)


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


def test_bar_perturbations_after_d_leave_d_membership_unchanged(conn):
    """Drives `harness.testing.invariance.perturbations`'s delete / multiply /
    shock / shuffle battery (the same machinery spec/04's feature invariance
    test, issue 8, will use) over `CTRL`'s bars, dated after D, and checks the
    universe builder's own membership and screen values at D are unaffected.
    """
    d_idx = TRADING_DAYS.index(D)
    later = TRADING_DAYS[d_idx + 60]
    rng = np.random.default_rng(0)

    reader = AsOfReader(conn, SNAPSHOT)
    before = universe.SmallcapBuilder().build(reader, "smallcap", [D])
    assert not before.empty, "the control symbol must be admitted before any perturbation"

    bars = _bars_frame(conn, "CTRL")
    for pname, bars_variant, _ in perturbations(bars, None, D, rng):
        variant_conn = _copy_store(conn)
        _replace_bars(variant_conn, "CTRL", bars_variant)
        variant_reader = AsOfReader(variant_conn, SNAPSHOT)

        after = universe.SmallcapBuilder().build(variant_reader, "smallcap", [D, later])
        after_d = after[after["date"] == D].reset_index(drop=True)
        pd.testing.assert_frame_equal(before.reset_index(drop=True), after_d,
                                      obj=f"bars perturbation {pname!r}")


def test_marketcap_and_listing_perturbation_after_d_leave_d_membership_unchanged(conn):
    """`harness.testing.invariance` models a bars-and-events stream; market cap
    and listing rows don't fit that shape, so they're perturbed directly here,
    alongside the bars battery above: an extreme post-D market-cap rewrite and
    a spurious future delisting.
    """
    d_idx = TRADING_DAYS.index(D)
    later = TRADING_DAYS[d_idx + 60]

    reader = AsOfReader(conn, SNAPSHOT)
    before = universe.SmallcapBuilder().build(reader, "smallcap", [D])

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


@pytest.mark.parametrize("table,row", [
    ("bars_daily", dict(market="us_equity", symbol="X", date="2020-01-02",
                        close=10.0, available_at="2020-01-03")),
    ("marketcap", dict(market="us_equity", symbol="X", date="2020-01-02",
                       marketcap=1e9, available_at="2020-01-03")),
    ("listing", dict(market="us_equity", symbol="X", event="listed", date="2020-01-02",
                     source="tickers", available_at="2020-01-03")),
])
def test_writer_refuses_available_at_other_than_date(table, row):
    """Pins the invariant the module docstring's single-windowed-read argument
    depends on (`harness.store.schema.AVAILABLE_ON_DATE`; `docs/store.md`
    "Availability invariant"): a row dated t but not known until some other
    date is refused outright, so it can never reach a `build()` call.
    """
    conn = connect(":memory:")
    register_snapshot(conn, "snap", "2020-01-01T00:00:00Z", 0, {})
    with pytest.raises(StoreWriteError):
        upsert(conn, table, "snap", [row])


def test_build_at_d_matches_build_at_d_and_later_with_compliant_future_rows_in_every_table():
    """The single-windowed-read design depends on every row this module reads
    being known no later than its own date, which the store now enforces
    (previous test). This checks the other half: a call given later dates,
    whose fetched window legitimately contains ordinary rows dated after D in
    bars_daily, marketcap AND listing, still agrees with a call asked only
    for D.
    """
    d_idx = TRADING_DAYS.index(D)
    later = TRADING_DAYS[d_idx + 60]
    delist_date = TRADING_DAYS[d_idx + 30]  # a listing-table row strictly between D and later

    conn = new_store()
    add_eligible_equity(conn, "CTRL")
    add_eligible_equity(conn, "FUTUREDELIST", delisted=delist_date)
    finalize(conn)
    reader = AsOfReader(conn, SNAPSHOT)

    alone = universe.SmallcapBuilder().build(reader, "smallcap", [D])
    with_later = universe.SmallcapBuilder().build(reader, "smallcap", [D, later])
    with_later_d = with_later[with_later["date"] == D].reset_index(drop=True)

    assert not alone.empty
    pd.testing.assert_frame_equal(alone.reset_index(drop=True), with_later_d)

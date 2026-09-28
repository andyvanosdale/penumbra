"""Boundary tests that pin exact behavior, not just pass/fail outcomes near a
threshold, so a mutation of `harness/universe.py` fails at least one test.

Reviewer-verified mutants that the rest of the suite let through: the
liquidity window ending D-2 instead of D-1; `HISTORY_SESSIONS = 249`; vol
computed on the unadjusted series; the vol window ending D-1 instead of D;
`ddof=0`; the price floor as `>` instead of `>=`; the liquidity floor as `>=`
instead of `>`. Each test below asserts an exact numeric value (not just a
boolean), or picks two constructions that a mutant and the correct code must
disagree on, so no mutant along these lines can pass silently.
"""

from __future__ import annotations

import math

import pytest

from harness import universe
from harness.store import AsOfReader
from tests.fixtures.universe_store import (D, SNAPSHOT, TRADING_DAYS, add_bars,
                                           add_eligible_equity, add_marketcap, add_split,
                                           add_symbol, finalize, new_store, price_path)


def _screen(conn, symbol, dates=(D,)):
    reader = AsOfReader(conn, SNAPSHOT)
    frame = universe._equity_screen_frame(reader, list(dates))
    return frame[frame["symbol"] == symbol].iloc[0]


# ------------------------------------------------------ liquidity: the window
def test_liquidity_median_pins_the_exact_d_minus_1_ending_window():
    """A monotonic ramp of dollar volume over the 22 sessions D-21..D: the
    three candidate 20-session windows (ending D-2, D-1 and D) each have a
    different median, one `STEP` apart, so any one-session shift is caught by
    an exact-value assertion regardless of where the floor sits.
    """
    d_idx = TRADING_DAYS.index(D)
    base, step = 400_000.0, 10_000.0

    conn = new_store()
    add_eligible_equity(conn, "RAMP")
    finalize(conn)
    for k, offset in enumerate(range(-21, 1)):
        date = TRADING_DAYS[d_idx + offset]
        conn.execute("UPDATE bars_daily SET dollar_volume = ? WHERE symbol = 'RAMP' AND date = ?",
                    (base + k * step, date))
    conn.commit()

    row = _screen(conn, "RAMP")
    correct = base + 10.5 * step         # sessions D-20..D-1
    ending_d_minus_2 = base + 9.5 * step  # sessions D-21..D-2
    ending_d = base + 11.5 * step         # sessions D-19..D
    assert row["dv_median_20_prev"] == pytest.approx(correct)
    assert row["dv_median_20_prev"] != pytest.approx(ending_d_minus_2)
    assert row["dv_median_20_prev"] != pytest.approx(ending_d)
    assert row["liquidity_ok"]  # correct > 500,000 floor; the two mutants sit on either side


def test_liquidity_floor_is_strict_exactly_500000_is_ineligible():
    d_idx = TRADING_DAYS.index(D)
    conn = new_store()
    add_eligible_equity(conn, "LIQBOUND")
    finalize(conn)
    for offset in range(-20, 0):
        date = TRADING_DAYS[d_idx + offset]
        conn.execute("UPDATE bars_daily SET dollar_volume = 500000.0 "
                    "WHERE symbol = 'LIQBOUND' AND date = ?", (date,))
    conn.commit()

    row = _screen(conn, "LIQBOUND")
    assert row["dv_median_20_prev"] == pytest.approx(universe.LIQUIDITY_FLOOR)
    assert not row["liquidity_ok"], "the floor is exclusive (>), not >="


# --------------------------------------------------- 250-day completeness
def test_exactly_250_sessions_is_eligible_249_is_not():
    d_idx = TRADING_DAYS.index(D)
    listed_date = TRADING_DAYS[d_idx - 249]  # the 250th session back, inclusive of D

    conn = new_store()
    add_eligible_equity(conn, "EXACT250", start=listed_date, listed=listed_date)
    add_eligible_equity(conn, "GAP250", start=listed_date, listed=listed_date)
    finalize(conn)
    # Delete GAP250's oldest bar: the 250th session back, the one session a
    # HISTORY_SESSIONS=249 mutant would never look at.
    conn.execute("DELETE FROM bars_daily WHERE symbol = 'GAP250' AND date = ?", (listed_date,))
    conn.commit()

    exact = _screen(conn, "EXACT250")
    gap = _screen(conn, "GAP250")
    assert exact["bar_count_250"] == 250 and exact["complete_250"]
    assert gap["bar_count_250"] == 249 and not gap["complete_250"]


# --------------------------------------------------------------------- vol
def test_vol_floor_pins_ddof1_not_ddof0():
    """20 alternating log returns give an exact sample (ddof=1) std of
    L*sqrt(20/19); `annual_vol=0.396` is chosen so the ddof=1 result (~0.4063)
    clears the 40% floor while the ddof=0 result (0.396) would not.
    """
    conn = new_store()
    add_eligible_equity(conn, "VOLBOUND", annual_vol=0.396)
    finalize(conn)

    row = _screen(conn, "VOLBOUND")
    expected_ddof1 = 0.396 * math.sqrt(20 / 19)
    assert row["rvol_20"] == pytest.approx(expected_ddof1)
    assert row["rvol_20"] != pytest.approx(0.396)  # the ddof=0 value
    assert row["vol_ok"]


def test_vol_window_ends_at_d_not_d_minus_1():
    """A flat price (zero log returns) through D-1, then one large jump on D.
    The correct window (D-19..D) is dominated by that single return; a window
    ending D-1 (D-20..D-1) never sees it and would compute zero vol.
    """
    d_idx = TRADING_DAYS.index(D)
    dates = TRADING_DAYS[:d_idx + 1]
    jump = 0.15
    closes = [100.0] * (len(dates) - 1) + [100.0 * math.exp(jump)]

    conn = new_store()
    add_symbol(conn, "JUMP")
    add_bars(conn, "JUMP", dates, closes)
    add_marketcap(conn, "JUMP", dates, [500_000_000.0] * len(dates))
    finalize(conn)

    row = _screen(conn, "JUMP")
    expected = (jump / math.sqrt(20)) * math.sqrt(252)
    assert row["rvol_20"] == pytest.approx(expected)
    assert row["rvol_20"] != 0.0  # what a window ending D-1 would give here
    assert row["vol_ok"]


def test_vol_uses_the_adjusted_series_not_the_unadjusted_one():
    """A 2-for-1 split inside the 20-day vol window ending D. The true
    (adjusted) vol is low, well under the floor; the unadjusted series shows a
    spurious ~-50% one-day "return" at the split that would blow the same
    window's vol far above the floor if it were used instead.
    """
    d_idx = TRADING_DAYS.index(D)
    dates = TRADING_DAYS
    split_date = dates[d_idx - 10]  # inside the 20-day window ending D

    daily_log_vol = 0.10 / math.sqrt(252)  # true vol well under the 40% floor
    raw = price_path(100.0, len(dates), daily_log_vol)
    closes = [c / 2.0 if d >= split_date else c for d, c in zip(dates, raw)]

    conn = new_store()
    add_symbol(conn, "SPLITVOL")
    add_bars(conn, "SPLITVOL", dates[:d_idx + 1], closes[:d_idx + 1])
    add_marketcap(conn, "SPLITVOL", dates[:d_idx + 1], [500_000_000.0] * (d_idx + 1))
    add_split(conn, "SPLITVOL", split_date, 2.0)
    finalize(conn)

    row = _screen(conn, "SPLITVOL")
    assert row["rvol_20"] == pytest.approx(0.10 * math.sqrt(20 / 19), rel=0.05)
    assert row["rvol_20"] < universe.VOL_FLOOR
    assert not row["vol_ok"]


# ------------------------------------------------------------- price floor
def test_price_floor_is_inclusive_exactly_2_00_is_eligible():
    conn = new_store()
    add_eligible_equity(conn, "PRICEBOUND", start_price=2.00)
    finalize(conn)
    conn.execute("UPDATE bars_daily SET close = 2.00, open = 2.00, high = 2.00, low = 2.00 "
                "WHERE symbol = 'PRICEBOUND' AND date = ?", (D,))
    conn.commit()

    row = _screen(conn, "PRICEBOUND")
    assert row["close"] == pytest.approx(2.00)
    assert row["price_ok"], "the floor is inclusive (>=), not >"

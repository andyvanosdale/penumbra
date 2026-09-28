"""Equity screens (spec/01 Parameters, Point-in-time construction): the DAILY
market-cap as-of rule, the missing-marketcap discovered-only rule, the D-1
median dollar-volume window, and the unadjusted price floor across a split.
"""

from __future__ import annotations

import math

import pytest

from harness import universe
from harness.store import AsOfReader
from tests.fixtures.universe_store import (D, DEFAULT_ANNUAL_VOL, SNAPSHOT, TRADING_DAYS,
                                           add_bars, add_eligible_equity, add_marketcap,
                                           add_split, add_symbol, finalize, new_store,
                                           price_path)


def _members(frame, date) -> set[str]:
    return set(frame.loc[frame["date"] == date, "symbol"])


# --------------------------------------------------------------------- market cap
def test_marketcap_is_read_exactly_as_of_d_never_a_future_row():
    d_idx = TRADING_DAYS.index(D)
    later = TRADING_DAYS[d_idx + 20]
    future_row_date = TRADING_DAYS[d_idx + 5]  # strictly between D and `later`

    conn = new_store()
    add_eligible_equity(conn, "MCAP", marketcap=None)
    # D's own row: comfortably below the ceiling. A "future" row (dated after D,
    # but still inside the panel fetched for the `later` request) that would flip
    # smallcap eligibility if it were ever used for D.
    add_marketcap(conn, "MCAP", [D, future_row_date], [500_000_000.0, 5_000_000_000.0])
    finalize(conn)
    reader = AsOfReader(conn, SNAPSHOT)

    frame = universe._equity_screen_frame(reader, [D, later])
    row = frame[(frame["symbol"] == "MCAP") & (frame["date"] == D)].iloc[0]
    assert row["marketcap"] == 500_000_000.0
    assert row["smallcap_cap_ok"]

    smallcap = universe.SmallcapBuilder().build(reader, "smallcap", [D, later])
    assert "MCAP" in _members(smallcap, D)


def test_missing_marketcap_is_ineligible_for_smallcap_and_eligible_for_discovered():
    conn = new_store()
    add_eligible_equity(conn, "NOCAP", marketcap=None)
    finalize(conn)
    reader = AsOfReader(conn, SNAPSHOT)

    smallcap = universe.SmallcapBuilder().build(reader, "smallcap", [D])
    discovered = universe.DiscoveredBuilder().build(reader, "discovered", [D])
    assert "NOCAP" not in _members(smallcap, D)
    assert "NOCAP" in _members(discovered, D)


def test_marketcap_at_or_above_the_ceiling_is_smallcap_ineligible_but_discovered_ok():
    conn = new_store()
    add_eligible_equity(conn, "LARGE", marketcap=universe.SMALLCAP_CEILING)
    finalize(conn)
    reader = AsOfReader(conn, SNAPSHOT)

    smallcap = universe.SmallcapBuilder().build(reader, "smallcap", [D])
    discovered = universe.DiscoveredBuilder().build(reader, "discovered", [D])
    assert "LARGE" not in _members(smallcap, D), "the ceiling is exclusive (below, not at-or-below)"
    assert "LARGE" in _members(discovered, D)


# ------------------------------------------------------------------- liquidity
def test_liquidity_floor_uses_the_20_sessions_ending_d_minus_1_not_d():
    """A day-D volume spike must not qualify a name whose D-1-ending window is
    thin. 11 of the 20 sessions ending D-1 are low-volume and 9 are moderately
    above the floor, so the correct median (the 10th and 11th order statistics)
    is the low value; an off-by-one window that dropped the oldest low session
    and admitted D's spike would push the median above the floor instead
    (10 low + 9 moderate + 1 spike -> median = avg(low, moderate) > floor).
    """
    d_idx = TRADING_DAYS.index(D)
    conn = new_store()
    add_eligible_equity(conn, "VOLW")
    finalize(conn)

    low, moderate, spike = 100_000.0, 1_000_000.0, 50_000_000.0
    for offset in range(-20, 0):
        date = TRADING_DAYS[d_idx + offset]
        value = low if offset <= -10 else moderate  # offsets -20..-10 (11 days) low
        conn.execute("UPDATE bars_daily SET dollar_volume = ? WHERE symbol = 'VOLW' AND date = ?",
                    (value, date))
    conn.execute("UPDATE bars_daily SET dollar_volume = ? WHERE symbol = 'VOLW' AND date = ?",
                (spike, D))
    conn.commit()

    reader = AsOfReader(conn, SNAPSHOT)
    frame = universe._equity_screen_frame(reader, [D])
    row = frame[frame["symbol"] == "VOLW"].iloc[0]
    assert row["dv_median_20_prev"] == pytest.approx(low)
    assert not row["liquidity_ok"]

    smallcap = universe.SmallcapBuilder().build(reader, "smallcap", [D])
    assert "VOLW" not in _members(smallcap, D)


def test_liquidity_floor_admits_a_name_whose_d_minus_1_window_clears_it():
    conn = new_store()
    add_eligible_equity(conn, "LIQ", dollar_volume=universe.LIQUIDITY_FLOOR * 2)
    finalize(conn)
    reader = AsOfReader(conn, SNAPSHOT)
    smallcap = universe.SmallcapBuilder().build(reader, "smallcap", [D])
    assert "LIQ" in _members(smallcap, D)


# --------------------------------------------------------------------- vol floor
def test_vol_floor_excludes_a_quiet_name():
    conn = new_store()
    add_eligible_equity(conn, "QUIET", annual_vol=0.15)  # below the 40% floor
    finalize(conn)
    reader = AsOfReader(conn, SNAPSHOT)
    smallcap = universe.SmallcapBuilder().build(reader, "smallcap", [D])
    assert "QUIET" not in _members(smallcap, D)


# ----------------------------------------------------------------- price floor
def test_price_floor_uses_the_unadjusted_close_across_a_split():
    """A 3-for-1 split partway through the history. The unadjusted close drops
    below the floor right after the split even though the split-and-dividend
    -adjusted series (used only for the vol screen) is smooth across it.
    """
    dates = TRADING_DAYS
    d_idx = dates.index(D)
    split_idx = d_idx + 20
    split_date = dates[split_idx]
    post_split_date = dates[split_idx + 5]

    daily_log_vol = DEFAULT_ANNUAL_VOL / math.sqrt(252)
    raw = price_path(4.00, len(dates), daily_log_vol)  # pre-split level, above the floor
    closes = [c / 3.0 if d >= split_date else c for d, c in zip(dates, raw)]

    conn = new_store()
    add_symbol(conn, "SPLIT")
    add_bars(conn, "SPLIT", dates, closes)
    add_marketcap(conn, "SPLIT", dates, [500_000_000.0] * len(dates))
    add_split(conn, "SPLIT", split_date, 3.0)
    finalize(conn)
    reader = AsOfReader(conn, SNAPSHOT)

    frame = universe._equity_screen_frame(reader, [D, post_split_date])
    pre = frame[(frame["symbol"] == "SPLIT") & (frame["date"] == D)].iloc[0]
    post = frame[(frame["symbol"] == "SPLIT") & (frame["date"] == post_split_date)].iloc[0]

    assert pre["close"] == pytest.approx(raw[d_idx])
    assert pre["price_ok"]
    assert post["close"] == pytest.approx(raw[split_idx + 5] / 3.0)
    assert post["close"] < universe.PRICE_FLOOR
    assert not post["price_ok"]
    # the adjusted series (vol screen input) stays smooth across the split
    assert post["vol_ok"]

    smallcap = universe.SmallcapBuilder().build(reader, "smallcap", [D, post_split_date])
    assert "SPLIT" in _members(smallcap, D)
    assert "SPLIT" not in _members(smallcap, post_split_date)

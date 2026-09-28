"""Equity eligibility (spec/01 Eligibility): listing boundary, category/exchange
filters and the 250-day bar-completeness rule.
"""

from __future__ import annotations

import sqlite3

import pytest

from harness import universe
from harness.store import AsOfReader
from tests.fixtures.universe_store import (D, SNAPSHOT, TRADING_DAYS, add_eligible_equity,
                                           finalize, new_store)


def _lanes(reader, dates):
    smallcap = universe.SmallcapBuilder().build(reader, "smallcap", dates)
    discovered = universe.DiscoveredBuilder().build(reader, "discovered", dates)
    return smallcap, discovered


def _members(frame, date) -> set[str]:
    return set(frame.loc[frame["date"] == date, "symbol"])


# ------------------------------------------------------------- listing boundary
def test_delisted_name_excluded_on_and_after_the_delisting_date():
    d_idx = TRADING_DAYS.index(D) + 100
    delist_date = TRADING_DAYS[d_idx]
    day_before = TRADING_DAYS[d_idx - 1]

    conn = new_store()
    add_eligible_equity(conn, "DELIST", delisted=delist_date)
    finalize(conn)
    reader = AsOfReader(conn, SNAPSHOT)

    smallcap, discovered = _lanes(reader, [day_before, delist_date])
    for frame in (smallcap, discovered):
        assert "DELIST" in _members(frame, day_before), "listed the day before delisting"
        assert "DELIST" not in _members(frame, delist_date), (
            "spec/02 Store: not listed on the delisting date itself")


# --------------------------------------------------------------- category/exchange
@pytest.mark.parametrize("label,category,exchange", [
    ("adr", "ADR Common Stock", "NASDAQ"),
    ("otc", "Domestic Common Stock", "OTC"),
    ("fund", "Domestic ETF", "NYSEARCA"),
    ("preferred", "Domestic Preferred Stock", "NYSE"),
    ("wrong_exchange", "Domestic Common Stock", "PINK"),
])
def test_eligibility_filters_exclude_non_qualifying_names(label, category, exchange):
    conn = new_store()
    add_eligible_equity(conn, "CTRL")
    add_eligible_equity(conn, label.upper(), category=category, exchange=exchange)
    finalize(conn)
    reader = AsOfReader(conn, SNAPSHOT)

    smallcap, discovered = _lanes(reader, [D])
    for frame in (smallcap, discovered):
        members = _members(frame, D)
        assert "CTRL" in members, "control symbol must remain eligible"
        assert label.upper() not in members, f"{label} ({category}, {exchange}) must be excluded"


@pytest.mark.parametrize("category", universe.ELIGIBLE_CATEGORIES)
def test_every_eligible_category_is_admitted(category):
    conn = new_store()
    add_eligible_equity(conn, "OK", category=category)
    finalize(conn)
    reader = AsOfReader(conn, SNAPSHOT)
    smallcap, _ = _lanes(reader, [D])
    assert "OK" in _members(smallcap, D)


# --------------------------------------------------------- 250-day completeness
def test_one_missing_bar_in_the_250_day_window_makes_the_name_ineligible():
    conn = new_store()
    add_eligible_equity(conn, "CTRL")
    add_eligible_equity(conn, "GAP")
    finalize(conn)

    d_idx = TRADING_DAYS.index(D)
    missing_date = TRADING_DAYS[d_idx - 100]  # inside the 250-session window ending D
    conn.execute("DELETE FROM bars_daily WHERE symbol = 'GAP' AND date = ?", (missing_date,))
    conn.commit()

    reader = AsOfReader(conn, SNAPSHOT)
    smallcap, discovered = _lanes(reader, [D])
    for frame in (smallcap, discovered):
        members = _members(frame, D)
        assert "CTRL" in members
        assert "GAP" not in members, "a missing bar is never forward-filled (spec/02)"


def test_missing_bar_stops_disqualifying_once_it_ages_out_of_the_window():
    conn = new_store()
    add_eligible_equity(conn, "GAP")
    finalize(conn)

    d_idx = TRADING_DAYS.index(D)
    missing_date = TRADING_DAYS[d_idx - 260]  # older than the 250-session window ending D
    conn.execute("DELETE FROM bars_daily WHERE symbol = 'GAP' AND date = ?", (missing_date,))
    conn.commit()

    reader = AsOfReader(conn, SNAPSHOT)
    smallcap, _ = _lanes(reader, [D])
    assert "GAP" in _members(smallcap, D), (
        "a gap outside the 250-day window ending D must not disqualify D")

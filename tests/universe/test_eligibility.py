"""Equity eligibility (spec/01 Eligibility): listing boundary, category/exchange
filters and the 250-day bar-completeness rule.
"""

from __future__ import annotations

import sqlite3

import pandas as pd
import pytest

from harness import universe
from harness.store import AsOfReader
from tests.fixtures.universe_store import (D, SNAPSHOT, TRADING_DAYS, add_eligible_equity,
                                           finalize, new_store)


class _FakeExchangeOnReader:
    """Wraps an `AsOfReader`, adding a synthetic `exchange_on` that returns a
    point-in-time exchange from a symbol's change history.

    Stands in for `AsOfReader.exchange_on`, which ingest/sharadar (issues 3+5)
    hasn't merged yet (PM ruling on issue 6's Q4). This checks the integration
    seam `harness.universe._exchange_on` calls through to `reader.exchange_on`
    when it exists, independent of the real loader.
    """

    def __init__(self, reader: AsOfReader, changes: dict[str, list[tuple[str, str]]]):
        self._reader = reader
        self._changes = changes  # symbol -> sorted [(effective_date, exchange), ...]

    def __getattr__(self, name):
        return getattr(self._reader, name)

    def exchange_on(self, market, symbols, date, as_of) -> pd.DataFrame:
        rows = []
        for sym in (symbols if symbols is not None else self._changes):
            exchange = None
            for effective, ex in self._changes.get(sym, []):
                if effective <= date:
                    exchange = ex
            if exchange is not None:
                rows.append({"symbol": sym, "exchange": exchange, "source": "actions"})
        return pd.DataFrame(rows, columns=["symbol", "exchange", "source"])


def _lanes(reader, dates):
    smallcap = universe.SmallcapBuilder().build(reader, "smallcap", dates)
    discovered = universe.DiscoveredBuilder().build(reader, "discovered", dates)
    return smallcap, discovered


def _members(frame, date) -> set[str]:
    return set(frame.loc[frame["date"] == date, "symbol"])


# ------------------------------------------------------------- listing boundary
def test_delisted_name_excluded_on_and_after_the_delisting_date():
    """spec/01 (penumbra-specs PR 10): a delisted name is excluded "on and
    after" its delisting date. `AsOfReader.listed` already implements this
    (spec/02 Store: no `delisted` event on or before D); this asserts it
    holds through this module's own vectorized replica of that rule.
    """
    d_idx = TRADING_DAYS.index(D) + 100
    delist_date = TRADING_DAYS[d_idx]
    day_before = TRADING_DAYS[d_idx - 1]

    # A calendar anchor with bars past the delisting date, so `day_after` is
    # itself a lane trading session (DELIST's own bars stop at delisting).
    conn = new_store()
    add_eligible_equity(conn, "CTRL")
    add_eligible_equity(conn, "DELIST", delisted=delist_date)
    finalize(conn)
    day_after = TRADING_DAYS[d_idx + 1]
    reader = AsOfReader(conn, SNAPSHOT)

    smallcap, discovered = _lanes(reader, [day_before, delist_date, day_after])
    for frame in (smallcap, discovered):
        assert "DELIST" in _members(frame, day_before), "listed the day before delisting"
        assert "DELIST" not in _members(frame, delist_date), "excluded ON the delisting date"
        assert "DELIST" not in _members(frame, day_after), "excluded AFTER the delisting date"


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


def test_exchange_is_point_in_time_ineligible_before_the_move_eligible_after():
    d_idx = TRADING_DAYS.index(D)
    move_date = TRADING_DAYS[d_idx + 10]
    before, after = TRADING_DAYS[d_idx], TRADING_DAYS[d_idx + 20]

    conn = new_store()
    add_eligible_equity(conn, "MOVED", exchange="OTC")  # current value; overridden by the fake
    finalize(conn)
    reader = _FakeExchangeOnReader(
        AsOfReader(conn, SNAPSHOT),
        {"MOVED": [("2000-01-01", "OTC"), (move_date, "NASDAQ")]})

    smallcap, discovered = _lanes(reader, [before, move_date, after])
    for frame in (smallcap, discovered):
        assert "MOVED" not in _members(frame, before), "still OTC before the move"
        assert "MOVED" in _members(frame, move_date), "NASDAQ effective on the move date"
        assert "MOVED" in _members(frame, after), "still NASDAQ after the move"


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

"""`write_lane_membership` (the store round trip) and the `UniverseBuilder`
interface: the `BUILDERS` registry and the lane-mismatch guard.
"""

from __future__ import annotations

import json

import pytest

from harness import universe
from harness.store import AsOfReader
from tests.fixtures.universe_store import D, SNAPSHOT, add_eligible_equity, finalize, new_store


@pytest.fixture()
def conn():
    c = new_store()
    add_eligible_equity(c, "CTRL")
    finalize(c)
    return c


def test_builders_registry_covers_both_equity_lanes():
    assert set(universe.BUILDERS) == set(universe.EQUITY_LANES)
    assert isinstance(universe.BUILDERS["smallcap"], universe.SmallcapBuilder)
    assert isinstance(universe.BUILDERS["discovered"], universe.DiscoveredBuilder)


def test_builder_rejects_a_lane_it_does_not_own():
    with pytest.raises(ValueError):
        universe.SmallcapBuilder().build(None, "discovered", [D])
    with pytest.raises(ValueError):
        universe.DiscoveredBuilder().build(None, "smallcap", [D])


def test_write_lane_membership_round_trips_through_the_store(conn):
    reader = AsOfReader(conn, SNAPSHOT)
    frame = universe.BUILDERS["smallcap"].build(reader, "smallcap", [D])
    assert not frame.empty

    n = universe.write_lane_membership(conn, SNAPSHOT, frame)
    assert n == len(frame)

    stored = reader.lane_membership("smallcap", D, D, D)
    assert list(stored["symbol"]) == list(frame["symbol"])
    assert stored["available_at"].iloc[0] == D
    values = json.loads(stored["screen_values"].iloc[0])
    assert values == frame.iloc[0]["screen_values"]


def test_write_lane_membership_on_an_empty_frame_writes_nothing(conn):
    assert universe.write_lane_membership(conn, SNAPSHOT, universe._empty_frame()) == 0


def test_build_rejects_a_date_that_is_not_a_lane_trading_session(conn):
    reader = AsOfReader(conn, SNAPSHOT)
    with pytest.raises(ValueError):
        universe.BUILDERS["smallcap"].build(reader, "smallcap", ["2021-01-02"])  # a Saturday-ish gap


def test_build_rejects_empty_dates(conn):
    reader = AsOfReader(conn, SNAPSHOT)
    with pytest.raises(ValueError):
        universe.BUILDERS["smallcap"].build(reader, "smallcap", [])

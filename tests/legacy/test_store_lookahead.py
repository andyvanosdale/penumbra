"""Lookahead tests for the point-in-time store — the single most important test
file in the project (plan §3.1, §7). If any of these fail, every downstream
result is suspect.
"""

import datetime as dt

import pandas as pd
import pytest

from legacy.store import PITStore


def _frame():
    # Three consecutive business days for one ticker.
    return pd.DataFrame({
        "ticker": ["AAA", "AAA", "AAA"],
        "date": ["2020-01-02", "2020-01-03", "2020-01-06"],
        "open": [10, 11, 12], "high": [11, 12, 13], "low": [9, 10, 11],
        "close": [10.5, 11.5, 12.5], "adj_close": [10.5, 11.5, 12.5],
        "volume": [1e6, 1e6, 1e6],
    })


def test_known_prices_never_returns_future_rows():
    store = PITStore(":memory:")
    store.write_prices(_frame())
    # As of Jan 3 we must NOT see the Jan 6 bar.
    got = store.get_known_prices(as_of="2020-01-03")
    assert set(got["date"]) == {"2020-01-02", "2020-01-03"}
    assert "2020-01-06" not in set(got["date"])


def test_known_prices_as_of_before_all_data_is_empty():
    store = PITStore(":memory:")
    store.write_prices(_frame())
    assert store.get_known_prices(as_of="2019-12-31").empty


def test_latest_known_close_respects_as_of():
    store = PITStore(":memory:")
    store.write_prices(_frame())
    assert store.latest_known_close("AAA", "2020-01-03") == 11.5
    assert store.latest_known_close("AAA", "2020-01-06") == 12.5
    assert store.latest_known_close("AAA", "2019-01-01") is None


def test_write_rejects_knowledge_date_before_event_date():
    store = PITStore(":memory:")
    df = _frame()
    df["knowledge_date"] = ["2019-01-01", "2020-01-03", "2020-01-06"]  # first is bad
    with pytest.raises(ValueError, match="lookahead at write time"):
        store.write_prices(df)


def test_custom_knowledge_date_delays_visibility():
    """A bar can be made knowable LATER than its event date (e.g. restated data),
    and must then be invisible until its knowledge_date."""
    store = PITStore(":memory:")
    df = _frame()
    df["knowledge_date"] = ["2020-01-02", "2020-01-03", "2020-01-10"]  # Jan 6 bar known Jan 10
    store.write_prices(df)
    got = store.get_known_prices(as_of="2020-01-06")
    assert "2020-01-06" not in set(got["date"])      # event happened, not yet knowable
    got2 = store.get_known_prices(as_of="2020-01-10")
    assert "2020-01-06" in set(got2["date"])


def test_oracle_sees_everything():
    store = PITStore(":memory:")
    store.write_prices(_frame())
    assert len(store.get_prices_oracle()) == 3

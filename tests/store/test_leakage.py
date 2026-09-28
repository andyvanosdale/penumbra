"""Store leakage test (spec/02 Leakage tests, first bullet).

An as-of read at D returns no row with `available_at` after D, for every table, on
both the single-date and the windowed read paths. Parametrized over
`harness.store.schema.TABLES`: a table added to the schema without a read here
fails `test_every_table_has_a_leakage_read`.

The one allowlisted exception is TICKERS `sector` (spec/04 Features: "Sector is
Sharadar TICKERS `sector`, a current classification with no history. It is the one
input the store leakage test allowlists").
"""

from __future__ import annotations

import datetime as dt
import sqlite3

import pandas as pd
import pytest

from harness.store import AsOfReader
from harness.store.reader import NON_PIT_ALLOWLIST, SYMBOL_ATTRIBUTES, end_of_day
from harness.store.schema import NON_PIT_TABLES, TABLES, TIMESTAMP
from tests.fixtures.store import END, SNAPSHOT, START, as_of_dates, build_store

pytestmark = pytest.mark.leakage

WIDE_START, WIDE_END = "2000-01-01", "2030-12-31"
EQ, CX = "us_equity", "binance_spot"


def _plus(d: str, n: int) -> str:
    return (dt.date.fromisoformat(d) + dt.timedelta(days=n)).isoformat()


def _cat(*frames: pd.DataFrame) -> pd.DataFrame:
    return pd.concat(frames, ignore_index=True)


# table -> (single-date read at `date`, windowed read); both as-of `a`.
# A single-date read is issued for dates on both sides of the as-of date.
READS = {
    "calendar": (
        lambda r, date, a: _cat(r.calendar("nyse", date, date, a), r.calendar("utc", date, date, a)),
        lambda r, a: _cat(r.calendar("nyse", WIDE_START, WIDE_END, a),
                          r.calendar("utc", WIDE_START, WIDE_END, a)),
    ),
    "symbols": (
        lambda r, date, a: _cat(r.symbols(EQ, None, a), r.symbols(CX, None, a)),
        None,  # not date-keyed: there is no window to read
    ),
    "bars_daily": (
        lambda r, date, a: _cat(*[r.bars(m, None, date, a, adj) for m in (EQ, CX)
                                  for adj in ("none", "split", "split_div")]),
        lambda r, a: _cat(*[r.panel(m, None, WIDE_START, WIDE_END, a, adj) for m in (EQ, CX)
                            for adj in ("none", "split", "split_div")]),
    ),
    "bars_hourly": (
        lambda r, date, a: r.hourly(CX, None, date, date, a),
        lambda r, a: r.hourly(CX, None, WIDE_START, WIDE_END, a),
    ),
    "actions": (
        lambda r, date, a: r.actions(EQ, None, date, date, a),
        lambda r, a: r.actions(EQ, None, WIDE_START, WIDE_END, a),
    ),
    "listing": (
        lambda r, date, a: _cat(r.listed(EQ, date, a), r.listed(CX, date, a),
                                r.listing(EQ, None, date, date, a)),
        lambda r, a: _cat(r.listing(EQ, None, WIDE_START, WIDE_END, a),
                          r.listing(CX, None, WIDE_START, WIDE_END, a)),
    ),
    "marketcap": (
        lambda r, date, a: r.marketcap(EQ, None, date, date, a),
        lambda r, a: r.marketcap(EQ, None, WIDE_START, WIDE_END, a),
    ),
    "events": (
        lambda r, date, a: r.events(EQ, None, date, date, a),
        lambda r, a: r.events(EQ, None, WIDE_START, WIDE_END, a),
    ),
    "lane_membership": (
        lambda r, date, a: _cat(r.lane_membership("smallcap", date, date, a),
                                r.lane_membership("crypto", date, date, a)),
        lambda r, a: _cat(r.lane_membership("smallcap", WIDE_START, WIDE_END, a),
                          r.lane_membership("crypto", WIDE_START, WIDE_END, a)),
    ),
}


@pytest.fixture(scope="module")
def conn() -> sqlite3.Connection:
    return build_store()


@pytest.fixture(scope="module")
def reader(conn) -> AsOfReader:
    return AsOfReader(conn, SNAPSHOT)


def _bound(table: str, as_of: str) -> str:
    return end_of_day(as_of) if TABLES[table].available_at == TIMESTAMP else as_of


def _future_rows(conn, table: str, as_of: str) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {table} WHERE snapshot_id = ? AND available_at > ?",
                        (SNAPSHOT, _bound(table, as_of))).fetchone()[0]


def test_every_table_has_a_leakage_read(conn):
    in_db = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")}
    assert in_db == set(TABLES) | set(NON_PIT_TABLES), (
        "every table is point-in-time (in TABLES) or explicitly exempt (NON_PIT_TABLES)")
    assert set(READS) == set(TABLES), "every point-in-time table needs a leakage read"


@pytest.mark.parametrize("table", sorted(TABLES))
def test_single_date_read_never_returns_future_rows(conn, reader, table):
    single, _ = READS[table]
    exercised = False
    for a in as_of_dates():
        for date in (_plus(a, -3), _plus(a, -1), a, _plus(a, 1), _plus(a, 2), _plus(a, 7)):
            out = single(reader, date, a)
            assert "available_at" in out.columns
            late = out[out["available_at"] > _bound(table, a)]
            assert late.empty, f"{table} as-of {a}, date {date}:\n{late}"
            exercised |= (not out.empty) and _future_rows(conn, table, a) > 0
    assert exercised, f"{table}: fixture never had both a returned row and a future row"


@pytest.mark.parametrize("table", sorted(TABLES))
def test_windowed_read_never_returns_future_rows(conn, reader, table):
    _, window = READS[table]
    if window is None:
        pytest.skip(f"{table} has no date dimension; its single read is the only path")
    exercised = False
    for a in as_of_dates():
        out = window(reader, a)
        late = out[out["available_at"] > _bound(table, a)]
        assert late.empty, f"{table} as-of {a}:\n{late}"
        exercised |= (not out.empty) and _future_rows(conn, table, a) > 0
    assert exercised, f"{table}: fixture never had both a returned row and a future row"


def _truncated(conn: sqlite3.Connection, as_of: str) -> sqlite3.Connection:
    """A copy of the store holding only rows available as-of `as_of`."""
    copy = sqlite3.connect(":memory:")
    conn.backup(copy)
    for t in TABLES:
        copy.execute(f"DELETE FROM {t} WHERE available_at > ?", (_bound(t, as_of),))
    copy.commit()
    return copy


@pytest.mark.parametrize("as_of", ["2021-03-09", "2021-03-10", "2021-03-12", "2021-03-16",
                                   "2021-03-17", "2021-03-23", "2021-03-24", END])
def test_reads_equal_reads_of_a_store_without_the_future(conn, reader, as_of):
    """Deleting every row available after D changes no as-of-D read: values too,
    including the adjusted series (no action after D is applied)."""
    past = AsOfReader(_truncated(conn, as_of), SNAPSHOT)
    for table, (single, window) in READS.items():
        for date in (START, _plus(as_of, -1), as_of, _plus(as_of, 7)):
            pd.testing.assert_frame_equal(single(reader, date, as_of), single(past, date, as_of),
                                          obj=f"{table} single {date} as-of {as_of}")
        if window is not None:
            pd.testing.assert_frame_equal(window(reader, as_of), window(past, as_of),
                                          obj=f"{table} window as-of {as_of}")


def test_symbols_non_point_in_time_allowlist(reader):
    # spec/04 Features: sector. spec/01 Eligibility: category, and exchange only
    # as exchange_on's fallback.
    assert set(NON_PIT_ALLOWLIST) == {("symbols", "sector"), ("symbols", "category"),
                                      ("symbols", "exchange")}
    assert "spec/04" in NON_PIT_ALLOWLIST[("symbols", "sector")]
    assert "spec/01" in NON_PIT_ALLOWLIST[("symbols", "category")]
    assert "spec/01" in NON_PIT_ALLOWLIST[("symbols", "exchange")]
    out = reader.symbols(EQ, None, END)
    assert tuple(out.columns) == SYMBOL_ATTRIBUTES, (
        "a new symbols attribute must be reviewed for point-in-time safety")
    assert out["sector"].notna().all()

"""Store schema, writer, adjustment, calendars, listing and oracle bounds (issue 16)."""

from __future__ import annotations

import sqlite3

import pytest

from harness.store import (AsOfReader, LANE_CALENDAR, SCHEMA_VERSION, build_nyse_calendar,
                           calendar_for_lane, connect, next_session, register_snapshot,
                           upsert)
from harness.store.oracle import HoldoutLockedError, OracleBoundError, OracleReader
from harness.store.schema import TABLES, SchemaVersionError, ensure_schema, schema_version
from harness.store.writer import StoreWriteError
from tests.fixtures.store import (DELIST_DATE, DELIST_LISTED, DELIST_SYM, DIV_AMOUNT, DIV_DATE,
                                  DIV_SYM, END, EVENT_AFTER_CLOSE, EVENT_BEFORE_CLOSE,
                                  SNAPSHOT, SPLIT_DATE, SPLIT_RATIO, SPLIT_SYM, START,
                                  build_store, days, unadjusted_close, weekdays)

EQ = "us_equity"


@pytest.fixture()
def conn() -> sqlite3.Connection:
    return build_store()


@pytest.fixture()
def reader(conn) -> AsOfReader:
    return AsOfReader(conn, SNAPSHOT)


def _close(df, symbol, date):
    row = df[(df["symbol"] == symbol) & (df["date"] == date)]
    assert len(row) == 1, (symbol, date, df)
    return float(row["close"].iloc[0])


def _counts(conn):
    return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            for t in list(TABLES) + ["snapshots"]}


# ------------------------------------------------------------------- schema
def test_schema_matches_table_metadata(conn):
    for name, spec in TABLES.items():
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({name})")]
        assert sorted(cols) == sorted(spec.all_columns), name
        pk = [r[1] for r in sorted(conn.execute(f"PRAGMA table_info({name})"),
                                   key=lambda r: r[5]) if r[5]]
        assert tuple(pk) == spec.key, name
        assert "snapshot_id" in spec.key and "available_at" in cols


def test_schema_version_recorded_and_mismatch_refused(conn):
    assert schema_version(conn) == SCHEMA_VERSION
    ensure_schema(conn)  # reopening at the same version is fine
    conn.execute("UPDATE meta SET value = ? WHERE key = 'schema_version'", (str(SCHEMA_VERSION + 1),))
    with pytest.raises(SchemaVersionError):
        ensure_schema(conn)


def test_bars_carry_every_architecture_column(conn):
    cols = {r[1] for r in conn.execute("PRAGMA table_info(bars_daily)")}
    assert {"dollar_volume", "close_vendor", "closeadj_vendor", "lastupdated"} <= cols
    cols = {r[1] for r in conn.execute("PRAGMA table_info(listing)")}
    assert {"reason", "exchange"} <= cols


# ------------------------------------------------------------------- writer
def _bar(**kw):
    row = dict(market=EQ, symbol="1", date="2021-03-01", close=1.0, available_at="2021-03-01")
    row.update(kw)
    return row


def test_writer_refuses_missing_or_malformed_available_at(conn):
    for bad in (None, "", "2021-3-1", "2021-03-01T00:00:00Z"):
        with pytest.raises(StoreWriteError, match="available_at"):
            upsert(conn, "bars_daily", SNAPSHOT, [_bar(available_at=bad)])
    with pytest.raises(StoreWriteError, match="available_at"):
        upsert(conn, "bars_daily", SNAPSHOT, [{k: v for k, v in _bar().items()
                                                if k != "available_at"}])


def test_writer_refuses_rows_available_before_their_date(conn):
    with pytest.raises(StoreWriteError, match="before"):
        upsert(conn, "bars_daily", SNAPSHOT, [_bar(date="2021-03-02", available_at="2021-03-01")])
    with pytest.raises(StoreWriteError, match="before"):
        upsert(conn, "events", SNAPSHOT, [dict(market=EQ, symbol="1", filing_date="2021-03-02",
                                               available_at="2021-03-01")])


def test_writer_requires_available_at_equal_to_date_for_date_known_tables(conn):
    """Batched reads (one panel as of the end of a range) are correct only if a row
    dated t is known on t for these tables (schema.AVAILABLE_ON_DATE)."""
    with pytest.raises(StoreWriteError, match="must equal"):
        upsert(conn, "bars_daily", SNAPSHOT, [_bar(date="2021-03-01", available_at="2021-03-02")])
    with pytest.raises(StoreWriteError, match="must equal"):
        upsert(conn, "marketcap", SNAPSHOT, [dict(market=EQ, symbol="1", date="2021-03-01",
                                                  marketcap=1e9, available_at="2021-03-02")])
    with pytest.raises(StoreWriteError, match="must equal"):
        upsert(conn, "listing", SNAPSHOT, [dict(market=EQ, symbol="1", event="delisted",
                                                date="2021-02-24", available_at="2021-03-03")])
    # EVENTS are the documented exception: known the session after filing.
    upsert(conn, "events", SNAPSHOT, [dict(market=EQ, symbol="1", filing_date="2021-03-01",
                                           available_at="2021-03-02")])


def test_writer_requires_a_registered_snapshot_and_known_columns(conn):
    with pytest.raises(StoreWriteError, match="not registered"):
        upsert(conn, "bars_daily", "nope", [_bar()])
    with pytest.raises(StoreWriteError, match="unknown columns"):
        upsert(conn, "bars_daily", SNAPSHOT, [_bar(adj_close=1.0)])
    with pytest.raises(StoreWriteError, match="differs"):
        upsert(conn, "bars_daily", SNAPSHOT, [_bar(snapshot_id="other")])


def test_a_failed_batch_writes_nothing(conn):
    before = _counts(conn)
    with pytest.raises(StoreWriteError):
        upsert(conn, "bars_daily", SNAPSHOT, [_bar(symbol="new"), _bar(available_at=None)])
    assert _counts(conn) == before


def test_reload_of_the_same_snapshot_is_idempotent(conn):
    before = _counts(conn)
    build_store(conn)
    assert _counts(conn) == before


def test_two_snapshots_coexist_and_reads_are_scoped(conn):
    before = _counts(conn)
    build_store(conn, snapshot_id="snap-b", price_scale=2.0)
    after = _counts(conn)
    assert after["snapshots"] == 2
    assert all(after[t] == 2 * before[t] for t in TABLES)
    d = "2021-03-05"
    a = AsOfReader(conn, SNAPSHOT).bars(EQ, DIV_SYM, d, d)
    b = AsOfReader(conn, "snap-b").bars(EQ, DIV_SYM, d, d)
    assert len(a) == len(b) == 1
    assert _close(b, DIV_SYM, d) == pytest.approx(2 * _close(a, DIV_SYM, d))
    with pytest.raises(KeyError):
        AsOfReader(conn, "snap-missing")


# --------------------------------------------------------------- adjustment
def test_split_reconstructed_before_and_after(reader):
    before, day_before = "2021-03-16", "2021-03-16"
    raw = unadjusted_close(SPLIT_SYM, day_before)

    # As-of the day before the split: the split is not known and not applied.
    for adj in ("none", "split", "split_div"):
        out = reader.panel(EQ, [SPLIT_SYM], START, END, before, adj)
        assert out["date"].max() == before
        assert _close(out, SPLIT_SYM, day_before) == pytest.approx(raw)

    # As-of the split date: earlier bars are divided by the ratio, volume multiplied.
    for adj in ("split", "split_div"):
        out = reader.panel(EQ, [SPLIT_SYM], START, END, SPLIT_DATE, adj)
        assert _close(out, SPLIT_SYM, day_before) == pytest.approx(raw / SPLIT_RATIO)
        assert _close(out, SPLIT_SYM, SPLIT_DATE) == pytest.approx(
            unadjusted_close(SPLIT_SYM, SPLIT_DATE))
        pre = out[out["date"] < SPLIT_DATE]
        assert (pre["volume"] == 1_000_000.0 * SPLIT_RATIO).all()
        # dollar volume is never adjusted
        raw_pre = reader.panel(EQ, [SPLIT_SYM], START, END, SPLIT_DATE, "none")
        raw_pre = raw_pre[raw_pre["date"] < SPLIT_DATE]
        assert list(pre["dollar_volume"]) == list(raw_pre["dollar_volume"])
        # The adjusted series is continuous across the split in the fixture.
        assert _close(out, SPLIT_SYM, SPLIT_DATE) / _close(out, SPLIT_SYM, day_before) == \
            pytest.approx((100.0 + weekdays().index(SPLIT_DATE)) / (100.0 + weekdays().index(day_before)))

    # Unadjusted reads never change.
    out = reader.panel(EQ, [SPLIT_SYM], START, END, END, "none")
    assert _close(out, SPLIT_SYM, day_before) == pytest.approx(raw)

    # Single-date read agrees with the panel.
    one = reader.bars(EQ, SPLIT_SYM, day_before, END, "split")
    assert _close(one, SPLIT_SYM, day_before) == pytest.approx(raw / SPLIT_RATIO)


def test_dividend_applied_in_split_div_only(reader):
    prev = weekdays()[weekdays().index(DIV_DATE) - 1]
    prev_close = unadjusted_close(DIV_SYM, prev)
    factor = 1.0 - DIV_AMOUNT / prev_close
    for as_of in (DIV_DATE, END):
        none = reader.panel(EQ, [DIV_SYM], START, END, as_of, "none")
        split = reader.panel(EQ, [DIV_SYM], START, END, as_of, "split")
        div = reader.panel(EQ, [DIV_SYM], START, END, as_of, "split_div")
        assert _close(split, DIV_SYM, prev) == pytest.approx(prev_close)
        assert _close(none, DIV_SYM, prev) == pytest.approx(prev_close)
        assert _close(div, DIV_SYM, prev) == pytest.approx(prev_close * factor)
        assert _close(div, DIV_SYM, DIV_DATE) == pytest.approx(unadjusted_close(DIV_SYM, DIV_DATE))
        assert list(div["volume"]) == list(none["volume"])
    # Before the ex-date the dividend is not known.
    div = reader.panel(EQ, [DIV_SYM], START, END, prev, "split_div")
    assert _close(div, DIV_SYM, prev) == pytest.approx(prev_close)


def test_actions_after_as_of_never_applied(reader):
    early = reader.panel(EQ, None, START, "2021-03-05", "2021-03-09", "split_div")
    raw = reader.panel(EQ, None, START, "2021-03-05", "2021-03-09", "none")
    assert early["close"].tolist() == pytest.approx(raw["close"].tolist())


def test_oracle_converts_later_bars_into_the_entry_basis(conn):
    o = OracleReader(conn, SNAPSHOT, last_date=END, holdout_start="2024-01-01")
    basis = "2021-03-16"
    out = o.bars(EQ, [SPLIT_SYM], basis, END, adjust="split", basis=basis)
    after = "2021-03-18"
    assert _close(out, SPLIT_SYM, after) == pytest.approx(
        unadjusted_close(SPLIT_SYM, after) * SPLIT_RATIO)
    assert _close(out, SPLIT_SYM, basis) == pytest.approx(unadjusted_close(SPLIT_SYM, basis))


# ---------------------------------------------------------------- calendars
def test_nyse_calendar_has_no_weekends_after_crypto_rows_are_loaded(conn, reader):
    assert conn.execute("SELECT COUNT(*) FROM bars_daily WHERE market = 'binance_spot' "
                        "AND strftime('%w', date) IN ('0', '6')").fetchone()[0] > 0
    assert conn.execute("SELECT COUNT(*) FROM bars_hourly").fetchone()[0] > 0
    build_nyse_calendar(conn, SNAPSHOT)  # rebuilding after crypto is loaded
    nyse = reader.calendar("nyse", START, END, END)
    assert list(nyse["date"]) == weekdays()
    utc = reader.calendar("utc", START, END, END)
    assert list(utc["date"]) == days()


def test_nyse_calendar_refuses_weekend_equity_bars(conn):
    upsert(conn, "bars_daily", SNAPSHOT, [_bar(date="2021-03-06", available_at="2021-03-06")])
    with pytest.raises(ValueError, match="weekend"):
        build_nyse_calendar(conn, SNAPSHOT)


def test_lane_calendar_map():
    assert LANE_CALENDAR == {"smallcap": "nyse", "discovered": "nyse", "crypto": "utc"}
    assert calendar_for_lane("crypto") == "utc"
    with pytest.raises(ValueError):
        calendar_for_lane("largecap")


def test_next_session_skips_the_weekend(conn):
    assert next_session(conn, SNAPSHOT, "nyse", "2021-03-12") == "2021-03-15"
    assert next_session(conn, SNAPSHOT, "utc", "2021-03-12") == "2021-03-13"
    assert next_session(conn, SNAPSHOT, "nyse", END) is None


# -------------------------------------------------------- listing and events
def test_listed_honours_listing_and_delisting_boundaries(reader):
    def listed(d, as_of=END):
        return set(reader.listed(EQ, d, as_of)["symbol"])

    day_before_listing = weekdays()[weekdays().index(DELIST_LISTED) - 1]
    day_before_delisting = weekdays()[weekdays().index(DELIST_DATE) - 1]
    assert DELIST_SYM not in listed(day_before_listing)
    assert DELIST_SYM in listed(DELIST_LISTED)
    assert DELIST_SYM in listed(day_before_delisting)
    assert DELIST_SYM not in listed(DELIST_DATE)
    assert DELIST_SYM not in listed(END)
    assert {SPLIT_SYM, DIV_SYM} <= listed(END)
    # As-of before the delisting is known, the name still reads as listed.
    assert DELIST_SYM in listed(END, as_of=day_before_delisting)
    assert set(reader.listed("binance_spot", START, START)["symbol"]) == {"BTCUSDT", "ETHUSDT"}


def test_delisting_reason_and_exchange(reader):
    out = reader.listing(EQ, DELIST_SYM, START, END, END)
    d = out[out["event"] == "delisted"].iloc[0]
    assert (d["date"], d["reason"], d["exchange"]) == (DELIST_DATE, "bankruptcyliquidation", "NASDAQ")


def test_ticker_change_keeps_one_permaticker(reader):
    acts = reader.actions(EQ, None, START, END, END)
    tc = acts[acts["action"].str.startswith("tickerchange")]
    assert set(tc["symbol"]) == {SPLIT_SYM}
    assert set(reader.symbols(EQ, None, END)["symbol"]) == {SPLIT_SYM, DIV_SYM, DELIST_SYM}


def test_after_close_filing_available_next_session(reader):
    sym, filed, available = EVENT_AFTER_CLOSE
    assert reader.events(EQ, sym, filed, filed, filed).empty
    got = reader.events(EQ, sym, filed, filed, available)
    assert list(got["available_at"]) == [available]
    sym, filed, available = EVENT_BEFORE_CLOSE
    assert list(reader.events(EQ, sym, filed, filed, filed)["available_at"]) == [available]


def test_marketcap_read(reader):
    out = reader.marketcap(EQ, [DIV_SYM], START, END, "2021-03-05")
    assert out["date"].max() == "2021-03-05" and len(out) == 5


# ------------------------------------------------------------------ oracle
def test_oracle_refuses_past_last_date(conn):
    o = OracleReader(conn, SNAPSHOT, last_date="2021-03-19", holdout_start="2024-01-01")
    assert o.bars(EQ, None, START, "2021-03-19")["date"].max() == "2021-03-19"
    for read in (lambda: o.bars(EQ, None, START, "2021-03-22"),
                 lambda: o.hourly("binance_spot", None, START, "2021-03-20"),
                 lambda: o.actions(EQ, None, START, END),
                 lambda: o.listing(EQ, None, START, END),
                 lambda: o.events(EQ, None, START, END),
                 lambda: o.calendar("nyse", START, END)):
        with pytest.raises(OracleBoundError):
            read()


def test_oracle_refuses_the_holdout_unless_unlocked(conn):
    holdout = "2021-03-15"
    locked = OracleReader(conn, SNAPSHOT, last_date=END, holdout_start=holdout)
    with pytest.raises(HoldoutLockedError):
        locked.bars(EQ, None, START, holdout)
    with pytest.raises(HoldoutLockedError):
        locked.events(EQ, None, START, END)
    assert locked.bars(EQ, None, START, "2021-03-12")["date"].max() == "2021-03-12"

    unlocked = OracleReader(conn, SNAPSHOT, last_date=END, holdout_start=holdout, unlocked=True)
    assert unlocked.bars(EQ, None, START, END)["date"].max() == END
    events = unlocked.events(EQ, None, START, END)
    assert len(events) == 2


def test_oracle_bound_is_also_in_the_sql(conn):
    o = OracleReader(conn, SNAPSHOT, last_date=END, holdout_start="2021-03-15")
    assert o.bound == "2021-03-14"
    o._check = lambda end: end  # a caller that bypasses the check still can't widen the read
    assert o.bars(EQ, None, START, END)["date"].max() <= "2021-03-14"
    assert o.hourly("binance_spot", None, START, END)["ts"].max() < "2021-03-15"


def test_oracle_reads_future_bars_the_as_of_reader_does_not(conn, reader):
    o = OracleReader(conn, SNAPSHOT, last_date=END, holdout_start="2024-01-01")
    assert o.bars(EQ, [DIV_SYM], "2021-03-10", "2021-03-12")["date"].tolist() == \
        ["2021-03-10", "2021-03-11", "2021-03-12"]
    assert reader.panel(EQ, [DIV_SYM], "2021-03-10", "2021-03-12", "2021-03-10")["date"].tolist() == \
        ["2021-03-10"]


def test_connect_on_a_file(tmp_path):
    path = tmp_path / "store.sqlite"
    c = connect(path)
    register_snapshot(c, "s", "2021-01-01T00:00:00Z", 0, {})
    c.close()
    assert schema_version(connect(path)) == SCHEMA_VERSION


def test_as_of_accepts_dates_and_midnight_timestamps_only(reader):
    import datetime as dt
    import pandas as pd
    a = reader.bars(EQ, DIV_SYM, "2021-03-05", "2021-03-05")
    b = reader.bars(EQ, DIV_SYM, dt.date(2021, 3, 5), pd.Timestamp("2021-03-05"))
    assert a.equals(b)
    with pytest.raises(ValueError):
        reader.bars(EQ, DIV_SYM, "2021-03-05", pd.Timestamp("2021-03-05 15:00"))
    with pytest.raises(ValueError):
        reader.bars(EQ, DIV_SYM, "2021-03-05", "2021-03-05T00:00:00Z")

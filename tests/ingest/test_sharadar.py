"""Tests for `ingest.sharadar` (issues 3, 5): SEP/TICKERS/ACTIONS/DAILY/EVENTS/SFP
into the store, against the hand-written vendor-shaped fixtures in
`tests/fixtures/sharadar.py`. No Sharadar API key exists; everything here runs
against fixtures, never the network (`docs/architecture.md` Testing).
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

import ingest.sharadar as sharadar
from harness.store import AsOfReader, connect
from tests.fixtures import sharadar as sfx
from tests.store.test_leakage import READS, _bound, _truncated

SNAPSHOT_ID = "sharadar-fixture-1"

# Tables this loader populates; bars_hourly and lane_membership are other
# units' concern (Binance ingest, the universe builder) and are never written
# here, so they are left out of the reused leakage machinery below.
OUR_TABLES = ["calendar", "symbols", "bars_daily", "actions", "listing", "marketcap", "events"]

EQ = "us_equity"


def _plus(d: str, n: int) -> str:
    import datetime as dt
    return (dt.date.fromisoformat(d) + dt.timedelta(days=n)).isoformat()


@pytest.fixture(scope="module")
def files(tmp_path_factory) -> dict[str, Path]:
    return sfx.write_files(tmp_path_factory.mktemp("sharadar-raw"))


@pytest.fixture(scope="module")
def loaded(files):
    conn = connect(":memory:")
    report = sharadar.load(conn, SNAPSHOT_ID, files)
    return conn, report


@pytest.fixture(scope="module")
def loaded_conn(loaded):
    return loaded[0]


@pytest.fixture(scope="module")
def report(loaded):
    return loaded[1]


@pytest.fixture(scope="module")
def reader(loaded_conn):
    return AsOfReader(loaded_conn, SNAPSHOT_ID)


def _rows(conn, table: str, **where) -> list[tuple]:
    clauses = " AND ".join(f"{k} = ?" for k in where)
    sql = f"SELECT * FROM {table} WHERE snapshot_id = ?" + (f" AND {clauses}" if clauses else "")
    cur = conn.execute(sql, (SNAPSHOT_ID, *where.values()))
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


# --------------------------------------------------------------- idempotency

def test_load_is_idempotent(files):
    conn = connect(":memory:")
    r1 = sharadar.load(conn, "idem-snap", files)
    r2 = sharadar.load(conn, "idem-snap", files)
    for table in r1.tables:
        assert r1.tables[table].rows_written == r2.tables[table].rows_written, table
    for table in ("symbols", "bars_daily", "actions", "listing", "marketcap", "events"):
        n = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE snapshot_id = ?",
                         ("idem-snap",)).fetchone()[0]
        assert n > 0
        sharadar.load(conn, "idem-snap", files)  # a third load changes nothing further
        n2 = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE snapshot_id = ?",
                          ("idem-snap",)).fetchone()[0]
        assert n2 == n, table


# ------------------------------------------------------ ticker -> permaticker

def test_recycled_ticker_maps_to_distinct_permatickers(loaded_conn):
    old_dates = {r["date"] for r in _rows(loaded_conn, "bars_daily", market=EQ, symbol=sfx.RECYCLED_OLD_PT)}
    new_dates = {r["date"] for r in _rows(loaded_conn, "bars_daily", market=EQ, symbol=sfx.RECYCLED_NEW_PT)}
    assert old_dates and new_dates
    assert old_dates.issubset({d.strftime("%Y-%m-%d") for d in pd.bdate_range(
        sfx.RECYCLED_OLD_FIRST, sfx.RECYCLED_OLD_LAST)})
    assert new_dates.issubset(set(sfx.WEEKDAYS))
    assert not (old_dates & new_dates)


def test_ticker_change_carries_history_under_one_permaticker(loaded_conn):
    """Issue 3's hand-check: AAA -> AAB is one permaticker's whole history."""
    dates = sorted(r["date"] for r in _rows(loaded_conn, "bars_daily", market=EQ, symbol=sfx.RENAME_PT))
    assert dates == sfx.WEEKDAYS
    change = _rows(loaded_conn, "actions", market=EQ, symbol=sfx.RENAME_PT, action="tickerchangeto")
    assert len(change) == 1
    assert change[0]["date"] == sfx.RENAME_DATE
    assert change[0]["contraticker"] == sfx.RENAME_OLD_TICKER
    sym = _rows(loaded_conn, "symbols", market=EQ, symbol=sfx.RENAME_PT)
    assert len(sym) == 1
    assert sym[0]["ticker"] == sfx.RENAME_NEW_TICKER  # current ticker
    assert sym[0]["available_at"] == "2015-01-02"      # first-ever listing, not the rename date


def test_unmapped_rows_are_rejected_not_silent(tmp_path):
    files_local = sfx.write_files(tmp_path / "raw")
    actions = pd.concat([sfx.actions_df(), pd.DataFrame([dict(
        date="2021-03-10", action="listed", ticker="NOPE", name=None, value=None,
        contraticker=None, contraname=None)])], ignore_index=True)
    sfx._zip_csv(actions, files_local["ACTIONS"], "SHARADAR_ACTIONS.csv")

    conn = connect(":memory:")
    rejects_dir = tmp_path / "rejects"
    rpt = sharadar.load(conn, "unmapped-snap", files_local, rejects_dir=rejects_dir)

    assert rpt.tables["ACTIONS"].unmapped == 1
    assert len(rpt.unmapped_rows["ACTIONS"]) == 1
    assert rpt.unmapped_rows["ACTIONS"].iloc[0]["ticker"] == "NOPE"
    reject_file = rejects_dir / "unmapped-snap-ACTIONS-rejects.csv"
    assert reject_file.exists()
    assert "NOPE" in reject_file.read_text()


def test_load_snapshot_reads_the_fetcher_document(tmp_path):
    from ingest.fetch.storage import Storage

    storage = Storage(str(tmp_path / "data-root"))
    raw_files = sfx.write_files(tmp_path / "scratch")
    groups = {}
    files_doc = {}
    for table, local_path in raw_files.items():
        # A Sharadar file restated under a versioned path, per PR 19's layout,
        # to prove load_snapshot reads the exact path the document names.
        rel = f"raw/sharadar/{table}/_v/2026Q3/{table}-2026Q3.zip"
        storage.write_bytes(rel, local_path.read_bytes())
        groups[table] = rel
        files_doc[rel] = {"size": storage.size(rel), "sha256": storage.sha256(rel)}

    doc = {"snapshot_id": "fetcher-snap-1", "created_at": "2026-04-01T00:00:00Z",
          "file_count": len(files_doc), "files": files_doc,
          "sources": {"sharadar": sorted(groups.values())}, "groups": {"sharadar": groups}}
    storage.write_json("snapshots/fetcher-snap-1.json", doc)

    conn = connect(":memory:")
    rpt = sharadar.load_snapshot(conn, storage, "fetcher-snap-1")

    assert rpt.tables["SEP"].rows_written == len(sfx.sep_df())
    row = conn.execute("SELECT document FROM snapshots WHERE snapshot_id = ?",
                       ("fetcher-snap-1",)).fetchone()
    assert row is not None
    stored_doc = json.loads(row[0])
    assert stored_doc["created_at"] == "2026-04-01T00:00:00Z"
    assert stored_doc["groups"]["sharadar"]["SEP"] == groups["SEP"]


def test_load_snapshot_missing_document_raises(tmp_path):
    from ingest.fetch.storage import Storage
    storage = Storage(str(tmp_path / "data-root"))
    conn = connect(":memory:")
    with pytest.raises(sharadar.SharadarLoadError):
        sharadar.load_snapshot(conn, storage, "does-not-exist")


# ------------------------------------------------------------------- SEP/OHLV

def test_sep_close_is_closeunadj_and_dollar_volume_matches(loaded_conn):
    rows = _rows(loaded_conn, "bars_daily", market=EQ, symbol=sfx.DIV_PT, date=sfx.WEEKDAYS[0])
    assert len(rows) == 1
    r = rows[0]
    expected = sfx._series(sfx.WEEKDAYS, base=40.0, step=0.1).iloc[0]
    assert r["close"] == pytest.approx(expected["closeunadj"])
    assert r["close_vendor"] == pytest.approx(expected["vendor_close"])
    assert r["closeadj_vendor"] == pytest.approx(expected["vendor_close"])
    assert r["dollar_volume"] == pytest.approx(r["close"] * r["volume"])
    assert r["available_at"] == sfx.WEEKDAYS[0]


def test_sep_imputed_ohlv_uses_closeunadj_over_close_ratio(loaded_conn):
    # A date after the split: vendor close == closeunadj, so the ratio is 1 and
    # imputed values equal the vendor's own OHLV exactly.
    d = sfx.WEEKDAYS[-1]
    r = _rows(loaded_conn, "bars_daily", market=EQ, symbol=sfx.RENAME_PT, date=d)[0]
    expected = sfx._series(sfx.WEEKDAYS, base=100.0, step=0.5, split_date=sfx.SPLIT_DATE,
                           split_ratio=sfx.SPLIT_RATIO)
    raw = expected[expected["date"] == d].iloc[0]
    assert r["close"] == pytest.approx(round(raw["closeunadj"], 4))
    assert r["open"] == pytest.approx(round(raw["vendor_close"] - 0.5, 4))


# ------------------------------------------------------------------ splits

def test_split_not_applied_before_it_is_known(reader):
    day_before_split = sfx.WEEKDAYS[sfx.WEEKDAYS.index(sfx.SPLIT_DATE) - 1]
    d0 = sfx.WEEKDAYS[0]
    bars = reader.bars(EQ, [sfx.RENAME_PT], d0, day_before_split, adjust="split")
    expected = sfx._series(sfx.WEEKDAYS, base=100.0, step=0.5, split_date=sfx.SPLIT_DATE,
                           split_ratio=sfx.SPLIT_RATIO)
    raw = expected[expected["date"] == d0].iloc[0]
    assert bars.iloc[0]["close"] == pytest.approx(round(raw["closeunadj"], 4))


def test_split_reconstructs_correctly_after_it_is_known(reader):
    d0 = sfx.WEEKDAYS[0]
    as_of = sfx.WEEKDAYS[-1]
    bars = reader.bars(EQ, [sfx.RENAME_PT], d0, as_of, adjust="split")
    expected = sfx._series(sfx.WEEKDAYS, base=100.0, step=0.5, split_date=sfx.SPLIT_DATE,
                           split_ratio=sfx.SPLIT_RATIO)
    raw = expected[expected["date"] == d0].iloc[0]
    # By construction the fixture's vendor `close` pre-split is closeunadj / ratio,
    # exactly what the as-of-after-split adjusted series should reproduce.
    assert bars.iloc[0]["close"] == pytest.approx(round(raw["vendor_close"], 4), abs=1e-6)


# --------------------------------------------------------------- dividends

def test_dividend_shows_only_in_split_div_series(reader, loaded_conn):
    d0 = sfx.WEEKDAYS[0]
    as_of = sfx.WEEKDAYS[-1]
    none_bars = reader.bars(EQ, [sfx.DIV_PT], d0, as_of, adjust="none")
    split_bars = reader.bars(EQ, [sfx.DIV_PT], d0, as_of, adjust="split")
    div_bars = reader.bars(EQ, [sfx.DIV_PT], d0, as_of, adjust="split_div")

    assert split_bars.iloc[0]["close"] == pytest.approx(none_bars.iloc[0]["close"])

    prev_day = sfx.WEEKDAYS[sfx.WEEKDAYS.index(sfx.DIV_DATE) - 1]
    prev_close = _rows(loaded_conn, "bars_daily", market=EQ, symbol=sfx.DIV_PT, date=prev_day)[0]["close"]
    factor = 1.0 - sfx.DIV_AMOUNT / prev_close
    assert div_bars.iloc[0]["close"] == pytest.approx(none_bars.iloc[0]["close"] * factor)
    assert div_bars.iloc[0]["close"] != pytest.approx(none_bars.iloc[0]["close"])


# ------------------------------------------------------------------ listing

def test_bankruptcy_delisting_carries_reason_and_exchange(loaded_conn):
    rows = _rows(loaded_conn, "listing", market=EQ, symbol=sfx.BANKRUPTCY_PT, event="delisted")
    assert len(rows) == 1
    assert rows[0]["reason"] == "bankruptcyliquidation"
    assert rows[0]["exchange"] == "NASDAQ"
    assert rows[0]["source"] == "actions"
    assert rows[0]["date"] == sfx.BANKRUPTCY_DATE


def test_acquisition_delisting_carries_reason_and_exchange(loaded_conn):
    rows = _rows(loaded_conn, "listing", market=EQ, symbol=sfx.ACQUIRED_PT, event="delisted")
    assert len(rows) == 1
    assert rows[0]["reason"] == "acquisitionby"
    assert rows[0]["exchange"] == "NYSE"


def test_tickers_fallback_when_actions_has_no_listing_rows(loaded_conn):
    listed = _rows(loaded_conn, "listing", market=EQ, symbol=sfx.FALLBACK_PT, event="listed")
    delisted = _rows(loaded_conn, "listing", market=EQ, symbol=sfx.FALLBACK_PT, event="delisted")
    assert len(listed) == 1 and listed[0]["source"] == "tickers_fallback"
    assert listed[0]["date"] == sfx.FALLBACK_FIRST
    assert len(delisted) == 1 and delisted[0]["source"] == "tickers_fallback"
    # Dated the first nyse session *after* lastpricedate, not lastpricedate
    # itself: lastpricedate is the name's real last trading day, and a name
    # is not listed on its own delisting date (spec/01).
    day_after_last = sfx.WEEKDAYS[sfx.WEEKDAYS.index(sfx.FALLBACK_LAST) + 1]
    assert delisted[0]["date"] == day_after_last
    assert delisted[0]["date"] != sfx.FALLBACK_LAST


def test_tickers_fallback_delisting_keeps_the_last_trading_day_listed(reader):
    still = reader.listed(EQ, sfx.FALLBACK_LAST, sfx.FALLBACK_LAST)
    assert sfx.FALLBACK_PT in set(still["symbol"])
    day_after_last = sfx.WEEKDAYS[sfx.WEEKDAYS.index(sfx.FALLBACK_LAST) + 1]
    gone = reader.listed(EQ, day_after_last, day_after_last)
    assert sfx.FALLBACK_PT not in set(gone["symbol"])


def test_active_symbol_has_no_delisted_event(loaded_conn):
    delisted = _rows(loaded_conn, "listing", market=EQ, symbol=sfx.RENAME_PT, event="delisted")
    assert delisted == []


def test_listed_reader_excludes_delisted_names(reader):
    day_before = sfx.WEEKDAYS[sfx.WEEKDAYS.index(sfx.BANKRUPTCY_DATE) - 1]
    still = reader.listed(EQ, day_before, day_before)
    assert sfx.BANKRUPTCY_PT in set(still["symbol"])
    # spec/02 Store: not listed on the delisting date itself ("no delisting
    # event on or before D"; docs/store.md "Open points").
    gone = reader.listed(EQ, sfx.BANKRUPTCY_DATE, sfx.BANKRUPTCY_DATE)
    assert sfx.BANKRUPTCY_PT not in set(gone["symbol"])


# --------------------------------------------------------------- exchange_on

def test_exchange_on_reflects_the_move_from_nasdaq_to_nyse(reader):
    day_before = sfx.WEEKDAYS[sfx.WEEKDAYS.index(sfx.MOVE_DATE) - 1]
    before = reader.exchange_on(EQ, [sfx.MOVE_PT], day_before, sfx.WEEKDAYS[-1])
    after = reader.exchange_on(EQ, [sfx.MOVE_PT], sfx.MOVE_DATE, sfx.WEEKDAYS[-1])
    assert before.iloc[0]["exchange"] == "NASDAQ"
    assert before.iloc[0]["source"] == "actions"
    assert after.iloc[0]["exchange"] == "NYSE"
    assert after.iloc[0]["source"] == "actions"

    # As-of before the move is known, the store hasn't seen the NYSE listing yet.
    as_of_before_move = day_before
    still_old = reader.exchange_on(EQ, [sfx.MOVE_PT], sfx.MOVE_DATE, as_of_before_move)
    assert still_old.iloc[0]["exchange"] == "NASDAQ"


def test_exchange_on_falls_back_to_tickers_when_no_actions_event(reader):
    out = reader.exchange_on(EQ, [sfx.FALLBACK_PT], sfx.FALLBACK_LAST, sfx.WEEKDAYS[-1])
    assert len(out) == 1
    assert out.iloc[0]["exchange"] == "NYSE"
    assert out.iloc[0]["source"] == "tickers_fallback"


@pytest.mark.leakage
def test_exchange_on_never_leaks_a_future_event(reader):
    day_before = sfx.WEEKDAYS[sfx.WEEKDAYS.index(sfx.MOVE_DATE) - 1]
    for a in (day_before, sfx.MOVE_DATE, sfx.WEEKDAYS[-1]):
        out = reader.exchange_on(EQ, [sfx.MOVE_PT], sfx.WEEKDAYS[-1], a)
        assert (out["available_at"] <= a).all()
        expected = "NASDAQ" if a < sfx.MOVE_DATE else "NYSE"
        assert out.iloc[0]["exchange"] == expected


# ---------------------------------------------------------------------- ADR/OTC

def test_adr_and_otc_names_are_stored_for_issue_6_to_exclude(loaded_conn):
    adr = _rows(loaded_conn, "symbols", market=EQ, symbol=sfx.ADR_PT)[0]
    otc = _rows(loaded_conn, "symbols", market=EQ, symbol=sfx.OTC_PT)[0]
    assert adr["category"] == "ADR Common Stock"
    assert otc["exchange"] == "OTC"


# ------------------------------------------------------------------------- DAILY

def test_marketcap_available_at_is_the_date(loaded_conn):
    r = _rows(loaded_conn, "marketcap", market=EQ, symbol=sfx.RENAME_PT, date=sfx.WEEKDAYS[0])[0]
    assert r["available_at"] == sfx.WEEKDAYS[0]
    assert r["marketcap"] > 0


# ------------------------------------------------------------------------ EVENTS

def test_events_available_next_session_friday_to_monday(loaded_conn):
    r = _rows(loaded_conn, "events", market=EQ, symbol=sfx.DIV_PT, filing_date=sfx.EVENT_FRIDAY)[0]
    assert r["available_at"] == sfx.EVENT_FRIDAY_AVAILABLE == "2021-03-15"


def test_events_available_next_session_friday_to_tuesday_after_holiday(loaded_conn):
    r = _rows(loaded_conn, "events", market=EQ, symbol=sfx.DIV_PT,
             filing_date=sfx.EVENT_HOLIDAY_FRIDAY)[0]
    assert r["available_at"] == sfx.EVENT_HOLIDAY_AVAILABLE == "2021-03-30"


# --------------------------------------------------------------------------- SFP

def test_sfp_loads_spy_only_under_its_own_symbol(loaded_conn):
    spy = _rows(loaded_conn, "bars_daily", market=EQ, symbol=sharadar.SFP_SYMBOL)
    assert len(spy) == len(sfx.WEEKDAYS)
    assert sharadar.SFP_SYMBOL == "SFP:SPY"
    assert not sharadar.SFP_SYMBOL.isdigit()  # never collides with a permaticker
    qqq = [r for r in _rows(loaded_conn, "bars_daily", market=EQ) if "QQQ" in str(r.get("symbol"))]
    assert qqq == []


# --------------------------------------------------------------------- calendar

def test_nyse_calendar_excludes_the_simulated_holiday(loaded_conn):
    dates = {r[0] for r in loaded_conn.execute(
        "SELECT date FROM calendar WHERE snapshot_id = ? AND calendar = 'nyse'", (SNAPSHOT_ID,))}
    assert sfx.HOLIDAY not in dates
    assert set(sfx.WEEKDAYS).issubset(dates)


# ----------------------------------------------------------------------- leakage

def _as_of_dates() -> list[str]:
    before = _plus(sfx.START, -1)
    after = _plus(sfx.END, 1)
    return [before, *sfx.WEEKDAYS, after]


@pytest.mark.leakage
@pytest.mark.parametrize("table", OUR_TABLES)
def test_no_leakage_single_date_read(reader, table):
    single, _ = READS[table]
    for a in _as_of_dates():
        for date in (a, _plus(a, -1), _plus(a, 1), _plus(a, 7)):
            out = single(reader, date, a)
            assert "available_at" in out.columns
            late = out[out["available_at"] > _bound(table, a)]
            assert late.empty, f"{table} as-of {a} date {date}:\n{late}"


@pytest.mark.leakage
@pytest.mark.parametrize("table", [t for t in OUR_TABLES if t != "symbols"])
def test_no_leakage_windowed_read(reader, table):
    _, window = READS[table]
    for a in _as_of_dates():
        out = window(reader, a)
        late = out[out["available_at"] > _bound(table, a)]
        assert late.empty, f"{table} as-of {a}:\n{late}"


@pytest.mark.leakage
@pytest.mark.parametrize("as_of", ["2021-03-09", "2021-03-10", "2021-03-15", "2021-03-17",
                                   "2021-03-20", "2021-03-24", "2021-03-30", sfx.WEEKDAYS[-1]])
def test_reads_match_a_store_without_the_future(loaded_conn, reader, as_of):
    past = AsOfReader(_truncated(loaded_conn, as_of), SNAPSHOT_ID)
    for table in OUR_TABLES:
        single, window = READS[table]
        for date in (sfx.WEEKDAYS[0], as_of, sfx.WEEKDAYS[-1]):
            pd.testing.assert_frame_equal(single(reader, date, as_of), single(past, date, as_of),
                                          obj=f"{table} single {date} as-of {as_of}")
        if window is not None:
            pd.testing.assert_frame_equal(window(reader, as_of), window(past, as_of),
                                          obj=f"{table} window as-of {as_of}")

"""Sharadar SEP, TICKERS, ACTIONS, DAILY, EVENTS and SFP raw exports -> the
point-in-time store (spec/02-data.md Sources, Store; spec/01-lanes-and-universe.md
Point-in-time construction, Delisting while a position is open; spec/04
`filing_2d`). Issues 3 and 5.

Nasdaq Data Link delivers each table as a zip of one CSV (``ingest/fetch/sharadar.py``,
PR 19). This module only takes paths to those files; it never fetches them and never
imports ``ingest.fetch``. ``load()`` is the entry point:

    load(conn, snapshot_id, files={"SEP": ..., "TICKERS": ..., "ACTIONS": ...,
                                   "DAILY": ..., "EVENTS": ..., "SFP": ...},
        snapshot_doc=None, rejects_dir=None)

All six tables are required. Everything is written through
``harness.store.writer``, never straight SQL, so the writer's validation (a
registered snapshot, a well-formed ``available_at``, no unknown column) applies
to every row.

No Sharadar API key exists (`docs/environment.md`), so this loader has never run
against a real export. Every column name and every semantic assumed below is the
best public documentation and third-party schema reproduction available, not a
verified vendor contract; ``docs/ingest-sharadar.md`` lists exactly what a first
real load must check before it is trusted.

## Assumed vendor schemas (state clearly; verify on first real load)

- SEP and SFP: ``ticker, date, open, high, low, close, volume, closeadj,
  closeunadj, lastupdated``. `close` is split-adjusted only; `closeadj` is
  split-and-dividend adjusted; `closeunadj` is raw. All three of open/high/low
  and volume in the file are split-adjusted (not dividend-adjusted), matching
  `close`.
- TICKERS: includes at least ``table, permaticker, ticker, name, exchange,
  isdelisted, category, sector, firstpricedate, lastpricedate, lastupdated``.
  ``table`` names which price table (SEP or SFP) the row describes; the issue
  is explicit that permaticker mapping uses ``table == 'SEP'`` rows only.
  **Assumed**: a ticker that was ever renamed or recycled has one TICKERS row
  per ticker symbol it held, each carrying the same `permaticker` and its own
  `firstpricedate`/`lastpricedate` window (this is what makes a (ticker, date)
  -> permaticker join well-defined without a separate history table). If a real
  export instead carries only the current ticker per permaticker, historical
  ticker windows would have to be reconstructed from ACTIONS `tickerchangefrom`
  / `tickerchangeto` rows instead, and this loader would need a follow-up fix.
- ACTIONS: ``date, action, ticker, name, value, contraticker, contraname``. No
  `permaticker` and no `lastupdated` column. `action` values used here:
  `listed`; the delisting-reason types named in spec/01 (`acquisitionby`,
  `mergerto`, `voluntarydelisting`, `bankruptcyliquidation`,
  `regulatorydelisting`) plus a generic `delisted` catch-all; `split`;
  `dividend`; `tickerchangefrom` / `tickerchangeto`; anything else (`spinoff`,
  `spinoffdividend`, `adrratiosplit`, `relation`, ...) is stored as a plain
  `actions` row with its own type and untouched `value`.
- DAILY: includes at least ``ticker, date, lastupdated, marketcap``.
- EVENTS: ``ticker, date, eventcodes, lastupdated``, `date` being the EDGAR
  filing date.

## Split value semantics (flagged per the issue; conservative reading)

The store's convention (`docs/store.md`) is `actions.value` = shares after /
shares before for a split (2.0 for a 2-for-1). **Assumed**: Sharadar's own
`value` for a `split` action is already in that convention (a 2-for-1 split is
recorded as 2.0, a 1-for-5 reverse split as 0.2), so this loader passes it
through unchanged. No Sharadar documentation text confirming the direction was
reachable from this environment; the fixture is built on that assumption, not
derived from a real export. The check a first real load must make: pick one
known split, and confirm the adjustment in `harness/store/adjust.py` (which
multiplies by `1 / value`) reconstructs the pre-split price from the post-split
one -- if it instead doubles a price that should have halved, invert this
assumption (`value = 1 / vendor_value`).

## Dividends and other action types

`dividend` `value` is passed through unchanged as cash-per-share in the ex-date
share basis, matching the store's convention directly (spinoffs, ADR ratio
changes and other types are stored with their own type and vendor `value`;
`harness/store/adjust.py` does not interpret them).
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import logging
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

import pandas as pd

from config import env
from harness.store import (build_nyse_calendar, connect, next_session,
                           register_snapshot, upsert)

_log = logging.getLogger(__name__)

REQUIRED_TABLES = ("SEP", "TICKERS", "ACTIONS", "DAILY", "EVENTS", "SFP")

LISTED_ACTION = "listed"
DELISTING_REASONS = {
    "acquisitionby", "mergerto", "voluntarydelisting",
    "bankruptcyliquidation", "regulatorydelisting",
    "delisted",  # generic/unspecified reason, if the vendor emits it directly
}

SFP_TICKER = "SPY"
SFP_SYMBOL = "SFP:SPY"   # never a permaticker, so it can't collide with one (issue 5)

_TRUE_STRINGS = {"y", "yes", "true", "t", "1"}


class SharadarLoadError(ValueError):
    """A required table or column was missing from the supplied files."""


@dataclass
class TableReport:
    rows_read: int
    rows_written: int
    unmapped: int = 0


@dataclass
class LoadReport:
    tables: dict[str, TableReport] = field(default_factory=dict)
    unmapped_rows: dict[str, pd.DataFrame] = field(default_factory=dict)
    deferred_events: int = 0
    calendar_sessions: int = 0

    def summary(self) -> str:
        lines = []
        for name, t in self.tables.items():
            extra = f", {t.unmapped} unmapped" if t.unmapped else ""
            lines.append(f"{name}: read {t.rows_read}, wrote {t.rows_written}{extra}")
        if self.deferred_events:
            lines.append(f"EVENTS: {self.deferred_events} filings past the calendar horizon, deferred")
        lines.append(f"calendar: {self.calendar_sessions} nyse sessions")
        return "\n".join(lines)


# --------------------------------------------------------------------- reading

def _read_table(path: str | Path) -> pd.DataFrame:
    """Read a Sharadar bulk-export file: a zip of one CSV, or a bare CSV.

    Everything comes back as strings; callers convert the columns they use.
    """
    path = Path(path)
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as zf:
            names = [n for n in zf.namelist() if not n.endswith("/")]
            if len(names) != 1:
                raise SharadarLoadError(
                    f"{path}: expected exactly one file in the zip, found {names}")
            with zf.open(names[0]) as fh:
                return pd.read_csv(fh, dtype=str, keep_default_na=False, na_values=[""],
                                   quoting=csv.QUOTE_MINIMAL)
    return pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])


def _numeric(df: pd.DataFrame, columns: list[str]) -> None:
    for c in columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")


def _date10(s: pd.Series) -> pd.Series:
    return s.astype(str).str.slice(0, 10)


def _is_true(s: pd.Series) -> pd.Series:
    return s.fillna("").str.strip().str.lower().isin(_TRUE_STRINGS)


# ------------------------------------------------------------- ticker mapping

def _ticker_ranges(tickers_raw: pd.DataFrame) -> pd.DataFrame:
    """TICKERS rows for the SEP price table: one row per (permaticker, ticker
    symbol it has held), with the price-date window that ticker covers.

    Recycled tickers are two permatickers sharing a ticker over disjoint
    windows; a ticker change is one permaticker with two windows under two
    tickers (see the module docstring's assumption).
    """
    df = tickers_raw[tickers_raw["table"] == "SEP"].copy()
    if df.empty:
        raise SharadarLoadError("TICKERS: no rows with table == 'SEP'")
    df["firstpricedate"] = _date10(df["firstpricedate"])
    df["lastpricedate"] = _date10(df["lastpricedate"])
    df["isdelisted"] = _is_true(df["isdelisted"])
    for c in ("name", "category", "exchange", "sector", "lastupdated"):
        if c not in df.columns:
            df[c] = None
    return df[["permaticker", "ticker", "name", "category", "exchange", "sector",
              "isdelisted", "firstpricedate", "lastpricedate", "lastupdated"]]


def _map_permaticker(df: pd.DataFrame, ranges: pd.DataFrame, ticker_col: str,
                     date_col: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Attach `permaticker` to each row of `df` by (ticker, date) against the
    TICKERS price-date windows. Returns (mapped, unmapped).

    Unmapped rows never raise; the caller logs and reports them (issue 3: "Log
    the unmapped count and write the unmapped rows to a rejects report, never
    silently").
    """
    left = df.reset_index(drop=True).copy()
    left["_row"] = left.index
    r = ranges[["ticker", "permaticker", "firstpricedate", "lastpricedate"]].rename(
        columns={"ticker": "_range_ticker"})
    merged = left.merge(r, left_on=ticker_col, right_on="_range_ticker", how="left")
    in_range = (merged["firstpricedate"].notna()
               & (merged["firstpricedate"] <= merged[date_col])
               & (merged[date_col] <= merged["lastpricedate"]))
    hits = merged[in_range].sort_values("firstpricedate").drop_duplicates("_row", keep="last")
    mapped_rows = set(hits["_row"])
    mapped = left[left["_row"].isin(mapped_rows)].merge(
        hits[["_row", "permaticker"]], on="_row").drop(columns="_row")
    unmapped = left[~left["_row"].isin(mapped_rows)].drop(columns="_row")
    return mapped, unmapped


# ---------------------------------------------------------------- table loads

def _load_symbols(conn, snapshot_id: str, ranges: pd.DataFrame, report: LoadReport) -> None:
    rows = []
    for permaticker, g in ranges.groupby("permaticker"):
        current = g.sort_values("lastpricedate").iloc[-1]
        rows.append(dict(
            market="us_equity", symbol=str(permaticker), ticker=current["ticker"],
            name=current["name"], category=current["category"], exchange=current["exchange"],
            sector=current["sector"] or None, lastupdated=current["lastupdated"] or None,
            available_at=g["firstpricedate"].min()))
    n = upsert(conn, "symbols", snapshot_id, rows)
    report.tables["TICKERS"] = TableReport(len(ranges), n)


def _load_sep(conn, snapshot_id: str, raw: pd.DataFrame, ranges: pd.DataFrame,
             report: LoadReport) -> None:
    df = raw.copy()
    _numeric(df, ["open", "high", "low", "close", "volume", "closeadj", "closeunadj"])
    df["date"] = _date10(df["date"])
    mapped, unmapped = _map_permaticker(df, ranges, "ticker", "date")
    if len(unmapped):
        _log.warning("SEP: %d rows with no permaticker mapping (unknown ticker/date)", len(unmapped))

    ratio = mapped["closeunadj"] / mapped["close"]
    rows = pd.DataFrame({
        "market": "us_equity", "symbol": mapped["permaticker"], "date": mapped["date"],
        "open": mapped["open"] * ratio, "high": mapped["high"] * ratio,
        "low": mapped["low"] * ratio, "close": mapped["closeunadj"],
        "volume": mapped["volume"] * ratio,
        "close_vendor": mapped["close"], "closeadj_vendor": mapped["closeadj"],
        "lastupdated": mapped["lastupdated"], "available_at": mapped["date"],
    })
    rows["dollar_volume"] = rows["close"] * rows["volume"]
    n = upsert(conn, "bars_daily", snapshot_id, rows)
    report.tables["SEP"] = TableReport(len(df), n, len(unmapped))
    report.unmapped_rows["SEP"] = unmapped


def _load_actions_and_listing(conn, snapshot_id: str, raw: pd.DataFrame,
                              ranges: pd.DataFrame, report: LoadReport) -> None:
    df = raw.copy()
    df["date"] = _date10(df["date"])
    _numeric(df, ["value"])
    mapped, unmapped = _map_permaticker(df, ranges, "ticker", "date")
    if len(unmapped):
        _log.warning("ACTIONS: %d rows with no permaticker mapping (unknown ticker/date)", len(unmapped))

    action_rows = pd.DataFrame({
        "market": "us_equity", "symbol": mapped["permaticker"], "date": mapped["date"],
        "action": mapped["action"], "value": mapped["value"], "ticker": mapped["ticker"],
        "contraticker": mapped.get("contraticker"), "contraname": mapped.get("contraname"),
        "available_at": mapped["date"],
    })
    n_actions = upsert(conn, "actions", snapshot_id, action_rows)

    exch = mapped.merge(ranges[["permaticker", "ticker", "exchange"]],
                        on=["permaticker", "ticker"], how="left")

    listing_rows = []
    for _, r in exch[exch["action"] == LISTED_ACTION].iterrows():
        listing_rows.append(dict(market="us_equity", symbol=r["permaticker"], event="listed",
                                 date=r["date"], reason=None, exchange=None, source="actions",
                                 available_at=r["date"]))
    delisted = exch[exch["action"].isin(DELISTING_REASONS)]
    for _, r in delisted.iterrows():
        listing_rows.append(dict(market="us_equity", symbol=r["permaticker"], event="delisted",
                                 date=r["date"], reason=r["action"], exchange=r["exchange"],
                                 source="actions", available_at=r["date"]))

    listed_permatickers = set(exch.loc[exch["action"] == LISTED_ACTION, "permaticker"])
    delisted_permatickers = set(delisted["permaticker"])
    for permaticker, g in ranges.groupby("permaticker"):
        if permaticker not in listed_permatickers:
            d = g["firstpricedate"].min()
            listing_rows.append(dict(market="us_equity", symbol=permaticker, event="listed",
                                     date=d, reason=None, exchange=None,
                                     source="tickers_fallback", available_at=d))
        if permaticker not in delisted_permatickers and bool(g["isdelisted"].any()):
            last = g.sort_values("lastpricedate").iloc[-1]
            listing_rows.append(dict(market="us_equity", symbol=permaticker, event="delisted",
                                     date=last["lastpricedate"], reason=None,
                                     exchange=last["exchange"], source="tickers_fallback",
                                     available_at=last["lastpricedate"]))
    n_listing = upsert(conn, "listing", snapshot_id, listing_rows)

    report.tables["ACTIONS"] = TableReport(len(df), n_actions, len(unmapped))
    report.unmapped_rows["ACTIONS"] = unmapped
    report.tables["listing"] = TableReport(len(listing_rows), n_listing)


def _load_marketcap(conn, snapshot_id: str, raw: pd.DataFrame, ranges: pd.DataFrame,
                    report: LoadReport) -> None:
    df = raw.copy()
    df["date"] = _date10(df["date"])
    _numeric(df, ["marketcap"])
    mapped, unmapped = _map_permaticker(df, ranges, "ticker", "date")
    if len(unmapped):
        _log.warning("DAILY: %d rows with no permaticker mapping (unknown ticker/date)", len(unmapped))
    rows = pd.DataFrame({
        "market": "us_equity", "symbol": mapped["permaticker"], "date": mapped["date"],
        "marketcap": mapped["marketcap"], "lastupdated": mapped.get("lastupdated"),
        "available_at": mapped["date"],
    })
    n = upsert(conn, "marketcap", snapshot_id, rows)
    report.tables["DAILY"] = TableReport(len(df), n, len(unmapped))
    report.unmapped_rows["DAILY"] = unmapped


def _load_events(conn, snapshot_id: str, raw: pd.DataFrame, ranges: pd.DataFrame,
                 report: LoadReport) -> None:
    """EVENTS -> `events`. `available_at` is always the next NYSE session after the
    filing date (spec/04 `filing_2d`): Sharadar EVENTS carries no acceptance time,
    so the filing-date exception ("known to be before 16:00 ET") never applies
    here (`docs/ingest-sharadar.md`).
    """
    df = raw.copy()
    df["date"] = _date10(df["date"])
    mapped, unmapped = _map_permaticker(df, ranges, "ticker", "date")
    if len(unmapped):
        _log.warning("EVENTS: %d rows with no permaticker mapping (unknown ticker/date)", len(unmapped))

    rows = []
    deferred = 0
    for _, r in mapped.iterrows():
        avail = next_session(conn, snapshot_id, "nyse", r["date"])
        if avail is None:
            deferred += 1
            continue
        rows.append(dict(market="us_equity", symbol=r["permaticker"], filing_date=r["date"],
                         eventcodes=r.get("eventcodes"), lastupdated=r.get("lastupdated"),
                         available_at=avail))
    n = upsert(conn, "events", snapshot_id, rows)
    if deferred:
        _log.warning("EVENTS: %d filings past the last known nyse session, deferred to a later load", deferred)
    report.tables["EVENTS"] = TableReport(len(df), n, len(unmapped))
    report.unmapped_rows["EVENTS"] = unmapped
    report.deferred_events = deferred


def _load_sfp(conn, snapshot_id: str, raw: pd.DataFrame, report: LoadReport) -> None:
    """SFP -> `bars_daily`, SPY only, symbol `SFP:SPY` (issue 5: the regime proxy;
    never a permaticker, so it can never collide with one)."""
    df = raw[raw["ticker"] == SFP_TICKER].copy()
    _numeric(df, ["open", "high", "low", "close", "volume", "closeadj", "closeunadj"])
    df["date"] = _date10(df["date"])
    ratio = df["closeunadj"] / df["close"]
    rows = pd.DataFrame({
        "market": "us_equity", "symbol": SFP_SYMBOL, "date": df["date"],
        "open": df["open"] * ratio, "high": df["high"] * ratio, "low": df["low"] * ratio,
        "close": df["closeunadj"], "volume": df["volume"] * ratio,
        "close_vendor": df["close"], "closeadj_vendor": df["closeadj"],
        "lastupdated": df["lastupdated"], "available_at": df["date"],
    })
    rows["dollar_volume"] = rows["close"] * rows["volume"]
    n = upsert(conn, "bars_daily", snapshot_id, rows)
    report.tables["SFP"] = TableReport(len(raw), n)


def _write_rejects(rejects_dir: str | Path, snapshot_id: str, report: LoadReport) -> None:
    out = Path(rejects_dir)
    out.mkdir(parents=True, exist_ok=True)
    for table, unmapped in report.unmapped_rows.items():
        if len(unmapped):
            unmapped.to_csv(out / f"{snapshot_id}-{table}-rejects.csv", index=False)


# --------------------------------------------------------------------- entry

def load(conn, snapshot_id: str, files: Mapping[str, str | Path],
        snapshot_doc: dict | None = None, rejects_dir: str | Path | None = None) -> LoadReport:
    """Load SEP, TICKERS, ACTIONS, DAILY, EVENTS and SFP into the store.

    `files` maps each of REQUIRED_TABLES to a raw export file (a zip of one CSV,
    or a bare CSV). Idempotent: reloading the same snapshot upserts the same
    rows and leaves every count unchanged (`harness.store.writer.upsert`'s
    primary-key upsert). Order matters: TICKERS builds the ticker->permaticker
    map every other table needs; SEP must load before the nyse calendar is
    built; the calendar must exist before EVENTS can compute `available_at`.
    """
    missing = [t for t in REQUIRED_TABLES if t not in files]
    if missing:
        raise SharadarLoadError(f"missing required table(s): {missing}")

    doc = dict(snapshot_doc) if snapshot_doc else {
        "snapshot_id": snapshot_id, "files": {k: str(v) for k, v in files.items()}}
    created_at = doc.get("created_at") or _dt.datetime.now(_dt.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    file_count = doc.get("file_count", len(files))
    register_snapshot(conn, snapshot_id, created_at, file_count, doc)

    report = LoadReport()

    tickers_raw = _read_table(files["TICKERS"])
    ranges = _ticker_ranges(tickers_raw)
    _load_symbols(conn, snapshot_id, ranges, report)

    sep_raw = _read_table(files["SEP"])
    _load_sep(conn, snapshot_id, sep_raw, ranges, report)

    report.calendar_sessions = build_nyse_calendar(conn, snapshot_id)

    actions_raw = _read_table(files["ACTIONS"])
    _load_actions_and_listing(conn, snapshot_id, actions_raw, ranges, report)

    daily_raw = _read_table(files["DAILY"])
    _load_marketcap(conn, snapshot_id, daily_raw, ranges, report)

    events_raw = _read_table(files["EVENTS"])
    _load_events(conn, snapshot_id, events_raw, ranges, report)

    sfp_raw = _read_table(files["SFP"])
    _load_sfp(conn, snapshot_id, sfp_raw, report)

    if rejects_dir is not None:
        _write_rejects(rejects_dir, snapshot_id, report)

    return report


# ----------------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(prog="python -m ingest.sharadar")
    sub = parser.add_subparsers(dest="command", required=True)
    p_load = sub.add_parser("load", help="load SEP/TICKERS/ACTIONS/DAILY/EVENTS/SFP into the store")
    p_load.add_argument("--snapshot-id", required=True)
    p_load.add_argument("--file", action="append", default=[], metavar="NAME=PATH",
                        help="repeatable; NAME is one of " + ", ".join(REQUIRED_TABLES))
    p_load.add_argument("--rejects-dir", default=None,
                        help="default: <PENUMBRA_DATA_ROOT>/rejects")
    args = parser.parse_args(argv)

    files: dict[str, str] = {}
    for item in args.file:
        name, sep, path = item.partition("=")
        if not sep:
            parser.error(f"--file expects NAME=PATH, got {item!r}")
        files[name] = path

    rejects_dir = args.rejects_dir
    if rejects_dir is None:
        try:
            rejects_dir = str(Path(env.data_root()) / "rejects") if env.is_local_root(env.data_root()) else None
        except env.MissingEnvVar:
            rejects_dir = None

    conn = connect(env.store_path())
    report = load(conn, args.snapshot_id, files, rejects_dir=rejects_dir)
    print(report.summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())

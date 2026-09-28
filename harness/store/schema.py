"""Store DDL and table metadata (spec/02 Store; docs/store.md).

The schema is created with `ensure_schema(conn)`. The version is recorded in the
`meta` table; opening a store written under a different version is refused rather
than migrated in place, because the store is a derived artifact and is rebuilt from
its snapshot (docs/architecture.md, "Store").

`TABLES` is the single description of every point-in-time table: its key, its
columns, the column that dates a row and the format of its `available_at`. The
writer validates against it and the store leakage test is parametrized over it.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

SCHEMA_VERSION = 1

MARKETS = ("us_equity", "binance_spot")

# Lane -> trading calendar (spec/02 Trading calendars).
LANE_CALENDAR = {"smallcap": "nyse", "discovered": "nyse", "crypto": "utc"}
CALENDARS = ("nyse", "utc")

# available_at formats: an ISO date, or an ISO UTC timestamp with milliseconds
# (hourly klines, whose available_at is the Binance close time).
DATE = "date"
TIMESTAMP = "timestamp"


@dataclass(frozen=True)
class Table:
    name: str
    key: tuple[str, ...]
    columns: tuple[str, ...]      # non-key payload columns, excluding available_at
    date_column: str | None       # the column that dates the row; available_at >= it
    available_at: str = DATE      # DATE or TIMESTAMP

    @property
    def all_columns(self) -> tuple[str, ...]:
        return self.key + self.columns + ("available_at",)


TABLES: dict[str, Table] = {t.name: t for t in (
    Table("calendar", ("calendar", "date", "snapshot_id"), (), "date"),
    Table("symbols", ("market", "symbol", "snapshot_id"),
          ("ticker", "name", "category", "exchange", "sector", "base", "quote",
           "lastupdated"),
          None),
    Table("bars_daily", ("market", "symbol", "date", "snapshot_id"),
          ("open", "high", "low", "close", "volume", "dollar_volume",
           "close_vendor", "closeadj_vendor", "lastupdated"),
          "date"),
    Table("bars_hourly", ("market", "symbol", "ts", "snapshot_id"),
          ("open", "high", "low", "close", "volume", "quote_volume"),
          "ts", TIMESTAMP),
    Table("actions", ("market", "symbol", "date", "action", "snapshot_id"),
          ("value", "ticker", "contraticker", "contraname", "lastupdated"),
          "date"),
    Table("listing", ("market", "symbol", "event", "date", "snapshot_id"),
          ("reason", "exchange", "source"),
          "date"),
    Table("marketcap", ("market", "symbol", "date", "snapshot_id"),
          ("marketcap", "lastupdated"),
          "date"),
    Table("events", ("market", "symbol", "filing_date", "snapshot_id"),
          ("eventcodes", "lastupdated"),
          "filing_date"),
    Table("lane_membership", ("lane", "market", "symbol", "date", "snapshot_id"),
          ("screen_values",),
          "date"),
)}

# Tables that are not point-in-time data and have no as-of read. The leakage test
# requires every table in the database to be in TABLES or here.
NON_PIT_TABLES = {
    "meta": "schema version; not market data",
    "snapshots": "snapshot registry; every read names its snapshot",
}

_DDL = f"""
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id TEXT PRIMARY KEY,
    created_at  TEXT NOT NULL,          -- ISO UTC timestamp
    file_count  INTEGER NOT NULL,
    document    TEXT NOT NULL           -- snapshot JSON from ingest/fetch/snapshot.py
);

CREATE TABLE IF NOT EXISTS calendar (
    calendar     TEXT NOT NULL CHECK (calendar IN ('nyse', 'utc')),
    date         TEXT NOT NULL,
    snapshot_id  TEXT NOT NULL REFERENCES snapshots(snapshot_id),
    available_at TEXT NOT NULL,
    PRIMARY KEY (calendar, date, snapshot_id)
);

CREATE TABLE IF NOT EXISTS symbols (
    market       TEXT NOT NULL CHECK (market IN ('us_equity', 'binance_spot')),
    symbol       TEXT NOT NULL,         -- permaticker (as text) or Binance pair
    snapshot_id  TEXT NOT NULL REFERENCES snapshots(snapshot_id),
    ticker       TEXT,
    name         TEXT,
    category     TEXT,
    exchange     TEXT,
    sector       TEXT,                  -- allowlisted non-point-in-time (spec/04)
    base         TEXT,
    quote        TEXT,
    lastupdated  TEXT,                  -- vendor metadata, never available_at
    available_at TEXT NOT NULL,
    PRIMARY KEY (market, symbol, snapshot_id)
);

CREATE TABLE IF NOT EXISTS bars_daily (
    market          TEXT NOT NULL CHECK (market IN ('us_equity', 'binance_spot')),
    symbol          TEXT NOT NULL,
    date            TEXT NOT NULL,
    snapshot_id     TEXT NOT NULL REFERENCES snapshots(snapshot_id),
    open            REAL,               -- unadjusted
    high            REAL,
    low             REAL,
    close           REAL,
    volume          REAL,
    dollar_volume   REAL,               -- unadjusted close x volume, or quote volume
    close_vendor    REAL,               -- SEP close (split-adjusted), audit only
    closeadj_vendor REAL,               -- SEP closeadj, audit only
    lastupdated     TEXT,
    available_at    TEXT NOT NULL,
    PRIMARY KEY (market, symbol, date, snapshot_id)
);
CREATE INDEX IF NOT EXISTS ix_bars_daily_panel
    ON bars_daily (snapshot_id, market, date, symbol, available_at);

CREATE TABLE IF NOT EXISTS bars_hourly (
    market       TEXT NOT NULL CHECK (market IN ('us_equity', 'binance_spot')),
    symbol       TEXT NOT NULL,
    ts           TEXT NOT NULL,         -- open time, ISO UTC
    snapshot_id  TEXT NOT NULL REFERENCES snapshots(snapshot_id),
    open         REAL,
    high         REAL,
    low          REAL,
    close        REAL,
    volume       REAL,
    quote_volume REAL,
    available_at TEXT NOT NULL,         -- close time, ISO UTC
    PRIMARY KEY (market, symbol, ts, snapshot_id)
);
CREATE INDEX IF NOT EXISTS ix_bars_hourly_panel
    ON bars_hourly (snapshot_id, market, ts, symbol, available_at);

CREATE TABLE IF NOT EXISTS actions (
    market       TEXT NOT NULL CHECK (market IN ('us_equity', 'binance_spot')),
    symbol       TEXT NOT NULL,
    date         TEXT NOT NULL,
    action       TEXT NOT NULL,         -- ACTIONS action type
    snapshot_id  TEXT NOT NULL REFERENCES snapshots(snapshot_id),
    value        REAL,                  -- split: shares after / before; dividend: cash
    ticker       TEXT,
    contraticker TEXT,
    contraname   TEXT,
    lastupdated  TEXT,
    available_at TEXT NOT NULL,
    PRIMARY KEY (market, symbol, date, action, snapshot_id)
);
CREATE INDEX IF NOT EXISTS ix_actions_read
    ON actions (snapshot_id, market, symbol, date);

CREATE TABLE IF NOT EXISTS listing (
    market       TEXT NOT NULL CHECK (market IN ('us_equity', 'binance_spot')),
    symbol       TEXT NOT NULL,
    event        TEXT NOT NULL CHECK (event IN ('listed', 'delisted')),
    date         TEXT NOT NULL,
    snapshot_id  TEXT NOT NULL REFERENCES snapshots(snapshot_id),
    reason       TEXT,                  -- ACTIONS action type of the delisting
    exchange     TEXT,                  -- exchange at delisting (haircut class)
    source       TEXT,                  -- actions | tickers | klines
    available_at TEXT NOT NULL,
    PRIMARY KEY (market, symbol, event, date, snapshot_id)
);
CREATE INDEX IF NOT EXISTS ix_listing_read
    ON listing (snapshot_id, market, event, date);

CREATE TABLE IF NOT EXISTS marketcap (
    market       TEXT NOT NULL CHECK (market IN ('us_equity', 'binance_spot')),
    symbol       TEXT NOT NULL,
    date         TEXT NOT NULL,
    snapshot_id  TEXT NOT NULL REFERENCES snapshots(snapshot_id),
    marketcap    REAL,
    lastupdated  TEXT,
    available_at TEXT NOT NULL,
    PRIMARY KEY (market, symbol, date, snapshot_id)
);
CREATE INDEX IF NOT EXISTS ix_marketcap_panel
    ON marketcap (snapshot_id, market, date, symbol);

CREATE TABLE IF NOT EXISTS events (
    market       TEXT NOT NULL CHECK (market IN ('us_equity', 'binance_spot')),
    symbol       TEXT NOT NULL,
    filing_date  TEXT NOT NULL,         -- EDGAR filing date
    snapshot_id  TEXT NOT NULL REFERENCES snapshots(snapshot_id),
    eventcodes   TEXT,
    lastupdated  TEXT,
    available_at TEXT NOT NULL,         -- next NYSE session, or the filing date
    PRIMARY KEY (market, symbol, filing_date, snapshot_id)
);
CREATE INDEX IF NOT EXISTS ix_events_read
    ON events (snapshot_id, market, available_at);

CREATE TABLE IF NOT EXISTS lane_membership (
    lane          TEXT NOT NULL CHECK (lane IN ({", ".join(repr(l) for l in LANE_CALENDAR)})),
    market        TEXT NOT NULL CHECK (market IN ('us_equity', 'binance_spot')),
    symbol        TEXT NOT NULL,
    date          TEXT NOT NULL,
    snapshot_id   TEXT NOT NULL REFERENCES snapshots(snapshot_id),
    screen_values TEXT,                 -- JSON of the screen values that admitted it
    available_at  TEXT NOT NULL,
    PRIMARY KEY (lane, market, symbol, date, snapshot_id)
);
CREATE INDEX IF NOT EXISTS ix_lane_membership_panel
    ON lane_membership (snapshot_id, lane, date);
"""


class SchemaVersionError(RuntimeError):
    """The store was written under a different schema version; rebuild it."""


def connect(path: str | Path = ":memory:") -> sqlite3.Connection:
    """Open a store at `path` (the caller resolves PENUMBRA_STORE_PATH) and ensure
    its schema."""
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA foreign_keys = ON")
    ensure_schema(conn)
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON")
    has_meta = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'meta'").fetchone()
    if has_meta:
        row = conn.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
        if row is not None and int(row[0]) != SCHEMA_VERSION:
            raise SchemaVersionError(
                f"store schema version {row[0]}, code expects {SCHEMA_VERSION}; "
                "rebuild the store from its snapshot")
    conn.executescript(_DDL)
    conn.execute("INSERT OR IGNORE INTO meta (key, value) VALUES ('schema_version', ?)",
                 (str(SCHEMA_VERSION),))
    conn.commit()


def schema_version(conn: sqlite3.Connection) -> int:
    return int(conn.execute(
        "SELECT value FROM meta WHERE key = 'schema_version'").fetchone()[0])

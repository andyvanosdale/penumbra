"""Point-in-time data store (plan §3.1) — the heart of the system.

Every row records both an *event time* (when it happened) and a *knowledge time*
(when it became knowable). Every query takes an `as_of` and is answered as:

    "What did I know about X as of time T?"

A daily OHLCV bar for date D is only knowable after the close of D, so its
`knowledge_date` is D itself. A feature built for a decision at the close of date
T may therefore use bars with `knowledge_date <= T`.

Backend: SQLite (Python stdlib) — zero-dependency and sufficient for years of work
at this scale (plan §3.1 allows DuckDB *or* SQLite). To upgrade to DuckDB later,
swap the connection and the `?`/`INSERT` calls; the public interface is unchanged.

TWO READ PATHS, deliberately:
  * get_known_prices(as_of, ...)   RESTRICTED. The only path feature code may use.
                                   Cannot return rows with knowledge_date > as_of.
  * get_prices_oracle(...)         UNRESTRICTED, future-aware. LABELER ONLY.
                                   Must never be imported by features.py.
"""

from __future__ import annotations

import datetime as _dt
import sqlite3
from pathlib import Path
from typing import Iterable, Optional, Sequence

import pandas as pd

PRICE_COLUMNS = [
    "ticker", "date", "open", "high", "low", "close", "adj_close", "volume",
    "knowledge_date",
]


def _to_iso(d) -> str:
    if isinstance(d, str):
        return d
    if isinstance(d, (_dt.date, _dt.datetime)):
        return d.strftime("%Y-%m-%d")
    return pd.Timestamp(d).strftime("%Y-%m-%d")


class PITStore:
    """As-of-aware price store. Open with a file path or ':memory:'."""

    def __init__(self, db_path: str | Path = ":memory:"):
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    # ------------------------------------------------------------------ schema
    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS prices (
                ticker         TEXT NOT NULL,
                date           TEXT NOT NULL,   -- event date (the bar's date)
                open           REAL,
                high           REAL,
                low            REAL,
                close          REAL,
                adj_close      REAL,
                volume         REAL,
                knowledge_date TEXT NOT NULL,   -- when this row became knowable
                PRIMARY KEY (ticker, date)
            );
            CREATE INDEX IF NOT EXISTS ix_prices_known
                ON prices (knowledge_date, ticker);
            CREATE INDEX IF NOT EXISTS ix_prices_ticker_date
                ON prices (ticker, date);
            """
        )
        self.conn.commit()

    # ------------------------------------------------------------------- writes
    def write_prices(self, df: pd.DataFrame) -> int:
        """Insert/replace price rows.

        Required columns: ticker, date, open, high, low, close, adj_close, volume.
        Optional: knowledge_date. If absent it defaults to the bar's own date
        (a daily bar is knowable at the close of its date).
        """
        df = df.copy()
        missing = {"ticker", "date", "open", "high", "low", "close",
                   "adj_close", "volume"} - set(df.columns)
        if missing:
            raise ValueError(f"write_prices missing columns: {sorted(missing)}")

        df["date"] = df["date"].map(_to_iso)
        if "knowledge_date" not in df.columns:
            df["knowledge_date"] = df["date"]
        else:
            df["knowledge_date"] = df["knowledge_date"].map(_to_iso)

        # Guardrail: a daily bar can never be knowable *before* its event date.
        bad = df["knowledge_date"] < df["date"]
        if bad.any():
            raise ValueError(
                f"{int(bad.sum())} rows have knowledge_date earlier than their "
                "event date — that would be lookahead at write time."
            )

        rows = df[PRICE_COLUMNS].itertuples(index=False, name=None)
        cur = self.conn.executemany(
            "INSERT OR REPLACE INTO prices "
            "(ticker,date,open,high,low,close,adj_close,volume,knowledge_date) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            rows,
        )
        self.conn.commit()
        return cur.rowcount

    # --------------------------------------------------------- RESTRICTED reads
    def get_known_prices(
        self,
        as_of,
        tickers: Optional[Sequence[str]] = None,
        start=None,
    ) -> pd.DataFrame:
        """Rows knowable as of `as_of` (knowledge_date <= as_of). The ONLY read
        path feature-building code is permitted to use.

        This method enforces the point-in-time contract: it is structurally
        impossible for it to return a row with knowledge_date > as_of.
        """
        as_of = _to_iso(as_of)
        sql = "SELECT * FROM prices WHERE knowledge_date <= ?"
        params: list = [as_of]
        if tickers is not None:
            tickers = list(tickers)
            sql += f" AND ticker IN ({','.join('?' * len(tickers))})"
            params += tickers
        if start is not None:
            sql += " AND date >= ?"
            params.append(_to_iso(start))
        sql += " ORDER BY ticker, date"
        df = pd.read_sql_query(sql, self.conn, params=params)

        # Belt-and-suspenders assertion: the data contract, re-checked at runtime.
        if not df.empty:
            assert (df["knowledge_date"] <= as_of).all(), (
                "PIT VIOLATION: get_known_prices returned a row with "
                "knowledge_date > as_of. This is a lookahead bug."
            )
        return df

    def known_bar(self, ticker: str, date, as_of) -> Optional[dict]:
        """Single bar for `date` if it is knowable as of `as_of`
        (knowledge_date <= as_of), else None. Raw-cursor fast path for the
        feature builder's hot loop — still fully point-in-time: it can never
        return a bar whose knowledge_date exceeds as_of.
        """
        row = self.conn.execute(
            "SELECT ticker,date,open,high,low,close,adj_close,volume,knowledge_date "
            "FROM prices WHERE ticker=? AND date=? AND knowledge_date<=? LIMIT 1",
            (ticker, _to_iso(date), _to_iso(as_of)),
        ).fetchone()
        return dict(row) if row else None

    def latest_known_close(self, ticker: str, as_of) -> Optional[float]:
        """Most recent adjusted close knowable as of `as_of`, or None."""
        as_of = _to_iso(as_of)
        row = self.conn.execute(
            "SELECT adj_close FROM prices "
            "WHERE ticker = ? AND knowledge_date <= ? "
            "ORDER BY date DESC LIMIT 1",
            (ticker, as_of),
        ).fetchone()
        return None if row is None else row["adj_close"]

    def trading_days(self, start=None, end=None) -> list[str]:
        """Distinct dates present in the store (the trading calendar we observe)."""
        sql = "SELECT DISTINCT date FROM prices"
        params: list = []
        clauses = []
        if start is not None:
            clauses.append("date >= ?"); params.append(_to_iso(start))
        if end is not None:
            clauses.append("date <= ?"); params.append(_to_iso(end))
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY date"
        return [r["date"] for r in self.conn.execute(sql, params).fetchall()]

    # ----------------------------------------------------- UNRESTRICTED (oracle)
    def get_prices_oracle(
        self, tickers: Optional[Sequence[str]] = None
    ) -> pd.DataFrame:
        """FULL price history with NO as-of restriction. Sees the future.

        ███ LABELER ONLY ███  (plan §3.3: the labeler is the only component
        permitted to look into the future.) features.py must NEVER call this.
        The leakage test-suite asserts that features.py does not reference it.
        """
        sql = "SELECT * FROM prices"
        params: list = []
        if tickers is not None:
            tickers = list(tickers)
            sql += f" WHERE ticker IN ({','.join('?' * len(tickers))})"
            params += tickers
        sql += " ORDER BY ticker, date"
        return pd.read_sql_query(sql, self.conn, params=params)

    # ------------------------------------------------------------------- misc
    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM prices").fetchone()[0]

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "PITStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

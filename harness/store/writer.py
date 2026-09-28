"""Idempotent store writer (spec/02 Store, "Ingest is idempotent and re-runnable").

Rows are upserted on the table's primary key, which includes `snapshot_id`, so a
reload of the same rows under the same snapshot changes nothing and a second
snapshot sits beside the first. Nothing is deleted and nothing is rebuilt from
filesystem state. A snapshot is registered before any of its rows are written.

Every row must carry `available_at`; the writer checks its format and that it is
not before the date that dates the row (a row cannot be known before it happened).
"""

from __future__ import annotations

import json
import re
import sqlite3
from typing import Iterable, Mapping

import pandas as pd

from harness.store.schema import AVAILABLE_ON_DATE, DATE, TABLES, TIMESTAMP

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")


class StoreWriteError(ValueError):
    """A batch failed validation; nothing from it was written."""


def register_snapshot(conn: sqlite3.Connection, snapshot_id: str, created_at: str,
                      file_count: int, document: Mapping | str) -> None:
    """Register a snapshot (idempotent). Must precede any row that names it."""
    doc = document if isinstance(document, str) else json.dumps(
        document, sort_keys=True, separators=(",", ":"))
    conn.execute(
        "INSERT INTO snapshots (snapshot_id, created_at, file_count, document) "
        "VALUES (?, ?, ?, ?) ON CONFLICT (snapshot_id) DO UPDATE SET "
        "created_at = excluded.created_at, file_count = excluded.file_count, "
        "document = excluded.document",
        (snapshot_id, created_at, int(file_count), doc))
    conn.commit()


def _snapshot_registered(conn: sqlite3.Connection, snapshot_id: str) -> bool:
    return conn.execute("SELECT 1 FROM snapshots WHERE snapshot_id = ?",
                        (snapshot_id,)).fetchone() is not None


def _records(rows: pd.DataFrame | Iterable[Mapping]) -> list[dict]:
    if isinstance(rows, pd.DataFrame):
        df = rows.astype(object).where(pd.notna(rows), None)
        return df.to_dict("records")
    return [dict(r) for r in rows]


def upsert(conn: sqlite3.Connection, table: str, snapshot_id: str,
           rows: pd.DataFrame | Iterable[Mapping]) -> int:
    """Validate and upsert `rows` into `table` under `snapshot_id`.

    `rows` carries the table's key and payload columns plus `available_at`;
    `snapshot_id` is set here (a row naming a different snapshot is refused).
    Columns the table doesn't have are refused. Returns the number of rows sent.
    The batch is all-or-nothing.
    """
    if table not in TABLES:
        raise StoreWriteError(f"unknown table {table!r}")
    spec = TABLES[table]
    if not _snapshot_registered(conn, snapshot_id):
        raise StoreWriteError(f"snapshot {snapshot_id!r} is not registered; "
                              "call register_snapshot first")
    records = _records(rows)
    if not records:
        return 0

    allowed = set(spec.all_columns)
    fmt = _TS_RE if spec.available_at == TIMESTAMP else _DATE_RE
    for i, r in enumerate(records):
        extra = set(r) - allowed
        if extra:
            raise StoreWriteError(f"{table} row {i}: unknown columns {sorted(extra)}")
        if r.get("snapshot_id", snapshot_id) != snapshot_id:
            raise StoreWriteError(f"{table} row {i}: snapshot_id {r['snapshot_id']!r} "
                                  f"differs from {snapshot_id!r}")
        r["snapshot_id"] = snapshot_id
        missing = [k for k in spec.key if r.get(k) is None]
        if missing:
            raise StoreWriteError(f"{table} row {i}: missing key columns {missing}")
        aa = r.get("available_at")
        if aa is None or not isinstance(aa, str) or not fmt.match(aa):
            raise StoreWriteError(
                f"{table} row {i}: available_at {aa!r} missing or not an ISO "
                f"{'UTC timestamp (YYYY-MM-DDTHH:MM:SS.fffZ)' if spec.available_at == TIMESTAMP else 'date'}")
        if spec.date_column is not None:
            dated = r[spec.date_column]
            dfmt = _TS_RE if spec.available_at == TIMESTAMP else _DATE_RE
            if not isinstance(dated, str) or not dfmt.match(dated):
                raise StoreWriteError(f"{table} row {i}: {spec.date_column} {dated!r} "
                                      "is not in the table's ISO format")
            if aa < dated:
                raise StoreWriteError(f"{table} row {i}: available_at {aa} is before "
                                      f"{spec.date_column} {dated}")
            if table in AVAILABLE_ON_DATE and aa != dated:
                raise StoreWriteError(
                    f"{table} row {i}: available_at {aa} must equal {spec.date_column} "
                    f"{dated} (spec/02; schema.AVAILABLE_ON_DATE)")

    cols = list(spec.all_columns)
    payload = [c for c in cols if c not in spec.key]
    sql = (f"INSERT INTO {table} ({', '.join(cols)}) "
           f"VALUES ({', '.join('?' for _ in cols)}) "
           f"ON CONFLICT ({', '.join(spec.key)}) DO UPDATE SET "
           + ", ".join(f"{c} = excluded.{c}" for c in payload))
    with conn:
        conn.executemany(sql, [tuple(r.get(c) for c in cols) for r in records])
    return len(records)

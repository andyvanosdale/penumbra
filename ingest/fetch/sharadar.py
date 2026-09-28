"""Sharadar tables via the Nasdaq Data Link datatables bulk export.

Each run asks the API for a fresh export of each table, polls until it is
ready, and stores it as a dated snapshot:
  raw/sharadar/<TABLE>/<TABLE>-<data_snapshot_time>.zip
A snapshot whose ``data_snapshot_time`` is already in the manifest is not
fetched again; ``--max-age-days`` (default 1) skips the API call entirely when
the newest local snapshot is younger than that. Old snapshots are kept: the
spec's run record names the snapshot a run used, and the vendor restates
history, so a re-download is never a substitute for the file a run was built
from.

Requires ``NASDAQ_DATA_LINK_API_KEY``. The key travels in the query string, as
the API requires; every error raised from this module has it redacted, so it
never reaches a log or a traceback.
"""

from __future__ import annotations

import datetime as _dt
import os
import re
import time
from typing import Iterable

from . import http
from .base import Source, Task, register
from .manifest import Manifest
from .storage import Storage

API = "https://data.nasdaq.com/api/v3/datatables"
PREFIX = "raw/sharadar"
DEFAULT_TABLES = ("SEP", "TICKERS", "ACTIONS", "DAILY", "EVENTS", "SFP")
TABLE_FILTERS = {"SFP": {"ticker": "SPY"}}   # SFP is only read for SPY (spec/02)


def request_export(sess, table: str, api_key: str, filters: dict | None = None,
                   poll_seconds: float = 10.0, max_wait: float = 1800.0) -> dict:
    """Ask for a bulk export and poll until the file is fresh. Returns the
    ``file`` block: {link, status, data_snapshot_time}."""
    params = {"qopts.export": "true", "api_key": api_key}
    for k, v in (filters or {}).items():
        params[k] = v
    deadline = time.monotonic() + max_wait
    while True:
        body = http.get_json(sess, f"{API}/SHARADAR/{table}.json", params=params,
                             secrets=[api_key], timeout=120)
        info = body["datatable_bulk_download"]["file"]
        if info.get("status") == "fresh":
            return info
        if time.monotonic() > deadline:
            raise TimeoutError(f"export of {table} not ready after {max_wait}s (status {info.get('status')})")
        time.sleep(poll_seconds)


def snapshot_tag(data_snapshot_time: str) -> str:
    return re.sub(r"[^0-9T]", "", data_snapshot_time.replace(" ", "T"))[:15]


@register
class Sharadar(Source):
    name = "sharadar"
    help = "Sharadar SEP, TICKERS, ACTIONS, DAILY, EVENTS, SFP(SPY) bulk exports"
    prefix = PREFIX
    snapshot_policy = "latest_per_group"      # one export per table

    def snapshot_group(self, key: str) -> str:
        return key[len(PREFIX) + 1:].split("/", 1)[0]

    def add_arguments(self, p):
        p.add_argument("--tables", default=",".join(DEFAULT_TABLES))
        p.add_argument("--max-age-days", type=float, default=1.0,
                       help="skip a table whose newest local snapshot is younger than this")

    def plan(self, storage: Storage, manifest: Manifest, args) -> Iterable[Task]:
        key = os.environ.get("NASDAQ_DATA_LINK_API_KEY")
        if not key:
            raise SystemExit("NASDAQ_DATA_LINK_API_KEY is not set")
        sess = http.session()
        now = _dt.datetime.now(_dt.timezone.utc)
        for table in [t for t in args.tables.split(",") if t]:
            newest = self._newest_local(manifest, table)
            if newest and (now - newest) < _dt.timedelta(days=args.max_age_days):
                continue
            info = request_export(sess, table, key, TABLE_FILTERS.get(table))
            tag = snapshot_tag(info["data_snapshot_time"])
            yield Task(key=f"{PREFIX}/{table}/{table}-{tag}.zip", version=info["data_snapshot_time"],
                       meta={"link": info["link"], "table": table})

    @staticmethod
    def _newest_local(manifest: Manifest, table: str) -> _dt.datetime | None:
        best = None
        for rel, e in manifest.entries.items():
            if e["key"].startswith(f"{PREFIX}/{table}/"):
                t = _dt.datetime.fromisoformat(e["fetched_at"])
                best = t if best is None or t > best else best
        return best

    def fetch(self, task: Task, storage: Storage, args) -> tuple[int, str]:
        sess = http.session()
        try:
            return http.download(sess, task.meta["link"], storage, task.dest, timeout=600)
        except Exception as exc:
            key = os.environ.get("NASDAQ_DATA_LINK_API_KEY")
            raise http.RedactedError(http.redact(f"{type(exc).__name__}: {exc}", [key])) from None

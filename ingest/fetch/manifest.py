"""Per-source manifest: what is already in the store and how we know it is whole.

One JSON file per source under ``manifests/<source>.json``. Each entry is keyed
by the file's path relative to the storage root and records size, sha256, the
vendor's own identifier for that version (an S3 ETag, a Sharadar snapshot time,
a yfinance last-row date) and when it was fetched. A file is "present" when the
manifest has it, the object exists in storage, and the sizes agree. Anything
else is fetched again.
"""

from __future__ import annotations

import datetime as _dt
from typing import Any

from .storage import Storage


def utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


class Manifest:
    def __init__(self, storage: Storage, source: str):
        self.storage = storage
        self.source = source
        self.rel = f"manifests/{source}.json"
        self.entries: dict[str, dict[str, Any]] = storage.read_json(self.rel, default={}) or {}
        self._dirty = False

    def has(self, rel: str, *, size: int | None = None, version: str | None = None) -> bool:
        e = self.entries.get(rel)
        if not e:
            return False
        if version is not None and e.get("version") != version:
            return False
        if size is not None and e.get("size") != size:
            return False
        actual = self.storage.size(rel)
        return actual is not None and actual == e.get("size")

    def record(self, rel: str, *, size: int, sha256: str, version: str | None = None, **extra) -> None:
        self.entries[rel] = {"size": size, "sha256": sha256, "version": version,
                             "fetched_at": utcnow(), **extra}
        self._dirty = True

    def forget(self, rel: str) -> None:
        if rel in self.entries:
            del self.entries[rel]
            self._dirty = True

    def save(self) -> None:
        if self._dirty:
            self.storage.write_json(self.rel, self.entries)
            self._dirty = False

    def __len__(self) -> int:
        return len(self.entries)

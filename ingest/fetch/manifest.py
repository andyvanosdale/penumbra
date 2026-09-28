"""Per-source manifest: what is already in the store and how we know it is whole.

One JSON file per source under ``manifests/<source>.json``. Entries are keyed by
the file's *stored path* relative to the storage root. Each entry carries the
logical ``key`` the source planned (the vendor's canonical path), the vendor's
identifier for that version (an S3 ETag, a Sharadar snapshot time, a yfinance
last-row date), size, sha256, when it was fetched, and whether it is the
``current`` version of its key.

Stored paths are immutable. When a vendor restates a file, the new bytes land at
a versioned path beside the old one, the old entry is marked superseded, and the
new entry becomes current. A snapshot that named the old path still verifies.
The one exception is a source that opts out (``Source.versioned = False``), such
as yfinance, whose files are rewritten in place and never enter a snapshot.

A key is "present" when it has a current entry for the requested version, the
object exists in storage, and the sizes agree. Anything else is fetched again.
"""

from __future__ import annotations

import datetime as _dt
import posixpath
from typing import Any

from .storage import Storage


def utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def versioned_path(key: str, version: str | None) -> str:
    """``raw/x/dir/file.zip`` + version ``abc`` -> ``raw/x/dir/_v/abc/file.zip``."""
    d, base = posixpath.split(key)
    tag = "".join(c for c in (version or "unversioned") if c.isalnum() or c in "-_.")[:64]
    return f"{d}/_v/{tag}/{base}" if d else f"_v/{tag}/{base}"


class Manifest:
    def __init__(self, storage: Storage, source: str, size_cache: dict[str, int] | None = None):
        self.storage = storage
        self.source = source
        self.rel = f"manifests/{source}.json"
        self.entries: dict[str, dict[str, Any]] = storage.read_json(self.rel, default={}) or {}
        for path, e in self.entries.items():          # entries written before versioning existed
            e.setdefault("key", path)
            e.setdefault("current", True)
        self._by_key: dict[str, str] = {p: e["key"] for p, e in self.entries.items()}
        self._current: dict[str, str] = {e["key"]: p for p, e in self.entries.items() if e.get("current")}
        self._sizes = size_cache
        self._dirty = False

    # -- queries ---------------------------------------------------------------
    def current(self, key: str) -> dict[str, Any] | None:
        p = self._current.get(key)
        return {"path": p, **self.entries[p]} if p else None

    def has(self, key: str, *, size: int | None = None, version: str | None = None) -> bool:
        e = self.current(key)
        if not e:
            return False
        if version is not None and e.get("version") != version:
            return False
        if size is not None and e.get("size") != size:
            return False
        actual = self._sizes.get(e["path"]) if self._sizes is not None else self.storage.size(e["path"])
        return actual is not None and actual == e.get("size")

    def current_entries(self) -> dict[str, dict[str, Any]]:
        return {p: e for p, e in self.entries.items() if e.get("current")}

    # -- updates -----------------------------------------------------------------
    def record(self, key: str, *, path: str, size: int, sha256: str, version: str | None = None,
               **extra) -> None:
        old = self._current.get(key)
        if old and old != path:
            self.entries[old]["current"] = False
            self.entries[old]["superseded_by"] = path
            self.entries[old]["superseded_at"] = utcnow()
        self.entries[path] = {"key": key, "version": version, "size": size, "sha256": sha256,
                              "fetched_at": utcnow(), "current": True, **extra}
        self._current[key] = path
        self._by_key[path] = key
        if self._sizes is not None:
            self._sizes[path] = size
        self._dirty = True

    def save(self) -> None:
        if self._dirty:
            self.storage.write_json(self.rel, self.entries)
            self._dirty = False

    def __len__(self) -> int:
        return len(self.entries)

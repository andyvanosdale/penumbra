"""Snapshot id: SHA-256 over the canonical manifest of every raw file (spec/02,
spec/03). Written to ``snapshots/<id>.json`` so a run can name the exact set
of vendor files it was built from and a later rebuild can verify them."""

from __future__ import annotations

import hashlib
import json

from .manifest import Manifest, utcnow
from .storage import Storage


def build(storage: Storage, sources: list[str]) -> tuple[str, dict]:
    files = {}
    for src in sources:
        m = Manifest(storage, src)
        for rel, e in sorted(m.entries.items()):
            files[rel] = {"size": e["size"], "sha256": e["sha256"], "source": src}
    canonical = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sid = hashlib.sha256(canonical).hexdigest()
    doc = {"snapshot_id": sid, "created_at": utcnow(), "file_count": len(files), "files": files}
    return sid, doc


def write(storage: Storage, sources: list[str]) -> str:
    sid, doc = build(storage, sources)
    rel = f"snapshots/{sid}.json"
    if not storage.exists(rel):
        storage.write_json(rel, doc)
    storage.write_json("snapshots/latest.json", {"snapshot_id": sid, "created_at": doc["created_at"]})
    return sid


def verify(storage: Storage, snapshot_id: str, sample: int | None = None) -> list[str]:
    """Re-hash the files a snapshot names; returns the paths that differ or are missing."""
    doc = storage.read_json(f"snapshots/{snapshot_id}.json")
    if not doc:
        raise FileNotFoundError(snapshot_id)
    bad = []
    items = list(doc["files"].items())
    if sample:
        items = items[:sample]
    for rel, e in items:
        if not storage.exists(rel) or storage.sha256(rel) != e["sha256"]:
            bad.append(rel)
    return bad

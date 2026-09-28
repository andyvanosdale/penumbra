"""Snapshot id: SHA-256 over the canonical manifest of the raw files a store is
built from (spec/02, spec/03). Written to ``snapshots/<id>.json`` so a run can
name the exact file set and a later rebuild can verify it.

Which files enter the snapshot is each source's policy:

- ``all``: every current file the source holds (Binance klines; funding files
  are excluded by the source because they are not in v1).
- ``latest_per_group``: one file per group, the newest by version (Sharadar:
  one export per table). The chosen file per group is written into the
  document under ``groups`` so a loader reads exactly that set.
- ``none``: never in a snapshot (yfinance: rewritten in place, never read by a
  committed run).

The hashed payload is ``{path: {size, sha256}}`` and nothing else, so the id is
the spec's id. Source names and group choices sit outside the hash.
"""

from __future__ import annotations

import hashlib
import json

from .base import REGISTRY, Source
from .manifest import Manifest, utcnow
from .storage import Storage


def select(source: Source, manifest: Manifest) -> tuple[dict[str, dict], dict[str, str]]:
    """Returns ({path: entry}, {group: path}) for the files this source contributes."""
    if source.snapshot_policy == "none":
        return {}, {}
    chosen: dict[str, dict] = {}
    groups: dict[str, str] = {}
    for path, e in manifest.current_entries().items():
        if not source.snapshot_include(e["key"], e):
            continue
        if source.snapshot_policy == "latest_per_group":
            g = source.snapshot_group(e["key"])
            prev = groups.get(g)
            if prev is None or (e.get("version") or "") > (chosen[prev].get("version") or ""):
                if prev is not None:
                    del chosen[prev]
                groups[g] = path
                chosen[path] = e
        else:
            chosen[path] = e
    return chosen, groups


def build(storage: Storage, sources: list[Source]) -> tuple[str, dict]:
    files: dict[str, dict] = {}
    by_source: dict[str, list[str]] = {}
    groups: dict[str, dict[str, str]] = {}
    for src in sources:
        m = Manifest(storage, src.name)
        chosen, grp = select(src, m)
        for path, e in sorted(chosen.items()):
            files[path] = {"size": e["size"], "sha256": e["sha256"]}
        by_source[src.name] = sorted(chosen)
        if grp:
            groups[src.name] = dict(sorted(grp.items()))
    canonical = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sid = hashlib.sha256(canonical).hexdigest()
    doc = {"snapshot_id": sid, "created_at": utcnow(), "file_count": len(files),
           "files": files, "sources": by_source, "groups": groups}
    return sid, doc


def write(storage: Storage, sources: list[Source] | None = None) -> str:
    sources = sources if sources is not None else [REGISTRY[n] for n in sorted(REGISTRY)]
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

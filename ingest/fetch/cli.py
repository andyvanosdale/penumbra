"""Command line for the fetcher.

    python -m ingest.fetch_data <source> [options]     fetch or update one source
    python -m ingest.fetch_data all [--funding]        every registered source
    python -m ingest.fetch_data status                 what the store holds
    python -m ingest.fetch_data snapshot               write the snapshot id
    python -m ingest.fetch_data verify <snapshot_id>   re-hash a snapshot's files

The storage root comes from ``--root`` or ``PENUMBRA_DATA_ROOT``: a directory,
a mounted volume, or ``s3://bucket/prefix`` (S3-compatible endpoints via
``PENUMBRA_S3_ENDPOINT``; credentials from the usual AWS environment).
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

from . import binance, sharadar, yfinance_source  # noqa: F401  (registers sources)
from . import snapshot
from .base import REGISTRY
from .manifest import Manifest
from .storage import Storage


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python -m ingest.fetch_data", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=os.environ.get("PENUMBRA_DATA_ROOT"),
                    help="storage root (default: $PENUMBRA_DATA_ROOT)")
    ap.add_argument("-v", "--verbose", action="store_true")
    sub = ap.add_subparsers(dest="command", required=True)

    for name, src in sorted(REGISTRY.items()):
        p = sub.add_parser(name, help=src.help)
        p.add_argument("--dry-run", action="store_true", help="plan only; download nothing")
        src.add_arguments(p)

    p = sub.add_parser("all", help="run every registered source")
    p.add_argument("--dry-run", action="store_true")
    for src in REGISTRY.values():
        src.add_arguments(p)

    sub.add_parser("status", help="per-source file counts and bytes")
    sub.add_parser("snapshot", help="write the snapshot id over every manifest")
    p = sub.add_parser("verify", help="re-hash the files a snapshot names")
    p.add_argument("snapshot_id")
    p.add_argument("--sample", type=int, default=None)
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    if not args.root:
        print("set --root or PENUMBRA_DATA_ROOT", file=sys.stderr)
        return 2
    storage = Storage(args.root)
    log = logging.getLogger("penumbra.fetch")

    if args.command == "status":
        for name in sorted(REGISTRY):
            m = Manifest(storage, name)
            total = sum(e["size"] for e in m.entries.values())
            print(f"{name:10s} {len(m):7d} files {total / 1e6:12.1f} MB")
        latest = storage.read_json("snapshots/latest.json")
        print(f"snapshot   {latest['snapshot_id'] if latest else '(none)'}")
        return 0
    if args.command == "snapshot":
        print(snapshot.write(storage, sorted(REGISTRY)))
        return 0
    if args.command == "verify":
        bad = snapshot.verify(storage, args.snapshot_id, args.sample)
        for rel in bad:
            print(f"MISMATCH {rel}")
        print(f"{len(bad)} mismatches")
        return 1 if bad else 0

    names = sorted(REGISTRY) if args.command == "all" else [args.command]
    rc = 0
    for name in names:
        src = REGISTRY[name]
        log.info("%s: root=%s", name, storage.root_url)
        try:
            res = src.run(storage, args)
        except SystemExit as exc:
            log.error("%s: %s", name, exc)
            rc = 2
            continue
        log.info("%s: planned=%d skipped=%d fetched=%d failed=%d bytes=%d",
                 name, res.planned, res.skipped, res.fetched, res.failed, res.bytes)
        for err in res.errors[:20]:
            log.warning("  %s", err)
        if res.failed:
            rc = 1
    return rc

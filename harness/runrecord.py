"""Configuration hash, run log, reproduce-from-snapshot and CLI (spec/03 "Run
record").

A run is `(lane, era, configuration hash, snapshot id)` (docs/architecture.md
"Runs"). This module owns the hash, the log under the data root, the
reproduce-from-snapshot command, and a small CLI. The leakage-suite gate
itself is issue 18's `harness/guards.py`; this module only carries its status
as a field.

`reproduce()` rebuilds a fresh store from a named snapshot's raw files, never
fetching (spec/02 "A run is reproduced by rebuilding the store from its
snapshot, never from a fresh download, because both vendors restate
history"). It imports `ingest.fetch.storage` and `ingest.fetch.snapshot` for
the storage root and hash verification, and each per-source loader (`LOADERS`)
lazily, so nothing here ever imports a fetcher source's `fetch` or `plan`
(`ingest/fetch/binance.py`, `ingest/fetch/sharadar.py`) or the `requests`
library they use.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as _dt
import hashlib
import json
import subprocess
import uuid
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Iterator

import fsspec

import config.env as env_mod
import config.eras as eras_mod
import config.params as params_mod

REPO_ROOT = Path(__file__).resolve().parents[1]

# Run kinds recorded in the log (issue 17 acceptance: "a run record can be
# written for every run kind").
RUN_KINDS = (
    "primary",
    "placebo",
    "positive_control",
    "capped",
    "close_fill",
    "benchmark",
    "plumbing",
    "screen",
    "reproduce",
)

# Kinds excluded from the dev configuration-hash count (spec/03 "Use of
# eras"): a control or diagnostic variant always shares its paired primary
# run's configuration hash, so counting it separately would not add
# information.
_CONTROL_AND_DIAGNOSTIC_KINDS = frozenset(
    {"placebo", "positive_control", "capped", "close_fill", "benchmark"}
)

# A `reproduce` run rebuilds the store from a snapshot; it is not a distinct
# configuration a researcher chose to try, so it is excluded from the count
# the same way a control or diagnostic variant is.
_EXCLUDED_FROM_DEV_HASH_COUNT = _CONTROL_AND_DIAGNOSTIC_KINDS | {"reproduce"}


def _json_default(obj: Any) -> Any:
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, (_dt.date, _dt.datetime)):
        return obj.isoformat()
    raise TypeError(f"not JSON serializable: {type(obj)!r}")


def canonical_json(obj: Any) -> str:
    """Sorted-key, whitespace-free JSON with exact decimals as strings."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=_json_default)


def eras_for_lane(lane: str) -> dict:
    return {name: eras_mod.era(lane, name) for name in ("dev", "validation", "holdout")}


def config_hash(
    lane: str,
    code_commit: str,
    params: Any = None,
    eras: Any = None,
) -> str:
    """SHA-256 over the canonical JSON of every locked parameter, the era
    bounds, the benchmark seed scheme, the stress cases, the control
    definitions and the code commit (spec/03 "Run record")."""
    if params is None:
        params = params_mod.ALL_LOCKED_PARAMS
    if eras is None:
        eras = eras_for_lane(lane)
    payload = {
        "lane": lane,
        "code_commit": code_commit,
        "params": params,
        "eras": eras,
    }
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CodeCommit:
    sha: str
    dirty: bool


def code_commit(repo_root: Path | str | None = None) -> CodeCommit:
    """The git HEAD of `repo_root` (default: this checkout), plus whether the
    working tree has uncommitted changes."""
    root = str(repo_root) if repo_root is not None else str(REPO_ROOT)

    def _git(*args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, check=True
        ).stdout.strip()

    sha = _git("rev-parse", "HEAD")
    status = _git("status", "--porcelain")
    return CodeCommit(sha=sha, dirty=bool(status))


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    lane: str
    era: str
    kind: str
    configuration_hash: str
    snapshot_id: str
    code_commit: str
    dirty: bool
    timestamp: str
    leakage_gate_status: Any
    holdout_unlocked: bool
    holdout_end: str | None
    seeds: tuple[int, ...]
    research_log_entry: str
    dev_config_hashes_before: int | None

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


class RunLog:
    """`runs/<run_id>.json` under a data root, via `fsspec` so the root can be
    local, a volume or `s3://`.

    The listing is derived from a glob over `runs/*.json` rather than a
    maintained index file: `s3fs` has no append semantics for S3 objects, and
    one JSON file per run already carries everything an index would."""

    def __init__(self, root_url: str):
        self.root_url = root_url
        self._fs, self._root_path = fsspec.core.url_to_fs(root_url)

    def _runs_dir(self) -> str:
        return f"{self._root_path.rstrip('/')}/runs"

    def _run_path(self, run_id: str) -> str:
        return f"{self._runs_dir()}/{run_id}.json"

    def record(
        self,
        *,
        lane: str,
        era: str,
        kind: str,
        configuration_hash: str,
        snapshot_id: str,
        commit: CodeCommit,
        research_log_entry: str,
        leakage_gate_status: Any = None,
        holdout_unlocked: bool = False,
        holdout_end: _dt.date | None = None,
        seeds: tuple[int, ...] = (),
        run_id: str | None = None,
        timestamp: _dt.datetime | None = None,
    ) -> RunRecord:
        if kind not in RUN_KINDS:
            raise ValueError(f"unknown run kind {kind!r}; expected one of {RUN_KINDS}")
        if era == "holdout" and not (holdout_unlocked and holdout_end is not None):
            raise ValueError(
                "refusing to record a holdout run without the unlock flag and a "
                "holdout end date (spec/03 Holdout)"
            )
        if era != "dev" and commit.dirty:
            raise ValueError(
                f"refusing to record a {era} run from a dirty working tree "
                "(spec/03 Run record)"
            )

        dev_config_hashes_before = None
        if era == "validation":
            dev_config_hashes_before = self._dev_config_hash_count(lane)

        record = RunRecord(
            run_id=run_id or uuid.uuid4().hex,
            lane=lane,
            era=era,
            kind=kind,
            configuration_hash=configuration_hash,
            snapshot_id=snapshot_id,
            code_commit=commit.sha,
            dirty=commit.dirty,
            timestamp=(timestamp or _dt.datetime.now(_dt.timezone.utc)).isoformat(),
            leakage_gate_status=leakage_gate_status,
            holdout_unlocked=holdout_unlocked,
            holdout_end=holdout_end.isoformat() if holdout_end else None,
            seeds=tuple(seeds),
            research_log_entry=research_log_entry,
            dev_config_hashes_before=dev_config_hashes_before,
        )
        self._write(record)
        return record

    def _dev_config_hash_count(self, lane: str) -> int:
        hashes: set[str] = set()
        for rec in self._iter_runs():
            if rec.get("lane") != lane or rec.get("era") != "dev":
                continue
            if rec.get("kind") in _EXCLUDED_FROM_DEV_HASH_COUNT:
                continue
            hashes.add(rec["configuration_hash"])
        return len(hashes)

    def _write(self, record: RunRecord) -> None:
        self._fs.makedirs(self._runs_dir(), exist_ok=True)
        payload = canonical_json(record.to_dict())
        with self._fs.open(self._run_path(record.run_id), "w") as f:
            f.write(payload)

    def _iter_runs(self) -> Iterator[dict]:
        runs_dir = self._runs_dir()
        if not self._fs.exists(runs_dir):
            return
        for path in sorted(self._fs.glob(f"{runs_dir}/*.json")):
            with self._fs.open(path, "r") as f:
                yield json.loads(f.read())

    def get(self, run_id: str) -> dict:
        with self._fs.open(self._run_path(run_id), "r") as f:
            return json.loads(f.read())

    def list(self, lane: str | None = None, era: str | None = None) -> Iterator[dict]:
        for rec in self._iter_runs():
            if lane is not None and rec.get("lane") != lane:
                continue
            if era is not None and rec.get("era") != era:
                continue
            yield rec


# --------------------------------------------------------- reproduce-from-snapshot

class ReproduceError(RuntimeError):
    """A snapshot could not be reproduced: an unknown id, a verification
    failure, or a source in the snapshot with no registered loader."""


def _load_sharadar(conn: Any, storage: Any, snapshot_id: str) -> Any:
    from ingest import sharadar as sharadar_mod
    return sharadar_mod.load_snapshot(conn, storage, snapshot_id)


def _no_binance_loader(conn: Any, storage: Any, snapshot_id: str) -> Any:
    raise ReproduceError(
        "no loader: the crypto lane was removed (spec change after issue 15)"
    )


# Per-source loaders a reproduced snapshot dispatches to. `binance` has none:
# the crypto lane was removed after the free-data screen (docs/architecture.md,
# "Status: v1 rule paused"), so a snapshot that still names Binance files
# raises rather than silently skipping them.
LOADERS: dict[str, Callable[[Any, Any, str], Any]] = {
    "sharadar": _load_sharadar,
    "binance": _no_binance_loader,
}


def _reproduce_configuration_hash(snapshot_id: str, commit_sha: str) -> str:
    """A reproduce run has no lane and reads none of `config/params.py`'s
    locked parameters, so spec/03's analytical `config_hash` does not apply;
    this is just enough to make each reproduce record's hash reproducible and
    tied to what it rebuilt."""
    payload = {"kind": "reproduce", "snapshot_id": snapshot_id, "code_commit": commit_sha}
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def reproduce(
    snapshot_id: str,
    *,
    data_root: str | None = None,
    store: str | Path | None = None,
    force: bool = False,
    sources: list[str] | None = None,
) -> tuple[Path, dict[str, int]]:
    """Rebuild a fresh store at `store` (default `config.env.store_path()`)
    from `snapshot_id`'s raw files under `data_root` (default
    `config.env.data_root()`), never fetching.

    Verifies every file the snapshot names before writing anything (an
    unknown id or any mismatch/missing file raises `ReproduceError` with
    nothing written). Dispatches each source the snapshot actually contains
    (`sources`, default: every one) through `LOADERS`. Writes into a temp file
    beside `store` and renames it into place only once every source has
    loaded cleanly; an existing file at `store` is refused unless
    `force=True`. Returns `(store_path, {table: row_count})`.
    """
    from ingest.fetch import snapshot as snapshot_mod
    from ingest.fetch.storage import Storage

    storage = Storage(data_root if data_root is not None else env_mod.data_root())

    try:
        bad = snapshot_mod.verify(storage, snapshot_id)
    except FileNotFoundError:
        raise ReproduceError(
            f"unknown snapshot id {snapshot_id!r}: no snapshots/{snapshot_id}.json "
            f"under {storage.root_url}"
        ) from None
    if bad:
        raise ReproduceError(
            f"snapshot {snapshot_id!r}: {len(bad)} file(s) failed verification "
            "(tampered or missing); nothing written:\n  " + "\n  ".join(bad)
        )
    doc = storage.read_json(f"snapshots/{snapshot_id}.json")

    store_path = Path(store) if store is not None else env_mod.store_path()
    if store_path.exists() and not force:
        raise ReproduceError(
            f"refusing to overwrite existing store at {store_path} (pass --force)"
        )

    present = {name for name, files in (doc.get("sources") or {}).items() if files}
    wanted = set(sources) if sources is not None else None
    to_load = sorted(present if wanted is None else present & wanted)
    unknown = [name for name in to_load if name not in LOADERS]
    if unknown:
        raise ReproduceError(f"no loader registered for source(s) {unknown}")

    from harness.store import connect as store_connect
    from harness.store.schema import TABLES

    store_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = store_path.with_name(f"{store_path.name}.reproduce-{uuid.uuid4().hex}.tmp")
    try:
        conn = store_connect(tmp_path)
        try:
            for name in to_load:
                LOADERS[name](conn, storage, snapshot_id)
            conn.commit()
        finally:
            conn.close()
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise
    tmp_path.replace(store_path)

    row_counts: dict[str, int] = {}
    conn = store_connect(store_path)
    try:
        for name in sorted(TABLES):
            n = conn.execute(
                f"SELECT COUNT(*) FROM {name} WHERE snapshot_id = ?", (snapshot_id,)
            ).fetchone()[0]
            if n:
                row_counts[name] = n
    finally:
        conn.close()
    return store_path, row_counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m harness.runrecord")
    sub = parser.add_subparsers(dest="command", required=True)

    hash_p = sub.add_parser("hash", help="print the configuration hash for a lane")
    hash_p.add_argument("--lane", required=True, choices=eras_mod.LANES)

    list_p = sub.add_parser("list", help="list recorded runs")
    list_p.add_argument("--lane", default=None, choices=eras_mod.LANES)
    list_p.add_argument("--era", default=None, choices=("dev", "validation", "holdout"))

    show_p = sub.add_parser("show", help="show one run record")
    show_p.add_argument("run_id")

    repro_p = sub.add_parser(
        "reproduce", help="rebuild the store from a named snapshot's raw files, never fetching"
    )
    repro_p.add_argument("snapshot_id")
    repro_p.add_argument("--store", default=None, help="store path (default: $PENUMBRA_STORE_PATH)")
    repro_p.add_argument("--force", action="store_true", help="overwrite an existing store file")
    repro_p.add_argument(
        "--sources", default=None,
        help="comma-separated source names to load (default: every source the snapshot contains)"
    )

    args = parser.parse_args(argv)

    if args.command == "hash":
        commit = code_commit()
        print(config_hash(args.lane, commit.sha))
        return 0

    try:
        run_log = RunLog(env_mod.data_root())
    except env_mod.MissingEnvVar as exc:
        raise SystemExit(str(exc)) from None

    if args.command == "list":
        for rec in run_log.list(lane=args.lane, era=args.era):
            print(canonical_json(rec))
        return 0

    if args.command == "show":
        print(canonical_json(run_log.get(args.run_id)))
        return 0

    if args.command == "reproduce":
        sources = [s.strip() for s in args.sources.split(",") if s.strip()] if args.sources else None
        try:
            store_path, row_counts = reproduce(
                args.snapshot_id, store=args.store, force=args.force, sources=sources,
            )
        except (env_mod.MissingEnvVar, ReproduceError) as exc:
            raise SystemExit(str(exc)) from None
        for table in sorted(row_counts):
            print(f"{table}: {row_counts[table]} rows")
        print(f"snapshot {args.snapshot_id}")
        print(f"store {store_path}")

        commit = code_commit()
        run_log.record(
            lane="all",
            era="dev",
            kind="reproduce",
            configuration_hash=_reproduce_configuration_hash(args.snapshot_id, commit.sha),
            snapshot_id=args.snapshot_id,
            commit=commit,
            research_log_entry="n/a: reproduce rebuilds the store, it is not a pre-registered run",
        )
        return 0

    parser.error(f"unknown command {args.command!r}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

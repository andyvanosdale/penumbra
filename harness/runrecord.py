"""Configuration hash, run log and CLI (spec/03 "Run record").

A run is `(lane, era, configuration hash, snapshot id)` (docs/architecture.md
"Runs"). This module owns the hash, the append-only log under the data root,
and a small CLI. The leakage-suite gate itself is issue 18's
`harness/guards.py`; this module only carries its status as a field.

The reproduce-from-snapshot command needs the fetcher (PR 19), the store
(issue 16) and the loaders (issues 3 and 4) and is not implemented here
(issue 17 tracks the remainder).
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as _dt
import hashlib
import json
import os
import subprocess
import uuid
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterator

import fsspec

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
)

# Kinds excluded from the dev configuration-hash count (spec/03 "Use of
# eras"): a control or diagnostic variant always shares its paired primary
# run's configuration hash, so counting it separately would not add
# information.
_CONTROL_AND_DIAGNOSTIC_KINDS = frozenset(
    {"placebo", "positive_control", "capped", "close_fill", "benchmark"}
)


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
    """`runs/<run_id>.json` plus the append-only `runs/index.jsonl` under a
    data root, via `fsspec` so the root can be local, a volume or `s3://`."""

    def __init__(self, root_url: str):
        self.root_url = root_url
        self._fs, self._root_path = fsspec.core.url_to_fs(root_url)

    def _runs_dir(self) -> str:
        return f"{self._root_path.rstrip('/')}/runs"

    def _run_path(self, run_id: str) -> str:
        return f"{self._runs_dir()}/{run_id}.json"

    def _index_path(self) -> str:
        return f"{self._runs_dir()}/index.jsonl"

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
        for rec in self._iter_index():
            if rec.get("lane") != lane or rec.get("era") != "dev":
                continue
            if rec.get("kind") in _CONTROL_AND_DIAGNOSTIC_KINDS:
                continue
            hashes.add(rec["configuration_hash"])
        return len(hashes)

    def _write(self, record: RunRecord) -> None:
        self._fs.makedirs(self._runs_dir(), exist_ok=True)
        payload = canonical_json(record.to_dict())
        with self._fs.open(self._run_path(record.run_id), "w") as f:
            f.write(payload)
        with self._fs.open(self._index_path(), "a") as f:
            f.write(payload + "\n")

    def _iter_index(self) -> Iterator[dict]:
        if not self._fs.exists(self._index_path()):
            return
        with self._fs.open(self._index_path(), "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)

    def get(self, run_id: str) -> dict:
        with self._fs.open(self._run_path(run_id), "r") as f:
            return json.loads(f.read())

    def list(self, lane: str | None = None, era: str | None = None) -> Iterator[dict]:
        for rec in self._iter_index():
            if lane is not None and rec.get("lane") != lane:
                continue
            if era is not None and rec.get("era") != era:
                continue
            yield rec


def _data_root() -> str:
    root = os.environ.get("PENUMBRA_DATA_ROOT")
    if not root:
        raise SystemExit(
            "PENUMBRA_DATA_ROOT is not set; see docs/running.md and "
            "docs/environment.md"
        )
    return root


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

    args = parser.parse_args(argv)

    if args.command == "hash":
        commit = code_commit()
        print(config_hash(args.lane, commit.sha))
        return 0

    run_log = RunLog(_data_root())

    if args.command == "list":
        for rec in run_log.list(lane=args.lane, era=args.era):
            print(canonical_json(rec))
        return 0

    if args.command == "show":
        print(canonical_json(run_log.get(args.run_id)))
        return 0

    parser.error(f"unknown command {args.command!r}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

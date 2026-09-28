"""The leakage gate (spec/02 Leakage tests): a run refuses to write results
unless the leakage suite (`pytest -m leakage`) passed on this commit, with a
clean working tree and at least one test collected.

`python -m harness.guards check` runs the suite and records the result under
the data root. `require_leakage_passed` is what a run calls before writing
anything.

`PENUMBRA_DATA_ROOT` is read directly from the environment for now; issue 2
(`config/env.py`) is building the single place every environment variable is
read, in parallel, and will switch this over.

This module owns the leakage gate only. The holdout unlock (issue 11) is a
second, separate responsibility of `harness/guards.py` per
`docs/architecture.md` and is not implemented here.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import posixpath
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Callable

import fsspec

RunFn = Callable[..., "subprocess.CompletedProcess[str]"]


class LeakageGateError(RuntimeError):
    """Raised when the leakage gate refuses a run."""


def _run(cmd: list[str], *, cwd: str | None = None) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def git_commit(cwd: str | None = None) -> str:
    proc = _run(["git", "rev-parse", "HEAD"], cwd=cwd)
    if proc.returncode != 0:
        raise RuntimeError(f"git rev-parse HEAD failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def git_dirty(cwd: str | None = None) -> bool:
    proc = _run(["git", "status", "--porcelain"], cwd=cwd)
    if proc.returncode != 0:
        raise RuntimeError(f"git status failed: {proc.stderr.strip()}")
    return bool(proc.stdout.strip())


def _leakage_record_url(root_url: str, commit: str) -> str:
    return f"{root_url.rstrip('/')}/runs/leakage/{commit}.json"


def _write_json(url: str, data: dict[str, Any]) -> None:
    fs, path = fsspec.core.url_to_fs(url)
    parent = posixpath.dirname(path)
    if parent:
        fs.makedirs(parent, exist_ok=True)
    with fs.open(path, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def _read_json(url: str) -> dict[str, Any]:
    fs, path = fsspec.core.url_to_fs(url)
    if not fs.exists(path):
        raise FileNotFoundError(url)
    with fs.open(path, "r") as f:
        return json.load(f)


def run_leakage_suite(*, repo_root: str | Path | None = None, run: RunFn = _run) -> dict[str, Any]:
    """Run `pytest -m leakage -q` via `run` (a subprocess.run-shaped callable,
    injectable so tests can fake the runner instead of recursing into pytest)
    and return a result record. Does not write anything."""

    repo_root = str(repo_root) if repo_root is not None else str(Path.cwd())
    commit = git_commit(cwd=repo_root)
    dirty = git_dirty(cwd=repo_root)
    with tempfile.TemporaryDirectory() as tmp:
        junit_path = Path(tmp) / "leakage-junit.xml"
        proc = run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-m",
                "leakage",
                "-q",
                f"--junit-xml={junit_path}",
            ],
            cwd=repo_root,
        )
        collected = 0
        if junit_path.exists():
            root = ET.parse(junit_path).getroot()
            suite = root if root.tag == "testsuite" else root.find("testsuite")
            if suite is not None:
                collected = int(suite.get("tests", 0))
    passed = proc.returncode == 0 and collected > 0
    return {
        "commit": commit,
        "dirty": dirty,
        "passed": passed,
        "collected": collected,
        "returncode": proc.returncode,
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
    }


def check(*, data_root: str | None = None, repo_root: str | Path | None = None, run: RunFn = _run) -> dict[str, Any]:
    """Run the leakage suite and write its record to
    `<data_root>/runs/leakage/<commit>.json`. Returns the record."""

    data_root = data_root if data_root is not None else os.environ.get("PENUMBRA_DATA_ROOT")
    if not data_root:
        raise RuntimeError("PENUMBRA_DATA_ROOT is not set")
    record = run_leakage_suite(repo_root=repo_root, run=run)
    _write_json(_leakage_record_url(data_root, record["commit"]), record)
    return record


def require_leakage_passed(root_url: str, commit: str) -> None:
    """Raise `LeakageGateError` unless a passing record exists for exactly
    this commit: the tree was clean, and at least one leakage test was
    collected (zero collected is a failure, not a pass)."""

    url = _leakage_record_url(root_url, commit)
    try:
        record = _read_json(url)
    except FileNotFoundError:
        raise LeakageGateError(f"no leakage gate record for commit {commit} at {url}") from None

    if record.get("commit") != commit:
        raise LeakageGateError(
            f"leakage gate record at {url} is for commit {record.get('commit')!r}, not {commit!r}"
        )
    if record.get("dirty"):
        raise LeakageGateError(f"leakage gate record for commit {commit} was taken with a dirty working tree")
    if not record.get("passed"):
        raise LeakageGateError(f"leakage suite failed on commit {commit}")
    if not record.get("collected"):
        raise LeakageGateError(f"leakage suite collected zero tests on commit {commit}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m harness.guards")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="run the leakage suite and record the result")
    args = parser.parse_args(argv)

    if args.cmd == "check":
        record = check()
        print(json.dumps(record, indent=2, sort_keys=True))
        return 0 if record["passed"] else 1
    return 1


if __name__ == "__main__":
    sys.exit(main())

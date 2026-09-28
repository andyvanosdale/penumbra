"""Unit tests for the leakage gate (harness/guards.py, spec/02 Leakage tests).

These test `require_leakage_passed` against hand-written records, and
`run_leakage_suite`/`check` against a fake subprocess runner — never a
recursive `pytest -m leakage` run.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from harness.guards import (
    LeakageGateError,
    _leakage_record_url,
    check,
    require_leakage_passed,
    run_leakage_suite,
)

COMMIT = "abc123"


def _write_record(root: Path, commit: str, **overrides) -> None:
    record = {
        "commit": commit,
        "dirty": False,
        "passed": True,
        "collected": 3,
        "returncode": 0,
        "timestamp": "2026-01-01T00:00:00+00:00",
    }
    record.update(overrides)
    path = Path(_leakage_record_url(str(root), commit))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record))


def test_refuses_when_no_record(tmp_path):
    with pytest.raises(LeakageGateError, match="no leakage gate record"):
        require_leakage_passed(str(tmp_path), COMMIT)


def test_refuses_on_failing_record(tmp_path):
    _write_record(tmp_path, COMMIT, passed=False)
    with pytest.raises(LeakageGateError, match="failed"):
        require_leakage_passed(str(tmp_path), COMMIT)


def test_refuses_on_record_for_different_commit(tmp_path):
    _write_record(tmp_path, "other-commit")
    with pytest.raises(LeakageGateError):
        require_leakage_passed(str(tmp_path), COMMIT)


def test_refuses_on_dirty_tree(tmp_path):
    _write_record(tmp_path, COMMIT, dirty=True)
    with pytest.raises(LeakageGateError, match="dirty"):
        require_leakage_passed(str(tmp_path), COMMIT)


def test_refuses_on_zero_collected(tmp_path):
    _write_record(tmp_path, COMMIT, collected=0)
    with pytest.raises(LeakageGateError, match="zero tests"):
        require_leakage_passed(str(tmp_path), COMMIT)


def test_passes_on_clean_passing_record(tmp_path):
    _write_record(tmp_path, COMMIT)
    require_leakage_passed(str(tmp_path), COMMIT)  # does not raise


_JUNIT_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest" tests="{tests}" failures="{failures}" errors="0" skipped="0"></testsuite></testsuites>
"""


def _fake_run(returncode: int, tests: int, failures: int = 0):
    def run(cmd, cwd=None):
        junit_path = next(
            Path(part.split("=", 1)[1]) for part in cmd if part.startswith("--junit-xml=")
        )
        junit_path.write_text(_JUNIT_TEMPLATE.format(tests=tests, failures=failures))
        return subprocess.CompletedProcess(cmd, returncode=returncode, stdout="", stderr="")

    return run


def test_run_leakage_suite_records_a_pass(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path)
    subprocess.run(["git", "config", "user.name", "test"], cwd=tmp_path)
    (tmp_path / "f.txt").write_text("x")
    subprocess.run(["git", "add", "."], cwd=tmp_path)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path)

    record = run_leakage_suite(repo_root=tmp_path, run=_fake_run(returncode=0, tests=5))
    assert record["passed"] is True
    assert record["collected"] == 5
    assert record["dirty"] is False


def test_run_leakage_suite_records_zero_collected_as_not_passed(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path)
    subprocess.run(["git", "config", "user.name", "test"], cwd=tmp_path)
    (tmp_path / "f.txt").write_text("x")
    subprocess.run(["git", "add", "."], cwd=tmp_path)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path)

    record = run_leakage_suite(repo_root=tmp_path, run=_fake_run(returncode=0, tests=0))
    assert record["collected"] == 0
    assert record["passed"] is False


def test_check_writes_record_under_data_root(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo)
    subprocess.run(["git", "config", "user.name", "test"], cwd=repo)
    (repo / "f.txt").write_text("x")
    subprocess.run(["git", "add", "."], cwd=repo)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo)

    data_root = tmp_path / "data"
    record = check(data_root=str(data_root), repo_root=repo, run=_fake_run(returncode=0, tests=3))
    commit = record["commit"]

    on_disk = json.loads(Path(_leakage_record_url(str(data_root), commit)).read_text())
    assert on_disk == record
    require_leakage_passed(str(data_root), commit)  # does not raise


def test_check_falls_back_to_config_env_data_root(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo)
    subprocess.run(["git", "config", "user.name", "test"], cwd=repo)
    (repo / "f.txt").write_text("x")
    subprocess.run(["git", "add", "."], cwd=repo)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo)

    data_root = tmp_path / "data"
    monkeypatch.setenv("PENUMBRA_DATA_ROOT", str(data_root))
    record = check(repo_root=repo, run=_fake_run(returncode=0, tests=3))
    commit = record["commit"]

    assert Path(_leakage_record_url(str(data_root), commit)).exists()

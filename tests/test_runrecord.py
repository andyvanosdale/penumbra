"""harness/runrecord.py: configuration hash, run log and CLI."""

from __future__ import annotations

import dataclasses
import datetime as _dt
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

from config import params
from harness import runrecord

REPO_ROOT = Path(__file__).resolve().parents[1]


# --- helpers: a generic dataclass-tree mutator, so the "every locked
# parameter changes the hash" test does not hand-pick a few fields. -----------
def _perturb_scalar(value):
    if isinstance(value, bool):
        return not value
    if isinstance(value, Decimal):
        return value + Decimal("1")
    if isinstance(value, int):
        return value + 1
    if isinstance(value, str):
        return value + "_perturbed"
    if isinstance(value, _dt.date):
        return value + _dt.timedelta(days=1)
    if value is None:
        return "not_none_sentinel"
    raise TypeError(f"do not know how to perturb a {type(value)!r} leaf: {value!r}")


def _mutations(obj):
    """Yield copies of `obj` with exactly one scalar leaf perturbed, walking
    the whole dataclass/tuple tree rather than a hand-picked subset."""
    if dataclasses.is_dataclass(obj):
        for f in dataclasses.fields(obj):
            value = getattr(obj, f.name)
            for mutated in _mutations(value):
                yield dataclasses.replace(obj, **{f.name: mutated})
    elif isinstance(obj, tuple):
        for i, item in enumerate(obj):
            for mutated in _mutations(item):
                yield obj[:i] + (mutated,) + obj[i + 1 :]
    else:
        yield _perturb_scalar(obj)


def test_mutation_walker_covers_every_field():
    # Sanity check on the helper itself: it should reach dozens of leaves, not
    # a handful, across the full locked-parameter tree.
    count = sum(1 for _ in _mutations(params.ALL_LOCKED_PARAMS))
    assert count > 30


def test_config_hash_changes_with_any_locked_parameter():
    lane = "smallcap"
    commit = "0" * 40
    baseline = runrecord.config_hash(lane, commit)
    checked = 0
    for mutated in _mutations(params.ALL_LOCKED_PARAMS):
        checked += 1
        assert runrecord.config_hash(lane, commit, params=mutated) != baseline
    assert checked > 30


def test_config_hash_changes_with_era_bounds():
    lane = "smallcap"
    commit = "0" * 40
    baseline = runrecord.config_hash(lane, commit)
    mutated_eras = dict(runrecord.eras_for_lane(lane))
    mutated_eras["dev"] = dataclasses.replace(
        mutated_eras["dev"], end=mutated_eras["dev"].end - _dt.timedelta(days=1)
    )
    assert runrecord.config_hash(lane, commit, eras=mutated_eras) != baseline


def test_config_hash_changes_with_code_commit():
    lane = "smallcap"
    assert runrecord.config_hash(lane, "a" * 40) != runrecord.config_hash(lane, "b" * 40)


def test_config_hash_deterministic_in_process():
    lane = "smallcap"
    commit = "c" * 40
    assert runrecord.config_hash(lane, commit) == runrecord.config_hash(lane, commit)


def test_config_hash_deterministic_across_processes():
    lane = "smallcap"
    commit = runrecord.code_commit().sha
    expected = runrecord.config_hash(lane, commit)
    result = subprocess.run(
        [sys.executable, "-m", "harness.runrecord", "hash", "--lane", lane],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == expected


def test_code_commit_shape():
    commit = runrecord.code_commit()
    assert len(commit.sha) == 40
    assert all(c in "0123456789abcdef" for c in commit.sha)
    assert isinstance(commit.dirty, bool)


# --- RunLog -------------------------------------------------------------------
def _commit(dirty: bool = False) -> runrecord.CodeCommit:
    return runrecord.CodeCommit(sha="a" * 40, dirty=dirty)


def test_record_written_for_every_run_kind(tmp_path):
    log = runrecord.RunLog(str(tmp_path))
    for kind in runrecord.RUN_KINDS:
        rec = log.record(
            lane="smallcap",
            era="dev",
            kind=kind,
            configuration_hash="hash-" + kind,
            snapshot_id="snap-1",
            commit=_commit(),
            research_log_entry="research_log/2026-01-01-test.md",
        )
        assert rec.kind == kind
        reread = log.get(rec.run_id)
        assert reread["kind"] == kind
        assert reread["configuration_hash"] == "hash-" + kind


def test_holdout_requires_unlock_and_end_date(tmp_path):
    log = runrecord.RunLog(str(tmp_path))
    with pytest.raises(ValueError):
        log.record(
            lane="crypto",
            era="holdout",
            kind="primary",
            configuration_hash="h",
            snapshot_id="s",
            commit=_commit(),
            research_log_entry="research_log/x.md",
        )
    with pytest.raises(ValueError):
        log.record(
            lane="crypto",
            era="holdout",
            kind="primary",
            configuration_hash="h",
            snapshot_id="s",
            commit=_commit(),
            research_log_entry="research_log/x.md",
            holdout_unlocked=True,
        )
    rec = log.record(
        lane="crypto",
        era="holdout",
        kind="primary",
        configuration_hash="h",
        snapshot_id="s",
        commit=_commit(),
        research_log_entry="research_log/x.md",
        holdout_unlocked=True,
        holdout_end=_dt.date(2026, 1, 1),
    )
    assert rec.holdout_unlocked is True
    assert rec.holdout_end == "2026-01-01"


def test_dirty_tree_refused_outside_dev(tmp_path):
    log = runrecord.RunLog(str(tmp_path))
    with pytest.raises(ValueError):
        log.record(
            lane="smallcap",
            era="validation",
            kind="primary",
            configuration_hash="h",
            snapshot_id="s",
            commit=_commit(dirty=True),
            research_log_entry="research_log/x.md",
        )


def test_dirty_tree_recorded_for_dev(tmp_path):
    log = runrecord.RunLog(str(tmp_path))
    rec = log.record(
        lane="smallcap",
        era="dev",
        kind="primary",
        configuration_hash="h",
        snapshot_id="s",
        commit=_commit(dirty=True),
        research_log_entry="research_log/x.md",
    )
    assert rec.dirty is True


def test_dev_config_hashes_before_excludes_controls_and_diagnostics(tmp_path):
    log = runrecord.RunLog(str(tmp_path))
    log.record(
        lane="smallcap", era="dev", kind="primary", configuration_hash="h1",
        snapshot_id="s", commit=_commit(), research_log_entry="research_log/x.md",
    )
    log.record(
        lane="smallcap", era="dev", kind="primary", configuration_hash="h2",
        snapshot_id="s", commit=_commit(), research_log_entry="research_log/x.md",
    )
    # A control run under a third, distinct hash must not inflate the count.
    log.record(
        lane="smallcap", era="dev", kind="placebo", configuration_hash="h3",
        snapshot_id="s", commit=_commit(), research_log_entry="research_log/x.md",
    )
    validation_rec = log.record(
        lane="smallcap", era="validation", kind="primary", configuration_hash="h2",
        snapshot_id="s", commit=_commit(), research_log_entry="research_log/x.md",
    )
    assert validation_rec.dev_config_hashes_before == 2


def test_list_filters_by_lane_and_era(tmp_path):
    log = runrecord.RunLog(str(tmp_path))
    log.record(
        lane="smallcap", era="dev", kind="primary", configuration_hash="h1",
        snapshot_id="s", commit=_commit(), research_log_entry="research_log/x.md",
    )
    log.record(
        lane="crypto", era="dev", kind="primary", configuration_hash="h2",
        snapshot_id="s", commit=_commit(), research_log_entry="research_log/x.md",
    )
    smallcap_runs = list(log.list(lane="smallcap"))
    assert len(smallcap_runs) == 1
    assert smallcap_runs[0]["lane"] == "smallcap"

    dev_runs = list(log.list(era="dev"))
    assert len(dev_runs) == 2


def test_unknown_run_kind_rejected(tmp_path):
    log = runrecord.RunLog(str(tmp_path))
    with pytest.raises(ValueError):
        log.record(
            lane="smallcap", era="dev", kind="not_a_kind", configuration_hash="h",
            snapshot_id="s", commit=_commit(), research_log_entry="research_log/x.md",
        )


def test_cli_hash(monkeypatch, capsys):
    monkeypatch.chdir(REPO_ROOT)
    exit_code = runrecord.main(["hash", "--lane", "smallcap"])
    assert exit_code == 0
    out = capsys.readouterr().out.strip()
    assert len(out) == 64  # hex sha256


def test_cli_list_and_show(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("PENUMBRA_DATA_ROOT", str(tmp_path))
    log = runrecord.RunLog(str(tmp_path))
    rec = log.record(
        lane="smallcap", era="dev", kind="primary", configuration_hash="h1",
        snapshot_id="s", commit=_commit(), research_log_entry="research_log/x.md",
    )
    capsys.readouterr()

    exit_code = runrecord.main(["list", "--lane", "smallcap"])
    assert exit_code == 0
    assert rec.run_id in capsys.readouterr().out

    exit_code = runrecord.main(["show", rec.run_id])
    assert exit_code == 0
    assert '"configuration_hash":"h1"' in capsys.readouterr().out

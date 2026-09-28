"""Tests for config/env.py (issue 2) plus the acceptance check it exists for:
a fresh checkout runs the legacy negative control with only environment
variables set (spec/02-data.md, Configuration).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from config import env

REPO_ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------- accessors

def test_data_root_missing_raises(monkeypatch):
    monkeypatch.delenv("PENUMBRA_DATA_ROOT", raising=False)
    with pytest.raises(env.MissingEnvVar) as exc:
        env.data_root()
    assert "PENUMBRA_DATA_ROOT" in str(exc.value)
    assert "docs/environment.md" in str(exc.value)


def test_data_root_present(monkeypatch):
    monkeypatch.setenv("PENUMBRA_DATA_ROOT", "/mnt/penumbra")
    assert env.data_root() == "/mnt/penumbra"


def test_store_path_missing_raises(monkeypatch):
    monkeypatch.delenv("PENUMBRA_STORE_PATH", raising=False)
    with pytest.raises(env.MissingEnvVar) as exc:
        env.store_path()
    assert "PENUMBRA_STORE_PATH" in str(exc.value)


def test_store_path_returns_a_path(monkeypatch, tmp_path):
    db = tmp_path / "store.sqlite"
    monkeypatch.setenv("PENUMBRA_STORE_PATH", str(db))
    assert env.store_path() == db


def test_s3_endpoint_optional(monkeypatch):
    monkeypatch.delenv("PENUMBRA_S3_ENDPOINT", raising=False)
    assert env.s3_endpoint() is None
    monkeypatch.setenv("PENUMBRA_S3_ENDPOINT", "https://s3.example.com")
    assert env.s3_endpoint() == "https://s3.example.com"


def test_nasdaq_key_missing_raises(monkeypatch):
    monkeypatch.delenv("NASDAQ_DATA_LINK_API_KEY", raising=False)
    with pytest.raises(env.MissingEnvVar) as exc:
        env.nasdaq_data_link_api_key()
    assert "NASDAQ_DATA_LINK_API_KEY" in str(exc.value)


def test_nasdaq_key_never_leaks_into_error_text(monkeypatch):
    secret = "sk-super-secret-value-should-never-appear"
    monkeypatch.setenv("NASDAQ_DATA_LINK_API_KEY", secret)
    assert env.nasdaq_data_link_api_key() == secret

    # Nothing this module raises, anywhere, should be able to echo the value:
    # MissingEnvVar is built only from the variable's name.
    err = env.MissingEnvVar("NASDAQ_DATA_LINK_API_KEY")
    assert secret not in str(err)
    assert secret not in repr(err)


def test_is_local_root():
    assert env.is_local_root("/mnt/penumbra")
    assert env.is_local_root("relative/path")
    assert not env.is_local_root("s3://bucket/prefix")


def test_legacy_data_root_requires_local_root(monkeypatch):
    monkeypatch.setenv("PENUMBRA_DATA_ROOT", "s3://bucket/prefix")
    with pytest.raises(ValueError, match="local"):
        env.legacy_data_root()


def test_legacy_data_root_is_a_subdir_of_data_root(monkeypatch, tmp_path):
    monkeypatch.setenv("PENUMBRA_DATA_ROOT", str(tmp_path))
    assert env.legacy_data_root() == tmp_path / "legacy"


# ------------------------------------------------------------ static path check

BANNED_SUBSTRINGS = ("/Users/", "/home/", "C:\\")
# The pattern we just removed from legacy/*.py: a hardcoded dir built relative
# to the file's own location, e.g. Path(__file__).resolve().parents[1] / "data".
PATH_FILE_DATA_RE = re.compile(r"Path\(__file__\)[^\n]*[\"']data[\"']")

_SKIP_DIR_PARTS = {"tests", ".git", "__pycache__", ".venv", "venv", "node_modules"}


def _repo_py_files_outside_tests():
    for path in REPO_ROOT.rglob("*.py"):
        rel = path.relative_to(REPO_ROOT)
        if _SKIP_DIR_PARTS.intersection(rel.parts[:-1]):
            continue
        yield path


def test_no_hardcoded_paths_outside_tests():
    offenders = []
    for path in _repo_py_files_outside_tests():
        text = path.read_text()
        rel = path.relative_to(REPO_ROOT)
        for needle in BANNED_SUBSTRINGS:
            if needle in text:
                offenders.append(f"{rel}: contains {needle!r}")
        if PATH_FILE_DATA_RE.search(text):
            offenders.append(f"{rel}: Path(__file__)-relative data directory")
    assert not offenders, "\n".join(offenders)


# -------------------------------------------------- legacy pipeline, env-only

def _run(module: str, args: list[str], env_vars: dict[str, str], cwd: Path):
    return subprocess.run(
        [sys.executable, "-m", module, *args],
        cwd=cwd,
        env=env_vars,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_legacy_negative_control_runs_with_only_data_root_set(tmp_path):
    """Acceptance check: a fresh checkout runs the negative control end to end
    (make_synthetic -> load_to_store -> dummy_feature) as a subprocess, with a
    clean environment carrying only PENUMBRA_DATA_ROOT.
    """
    clean_env = {
        "PATH": os.environ.get("PATH", ""),
        "PENUMBRA_DATA_ROOT": str(tmp_path),
        # Real HOME, not tmp_path: some deps (e.g. pandas' dateutil) resolve
        # user-site packages off it. No other PENUMBRA_*/NASDAQ_* var is set.
        "HOME": os.environ.get("HOME", ""),
    }

    synth = _run(
        "legacy.make_synthetic",
        ["--start", "2019-01-01", "--end", "2020-12-31", "--seed", "7"],
        clean_env,
        REPO_ROOT,
    )
    assert synth.returncode == 0, synth.stderr

    load = _run("legacy.load_to_store", [], clean_env, REPO_ROOT)
    assert load.returncode == 0, load.stderr

    dummy = _run("legacy.dummy_feature", [], clean_env, REPO_ROOT)
    assert dummy.returncode == 0, dummy.stdout + dummy.stderr
    assert "PASS" in dummy.stdout

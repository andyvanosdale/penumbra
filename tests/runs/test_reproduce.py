"""Tests for `harness.runrecord.reproduce` (issue 17): rebuilding the store
from a named snapshot's raw files, never fetching (spec/02: "A run is
reproduced by rebuilding the store from its snapshot, never from a fresh
download, because both vendors restate history"). No network: the fixtures
below build a fetcher-shaped snapshot by hand, the way `ingest/fetch_data.py`
would have written one, and `test_reproduce_never_touches_the_network` proves
the command itself never calls out.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import requests

from harness import runrecord
from harness.store import connect
from harness.store.schema import TABLES
from ingest.fetch import snapshot as snapshot_mod
from ingest.fetch.binance import Binance
from ingest.fetch.manifest import Manifest
from ingest.fetch.sharadar import Sharadar
from ingest.fetch.storage import Storage
from tests.fixtures import sharadar as sfx

REPO_ROOT = Path(__file__).resolve().parents[2]

# Tables ingest.sharadar.load populates against the fixture (tests/ingest/test_sharadar.py).
SHARADAR_TABLES = ["calendar", "symbols", "bars_daily", "actions", "listing", "marketcap", "events"]

BINANCE_STUB_REL = "raw/binance/data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2021-03.zip"


def _write_sharadar_manifest(storage: Storage, raw_dir: Path) -> None:
    """Write the Sharadar fixture's raw files into `storage` and record them in
    a manifest, the way `ingest/fetch/sharadar.py` would have."""
    manifest = Manifest(storage, "sharadar")
    for table, local_path in sfx.write_files(raw_dir).items():
        rel = f"raw/sharadar/{table}/{table}-test.zip"
        storage.write_bytes(rel, local_path.read_bytes())
        manifest.record(rel, path=rel, size=storage.size(rel), sha256=storage.sha256(rel),
                        version="test")
    manifest.save()


def _write_binance_stub(storage: Storage) -> None:
    """One fake kline file, just to make the snapshot's `sources.binance`
    non-empty for the no-loader test. Its contents are never read: the
    binance loader raises before any file would be opened."""
    manifest = Manifest(storage, "binance")
    storage.write_bytes(BINANCE_STUB_REL, b"not a real kline file")
    manifest.record(BINANCE_STUB_REL, path=BINANCE_STUB_REL, size=storage.size(BINANCE_STUB_REL),
                    sha256=storage.sha256(BINANCE_STUB_REL), version="etag-1")
    manifest.save()


def build_snapshot(storage: Storage, raw_dir: Path, *, with_binance: bool = False) -> str:
    _write_sharadar_manifest(storage, raw_dir)
    sources = [Sharadar()]
    if with_binance:
        _write_binance_stub(storage)
        sources.append(Binance())
    return snapshot_mod.write(storage, sources=sources)


def _dump_tables(conn, snapshot_id: str) -> dict[str, list[tuple]]:
    """A canonical dump of every table's rows for this snapshot, since two
    SQLite files built independently need not be byte-identical even when
    their contents are (page layout, vacuum state, ...)."""
    dump = {}
    for name, table in sorted(TABLES.items()):
        cols = ", ".join(table.all_columns)
        rows = conn.execute(
            f"SELECT {cols} FROM {name} WHERE snapshot_id = ? ORDER BY {cols}", (snapshot_id,)
        ).fetchall()
        dump[name] = rows
    return dump


@pytest.fixture
def data_root(tmp_path) -> Storage:
    return Storage(str(tmp_path / "data-root"))


@pytest.fixture
def snapshot_id(data_root, tmp_path) -> str:
    return build_snapshot(data_root, tmp_path / "raw-fixture")


# --------------------------------------------------------------------- basics

def test_reproduce_builds_expected_rows(data_root, snapshot_id, tmp_path):
    store_path = tmp_path / "store.sqlite"
    result_path, row_counts = runrecord.reproduce(
        snapshot_id, data_root=data_root.root_url, store=str(store_path))

    assert result_path == store_path
    assert store_path.exists()
    for table in SHARADAR_TABLES:
        assert row_counts.get(table, 0) > 0, table

    conn = connect(store_path)
    try:
        n = conn.execute(
            "SELECT COUNT(*) FROM symbols WHERE snapshot_id = ?", (snapshot_id,)).fetchone()[0]
        assert n == row_counts["symbols"] > 0
        row = conn.execute(
            "SELECT document FROM snapshots WHERE snapshot_id = ?", (snapshot_id,)).fetchone()
        assert row is not None
    finally:
        conn.close()


# -------------------------------------------------------------- verify first

def test_tampered_file_aborts_with_nothing_written(data_root, snapshot_id, tmp_path):
    doc = data_root.read_json(f"snapshots/{snapshot_id}.json")
    tampered_rel = sorted(doc["files"])[0]
    data_root.write_bytes(tampered_rel, b"these are not the bytes the snapshot hashed")

    store_path = tmp_path / "store.sqlite"
    with pytest.raises(runrecord.ReproduceError, match="verification"):
        runrecord.reproduce(snapshot_id, data_root=data_root.root_url, store=str(store_path))

    assert not store_path.exists()
    assert list(tmp_path.glob("store.sqlite*")) == []


def test_missing_file_aborts(data_root, snapshot_id, tmp_path):
    doc = data_root.read_json(f"snapshots/{snapshot_id}.json")
    missing_rel = sorted(doc["files"])[0]
    data_root.remove(missing_rel)

    store_path = tmp_path / "store.sqlite"
    with pytest.raises(runrecord.ReproduceError, match="verification"):
        runrecord.reproduce(snapshot_id, data_root=data_root.root_url, store=str(store_path))

    assert not store_path.exists()


def test_unknown_snapshot_id_is_a_clear_error(data_root, tmp_path):
    with pytest.raises(runrecord.ReproduceError, match="unknown snapshot id"):
        runrecord.reproduce("does-not-exist", data_root=data_root.root_url,
                            store=str(tmp_path / "store.sqlite"))


# -------------------------------------------------------------------- --force

def test_force_controls_overwrite(data_root, snapshot_id, tmp_path):
    store_path = tmp_path / "store.sqlite"
    runrecord.reproduce(snapshot_id, data_root=data_root.root_url, store=str(store_path))
    assert store_path.exists()

    with pytest.raises(runrecord.ReproduceError, match="refusing to overwrite"):
        runrecord.reproduce(snapshot_id, data_root=data_root.root_url, store=str(store_path))

    result_path, row_counts = runrecord.reproduce(
        snapshot_id, data_root=data_root.root_url, store=str(store_path), force=True)
    assert result_path == store_path
    assert row_counts["symbols"] > 0


# ---------------------------------------------------------------- no network

def test_reproduce_never_touches_the_network(monkeypatch, data_root, snapshot_id, tmp_path):
    def _boom(*args, **kwargs):
        raise AssertionError("reproduce must never touch the network")

    monkeypatch.setattr(requests.sessions.Session, "request", _boom)
    monkeypatch.setattr(requests, "get", _boom)
    monkeypatch.setattr(requests, "post", _boom)

    _, row_counts = runrecord.reproduce(
        snapshot_id, data_root=data_root.root_url, store=str(tmp_path / "store.sqlite"))
    assert row_counts["symbols"] > 0


# --------------------------------------------------------------- determinism

def test_reproduce_is_deterministic(data_root, snapshot_id, tmp_path):
    path1, _ = runrecord.reproduce(
        snapshot_id, data_root=data_root.root_url, store=str(tmp_path / "a.sqlite"))
    path2, _ = runrecord.reproduce(
        snapshot_id, data_root=data_root.root_url, store=str(tmp_path / "b.sqlite"))

    conn1, conn2 = connect(path1), connect(path2)
    try:
        dump1, dump2 = _dump_tables(conn1, snapshot_id), _dump_tables(conn2, snapshot_id)
    finally:
        conn1.close()
        conn2.close()
    assert dump1 == dump2
    assert any(rows for rows in dump1.values())  # sanity: not comparing two empty stores


# --------------------------------------------------------- binance no-loader

def test_binance_without_loader_raises(data_root, tmp_path):
    snap_id = build_snapshot(data_root, tmp_path / "raw-fixture", with_binance=True)
    store_path = tmp_path / "store.sqlite"

    with pytest.raises(runrecord.ReproduceError, match="crypto lane was removed"):
        runrecord.reproduce(snap_id, data_root=data_root.root_url, store=str(store_path))
    assert not store_path.exists()

    # --sources sharadar excludes binance, so the same snapshot reproduces cleanly.
    result_path, row_counts = runrecord.reproduce(
        snap_id, data_root=data_root.root_url, store=str(store_path), sources=["sharadar"])
    assert result_path == store_path
    assert row_counts["symbols"] > 0


# ------------------------------------------------------------------- run log

def test_cli_reproduce_writes_a_run_log_record(monkeypatch, data_root, snapshot_id, tmp_path):
    monkeypatch.setenv("PENUMBRA_DATA_ROOT", data_root.root_url)
    store_path = tmp_path / "store.sqlite"

    exit_code = runrecord.main(["reproduce", snapshot_id, "--store", str(store_path)])
    assert exit_code == 0
    assert store_path.exists()

    run_log = runrecord.RunLog(data_root.root_url)
    records = [r for r in run_log.list() if r["kind"] == "reproduce"]
    assert len(records) == 1
    assert records[0]["snapshot_id"] == snapshot_id
    assert records[0]["era"] == "dev"
    assert records[0]["dirty"] in (True, False)


def test_cli_reproduce_refuses_overwrite_without_force(monkeypatch, data_root, snapshot_id, tmp_path):
    monkeypatch.setenv("PENUMBRA_DATA_ROOT", data_root.root_url)
    store_path = tmp_path / "store.sqlite"
    store_path.write_bytes(b"pre-existing file, not a store")

    with pytest.raises(SystemExit, match="refusing to overwrite"):
        runrecord.main(["reproduce", snapshot_id, "--store", str(store_path)])

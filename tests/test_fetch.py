"""Unit tests for ingest/fetch: storage atomicity, manifest skip logic, the
Binance listing parser and planner, yfinance merge/restatement detection, and
snapshot id determinism. No network: sources are exercised with fakes."""

from __future__ import annotations

import argparse
import json

import pandas as pd
import pytest

from ingest.fetch import binance, snapshot
from ingest.fetch import yfinance_source as yfs
from ingest.fetch.base import Source, Task
from ingest.fetch.manifest import Manifest
from ingest.fetch.storage import Storage


@pytest.fixture
def root(tmp_path):
    return Storage(str(tmp_path / "data"))


# -- storage -----------------------------------------------------------------

def test_atomic_write_commits_and_discards(root):
    root.write_bytes("a/b.txt", b"hello")
    assert root.read_bytes("a/b.txt") == b"hello"
    assert not root.exists("a/b.txt.part")
    with root.open_atomic("a/c.txt") as w:
        w.write(b"partial")
        # no commit
    assert not root.exists("a/c.txt")
    assert not root.exists("a/c.txt.part")


def test_sha256_matches_writer(root):
    with root.open_atomic("x.bin") as w:
        w.write(b"abc")
        w.commit()
        digest = w.sha256
    assert root.sha256("x.bin") == digest
    assert root.size("x.bin") == 3


# -- manifest ----------------------------------------------------------------

def test_manifest_has_requires_object_and_size(root):
    m = Manifest(root, "t")
    root.write_bytes("f.zip", b"1234")
    m.record("f.zip", size=4, sha256="x", version="v1")
    m.save()
    m2 = Manifest(root, "t")
    assert m2.has("f.zip", size=4, version="v1")
    assert not m2.has("f.zip", version="v2")          # vendor published a new version
    assert not m2.has("f.zip", size=5)                 # listing says a different size
    root.remove("f.zip")
    assert not m2.has("f.zip", size=4, version="v1")   # object gone from storage


# -- runner ------------------------------------------------------------------

class FakeSource(Source):
    name = "fake"

    def __init__(self):
        self.calls = 0

    def plan(self, storage, manifest, args):
        yield Task(rel="raw/fake/one.bin", version="e1", size=3)
        yield Task(rel="raw/fake/two.bin", version="e2", size=3)

    def fetch(self, task, storage, args):
        self.calls += 1
        if task.rel.endswith("two.bin") and self.calls == 2:
            raise IOError("boom")
        with storage.open_atomic(task.rel) as w:
            w.write(b"abc")
            w.commit()
            return w.size, w.sha256


def test_runner_skips_present_and_survives_failures(root):
    src = FakeSource()
    args = argparse.Namespace(dry_run=False)
    r1 = src.run(root, args)
    assert (r1.planned, r1.fetched, r1.failed, r1.skipped) == (2, 1, 1, 0)
    r2 = src.run(root, args)
    assert (r2.skipped, r2.fetched, r2.failed) == (1, 1, 0)
    r3 = src.run(root, args)
    assert (r3.skipped, r3.fetched) == (2, 0)


# -- binance -----------------------------------------------------------------

LISTING = """<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Name>data.binance.vision</Name>
<Prefix>data/spot/monthly/klines/BTCUSDT/1d/</Prefix><IsTruncated>true</IsTruncated><NextMarker>k2</NextMarker>
<Contents><Key>data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2017-08.zip</Key><LastModified>2021-06-22T11:34:18.000Z</LastModified><ETag>&quot;de69&quot;</ETag><Size>1150</Size></Contents>
<Contents><Key>data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2017-08.zip.CHECKSUM</Key><LastModified>2021-06-22T11:34:18.000Z</LastModified><ETag>&quot;1621&quot;</ETag><Size>88</Size></Contents>
<CommonPrefixes><Prefix>data/spot/monthly/klines/0GBNB/</Prefix></CommonPrefixes>
</ListBucketResult>"""


def test_parse_listing():
    objs, prefixes, marker = binance.parse_listing(LISTING)
    assert [o["key"].rsplit("/", 1)[-1] for o in objs] == ["BTCUSDT-1d-2017-08.zip", "BTCUSDT-1d-2017-08.zip.CHECKSUM"]
    assert objs[0]["etag"] == "de69" and objs[0]["size"] == 1150
    assert prefixes == ["data/spot/monthly/klines/0GBNB/"]
    assert marker == "k2"


def test_next_month():
    assert binance._next_month("2024-12") == "2025-01"
    assert binance._next_month("2024-01") == "2024-02"


# -- yfinance ----------------------------------------------------------------

def _frame(dates, adj):
    return pd.DataFrame({"date": dates, "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0,
                         "adj_close": adj, "volume": 1})


def test_merge_appends_new_rows():
    old = _frame(["2024-01-02", "2024-01-03"], [10.0, 11.0])
    new = _frame(["2024-01-03", "2024-01-04"], [11.0, 12.0])
    merged, restated = yfs.merge(old, new)
    assert not restated
    assert list(merged["date"]) == ["2024-01-02", "2024-01-03", "2024-01-04"]


def test_merge_detects_restatement():
    old = _frame(["2024-01-02", "2024-01-03"], [10.0, 11.0])
    new = _frame(["2024-01-03", "2024-01-04"], [5.5, 6.0])   # split re-adjusted history
    merged, restated = yfs.merge(old, new)
    assert restated and merged is old


def test_last_session_skips_weekend():
    import datetime as dt
    assert yfs.last_session(dt.date(2024, 1, 8)) == dt.date(2024, 1, 5)   # Monday -> Friday


# -- snapshot ----------------------------------------------------------------

def test_snapshot_id_is_deterministic_and_verifies(root):
    m = Manifest(root, "s")
    root.write_bytes("raw/s/a.zip", b"aaa")
    m.record("raw/s/a.zip", size=3, sha256=root.sha256("raw/s/a.zip"), version="1")
    m.save()
    sid1 = snapshot.write(root, ["s"])
    sid2 = snapshot.write(root, ["s"])
    assert sid1 == sid2 and len(sid1) == 64
    assert snapshot.verify(root, sid1) == []
    root.write_bytes("raw/s/a.zip", b"aab")
    assert snapshot.verify(root, sid1) == ["raw/s/a.zip"]
    assert json.load(open(root.full("snapshots/latest.json")))["snapshot_id"] == sid1

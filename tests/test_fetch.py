"""Unit tests for ingest/fetch: storage atomicity, manifest and versioning, the
runner, the Binance listing parser and daily-tail planner, the Sharadar export
flow and key redaction, yfinance merge and restatement, and snapshot policy and
determinism. No network: vendors are replaced by fakes."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import types

import pandas as pd
import pytest

from ingest.fetch import binance, http, sharadar, snapshot
from ingest.fetch import yfinance_source as yfs
from ingest.fetch.base import Source, Task
from ingest.fetch.manifest import Manifest, versioned_path
from ingest.fetch.storage import Storage


@pytest.fixture
def root(tmp_path):
    return Storage(str(tmp_path / "data"))


def _put(storage, source, rel, data: bytes):
    with storage.open_atomic(rel) as w:
        w.write(data)
        w.commit()
        return w.size, w.sha256


# -- storage -----------------------------------------------------------------

def test_atomic_write_commits_and_discards(root):
    root.write_bytes("a/b.txt", b"hello")
    assert root.read_bytes("a/b.txt") == b"hello"
    assert not root.exists("a/b.txt.part")
    with root.open_atomic("a/c.txt") as w:
        w.write(b"partial")
    assert not root.exists("a/c.txt") and not root.exists("a/c.txt.part")


def test_sha256_and_sizes(root):
    _, digest = _put(root, "s", "raw/s/x.bin", b"abc")
    assert root.sha256("raw/s/x.bin") == digest
    assert root.sizes("raw/s") == {"raw/s/x.bin": 3}
    assert root.sizes("raw/nothing") == {}


# -- manifest ----------------------------------------------------------------

def test_manifest_has_requires_object_and_size(root):
    m = Manifest(root, "t")
    root.write_bytes("f.zip", b"1234")
    m.record("f.zip", path="f.zip", size=4, sha256="x", version="v1")
    m.save()
    m2 = Manifest(root, "t")
    assert m2.has("f.zip", size=4, version="v1")
    assert not m2.has("f.zip", version="v2")          # vendor published a new version
    assert not m2.has("f.zip", size=5)                 # listing says a different size
    root.remove("f.zip")
    assert not m2.has("f.zip", size=4, version="v1")   # object gone from storage


def test_manifest_size_cache_avoids_storage_calls(root):
    m = Manifest(root, "t", size_cache={"f.zip": 4})
    m.record("f.zip", path="f.zip", size=4, sha256="x", version="v1")
    assert m.has("f.zip", version="v1")               # no object on disk; cache answers


def test_versioned_path():
    assert versioned_path("raw/b/d/BTC-2024-01.zip", 'ab"c') == "raw/b/d/_v/abc/BTC-2024-01.zip"


# -- runner and restatement ----------------------------------------------------

class FakeSource(Source):
    name = "fake"
    prefix = "raw/fake"

    def __init__(self):
        self.tasks = [Task(key="raw/fake/one.bin", version="e1", size=3),
                      Task(key="raw/fake/two.bin", version="e2", size=3)]
        self.payload = b"abc"
        self.calls = 0
        self.fail_once = None

    def plan(self, storage, manifest, args):
        yield from self.tasks

    def fetch(self, task, storage, args):
        self.calls += 1
        if self.fail_once == task.key:
            self.fail_once = None
            raise IOError("boom")
        return _put(storage, self.name, task.dest, self.payload)


ARGS = argparse.Namespace(dry_run=False)


def test_runner_skips_present_and_survives_failures(root):
    src = FakeSource()
    src.fail_once = "raw/fake/two.bin"
    r1 = src.run(root, ARGS)
    assert (r1.planned, r1.fetched, r1.failed, r1.skipped) == (2, 1, 1, 0)
    r2 = src.run(root, ARGS)
    assert (r2.skipped, r2.fetched, r2.failed) == (1, 1, 0)
    r3 = src.run(root, ARGS)
    assert (r3.skipped, r3.fetched) == (2, 0)


def test_restatement_keeps_old_version_and_old_snapshot_verifies(root):
    src = FakeSource()
    src.run(root, ARGS)
    sid1 = snapshot.write(root, [src])
    assert snapshot.verify(root, sid1) == []

    # Vendor republishes one.bin under a new ETag with different bytes.
    src.tasks[0] = Task(key="raw/fake/one.bin", version="e1-new", size=3)
    src.payload = b"xyz"
    r = src.run(root, ARGS)
    assert (r.fetched, r.skipped) == (1, 1)

    assert root.read_bytes("raw/fake/one.bin") == b"abc"                       # old bytes untouched
    new_path = versioned_path("raw/fake/one.bin", "e1-new")
    assert root.read_bytes(new_path) == b"xyz"
    m = Manifest(root, "fake")
    assert m.current("raw/fake/one.bin")["path"] == new_path
    assert m.entries["raw/fake/one.bin"]["superseded_by"] == new_path
    assert not m.entries["raw/fake/one.bin"]["current"]

    assert snapshot.verify(root, sid1) == []                                    # snapshot N still good
    sid2 = snapshot.write(root, [src])
    assert sid2 != sid1
    doc = json.loads(root.read_text(f"snapshots/{sid2}.json"))
    assert set(doc["files"]) == {new_path, "raw/fake/two.bin"}                  # current versions only


def test_unversioned_source_rewrites_in_place(root):
    class InPlace(FakeSource):
        name = "inplace"
        prefix = "raw/inplace"
        versioned = False
    src = InPlace()
    src.tasks = [Task(key="raw/inplace/a.csv", version="through:2024-01-02")]
    src.run(root, ARGS)
    src.tasks = [Task(key="raw/inplace/a.csv", version="through:2024-01-03")]
    src.payload = b"new"
    src.run(root, ARGS)
    assert root.read_bytes("raw/inplace/a.csv") == b"new"
    assert len(Manifest(root, "inplace")) == 1


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


def _obj(key, etag="e", size=1):
    return {"key": key, "etag": etag, "size": size, "last_modified": "2024-01-01T00:00:00.000Z"}


def test_binance_daily_tail_starts_after_last_monthly(monkeypatch, root):
    bucket = {
        "data/spot/monthly/klines/BTCUSDT/1d/": [
            _obj("data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2024-01.zip"),
            _obj("data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2024-01.zip.CHECKSUM"),
            _obj("data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2024-02.zip"),
        ],
        "data/spot/daily/klines/BTCUSDT/1d/": [
            _obj("data/spot/daily/klines/BTCUSDT/1d/BTCUSDT-1d-2024-02-27.zip"),   # covered by monthly
            _obj("data/spot/daily/klines/BTCUSDT/1d/BTCUSDT-1d-2024-03-01.zip"),
            _obj("data/spot/daily/klines/BTCUSDT/1d/BTCUSDT-1d-2024-03-02.zip"),
        ],
    }
    calls = []

    def fake_list_bucket(sess, prefix, delimiter=None):
        calls.append(prefix)
        yield from bucket.get(prefix, [])

    monkeypatch.setattr(binance, "list_bucket", fake_list_bucket)
    monkeypatch.setattr(binance.http, "session", lambda: None)
    args = argparse.Namespace(quote="USDT", pairs="BTCUSDT", intervals="1d", funding=False, no_daily_tail=False)
    keys = [t.key for t in binance.Binance().plan(root, Manifest(root, "binance"), args)]
    assert keys == [
        "raw/binance/data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2024-01.zip",
        "raw/binance/data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2024-02.zip",
        "raw/binance/data/spot/daily/klines/BTCUSDT/1d/BTCUSDT-1d-2024-03-01.zip",
        "raw/binance/data/spot/daily/klines/BTCUSDT/1d/BTCUSDT-1d-2024-03-02.zip",
    ]
    assert calls.count("data/spot/monthly/klines/BTCUSDT/1d/") == 1          # monthly listed once


def test_binance_funding_excluded_from_snapshot():
    src = binance.Binance()
    assert src.snapshot_include("raw/binance/data/spot/monthly/klines/X/1d/a.zip", {})
    assert not src.snapshot_include("raw/binance/data/futures/um/monthly/fundingRate/X/a.zip", {})


# -- sharadar ----------------------------------------------------------------

class FakeResponse:
    def __init__(self, status, payload=None, url=""):
        self.status_code = status
        self._payload = payload
        self.url = url
        self.ok = status < 400

    def raise_for_status(self):
        if not self.ok:
            import requests
            raise requests.HTTPError(f"{self.status_code} Client Error for url: {self.url}")

    def json(self):
        return self._payload


class FakeSession:
    """Scripted responses; records every request's params."""

    def __init__(self, script):
        self.script = list(script)
        self.requests = []

    def get(self, url, params=None, timeout=None, **kw):
        self.requests.append((url, dict(params or {})))
        status, payload = self.script.pop(0)
        full = url + "?" + "&".join(f"{k}={v}" for k, v in (params or {}).items())
        return FakeResponse(status, payload, url=full)


def _export(status, when="2026-09-27 08:15:00"):
    return {"datatable_bulk_download": {"file": {"status": status, "link": "https://x/file.zip",
                                                 "data_snapshot_time": when}}}


def test_sharadar_export_polls_until_fresh_and_filters_sfp(monkeypatch):
    sess = FakeSession([(200, _export("creating")), (200, _export("regenerating")), (200, _export("fresh"))])
    monkeypatch.setattr(sharadar.time, "sleep", lambda s: None)
    info = sharadar.request_export(sess, "SFP", "SECRET", sharadar.TABLE_FILTERS["SFP"], poll_seconds=0)
    assert info["status"] == "fresh"
    assert len(sess.requests) == 3
    url, params = sess.requests[0]
    assert url.endswith("/SHARADAR/SFP.json")
    assert params["ticker"] == "SPY" and params["qopts.export"] == "true"


def test_sharadar_plan_names_file_by_snapshot_time_and_skips_fresh_tables(monkeypatch, root):
    sess = FakeSession([(200, _export("fresh", "2026-09-27 08:15:00"))])
    monkeypatch.setattr(sharadar.http, "session", lambda: sess)
    monkeypatch.setenv("NASDAQ_DATA_LINK_API_KEY", "SECRET")
    m = Manifest(root, "sharadar")
    # ACTIONS fetched a minute ago: skipped under max-age 1 day without an API call.
    m.record("raw/sharadar/ACTIONS/ACTIONS-20260927T0000.zip", path="raw/sharadar/ACTIONS/ACTIONS-20260927T0000.zip",
             size=1, sha256="x", version="2026-09-27 00:00:00", table="ACTIONS")
    args = argparse.Namespace(tables="ACTIONS,SEP", max_age_days=1.0)
    tasks = list(sharadar.Sharadar().plan(root, m, args))
    assert [t.key for t in tasks] == ["raw/sharadar/SEP/SEP-20260927T081500.zip"]
    assert tasks[0].version == "2026-09-27 08:15:00"
    assert len(sess.requests) == 1


def test_sharadar_error_redacts_api_key(monkeypatch):
    sess = FakeSession([(403, None)])
    with pytest.raises(http.RedactedError) as exc:
        sharadar.request_export(sess, "SEP", "SECRET-KEY-123", poll_seconds=0)
    assert "SECRET-KEY-123" not in str(exc.value)
    assert "403" in str(exc.value)


def test_sharadar_snapshot_one_export_per_table(root):
    src = sharadar.Sharadar()
    m = Manifest(root, "sharadar")
    for tag, when in (("20260901T000000", "2026-09-01 00:00:00"), ("20260927T081500", "2026-09-27 08:15:00")):
        p = f"raw/sharadar/SEP/SEP-{tag}.zip"
        _put(root, "sharadar", p, tag.encode())
        m.record(p, path=p, size=len(tag), sha256=root.sha256(p), version=when, table="SEP")
    p = "raw/sharadar/DAILY/DAILY-20260901T000000.zip"
    _put(root, "sharadar", p, b"d")
    m.record(p, path=p, size=1, sha256=root.sha256(p), version="2026-09-01 00:00:00", table="DAILY")
    m.save()
    sid, doc = snapshot.build(root, [src])
    assert set(doc["files"]) == {"raw/sharadar/SEP/SEP-20260927T081500.zip", p}
    assert doc["groups"]["sharadar"] == {"SEP": "raw/sharadar/SEP/SEP-20260927T081500.zip", "DAILY": p}


# -- yfinance ----------------------------------------------------------------

def _frame(dates, adj):
    return pd.DataFrame({"date": dates, "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0,
                         "adj_close": adj, "volume": 1})


def _yf_frame(dates, adj):
    df = pd.DataFrame({"Date": pd.to_datetime(dates), "Open": 1.0, "High": 1.0, "Low": 1.0,
                       "Close": 1.0, "Adj Close": adj, "Volume": 1})
    return df.set_index("Date")


def test_merge_appends_new_rows():
    merged, restated = yfs.merge(_frame(["2024-01-02", "2024-01-03"], [10.0, 11.0]),
                                 _frame(["2024-01-03", "2024-01-04"], [11.0, 12.0]))
    assert not restated and list(merged["date"]) == ["2024-01-02", "2024-01-03", "2024-01-04"]


def test_merge_detects_restatement():
    old = _frame(["2024-01-02", "2024-01-03"], [10.0, 11.0])
    merged, restated = yfs.merge(old, _frame(["2024-01-03", "2024-01-04"], [5.5, 6.0]))
    assert restated and merged is old


def test_yfinance_fetch_refetches_full_history_on_restatement(monkeypatch, root):
    calls = []

    def fake_download(yf, ticker, start, end):
        calls.append((start, end))
        if len(calls) == 1:                       # overlap window: split-adjusted history
            return _yf_frame(["2024-01-03", "2024-01-04"], [5.5, 6.0])
        return _yf_frame(["2024-01-02", "2024-01-03", "2024-01-04"], [5.0, 5.5, 6.0])

    monkeypatch.setattr(yfs, "_download", fake_download)
    monkeypatch.setitem(__import__("sys").modules, "yfinance", types.SimpleNamespace())
    yfs.write_csv(root, "raw/yfinance/ABC.csv", _frame(["2024-01-02", "2024-01-03"], [10.0, 11.0]))
    task = Task(key="raw/yfinance/ABC.csv", version="through:2024-01-04",
                meta={"ticker": "ABC", "start": "2024-01-02", "through": "2024-01-04"}, dest="raw/yfinance/ABC.csv")
    yfs.YFinance().fetch(task, root, argparse.Namespace(full=False))
    assert len(calls) == 2 and calls[1][0] == "2024-01-02"
    out = yfs.read_csv(root, "raw/yfinance/ABC.csv")
    assert list(out["adj_close"]) == [5.0, 5.5, 6.0]
    assert task.meta["restated"] is True


def test_yfinance_never_in_snapshot(root):
    src = yfs.YFinance()
    m = Manifest(root, "yfinance")
    _put(root, "yfinance", "raw/yfinance/SPY.csv", b"x")
    m.record("raw/yfinance/SPY.csv", path="raw/yfinance/SPY.csv", size=1, sha256="s", version="through:2024-01-02")
    m.save()
    sid, doc = snapshot.build(root, [src])
    assert doc["files"] == {} and doc["sources"]["yfinance"] == []


def test_last_session_skips_weekend():
    assert yfs.last_session(dt.date(2024, 1, 8)) == dt.date(2024, 1, 5)


# -- snapshot ----------------------------------------------------------------

def test_snapshot_id_hashes_only_path_size_sha(root):
    src = FakeSource()
    src.run(root, ARGS)
    sid, doc = snapshot.build(root, [src])
    import hashlib
    payload = json.dumps({p: {"size": e["size"], "sha256": e["sha256"]} for p, e in doc["files"].items()},
                         sort_keys=True, separators=(",", ":")).encode()
    assert sid == hashlib.sha256(payload).hexdigest()
    assert snapshot.write(root, [src]) == sid                         # deterministic
    root.write_bytes("raw/fake/two.bin", b"aab")
    assert snapshot.verify(root, sid) == ["raw/fake/two.bin"]

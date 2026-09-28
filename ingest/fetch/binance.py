"""Binance public data (https://data.binance.vision).

Files are immutable once published, so presence plus the bucket's ETag and size
is enough to skip them. When the bucket republishes a file under a new ETag the
runner stores the new bytes beside the old (``_v/<etag>/``), never over them. Monthly files cover closed months; the current month
is filled from daily files until its monthly file appears. Every file has a
sibling ``.CHECKSUM`` (sha256) that is verified before the file is kept.

Layout under the root mirrors the bucket:
  raw/binance/data/spot/monthly/klines/<PAIR>/<INTERVAL>/<PAIR>-<INTERVAL>-YYYY-MM.zip
  raw/binance/data/spot/daily/klines/<PAIR>/<INTERVAL>/<PAIR>-<INTERVAL>-YYYY-MM-DD.zip
  raw/binance/data/futures/um/monthly/fundingRate/<PAIR>/<PAIR>-fundingRate-YYYY-MM.zip
"""

from __future__ import annotations

import datetime as _dt
import xml.etree.ElementTree as ET
from typing import Iterable, Iterator

from . import http
from .base import Source, Task, register
from .manifest import Manifest
from .storage import Storage

LISTING = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
FILES = "https://data.binance.vision"
NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"
PREFIX = "raw/binance"


def parse_listing(xml_text: str) -> tuple[list[dict], list[str], str | None]:
    """Returns (objects, common_prefixes, next_marker)."""
    root = ET.fromstring(xml_text)
    objs = []
    for c in root.iter(f"{NS}Contents"):
        objs.append({
            "key": c.find(f"{NS}Key").text,
            "etag": (c.find(f"{NS}ETag").text or "").strip('"'),
            "size": int(c.find(f"{NS}Size").text),
            "last_modified": c.find(f"{NS}LastModified").text,
        })
    prefixes = [p.find(f"{NS}Prefix").text for p in root.iter(f"{NS}CommonPrefixes")]
    truncated = (root.findtext(f"{NS}IsTruncated") or "false") == "true"
    marker = None
    if truncated:
        marker = root.findtext(f"{NS}NextMarker")
        if not marker and objs:
            marker = objs[-1]["key"]
    return objs, prefixes, marker


def list_bucket(sess, prefix: str, delimiter: str | None = None) -> Iterator[dict | str]:
    marker = None
    while True:
        params = {"prefix": prefix, "max-keys": "1000"}
        if delimiter:
            params["delimiter"] = delimiter
        if marker:
            params["marker"] = marker
        r = sess.get(LISTING, params=params, timeout=60)
        r.raise_for_status()
        objs, prefixes, marker = parse_listing(r.text)
        yield from prefixes
        yield from objs
        if not marker:
            return


def list_pairs(sess, quote: str, market: str = "spot") -> list[str]:
    base = f"data/{market}/monthly/klines/"
    pairs = []
    for p in list_bucket(sess, base, delimiter="/"):
        if isinstance(p, str):
            pair = p[len(base):].strip("/")
            if pair.endswith(quote):
                pairs.append(pair)
    return sorted(pairs)



@register
class Binance(Source):
    name = "binance"
    help = "Binance public spot klines (1d, 1h) and USD-M funding rates"
    prefix = PREFIX
    snapshot_policy = "all"

    def snapshot_include(self, key: str, entry: dict) -> bool:
        # Funding rates are not in v1 (spec/04 Flags); they never enter a snapshot.
        return "/futures/" not in key

    def add_arguments(self, p):
        p.add_argument("--quote", default="USDT", help="quote asset suffix (default USDT)")
        p.add_argument("--pairs", default="", help="comma-separated pairs; default all with the quote")
        p.add_argument("--intervals", default="1d,1h", help="kline intervals (default 1d,1h)")
        p.add_argument("--funding", action="store_true", help="also fetch USD-M funding rates")
        p.add_argument("--no-daily-tail", action="store_true",
                       help="do not fill the current month from daily files")

    def plan(self, storage: Storage, manifest: Manifest, args) -> Iterable[Task]:
        sess = http.session()
        pairs = [x for x in args.pairs.split(",") if x] or list_pairs(sess, args.quote)
        intervals = [x for x in args.intervals.split(",") if x]
        today = _dt.date.today()
        this_month = today.strftime("%Y-%m")
        for pair in pairs:
            for iv in intervals:
                prefix = f"data/spot/monthly/klines/{pair}/{iv}/"
                monthly = [o for o in list_bucket(sess, prefix)
                           if isinstance(o, dict) and o["key"].endswith(".zip")]
                for obj in monthly:
                    yield self._task(obj)
                if not args.no_daily_tail:
                    # Daily files for the months the monthly listing does not yet cover.
                    last_month = None
                    for obj in monthly:
                        m = obj["key"][:-4].rsplit("-", 2)
                        last_month = max(last_month or "", f"{m[-2]}-{m[-1]}")
                    start = _next_month(last_month) if last_month else this_month
                    dprefix = f"data/spot/daily/klines/{pair}/{iv}/"
                    for obj in list_bucket(sess, dprefix):
                        if isinstance(obj, dict) and obj["key"].endswith(".zip"):
                            day = obj["key"][:-4].rsplit("-", 3)
                            month = f"{day[-3]}-{day[-2]}"
                            if month >= start:
                                yield self._task(obj)
            if args.funding:
                base = pair
                prefix = f"data/futures/um/monthly/fundingRate/{base}/"
                yield from self._objects(sess, prefix)

    def _objects(self, sess, prefix: str) -> Iterator[Task]:
        for obj in list_bucket(sess, prefix):
            if isinstance(obj, dict) and obj["key"].endswith(".zip"):
                yield self._task(obj)

    @staticmethod
    def _task(obj: dict) -> Task:
        return Task(key=f"{PREFIX}/{obj['key']}", version=obj["etag"], size=obj["size"],
                    meta={"last_modified": obj["last_modified"]})

    def fetch(self, task: Task, storage: Storage, args) -> tuple[int, str]:
        sess = http.session()
        key = task.key[len(PREFIX) + 1:]
        expected = None
        r = sess.get(f"{FILES}/{key}.CHECKSUM", timeout=60)
        if r.ok and r.text.strip():
            expected = r.text.split()[0].strip()
        task.meta["verified"] = expected is not None
        return http.download(sess, f"{FILES}/{key}", storage, task.dest, expect_sha256=expected)


def _next_month(ym: str) -> str:
    y, m = int(ym[:4]), int(ym[5:7])
    return f"{y + (m // 12)}-{(m % 12) + 1:02d}"

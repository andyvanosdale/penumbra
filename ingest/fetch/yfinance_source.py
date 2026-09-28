"""yfinance daily bars, one CSV per ticker, for the free-data screen and the
legacy plumbing test. Never read by a committed run (spec/02).

  raw/yfinance/<TICKER>.csv   columns: date, open, high, low, close, adj_close, volume

Update mode re-downloads a short overlap window and compares it with what is
stored; if the vendor restated history (a split or dividend re-adjusts every
prior adjusted close) the whole ticker is refetched, otherwise only the new
rows are appended. ``--full`` refetches everything.
"""

from __future__ import annotations

import datetime as _dt
import io
from pathlib import Path
from typing import Iterable

import pandas as pd

from .base import Source, Task, register
from .manifest import Manifest
from .storage import Storage

PREFIX = "raw/yfinance"
COLUMNS = ["date", "open", "high", "low", "close", "adj_close", "volume"]
OVERLAP_DAYS = 10


def last_session(today: _dt.date | None = None) -> _dt.date:
    """Most recent weekday strictly before today (yfinance's last complete bar)."""
    d = (today or _dt.date.today()) - _dt.timedelta(days=1)
    while d.weekday() >= 5:
        d -= _dt.timedelta(days=1)
    return d


def normalize(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=COLUMNS)
    df = df.reset_index()
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    out = pd.DataFrame({
        "date": pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d"),
        "open": df["Open"], "high": df["High"], "low": df["Low"],
        "close": df["Close"], "adj_close": df["Adj Close"], "volume": df["Volume"],
    })
    return out.dropna(subset=["close"]).sort_values("date").drop_duplicates("date", keep="last")


def merge(existing: pd.DataFrame, fresh: pd.DataFrame, tol: float = 1e-4) -> tuple[pd.DataFrame, bool]:
    """Append ``fresh`` onto ``existing``. Returns (merged, restated). Restated
    means the overlap disagreed on adj_close, in which case the caller should
    refetch the full history instead of trusting the merge."""
    if existing.empty:
        return fresh, False
    overlap = existing.merge(fresh, on="date", suffixes=("_old", "_new"))
    if not overlap.empty:
        rel = ((overlap["adj_close_old"] - overlap["adj_close_new"]).abs()
               / overlap["adj_close_old"].abs().clip(lower=1e-9))
        if (rel > tol).any():
            return existing, True
    merged = pd.concat([existing, fresh[~fresh["date"].isin(existing["date"])]], ignore_index=True)
    return merged.sort_values("date").reset_index(drop=True), False


def read_csv(storage: Storage, rel: str) -> pd.DataFrame:
    if not storage.exists(rel):
        return pd.DataFrame(columns=COLUMNS)
    return pd.read_csv(io.BytesIO(storage.read_bytes(rel)), dtype={"date": str})


def write_csv(storage: Storage, rel: str, df: pd.DataFrame) -> tuple[int, str]:
    data = df[COLUMNS].to_csv(index=False).encode("utf-8")
    with storage.open_atomic(rel) as w:
        w.write(data)
        w.commit()
        return w.size, w.sha256


def _download(yf, ticker: str, start: str, end: str):
    return yf.download(ticker, start=start, end=end, progress=False, auto_adjust=False, threads=False)


def load_tickers(args) -> list[str]:
    if args.tickers:
        return [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    if args.tickers_file:
        lines = Path(args.tickers_file).read_text().splitlines()
        return [l.strip().upper() for l in lines if l.strip() and not l.startswith("#")]
    raise SystemExit("yfinance: give --tickers or --tickers-file")


@register
class YFinance(Source):
    name = "yfinance"
    help = "yfinance daily bars per ticker (screen and legacy control only)"
    prefix = PREFIX
    versioned = False              # rewritten in place by design
    snapshot_policy = "none"       # never read by a committed run (spec/02)

    def add_arguments(self, p):
        p.add_argument("--tickers", default="", help="comma-separated tickers")
        p.add_argument("--tickers-file", default="", help="file with one ticker per line")
        p.add_argument("--start", default="2015-01-01")
        p.add_argument("--full", action="store_true", help="refetch full history for every ticker")

    def plan(self, storage: Storage, manifest: Manifest, args) -> Iterable[Task]:
        through = last_session().isoformat()
        for t in load_tickers(args):
            yield Task(key=f"{PREFIX}/{t}.csv", version=f"through:{through}",
                       meta={"ticker": t, "start": args.start, "through": through})

    def should_skip(self, task: Task, manifest: Manifest) -> bool:
        return manifest.has(task.key, version=task.version)

    def fetch(self, task: Task, storage: Storage, args) -> tuple[int, str]:
        import yfinance as yf
        ticker, start = task.meta["ticker"], task.meta["start"]
        end = (_dt.date.fromisoformat(task.meta["through"]) + _dt.timedelta(days=1)).isoformat()
        existing = pd.DataFrame(columns=COLUMNS) if args.full else read_csv(storage, task.dest)
        fetch_from = start
        if not existing.empty:
            last = _dt.date.fromisoformat(existing["date"].max())
            fetch_from = (last - _dt.timedelta(days=OVERLAP_DAYS)).isoformat()
        fresh = normalize(_download(yf, ticker, fetch_from, end), ticker)
        merged, restated = merge(existing, fresh)
        if restated:
            merged = normalize(_download(yf, ticker, start, end), ticker)
        if merged.empty:
            raise ValueError(f"no data for {ticker}")
        task.meta["rows"] = int(len(merged))
        task.meta["restated"] = bool(restated)
        return write_csv(storage, task.dest, merged)

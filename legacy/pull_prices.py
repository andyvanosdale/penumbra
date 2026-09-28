"""Pull daily OHLCV for the universe + sector ETFs and save an immutable, dated
raw snapshot (plan §5, §10.2, §6.5 data-versioning).

Requires `yfinance` and network access. Run on your machine, not in a sandbox:

    python -m legacy.pull_prices --start 2018-01-01 --end 2024-12-31

Output: data/raw/prices_<snapshot_date>.parquet  (never overwritten silently).
Columns: ticker, date, open, high, low, close, adj_close, volume.

The snapshot is immutable by convention: if it exists, this script refuses to
overwrite it. To re-pull, pass --snapshot-date with a new date.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import sys
from pathlib import Path

import pandas as pd

from legacy.universe import ALL_SYMBOLS

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def pull(symbols, start, end) -> pd.DataFrame:
    try:
        import yfinance as yf
    except ImportError:
        sys.exit("yfinance not installed. `pip install -r requirements.txt` "
                 "or use ingest/make_synthetic.py for an offline snapshot.")

    frames = []
    for sym in symbols:
        df = yf.download(sym, start=start, end=end, progress=False, auto_adjust=False)
        if df.empty:
            print(f"  WARNING: no data for {sym}", file=sys.stderr)
            continue
        df = df.reset_index()
        # yfinance may return a MultiIndex column frame for single tickers.
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        out = pd.DataFrame({
            "ticker": sym,
            "date": pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d"),
            "open": df["Open"], "high": df["High"], "low": df["Low"],
            "close": df["Close"], "adj_close": df["Adj Close"],
            "volume": df["Volume"],
        })
        frames.append(out)
        print(f"  {sym}: {len(out)} rows")
    if not frames:
        sys.exit("No data pulled for any symbol.")
    return pd.concat(frames, ignore_index=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", default="2018-01-01")
    ap.add_argument("--end", default=_dt.date.today().strftime("%Y-%m-%d"))
    ap.add_argument("--snapshot-date", default=_dt.date.today().strftime("%Y-%m-%d"))
    args = ap.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / f"prices_{args.snapshot_date}.parquet"
    if out_path.exists():
        sys.exit(f"Snapshot already exists (immutable): {out_path}\n"
                 "Pass a new --snapshot-date to re-pull.")

    print(f"Pulling {len(ALL_SYMBOLS)} symbols {args.start} -> {args.end} ...")
    df = pull(ALL_SYMBOLS, args.start, args.end)
    df.to_parquet(out_path, index=False)
    print(f"\nSaved immutable snapshot: {out_path}  ({len(df)} rows)")


if __name__ == "__main__":
    main()

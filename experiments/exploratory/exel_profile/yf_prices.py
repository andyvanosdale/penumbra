#!/usr/bin/env python3
"""Daily OHLCV from yfinance for a list of tickers, in resumable batches.

    python yf_prices.py --tickers ticker_cik.csv --out px_hist --start 2009-01-01 --end 2022-01-05
    python yf_prices.py --tickers ticker_cik.csv --out px      --start 2022-01-01 --end 2026-10-18

The ticker file needs a `symbol` column; with --mapped-only, rows whose `cik` is empty are
skipped. Each batch is written to <out>/batch_NNNN.pkl (a pandas DataFrame with date, open,
high, low, close, adj_close, volume, ticker); an existing batch file is not re-fetched.

Known limits: yfinance carries current listings only (survivorship), its `Close` is split-
adjusted, and `fc.yahoo.com` (the crumb host) may be unreachable; the chart endpoint works
without a crumb.
"""
from __future__ import annotations
import argparse, logging, os, time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd, yfinance as yf

logging.getLogger("yfinance").setLevel(logging.CRITICAL)


def fetch(b, start, end):
    df = yf.download(b, start=start, end=end, auto_adjust=False, actions=False, progress=False, threads=False, group_by="ticker", timeout=30)
    frames = []
    if df is None or df.empty: return pd.DataFrame()
    if not isinstance(df.columns, pd.MultiIndex): df.columns = pd.MultiIndex.from_product([[b[0]], df.columns])
    for t in b:
        if t not in df.columns.get_level_values(0): continue
        sub = df[t].dropna(how="all")
        if sub.empty: continue
        sub = sub.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Adj Close": "adj_close", "Volume": "volume"})[["open", "high", "low", "close", "adj_close", "volume"]].copy()
        sub.index = pd.to_datetime(sub.index).tz_localize(None); sub.index.name = "date"; sub["ticker"] = t; frames.append(sub.reset_index())
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--tickers", required=True); ap.add_argument("--out", required=True); ap.add_argument("--start", required=True); ap.add_argument("--end", required=True)
    ap.add_argument("--batch", type=int, default=20); ap.add_argument("--workers", type=int, default=4); ap.add_argument("--mapped-only", action="store_true")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    lst = pd.read_csv(a.tickers, keep_default_na=False)
    if a.mapped_only and "cik" in lst: lst = lst[lst["cik"].astype(str) != ""]
    tickers = lst["symbol"].tolist(); batches = [tickers[i:i + a.batch] for i in range(0, len(tickers), a.batch)]

    def work(i, b):
        out = os.path.join(a.out, f"batch_{i:04d}.pkl")
        if os.path.exists(out): return i, "cached"
        err = ""
        for attempt in range(4):
            try:
                df = fetch(b, a.start, a.end); got = set(df["ticker"]) if not df.empty else set(); miss = [t for t in b if t not in got]
                if miss:
                    d2 = fetch(miss, a.start, a.end)
                    if not d2.empty: df = pd.concat([df, d2], ignore_index=True); miss = [t for t in b if t not in set(df["ticker"])]
                (df if not df.empty else pd.DataFrame(columns=["date", "ticker"])).to_pickle(out)
                return i, f"ok miss={len(miss)}"
            except Exception as e:
                err = repr(e)[:100]; time.sleep(2 * 2 ** attempt)
        return i, f"FAIL {err}"

    t0 = time.time(); done = 0
    with ThreadPoolExecutor(a.workers) as ex:
        futs = [ex.submit(work, i, b) for i, b in enumerate(batches)]
        for f in as_completed(futs):
            i, msg = f.result(); done += 1
            if done % 10 == 0 or "FAIL" in msg: print(f"{done}/{len(batches)} batch {i} {msg} {time.time() - t0:.0f}s", flush=True)
    print("DONE", len(batches), "batches", f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()

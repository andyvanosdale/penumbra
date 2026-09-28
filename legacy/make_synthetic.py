"""Generate a SYNTHETIC OHLCV snapshot so the harness runs fully offline.

███ THIS IS NOT REAL MARKET DATA ███
It exists only to exercise the harness end-to-end when yfinance/network are
unavailable (e.g. in a sandbox). For real results, use ingest/pull_prices.py.

Design (so the negative-control null is honest):
  * Each sector ETF follows a geometric random walk (small daily drift + vol).
  * Each ticker return = beta * sector_return + idiosyncratic noise.
  * Day-of-week has ZERO effect on returns. The dummy "is it Monday" feature is
    therefore genuinely uninformative, and the harness MUST report no edge. If it
    finds an edge here, there is a bug.

The snapshot is written with a SYNTH_ prefix so it can never be confused with a
real pull, and tagged with the generation date.
"""

from __future__ import annotations

import argparse
import datetime as _dt

import numpy as np
import pandas as pd

from config.env import legacy_data_root
from legacy.universe import TICKER_TO_ETF, ETFS


def _business_days(start: str, end: str) -> pd.DatetimeIndex:
    return pd.bdate_range(start=start, end=end)


def generate(start: str, end: str, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    days = _business_days(start, end)
    n = len(days)
    frames = []

    # --- sector ETF paths -------------------------------------------------
    etf_returns = {}
    for etf in ETFS:
        mu = rng.uniform(0.0001, 0.0004)         # small positive daily drift
        vol = rng.uniform(0.008, 0.014)          # daily vol
        r = rng.normal(mu, vol, n)
        etf_returns[etf] = r
        frames.append(_ohlcv_from_returns(etf, days, r, rng, base=80.0))

    # --- ticker paths: beta * sector + idiosyncratic ---------------------
    for tkr, etf in TICKER_TO_ETF.items():
        beta = rng.uniform(0.7, 1.3)
        idio_vol = rng.uniform(0.010, 0.022)
        idio = rng.normal(0.0, idio_vol, n)
        r = beta * etf_returns[etf] + idio       # NO day-of-week term, by design
        frames.append(_ohlcv_from_returns(tkr, days, r, rng,
                                          base=rng.uniform(40, 300)))

    return pd.concat(frames, ignore_index=True)


def _ohlcv_from_returns(symbol, days, daily_returns, rng, base) -> pd.DataFrame:
    close = base * np.cumprod(1.0 + daily_returns)
    prev = np.concatenate([[base], close[:-1]])
    # Construct a plausible OHLC envelope around the close.
    intraday = np.abs(rng.normal(0, 0.004, len(close)))
    open_ = prev * (1 + rng.normal(0, 0.002, len(close)))
    high = np.maximum(open_, close) * (1 + intraday)
    low = np.minimum(open_, close) * (1 - intraday)
    volume = rng.integers(1_000_000, 30_000_000, len(close)).astype(float)
    return pd.DataFrame({
        "ticker": symbol,
        "date": days.strftime("%Y-%m-%d"),
        "open": open_, "high": high, "low": low,
        "close": close, "adj_close": close,   # synthetic = already adjusted
        "volume": volume,
    })


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", default="2018-01-01")
    ap.add_argument("--end", default="2022-12-31")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    raw_dir = legacy_data_root() / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    stamp = _dt.date.today().strftime("%Y-%m-%d")
    out = raw_dir / f"SYNTH_prices_{stamp}.csv"
    df = generate(args.start, args.end, seed=args.seed)
    df.to_csv(out, index=False)
    print(f"Wrote SYNTHETIC snapshot: {out}")
    print(f"  symbols: {df['ticker'].nunique()}, rows: {len(df)}, "
          f"dates: {df['date'].min()} -> {df['date'].max()}")
    print("  NOTE: synthetic data — for plumbing only, not real results.")


if __name__ == "__main__":
    main()

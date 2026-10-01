"""Synthetic bars for the screen tests: random walks with jumps, in the yfinance and Binance shapes."""
from __future__ import annotations

import numpy as np
import pandas as pd


def equity_bars(n_tickers: int = 12, n_sessions: int = 420, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2019-01-02", periods=n_sessions)
    frames = []
    for j in range(n_tickers):
        r = rng.normal(0, 0.03, n_sessions)
        jumps = rng.random(n_sessions) < 0.05
        r[jumps] += rng.choice([-1, 1], jumps.sum()) * rng.uniform(0.08, 0.25, jumps.sum())
        close = 20 * np.exp(np.cumsum(r))
        open_ = close * np.exp(rng.normal(0, 0.01, n_sessions))
        high = np.maximum(open_, close) * np.exp(np.abs(rng.normal(0, 0.01, n_sessions)))
        low = np.minimum(open_, close) * np.exp(-np.abs(rng.normal(0, 0.01, n_sessions)))
        vol = rng.lognormal(12, 0.6, n_sessions)
        vol[rng.random(n_sessions) < 0.05] *= 4
        frames.append(pd.DataFrame({"date": dates, "ticker": f"T{j:02d}", "open": open_, "high": high, "low": low,
                                    "close": close, "adj_close": close * 0.97, "volume": vol}))
    return pd.concat(frames, ignore_index=True)


def crypto_klines(n_symbols: int = 15, n_days: int = 420, seed: int = 1) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    days = pd.date_range("2019-01-01", periods=n_days, freq="D")
    d1, h1 = [], []
    for j in range(n_symbols):
        r = rng.normal(0, 0.04, n_days)
        close = 10 * np.exp(np.cumsum(r))
        open_ = np.concatenate([[close[0]], close[:-1]])
        high = np.maximum(open_, close) * 1.01
        low = np.minimum(open_, close) * 0.99
        qv = rng.lognormal(16 - j * 0.2, 0.5, n_days)
        sym = f"C{j:02d}USDT"
        d1.append(pd.DataFrame({"open_time": days, "symbol": sym, "open": open_, "high": high, "low": low, "close": close,
                                "volume": qv / close, "quote_volume": qv}))
        h1.append(pd.DataFrame({"open_time": days + pd.Timedelta(hours=1), "open": open_ * np.exp(rng.normal(0, 0.003, n_days)), "symbol": sym}))
    return pd.concat(d1, ignore_index=True), pd.concat(h1, ignore_index=True)


def perturb_after(bars: pd.DataFrame, cutoff: pd.Timestamp, seed: int = 7, date_col: str = "date") -> pd.DataFrame:
    """Multiply every price and volume on bars dated after `cutoff` by random factors."""
    rng = np.random.default_rng(seed)
    out = bars.copy()
    m = out[date_col] > cutoff
    for c in ("open", "high", "low", "close", "adj_close", "volume", "quote_volume"):
        if c in out:
            out.loc[m, c] = out.loc[m, c] * rng.uniform(0.5, 1.8, m.sum())
    return out

#!/usr/bin/env python3
"""Free-data screen of the Penumbra v1 mean-reversion rule (issue #15).

Standalone: pandas, numpy, yfinance, requests. Nothing here depends on harness/.

Stages (run in order; each caches under data/raw/ and is idempotent):

    python experiments/screen_free_data.py universe   # Nasdaq Trader -> common-stock list
    python experiments/screen_free_data.py prices     # yfinance daily OHLCV, 2015-01-01..2023-12-31
    python experiments/screen_free_data.py caps       # yfinance current market cap per ticker
    python experiments/screen_free_data.py crypto     # Binance public bucket 1d (+1h) klines
    python experiments/screen_free_data.py run        # the screen; writes data/processed/

Rule, universe and costs follow penumbra-specs spec/01, 04, 05, 06 at b1616412 and the
pre-registration in research_log/2026-09-28-free-data-screen.md. No parameter here is fitted.
"""
from __future__ import annotations

import argparse
import io
import json
import logging
import math
import os
import re
import sys
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
UNI = RAW / "universe"
YF = RAW / "yf"
BIN = RAW / "binance"
for d in (UNI, YF, BIN, PROC):
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- locked parameters (spec)
K_SHOCK = 2.0                # candidate when shock <= -K_SHOCK
TIME_STOP_SESSIONS = 10      # exit at the open after the 10th session following the fill
STOP_RANGE_MULT = 1.5        # stop = fill - 1.5 * signal-day (high - low)
ORDER_USD = 10_000.0
EQ_CAP_USD = 2_000_000_000.0
EQ_DV_FLOOR = 500_000.0      # median daily dollar volume over D-20..D-1
EQ_VOL_FLOOR = 0.40          # 20-day annualized realized vol
EQ_PRICE_FLOOR = 2.0         # unadjusted close on D
EQ_HISTORY = 250             # full 250-session history required
EQ_ANN = 252
CR_TOP_N = 100
CR_VOL_FLOOR = 0.20
CR_HISTORY = 30
CR_ANN = 365
EQ_START, EQ_END = "2015-01-01", "2023-12-31"   # holdout 2024-01-01 onward is never downloaded
CR_START, CR_END = "2018-01-01", "2022-12-31"   # crypto dev era only
FWD_H = 5
COST_LEVELS_BPS = [0, 50, 100]                  # round trip, plus the spec model ("spec")
EQ_SPREAD_FLOOR = 0.0025
EQ_TICK = 0.01
CR_TAKER = 0.0010
CR_SPREAD_FLOOR_TOP20 = 0.0005
CR_SPREAD_FLOOR_OTHER = 0.0015

# crypto exclusion list (spec/01): stablecoins / fiat-pegged, leveraged, wrapped or staked
CR_STABLE = {"USDC", "BUSD", "TUSD", "USDP", "DAI", "FDUSD", "PAX", "USDS", "USDSB", "SUSD",
             "GUSD", "UST", "USTC", "EUR", "GBP", "AUD", "BRL", "RUB", "TRY", "UAH", "BIDR",
             "IDRT", "NGN", "VAI", "USDN", "AEUR", "EURI", "XUSD", "PYUSD", "USD1", "USDE", "FDUSD"}
CR_WRAPPED = {"WBTC", "BETH", "WETH", "WBETH", "WNXM", "STETH", "RETH", "CBETH", "WSOL", "TBTC", "BTCB",
              "SOLV", "SBTC", "WSTETH", "BNBX", "LDO_ST"}
CR_LEV_RE = re.compile(r"(UP|DOWN|BULL|BEAR)$")

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) penumbra-screen/0.1"}
log = logging.getLogger("screen")


def _http(url: str, tries: int = 4, timeout: int = 60, **kw) -> requests.Response:
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=timeout, **kw)
            if r.status_code == 200:
                return r
            last = RuntimeError(f"HTTP {r.status_code} for {url}")
            if r.status_code == 404:
                raise last
        except requests.RequestException as e:  # noqa: PERF203
            last = e
        time.sleep(2 * (i + 1))
    raise last  # type: ignore[misc]


# ================================================================ stage: universe
COMMON_RE = re.compile(r"common stock|common shares|ordinary shares|class [a-c] (common|ordinary|shares)", re.I)
EXCL_RE = re.compile(
    r"warrant|\bright|\bunit|preferred|preference|depositary|\bads\b|\badr\b|\bnote|debenture|"
    r"\bbond|trust preferred|\bfund\b|\betf\b|\betn\b|closed.end|capital securities|"
    r"subordinated|senior|convertible|when.issued|contingent value|tracking stock|\bspac\b|"
    r"acquisition corp|acquisition co\b|acquisition holdings|acquisition ltd|acquisition inc|"
    r"acquisition corporation|acquisitions corp|blank check|\blp\b|limited partnership|\bl\.p\.",
    re.I,
)


def stage_universe() -> pd.DataFrame:
    nq = pd.read_csv(UNI / "nasdaqlisted.txt", sep="|", dtype=str).iloc[:-1]
    ot = pd.read_csv(UNI / "otherlisted.txt", sep="|", dtype=str).iloc[:-1]
    steps = {"nasdaqlisted_rows": len(nq), "otherlisted_rows": len(ot)}
    nq = nq[(nq["Test Issue"] == "N") & (nq["ETF"] == "N")]
    nq = nq[~nq["Symbol"].str.contains(r"[\$\.\^]", regex=True, na=False)]
    nq = nq.assign(exchange="NASDAQ", symbol=nq["Symbol"].str.strip(), name=nq["Security Name"].str.strip())
    ot = ot[(ot["Test Issue"] == "N") & (ot["ETF"] == "N") & ot["Exchange"].isin(["N", "A", "P", "Z"])]
    ot = ot[~ot["ACT Symbol"].str.contains(r"[\$\^]", regex=True, na=False)]
    ot = ot.assign(exchange=ot["Exchange"].map({"N": "NYSE", "A": "NYSEMKT", "P": "NYSEARCA", "Z": "BATS"}),
                   symbol=ot["ACT Symbol"].str.strip().str.replace(".", "-", regex=False),
                   name=ot["Security Name"].str.strip())
    df = pd.concat([nq[["symbol", "name", "exchange"]], ot[["symbol", "name", "exchange"]]], ignore_index=True)
    steps["after_exchange_etf_test_filters"] = len(df)
    df = df[df["name"].str.contains(COMMON_RE, regex=True, na=False)]
    steps["after_common_stock_match"] = len(df)
    df = df[~df["name"].str.contains(EXCL_RE, regex=True, na=False)]
    steps["after_exclusions"] = len(df)
    df = df.drop_duplicates("symbol").sort_values("symbol").reset_index(drop=True)
    steps["unique_symbols"] = len(df)
    df.to_csv(UNI / "common_stock_list.csv", index=False)
    (UNI / "universe_build_steps.json").write_text(json.dumps(steps, indent=2))
    log.info("universe list: %s", steps)
    return df


# ================================================================ stage: prices (yfinance)
def _yf_batch(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    import yfinance as yf
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)
    df = yf.download(tickers, start=start, end=end, auto_adjust=False, actions=False, progress=False,
                     threads=False, group_by="ticker", timeout=60)
    frames = []
    if df is None or df.empty:
        return pd.DataFrame()
    if not isinstance(df.columns, pd.MultiIndex):
        df.columns = pd.MultiIndex.from_product([[tickers[0]], df.columns])
    for t in tickers:
        if t not in df.columns.get_level_values(0):
            continue
        sub = df[t].dropna(how="all")
        if sub.empty:
            continue
        sub = sub.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close",
                                  "Adj Close": "adj_close", "Volume": "volume"})
        sub = sub[["open", "high", "low", "close", "adj_close", "volume"]].copy()
        sub.index = pd.to_datetime(sub.index).tz_localize(None)
        sub.index.name = "date"
        sub["ticker"] = t
        frames.append(sub.reset_index())
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def stage_prices(batch_size: int = 60, workers: int = 4) -> None:
    lst = pd.read_csv(UNI / "common_stock_list.csv")
    tickers = lst["symbol"].tolist()
    batches = [tickers[i:i + batch_size] for i in range(0, len(tickers), batch_size)]
    end_excl = (pd.Timestamp(EQ_END) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    failed: dict[str, str] = {}
    todo = [(i, b) for i, b in enumerate(batches) if not (YF / f"batch_{i:04d}.parquet").exists()]
    log.info("prices: %d tickers, %d batches, %d to fetch", len(tickers), len(batches), len(todo))

    def work(i, b):
        for attempt in range(3):
            try:
                df = _yf_batch(b, EQ_START, end_excl)
                got = set(df["ticker"].unique()) if not df.empty else set()
                miss = [t for t in b if t not in got]
                if miss:  # one retry of the misses, singly, to separate delisted from transient
                    df2 = _yf_batch(miss, EQ_START, end_excl)
                    if not df2.empty:
                        df = pd.concat([df, df2], ignore_index=True)
                        got |= set(df2["ticker"].unique())
                        miss = [t for t in b if t not in got]
                (df if not df.empty else pd.DataFrame(columns=["date", "ticker"])).to_parquet(YF / f"batch_{i:04d}.parquet", index=False)
                return i, miss, None
            except Exception as e:  # noqa: BLE001
                err = repr(e)[:200]
                time.sleep(5 * (attempt + 1))
        return i, b, err

    t0 = time.time()
    with ThreadPoolExecutor(workers) as ex:
        futs = [ex.submit(work, i, b) for i, b in todo]
        for n, f in enumerate(as_completed(futs), 1):
            i, miss, err = f.result()
            for t in miss:
                failed[t] = err or "no data returned"
            if n % 10 == 0:
                log.info("prices: %d/%d batches, %.0fs, %d tickers without data so far", n, len(todo), time.time() - t0, len(failed))
    prev = json.loads((YF / "failed_tickers.json").read_text()) if (YF / "failed_tickers.json").exists() else {}
    prev.update(failed)
    (YF / "failed_tickers.json").write_text(json.dumps(prev, indent=1, sort_keys=True))
    log.info("prices done: %.0fs; %d tickers without data", time.time() - t0, len(prev))


def stage_caps(workers: int = 8) -> None:
    import yfinance as yf
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)
    lst = pd.read_csv(UNI / "common_stock_list.csv")
    out_path = UNI / "market_caps.csv"
    done = pd.read_csv(out_path) if out_path.exists() else pd.DataFrame(columns=["symbol", "market_cap", "shares", "last_price", "error", "source"])
    scr = UNI / "nasdaq_screener_stocks.json"
    if scr.exists() and "screener" not in set(done.get("source", pd.Series(dtype=str))):
        # Nasdaq screener export (api.nasdaq.com/api/screener/stocks?download=true), supplied by the
        # owner on 2026-09-28. Primary cap source; 0.00 means the screener has no cap for the name.
        rows = json.loads(scr.read_text())["data"]["rows"]
        sc = pd.DataFrame(rows)
        sc["symbol"] = sc["symbol"].str.strip().str.replace("/", "-", regex=False).str.replace("^", "-", regex=False)
        sc["market_cap"] = pd.to_numeric(sc["marketCap"], errors="coerce")
        sc["last_price"] = pd.to_numeric(sc["lastsale"].str.replace("[$,]", "", regex=True), errors="coerce")
        sc = sc[sc["market_cap"] > 0][["symbol", "market_cap", "last_price"]].drop_duplicates("symbol")
        sc["shares"], sc["error"], sc["source"] = np.nan, "", "screener"
        done = pd.concat([sc[sc["symbol"].isin(lst["symbol"])], done], ignore_index=True).drop_duplicates("symbol")
        done.to_csv(out_path, index=False)
        log.info("caps: %d symbols from the Nasdaq screener", (done["source"] == "screener").sum())
    todo = [s for s in lst["symbol"] if s not in set(done["symbol"])]
    log.info("caps: %d tickers to fetch", len(todo))

    def one(s):
        for attempt in range(3):
            try:
                fi = yf.Ticker(s).fast_info
                return {"symbol": s, "market_cap": fi["marketCap"], "shares": fi["shares"], "last_price": fi["lastPrice"], "error": "", "source": "yfinance"}
            except Exception as e:  # noqa: BLE001
                err = repr(e)[:120]
                time.sleep(1 + attempt)
        return {"symbol": s, "market_cap": np.nan, "shares": np.nan, "last_price": np.nan, "error": err, "source": "yfinance"}

    rows, t0 = [], time.time()
    with ThreadPoolExecutor(workers) as ex:
        for n, r in enumerate(ex.map(one, todo), 1):
            rows.append(r)
            if n % 250 == 0:
                pd.concat([done, pd.DataFrame(rows)]).to_csv(out_path, index=False)
                log.info("caps: %d/%d, %.0fs", n, len(todo), time.time() - t0)
    pd.concat([done, pd.DataFrame(rows)]).to_csv(out_path, index=False)
    log.info("caps done: %.0fs", time.time() - t0)


# ================================================================ stage: crypto (Binance bucket)
S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
BV = "https://data.binance.vision"


def _s3_list(prefix: str) -> list[str]:
    out, marker = [], None
    while True:
        url = f"{S3}?delimiter=/&prefix={prefix}&max-keys=1000" + (f"&marker={marker}" if marker else "")
        xml = _http(url).text
        out += re.findall(r"<Prefix>([^<]+)</Prefix>", xml)[1:]  # first <Prefix> echoes the query
        m = re.search(r"<NextMarker>([^<]+)</NextMarker>", xml)
        if not m:
            break
        marker = m.group(1)
    return out


def _kline_zip(symbol: str, interval: str, ym: str) -> pd.DataFrame | None:
    p = BIN / interval / f"{symbol}-{interval}-{ym}.zip"
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        url = f"{BV}/data/spot/monthly/klines/{symbol}/{interval}/{symbol}-{interval}-{ym}.zip"
        try:
            r = _http(url, tries=3)
        except Exception as e:  # noqa: BLE001
            if "404" in repr(e):
                p.with_suffix(".missing").touch()
                return None
            raise
        p.write_bytes(r.content)
    if p.with_suffix(".missing").exists() and not p.exists():
        return None
    with zipfile.ZipFile(p) as z:
        raw = z.read(z.namelist()[0])
    df = pd.read_csv(io.BytesIO(raw), header=None)
    if isinstance(df.iloc[0, 0], str):  # newer files carry a header row
        df = df.iloc[1:].astype(float)
    df = df.iloc[:, :11]
    df.columns = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume", "trades", "tb_base", "tb_quote"]
    ot = df["open_time"].astype("int64")
    ot = np.where(ot > 10**14, ot // 1000, ot)  # microsecond timestamps in 2025+ files
    df["open_time"] = pd.to_datetime(ot, unit="ms")
    df["symbol"] = symbol
    return df


def stage_crypto(workers: int = 8, need_1h: bool = True) -> None:
    syms_path = BIN / "usdt_symbols.json"
    if syms_path.exists():
        syms = json.loads(syms_path.read_text())
    else:
        prefixes = _s3_list("data/spot/monthly/klines/")
        syms = sorted({p.split("/")[-2] for p in prefixes if p.split("/")[-2].endswith("USDT")})
        syms_path.write_text(json.dumps(syms))
    log.info("crypto: %d USDT symbols listed in the bucket", len(syms))
    months = pd.period_range(CR_START, CR_END, freq="M").strftime("%Y-%m").tolist()
    # 1d for everything (small); then 1h only for symbols that ever enter the universe.
    t0 = time.time()

    def pull(sym, interval):
        frames = [f for f in (_kline_zip(sym, interval, ym) for ym in months) if f is not None]
        return sym, (pd.concat(frames, ignore_index=True) if frames else None)

    daily_path = BIN / "klines_1d.parquet"
    if not daily_path.exists():
        frames = []
        with ThreadPoolExecutor(workers) as ex:
            for n, (sym, df) in enumerate(ex.map(lambda s: pull(s, "1d"), syms), 1):
                if df is not None:
                    frames.append(df)
                if n % 50 == 0:
                    log.info("crypto 1d: %d/%d symbols, %.0fs", n, len(syms), time.time() - t0)
        d1 = pd.concat(frames, ignore_index=True)
        d1.to_parquet(daily_path, index=False)
    else:
        d1 = pd.read_parquet(daily_path)
    log.info("crypto 1d: %d rows, %d symbols", len(d1), d1["symbol"].nunique())
    if not need_1h:
        return
    # symbols that could enter the top-100 by 30-day quote volume: compute the universe once.
    uni_syms = sorted(crypto_universe_symbols(d1))
    log.info("crypto 1h: %d symbols ever in the universe", len(uni_syms))
    hourly_path = BIN / "klines_1h_0100.parquet"
    if not hourly_path.exists():
        frames = []
        with ThreadPoolExecutor(workers) as ex:
            for n, (sym, df) in enumerate(ex.map(lambda s: pull(s, "1h"), uni_syms), 1):
                if df is not None:
                    df = df[df["open_time"].dt.hour == 1][["open_time", "open", "symbol"]]
                    frames.append(df)
                if n % 25 == 0:
                    log.info("crypto 1h: %d/%d symbols, %.0fs", n, len(uni_syms), time.time() - t0)
        pd.concat(frames, ignore_index=True).to_parquet(hourly_path, index=False)
    log.info("crypto done: %.0fs", time.time() - t0)


def crypto_base(sym: str) -> str:
    return sym[:-4]


def crypto_eligible_base(base: str) -> bool:
    if base in CR_STABLE or base in CR_WRAPPED:
        return False
    if CR_LEV_RE.search(base) and base not in {"JUP", "SYRUP"}:  # real tokens whose names end in UP (listed after the dev era)
        return False
    return True


def crypto_universe_symbols(d1: pd.DataFrame) -> set[str]:
    panel = crypto_panel(d1)
    return set(panel.loc[panel["in_universe"], "symbol"].unique())


# ================================================================ panels
def equity_panel() -> pd.DataFrame:
    """Long panel of daily bars with features and eligibility flags (equities)."""
    parts = [pd.read_parquet(p) for p in sorted(YF.glob("batch_*.parquet"))]
    px = pd.concat([p for p in parts if not p.empty], ignore_index=True)
    px = px.dropna(subset=["close"]).sort_values(["ticker", "date"]).reset_index(drop=True)
    px = px[(px["date"] >= EQ_START) & (px["date"] <= EQ_END)]
    # bars with a zero open/low (yfinance placeholder rows on no-trade days) are treated as missing
    px = px[(px["close"] > 0) & (px["adj_close"] > 0) & (px["open"] > 0) & (px["low"] > 0) & (px["high"] > 0)]
    g = px.groupby("ticker", sort=False)
    f = px["adj_close"] / px["close"]
    px["a_open"], px["a_high"], px["a_low"], px["a_close"] = px["open"] * f, px["high"] * f, px["low"] * f, px["adj_close"]
    px["dollar_vol"] = px["close"] * px["volume"]
    px["ret_1"] = np.log(px["a_close"]) - np.log(g["a_close"].shift(1))
    g = px.groupby("ticker", sort=False)
    px["rvol_20"] = g["ret_1"].rolling(20, min_periods=20).std().reset_index(level=0, drop=True) * math.sqrt(EQ_ANN)
    px["rvol_20_prev"] = g["rvol_20"].shift(1)
    px["shock"] = px["ret_1"] / (px["rvol_20_prev"] / math.sqrt(EQ_ANN))
    px["mean_close_20"] = g["a_close"].rolling(20, min_periods=20).mean().reset_index(level=0, drop=True)
    px["med_dv_20_prev"] = g["dollar_vol"].rolling(20, min_periods=20).median().reset_index(level=0, drop=True)
    px["med_dv_20_prev"] = px.groupby("ticker", sort=False)["med_dv_20_prev"].shift(1)
    # session index per ticker and a full-history check: 250 bars ending D that span exactly
    # 250 NYSE sessions (no gaps), using the union calendar of all tickers.
    cal = pd.Index(sorted(px["date"].unique()))
    px["sidx"] = cal.get_indexer(px["date"])
    px["sidx_lag"] = px["sidx"] - px.groupby("ticker", sort=False)["sidx"].shift(EQ_HISTORY - 1)
    px["full_hist"] = px["sidx_lag"] == (EQ_HISTORY - 1)
    # Abdi-Ranaldo spread estimate over the 20 sessions ending D-1 (spec/06), on adjusted bars
    eta = (np.log(px["a_high"]) + np.log(px["a_low"])) / 2
    c = np.log(px["a_close"])
    eta_prev = eta.groupby(px["ticker"]).shift(1)
    c_prev = c.groupby(px["ticker"]).shift(1)
    s2 = 4 * (c_prev - eta_prev) * (c_prev - eta)          # two-day estimate for the pair (D-1, D)
    s2 = s2.clip(lower=0)
    px["ar_s2"] = s2
    ar_mean = px.groupby("ticker", sort=False)["ar_s2"].rolling(20, min_periods=20).mean().reset_index(level=0, drop=True)
    px["ar_spread"] = np.sqrt(ar_mean)
    px["ar_spread_prev"] = px.groupby("ticker", sort=False)["ar_spread"].shift(1)
    px = px.drop(columns=["ar_s2", "sidx_lag"])
    px["in_universe"] = (px["full_hist"] & (px["med_dv_20_prev"] >= EQ_DV_FLOOR) & (px["rvol_20"] > EQ_VOL_FLOOR)
                         & (px["close"] >= EQ_PRICE_FLOOR) & px["rvol_20_prev"].notna())
    return px.reset_index(drop=True)


def crypto_panel(d1: pd.DataFrame) -> pd.DataFrame:
    px = d1.rename(columns={"open_time": "date"})[["date", "symbol", "open", "high", "low", "close", "quote_volume"]].copy()
    px["date"] = px["date"].dt.normalize()
    px = px[(px["date"] >= CR_START) & (px["date"] <= CR_END)]
    px = px[px["symbol"].map(lambda s: crypto_eligible_base(crypto_base(s)))]
    px = px[(px["close"] > 0) & (px["open"] > 0) & (px["low"] > 0) & (px["high"] > 0)].sort_values(["symbol", "date"]).reset_index(drop=True)
    px["ticker"] = px["symbol"]
    px["a_open"], px["a_high"], px["a_low"], px["a_close"] = px["open"], px["high"], px["low"], px["close"]
    px["dollar_vol"] = px["quote_volume"]
    g = px.groupby("ticker", sort=False)
    px["ret_1"] = np.log(px["a_close"]) - np.log(g["a_close"].shift(1))
    g = px.groupby("ticker", sort=False)
    px["rvol_20"] = g["ret_1"].rolling(20, min_periods=20).std().reset_index(level=0, drop=True) * math.sqrt(CR_ANN)
    px["rvol_30"] = g["ret_1"].rolling(30, min_periods=30).std().reset_index(level=0, drop=True) * math.sqrt(CR_ANN)
    px["rvol_20_prev"] = g["rvol_20"].shift(1)
    px["shock"] = px["ret_1"] / (px["rvol_20_prev"] / math.sqrt(CR_ANN))
    px["mean_close_20"] = g["a_close"].rolling(20, min_periods=20).mean().reset_index(level=0, drop=True)
    px["med_dv_20_prev"] = g["dollar_vol"].rolling(20, min_periods=20).median().reset_index(level=0, drop=True)
    px["med_dv_20_prev"] = px.groupby("ticker", sort=False)["med_dv_20_prev"].shift(1)
    px["qv_30"] = g["dollar_vol"].rolling(30, min_periods=30).sum().reset_index(level=0, drop=True)
    cal = pd.Index(sorted(px["date"].unique()))
    px["sidx"] = cal.get_indexer(px["date"])
    lag = px["sidx"] - px.groupby("ticker", sort=False)["sidx"].shift(CR_HISTORY - 1)
    px["full_hist"] = lag == (CR_HISTORY - 1)
    eta = (np.log(px["a_high"]) + np.log(px["a_low"])) / 2
    c = np.log(px["a_close"])
    eta_prev = eta.groupby(px["ticker"]).shift(1)
    c_prev = c.groupby(px["ticker"]).shift(1)
    px["ar_s2"] = (4 * (c_prev - eta_prev) * (c_prev - eta)).clip(lower=0)
    ar_mean = px.groupby("ticker", sort=False)["ar_s2"].rolling(20, min_periods=20).mean().reset_index(level=0, drop=True)
    px["ar_spread"] = np.sqrt(ar_mean)
    px["ar_spread_prev"] = px.groupby("ticker", sort=False)["ar_spread"].shift(1)
    px = px.drop(columns=["ar_s2"])
    base_ok = px["full_hist"] & px["qv_30"].notna() & (px["rvol_30"] > CR_VOL_FLOOR) & px["rvol_20_prev"].notna()
    px["rank_qv"] = px[base_ok].groupby("date")["qv_30"].rank(ascending=False, method="first")
    px["in_universe"] = base_ok & (px["rank_qv"] <= CR_TOP_N)
    px["top20"] = base_ok & (px["rank_qv"] <= 20)
    return px.reset_index(drop=True)



# ================================================================ the screen
FILLS = ["close", "next_open", "next_close"]
W = 16  # sessions scanned after the fill session (10 managed sessions + gaps + the exit-fill session)


def _wide(px: pd.DataFrame, col: str, cal: pd.Index, tickers: pd.Index) -> np.ndarray:
    return px.pivot(index="date", columns="ticker", values=col).reindex(index=cal, columns=tickers).to_numpy(dtype=float)


def _shift(a: np.ndarray, n: int) -> np.ndarray:
    """a[i+n] aligned at i (rows are sessions); NaN past the end."""
    out = np.full_like(a, np.nan)
    if n > 0:
        out[:-n] = a[n:]
    elif n < 0:
        out[-n:] = a[:n]
    else:
        out[:] = a
    return out


def build_arrays(px: pd.DataFrame, lane: str, o1: pd.DataFrame | None = None) -> dict:
    cal = pd.Index(sorted(px["date"].unique()))
    tickers = pd.Index(sorted(px["ticker"].unique()))
    A = {"cal": cal, "tickers": tickers, "lane": lane}
    for c in ["a_open", "a_high", "a_low", "a_close", "close", "shock", "mean_close_20", "rvol_20", "med_dv_20_prev",
              "ar_spread_prev"]:
        A[c] = _wide(px, c, cal, tickers)
    A["in_universe"] = _wide(px, "in_universe", cal, tickers) == 1.0
    A["top20"] = (_wide(px, "top20", cal, tickers) == 1.0) if "top20" in px else np.zeros_like(A["in_universe"])
    if o1 is not None:  # crypto: open of the 01:00 UTC 1h kline, aligned to the UTC day
        o1 = o1.assign(date=o1["open_time"].dt.normalize(), ticker=o1["symbol"]).rename(columns={"open": "o1"})
        o1 = o1.drop_duplicates(["date", "ticker"])
        A["o1"] = _wide(o1, "o1", cal, tickers)
    return A


def spec_cost(A: dict, si: np.ndarray, tj: np.ndarray) -> np.ndarray:
    """Round-trip cost fraction of notional per spec/06 for a candidate on signal session si, name tj."""
    lane = A["lane"]
    ann = EQ_ANN if lane != "crypto" else CR_ANN
    s = A["ar_spread_prev"][si, tj]
    s = np.where(np.isnan(s), 0.0, s)
    if lane == "crypto":
        floor = np.where(A["top20"][si, tj], CR_SPREAD_FLOOR_TOP20, CR_SPREAD_FLOOR_OTHER)
        fee = 2 * CR_TAKER
    else:
        floor = np.maximum(EQ_SPREAD_FLOOR, EQ_TICK / A["close"][si, tj])
        fee = 0.0
    s = np.maximum(s, floor)
    half = s / 2
    sigma_d = A["rvol_20"][si, tj] / math.sqrt(ann)
    med = A["med_dv_20_prev"][si, tj]
    part_in = ORDER_USD / (0.10 * med)
    part_out = ORDER_USD / med
    slip_in = 0.5 * sigma_d * np.sqrt(part_in)
    slip_out = 0.5 * sigma_d * np.sqrt(part_out)
    return (2 * half + slip_in) + (half + slip_out) + fee


def simulate(A: dict, fill: str, cap_mask: np.ndarray | None) -> pd.DataFrame:
    """Run the rule for one fill convention. Returns one row per candidate (filled or not)."""
    O, H, L, C = A["a_open"], A["a_high"], A["a_low"], A["a_close"]
    if A["lane"] == "crypto" and fill == "next_open" and "o1" in A:
        O = A["o1"]  # the 01:00 UTC open is the executable open for a job that runs after the daily close
    n_sess, n_tk = C.shape
    univ = A["in_universe"] if cap_mask is None else (A["in_universe"] & cap_mask[None, :])
    cand = univ & (A["shock"] <= -K_SHOCK)
    off = 0 if fill == "close" else 1  # fill session offset from the signal session
    si_all, tj_all = np.nonzero(cand)
    order = np.lexsort((tj_all, si_all))
    si_all, tj_all = si_all[order], tj_all[order]
    # no re-entry while held: process by ticker in session order, tracking the exit session of the open trade.
    # First run the exit logic for every candidate as if independent, then filter sequentially.
    F = si_all + off
    ok = F < n_sess
    si, tj, F = si_all[ok], tj_all[ok], F[ok]
    if fill == "close":
        entry = C[si, tj]
    elif fill == "next_open":
        entry = O[F, tj]
    else:
        entry = C[F, tj]
    rng = H[si, tj] - L[si, tj]
    unfilled = np.isnan(entry) | (rng <= 0) | np.isnan(rng)
    stop = entry - STOP_RANGE_MULT * rng
    target = A["mean_close_20"][si, tj]
    n = len(si)
    # windows of the W sessions after the fill session
    idx = F[:, None] + np.arange(1, W + 1)[None, :]
    inb = idx < n_sess
    idxc = np.minimum(idx, n_sess - 1)
    Ow, Hw, Lw, Cw = (X[idxc, tj[:, None]] for X in (O, H, L, C))
    valid = inb & ~np.isnan(Cw) & ~np.isnan(Ow)
    # next valid session index (within the window) for each k
    nxt = np.full((n, W), -1, dtype=int)
    last = np.full(n, -1, dtype=int)
    for k in range(W - 1, -1, -1):
        nxt[:, k] = last
        last = np.where(valid[:, k], k, last)
    exit_k = np.full(n, -1); exit_type = np.full(n, "", dtype=object); exit_px = np.full(n, np.nan)
    cnt = np.zeros(n, dtype=int)
    done = unfilled.copy()
    for k in range(W):
        v = valid[:, k] & ~done
        cnt[v] += 1
        o, l, c = Ow[:, k], Lw[:, k], Cw[:, k]
        st_open = v & (o <= stop)
        st_low = v & ~st_open & (l < stop)
        tg = v & ~st_open & ~st_low & (c >= target)
        tm = v & ~st_open & ~st_low & ~tg & (cnt >= TIME_STOP_SESSIONS)
        exit_k[st_open] = k; exit_type[st_open] = "stop"; exit_px[st_open] = o[st_open]
        exit_k[st_low] = k; exit_type[st_low] = "stop"; exit_px[st_low] = stop[st_low]
        if fill == "close":  # close-fill diagnostic: target fills at the triggering close
            exit_k[tg] = k; exit_type[tg] = "target"; exit_px[tg] = c[tg]
        else:
            nk = nxt[:, k]
            has = tg & (nk >= 0)
            exit_k[has] = nk[has]; exit_type[has] = "target"; exit_px[has] = Ow[has, nk[has]]
            trunc = tg & (nk < 0)
            exit_k[trunc] = k; exit_type[trunc] = "truncated"; exit_px[trunc] = c[trunc]
        nk = nxt[:, k]
        has = tm & (nk >= 0)
        exit_k[has] = nk[has]; exit_type[has] = "time"; exit_px[has] = Ow[has, nk[has]]
        trunc = tm & (nk < 0)
        exit_k[trunc] = k; exit_type[trunc] = "truncated"; exit_px[trunc] = c[trunc]
        done |= st_open | st_low | tg | tm
    # never reached 10 valid sessions inside the window (data end or long halt): close at the last valid close
    open_still = ~done
    if open_still.any():
        lastk = np.where(valid, np.arange(W)[None, :], -1).max(axis=1)
        has = open_still & (lastk >= 0)
        exit_k[has] = lastk[has]; exit_type[has] = "truncated"; exit_px[has] = Cw[has, lastk[has]]
        none = open_still & (lastk < 0)
        unfilled |= none
    filled = ~unfilled
    # no re-entry while held (spec/05 step 4): sequential filter per ticker on signal sessions
    keep = np.ones(n, dtype=bool)
    exit_sess = F + 1 + exit_k
    last_exit = {}
    for i in range(n):
        if not filled[i]:
            continue
        t = tj[i]
        le = last_exit.get(t, -1)
        if si[i] < le:  # held at this signal's close (exit session strictly after the signal session)
            keep[i] = False
            continue
        last_exit[t] = exit_sess[i]
    filled &= keep
    gross = np.where(filled, exit_px / entry - 1.0, np.nan)
    # 5-day forward return from the fill, same price type, and the same-day universe mean of it
    if fill == "close":
        P = C; base_off = 0
    elif fill == "next_open":
        P = O; base_off = 1
    else:
        P = C; base_off = 1
    fwd_all = _shift(P, base_off + FWD_H) / _shift(P, base_off) - 1.0
    um = np.where(univ, fwd_all, np.nan)
    with np.errstate(all="ignore"):
        uni_fwd = np.nanmean(um, axis=1)
        uni_n = np.sum(~np.isnan(um), axis=1)
    fwd5 = fwd_all[si, tj]
    # universe comparator for the realized trade: EW mean over U_D of the return from the same fill
    # (same session and price type) to the exit session at the exit's price type (open, or close for stops)
    exit_is_open = np.isin(exit_type, ["target", "time"]) if fill != "close" else np.isin(exit_type, ["time"])
    bench = np.full(n, np.nan)
    days = np.unique(si[filled])
    fillP = C if fill != "next_open" else O
    for d in days:
        rows = np.nonzero((si == d) & filled)[0]
        u = univ[d]
        if not u.any():
            continue
        p0 = fillP[d + off, u]
        for k in np.unique(exit_k[rows]):
            for is_open in (True, False):
                r = rows[(exit_k[rows] == k) & (exit_is_open[rows] == is_open)]
                if len(r) == 0:
                    continue
                x = d + off + 1 + k
                if x >= n_sess:
                    continue
                px_x = (O if is_open else C)[x, u]
                with np.errstate(all="ignore"):
                    bench[r] = np.nanmean(px_x / p0 - 1.0)
    out = pd.DataFrame({
        "signal_date": A["cal"][si], "ticker": A["tickers"][tj], "fill": fill, "filled": filled,
        "unfilled_reason": np.where(unfilled, np.where(np.isnan(entry), "no_bar", "zero_range"), np.where(keep, "", "held")),
        "entry": entry, "stop": stop, "target": target, "exit_type": exit_type, "exit_px": exit_px,
        "sessions_held": np.where(filled, exit_k + 1, np.nan), "gross": gross, "bench": bench,
        "fwd5": fwd5, "uni_fwd5": uni_fwd[si], "uni_n": uni_n[si], "cost_spec": spec_cost(A, si, tj),
        "cost_tier": (2 * (CR_TAKER + np.where(A["top20"][si, tj], CR_SPREAD_FLOOR_TOP20, CR_SPREAD_FLOOR_OTHER))
                      if A["lane"] == "crypto" else np.full(n, np.nan)),
        "shock": A["shock"][si, tj], "year": pd.DatetimeIndex(A["cal"][si]).year,
    })
    out["exit_date"] = np.where(filled, A["cal"].to_numpy()[np.minimum(exit_sess, n_sess - 1)], np.datetime64("NaT"))
    return out


def _z(daily: pd.Series) -> tuple[float, int]:
    daily = daily.dropna()
    if len(daily) < 2:
        return np.nan, len(daily)
    return float(daily.mean() / (daily.std(ddof=1) / math.sqrt(len(daily)))), int(len(daily))


def summarize(tr: pd.DataFrame, cost_bps: float | str) -> dict:
    per_trade = cost_bps in ("spec", "tier")
    c = tr["cost_" + cost_bps] if per_trade else cost_bps / 1e4
    f = tr[tr["filled"]].copy()
    f["net"] = f["gross"] - (c[tr["filled"]] if per_trade else c)
    f["net_minus_bench"] = f["net"] - f["bench"]
    cand = tr.copy()
    cand["fwd5_net_excess"] = cand["fwd5"] - cand["uni_fwd5"] - c
    z_net, nd_net = _z(f.groupby("signal_date")["net_minus_bench"].mean())
    z_f5, nd_f5 = _z(cand.dropna(subset=["fwd5_net_excess"]).groupby("signal_date")["fwd5_net_excess"].mean())
    return {
        "candidates": int(len(tr)), "filled": int(len(f)),
        "mean_net": float(f["net"].mean()) if len(f) else np.nan, "median_net": float(f["net"].median()) if len(f) else np.nan,
        "mean_gross": float(f["gross"].mean()) if len(f) else np.nan,
        "hit_rate": float((f["net"] > 0).mean()) if len(f) else np.nan,
        "mean_net_minus_bench": float(f["net_minus_bench"].mean()) if len(f) else np.nan,
        "z_net_vs_universe": z_net, "entry_days": nd_net,
        "fwd5_excess": float(cand["fwd5_net_excess"].mean()), "fwd5_n": int(cand["fwd5_net_excess"].notna().sum()),
        "z_fwd5": z_f5, "fwd5_days": nd_f5,
        "mean_cost": float(c.mean()) if per_trade else float(c),
        "share_stop": float((f["exit_type"] == "stop").mean()) if len(f) else np.nan,
        "share_target": float((f["exit_type"] == "target").mean()) if len(f) else np.nan,
        "share_time": float((f["exit_type"] == "time").mean()) if len(f) else np.nan,
        "share_truncated": float((f["exit_type"] == "truncated").mean()) if len(f) else np.nan,
    }


def report(trades: dict[str, pd.DataFrame], market: str, universe: str) -> pd.DataFrame:
    rows = []
    for fill, tr in trades.items():
        for cost in COST_LEVELS_BPS + (["tier", "spec"] if market == "crypto" else ["spec"]):
            for yr, sub in [("all", tr)] + [(str(y), g) for y, g in tr.groupby("year")]:
                rows.append({"market": market, "universe": universe, "fill": fill, "cost": str(cost), "year": yr, **summarize(sub, cost)})
    return pd.DataFrame(rows)


def universe_size_stats(A: dict, cap_mask):
    u = A["in_universe"] if cap_mask is None else (A["in_universe"] & cap_mask[None, :])
    n = u.sum(axis=1)
    return {"median_daily_universe": float(np.median(n)), "p10": float(np.percentile(n, 10)), "p90": float(np.percentile(n, 90)),
            "sessions": int(len(n)), "names_ever": int(u.any(axis=0).sum())}


def headline_markdown(res: pd.DataFrame) -> str:
    """Per market/universe: candidates, trades, next-open net edge per trade at each cost level, close-fill edge, z."""
    lines = []
    fmt = lambda x: "n/a" if pd.isna(x) else f"{x * 1e4:+.0f}"
    for (mk, un), g in res[res["year"] == "all"].groupby(["market", "universe"], sort=False):
        costs = [c for c in ["0", "50", "100", "tier", "spec"] if c in set(g["cost"])]
        lines.append(f"\n**{mk} / {un}**\n")
        lines.append("| fill | candidates | trades | " + " | ".join(f"5d excess @{c}" for c in costs) + " | " +
                     " | ".join(f"net/trade @{c}" for c in costs) + " | hit @0 | z 5d @0 | z net @0 | days |")
        lines.append("|" + "---|" * (5 + 2 * len(costs)))
        for fill in FILLS:
            r = {c: g[(g["fill"] == fill) & (g["cost"] == c)].iloc[0] for c in costs}
            r0 = r["0"]
            lines.append(f"| {fill} | {int(r0['candidates'])} | {int(r0['filled'])} | "
                         + " | ".join(fmt(r[c]["fwd5_excess"]) for c in costs) + " | "
                         + " | ".join(fmt(r[c]["mean_net"]) for c in costs)
                         + f" | {r0['hit_rate']:.3f} | {r0['z_fwd5']:+.2f} | {r0['z_net_vs_universe']:+.2f} | {int(r0['entry_days'])} |")
    lines.append("\nAll return figures are basis points per trade. 5d excess = 5-session forward return from the fill minus the same-day universe mean, net of the column's round-trip cost. net/trade = realized rule return net of cost. z's are day-clustered at zero cost.")
    return "\n".join(lines)


def per_year_markdown(res: pd.DataFrame, market: str, universe: str, fill: str = "next_open") -> str:
    g = res[(res["market"] == market) & (res["universe"] == universe) & (res["fill"] == fill) & (res["cost"] == "0")]
    g = g.sort_values("year", key=lambda s: s.replace("all", "9999").astype(int))
    lines = [f"\n**{market} / {universe} / {fill} fill, zero cost, by year**\n",
             "| year | candidates | trades | 5d excess (bps) | net/trade (bps) | median net (bps) | hit | z 5d | z net | days | stop/target/time |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in g.iterrows():
        lines.append(f"| {r['year']} | {int(r['candidates'])} | {int(r['filled'])} | {r['fwd5_excess']*1e4:+.0f} | {r['mean_net']*1e4:+.0f} | {r['median_net']*1e4:+.0f} | {r['hit_rate']:.3f} | {r['z_fwd5']:+.2f} | {r['z_net_vs_universe']:+.2f} | {int(r['entry_days'])} | {r['share_stop']:.2f}/{r['share_target']:.2f}/{r['share_time']:.2f} |")
    return "\n".join(lines)


def stage_run() -> None:
    t0 = time.time()
    meta: dict = {"run_at": pd.Timestamp.utcnow().isoformat(), "spec_commit": "b1616412", "markets": {}}
    all_rows = []
    # ---------------- equities
    px = equity_panel()
    caps = pd.read_csv(UNI / "market_caps.csv")
    A = build_arrays(px, "equity")
    capmap = caps.set_index("symbol")["market_cap"].reindex(A["tickers"])
    small = (capmap < EQ_CAP_USD).to_numpy() & capmap.notna().to_numpy()
    meta["markets"]["equity"] = {
        "tickers_with_prices": int(len(A["tickers"])), "sessions": int(len(A["cal"])),
        "first_session": str(A["cal"][0].date()), "last_session": str(A["cal"][-1].date()),
        "tickers_with_cap": int(capmap.notna().sum()), "tickers_under_cap": int(small.sum()),
        "cap_source_counts": caps["source"].value_counts().to_dict() if "source" in caps else {},
        "universe_smallcap": universe_size_stats(A, small), "universe_uncapped": universe_size_stats(A, None),
    }
    log.info("equity panel: %s", meta["markets"]["equity"])
    for uname, mask in [("smallcap", small), ("uncapped", None)]:
        trades = {}
        for fill in FILLS:
            trades[fill] = simulate(A, fill, mask)
            log.info("equity %s %s: %d candidates, %d filled, %.0fs", uname, fill, len(trades[fill]), trades[fill]["filled"].sum(), time.time() - t0)
        rep = report(trades, "equity", uname)
        all_rows.append(rep)
        pd.concat(trades.values()).to_parquet(RAW / f"trades_equity_{uname}.parquet", index=False)
    del px, A
    # ---------------- crypto
    d1 = pd.read_parquet(BIN / "klines_1d.parquet")
    cpx = crypto_panel(d1)
    o1 = pd.read_parquet(BIN / "klines_1h_0100.parquet") if (BIN / "klines_1h_0100.parquet").exists() else None
    A = build_arrays(cpx, "crypto", o1)
    meta["markets"]["crypto"] = {
        "symbols_after_exclusions": int(len(A["tickers"])), "days": int(len(A["cal"])),
        "first_day": str(A["cal"][0].date()), "last_day": str(A["cal"][-1].date()),
        "next_open_source": "1h kline open at 01:00 UTC on D+1" if o1 is not None else "1d open on D+1 (equals the signal close)",
        "o1_coverage_of_universe_cells": float(np.mean(~np.isnan(A["o1"][A["in_universe"]]))) if o1 is not None else None,
        "universe": universe_size_stats(A, None),
    }
    log.info("crypto panel: %s", meta["markets"]["crypto"])
    trades = {}
    for fill in FILLS:
        trades[fill] = simulate(A, fill, None)
        log.info("crypto %s: %d candidates, %d filled", fill, len(trades[fill]), trades[fill]["filled"].sum())
    all_rows.append(report(trades, "crypto", "top100"))
    pd.concat(trades.values()).to_parquet(RAW / "trades_crypto.parquet", index=False)
    res = pd.concat(all_rows, ignore_index=True)
    res.to_csv(PROC / "screen_free_data_results.csv", index=False)
    meta["runtime_s"] = round(time.time() - t0)
    (PROC / "screen_free_data_meta.json").write_text(json.dumps(meta, indent=2, default=str))
    # headline: next-open, zero cost, all years
    head = res[(res["year"] == "all")].pivot_table(index=["market", "universe", "fill"], columns="cost",
                                                   values=["fwd5_excess", "mean_net", "z_fwd5", "z_net_vs_universe", "filled", "candidates"])
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    print(head.to_string())
    md = "# Free-data screen: headline tables\n" + headline_markdown(res)
    for mk, un in [("equity", "smallcap"), ("equity", "uncapped"), ("crypto", "top100")]:
        md += "\n" + per_year_markdown(res, mk, un)
        md += "\n" + per_year_markdown(res, mk, un, "close")
    (PROC / "screen_free_data_tables.md").write_text(md)
    log.info("run done in %.0fs", time.time() - t0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["universe", "prices", "caps", "crypto", "run"])
    ap.add_argument("--no-1h", action="store_true")
    a = ap.parse_args()
    if a.stage == "universe":
        stage_universe()
    elif a.stage == "prices":
        stage_prices()
    elif a.stage == "caps":
        stage_caps()
    elif a.stage == "crypto":
        stage_crypto(need_1h=not a.no_1h)
    elif a.stage == "run":
        stage_run()

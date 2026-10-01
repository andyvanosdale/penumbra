"""Data layer of the screening engine: pulls, feature panels, as-of arrays, cache.

Everything lives under `$PENUMBRA_DATA_ROOT/screen/` (a local root; docs/environment.md):

    raw/universe/   Nasdaq Trader lists, the common-stock list, market caps
    raw/yf/         yfinance daily bars, one parquet per batch of tickers
    raw/binance/    monthly kline zips, klines_1d.parquet, klines_1h_0100.parquet
    cache/          feature panels (parquet), keyed by window and code version
    processed/      run outputs

The pull windows are the pre-registered ones (research_log/2026-10-01-wave-1-screen.md):
equities 2009-01-01 -> 2023-12-31, crypto 2018-01-01 -> 2024-12-31. The holdout eras
(equities 2024-01-01 onward, crypto 2025-01-01 onward) are never downloaded: the pull
functions refuse an end date at or past the holdout start.

The stage code is the v1 script's, with the windows made parameters. The panels add the
wave-1 features (zscore_20, vol_pctl_250, vol_ratio_20, trailing returns, 250-day high)
without changing any v1 column, so the v1 rule reproduces through them (the regression
in `engine.py`).
"""
from __future__ import annotations

import io
import json
import logging
import math
import os
import re
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import requests

log = logging.getLogger("screen.data")

PANEL_VERSION = "wave1-1"  # bump when a panel column definition changes; invalidates the cache

# ---------------------------------------------------------------- windows and holdout
EQ_PULL_START, EQ_PULL_END = "2009-01-01", "2023-12-31"
CR_PULL_START, CR_PULL_END = "2018-01-01", "2024-12-31"
HOLDOUT_START = {"equity": "2024-01-01", "crypto": "2025-01-01"}

# ---------------------------------------------------------------- locked universe parameters (spec/01, v1)
EQ_CAP_USD = 2_000_000_000.0
EQ_DV_FLOOR = 500_000.0      # median daily dollar volume over D-20..D-1
EQ_VOL_FLOOR = 0.40          # 20-day annualized realized vol
EQ_PRICE_FLOOR = 2.0         # close on D
EQ_HISTORY = 250             # full 250-session history required
EQ_ANN = 252
CR_TOP_N = 100
CR_VOL_FLOOR = 0.20
CR_HISTORY = 30
CR_ANN = 365

CR_STABLE = {"USDC", "BUSD", "TUSD", "USDP", "DAI", "FDUSD", "PAX", "USDS", "USDSB", "SUSD",
             "GUSD", "UST", "USTC", "EUR", "GBP", "AUD", "BRL", "RUB", "TRY", "UAH", "BIDR",
             "IDRT", "NGN", "VAI", "USDN", "AEUR", "EURI", "XUSD", "PYUSD", "USD1", "USDE", "FDUSD"}
CR_WRAPPED = {"WBTC", "BETH", "WETH", "WBETH", "WNXM", "STETH", "RETH", "CBETH", "WSOL", "TBTC", "BTCB",
              "SOLV", "SBTC", "WSTETH", "BNBX", "LDO_ST"}
CR_LEV_RE = re.compile(r"(UP|DOWN|BULL|BEAR)$")

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) penumbra-screen/0.2"}


# ---------------------------------------------------------------- roots
@dataclass(frozen=True)
class Roots:
    raw: Path
    uni: Path
    yf: Path
    binance: Path
    cache: Path
    processed: Path


def roots(create: bool = True) -> Roots:
    from config.env import data_root, is_local_root
    root = data_root()
    if not is_local_root(root):
        raise SystemExit("the screen needs a local PENUMBRA_DATA_ROOT")
    base = Path(root) / "screen"
    r = Roots(base / "raw", base / "raw" / "universe", base / "raw" / "yf", base / "raw" / "binance",
              base / "cache", base / "processed")
    if create:
        for d in (r.uni, r.yf, r.binance, r.cache, r.processed):
            d.mkdir(parents=True, exist_ok=True)
    return r


def check_not_holdout(market: str, end: str) -> None:
    if pd.Timestamp(end) >= pd.Timestamp(HOLDOUT_START[market]):
        raise ValueError(f"{market} pull end {end} reaches the holdout ({HOLDOUT_START[market]} onward); refused")


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


# ================================================================ stage: universe list
NASDAQ_TRADER = "https://www.nasdaqtrader.com/dynamic/SymDir/"
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
    """Nasdaq Trader directory -> common-stock list (v1 filters, unchanged)."""
    R = roots()
    for name in ("nasdaqlisted.txt", "otherlisted.txt"):
        p = R.uni / name
        if not p.exists():
            p.write_bytes(_http(NASDAQ_TRADER + name).content)
    nq = pd.read_csv(R.uni / "nasdaqlisted.txt", sep="|", dtype=str, keep_default_na=False).iloc[:-1]
    ot = pd.read_csv(R.uni / "otherlisted.txt", sep="|", dtype=str, keep_default_na=False).iloc[:-1]
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
    df.to_csv(R.uni / "common_stock_list.csv", index=False)
    (R.uni / "universe_build_steps.json").write_text(json.dumps(steps, indent=2))
    log.info("universe list: %s", steps)
    return df


def common_stock_list() -> pd.DataFrame:
    return pd.read_csv(roots().uni / "common_stock_list.csv", keep_default_na=False)


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


def stage_prices(start: str = EQ_PULL_START, end: str = EQ_PULL_END, batch_size: int = 60, workers: int = 4) -> None:
    check_not_holdout("equity", end)
    R = roots()
    tickers = common_stock_list()["symbol"].tolist()
    batches = [tickers[i:i + batch_size] for i in range(0, len(tickers), batch_size)]
    end_excl = (pd.Timestamp(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    failed: dict[str, str] = {}
    todo = [(i, b) for i, b in enumerate(batches) if not (R.yf / f"batch_{i:04d}.parquet").exists()]
    log.info("prices: %d tickers, %d batches, %d to fetch, %s..%s", len(tickers), len(batches), len(todo), start, end)

    def work(i, b):
        err = None
        for attempt in range(3):
            try:
                df = _yf_batch(b, start, end_excl)
                got = set(df["ticker"].unique()) if not df.empty else set()
                miss = [t for t in b if t not in got]
                if miss:  # one retry of the misses, singly, to separate delisted from transient
                    df2 = _yf_batch(miss, start, end_excl)
                    if not df2.empty:
                        df = pd.concat([df, df2], ignore_index=True)
                        got |= set(df2["ticker"].unique())
                        miss = [t for t in b if t not in got]
                (df if not df.empty else pd.DataFrame(columns=["date", "ticker"])).to_parquet(R.yf / f"batch_{i:04d}.parquet", index=False)
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
    fp = R.yf / "failed_tickers.json"
    prev = json.loads(fp.read_text()) if fp.exists() else {}
    prev.update(failed)
    fp.write_text(json.dumps({str(k): v for k, v in prev.items()}, indent=1, sort_keys=True))
    (R.yf / "pull_window.json").write_text(json.dumps({"start": start, "end": end}))
    log.info("prices done: %.0fs; %d tickers without data", time.time() - t0, len(prev))


SCREENER_URL = "https://api.nasdaq.com/api/screener/stocks?download=true"


def stage_caps(workers: int = 8) -> None:
    """Current market caps: the Nasdaq screener export first, yfinance fast_info for the rest (as v1)."""
    import yfinance as yf
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)
    R = roots()
    lst = common_stock_list()
    out_path = R.uni / "market_caps.csv"
    done = pd.read_csv(out_path) if out_path.exists() else pd.DataFrame(columns=["symbol", "market_cap", "shares", "last_price", "error", "source"])
    scr = R.uni / "nasdaq_screener_stocks.json"
    if not scr.exists():
        try:
            scr.write_bytes(_http(SCREENER_URL, tries=2, timeout=120).content)
            log.info("caps: Nasdaq screener export downloaded")
        except Exception as e:  # noqa: BLE001
            log.warning("caps: Nasdaq screener not reachable (%s); yfinance only", repr(e)[:120])
    if scr.exists() and "screener" not in set(done.get("source", pd.Series(dtype=str))):
        rows = json.loads(scr.read_text())["data"]["rows"]
        sc = pd.DataFrame(rows)
        sc["symbol"] = sc["symbol"].str.strip().str.replace("/", "-", regex=False).str.replace("^", "-", regex=False)
        sc["market_cap"] = pd.to_numeric(sc["marketCap"], errors="coerce")
        sc["last_price"] = pd.to_numeric(sc["lastsale"].str.replace("[$,]", "", regex=True), errors="coerce")
        sc = sc[sc["market_cap"] > 0][["symbol", "market_cap", "last_price"]].drop_duplicates("symbol")
        sc["shares"], sc["error"], sc["source"] = np.nan, "", "screener"
        done = pd.concat([sc[sc["symbol"].isin(lst["symbol"])], done], ignore_index=True).drop_duplicates("symbol")
        done.to_csv(out_path, index=False)
        log.info("caps: %d symbols from the Nasdaq screener", int((done["source"] == "screener").sum()))
    todo = [s for s in lst["symbol"] if s not in set(done["symbol"])]
    log.info("caps: %d tickers to fetch from yfinance", len(todo))

    def one(s):
        err = ""
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


def market_caps() -> pd.Series:
    caps = pd.read_csv(roots().uni / "market_caps.csv", keep_default_na=False, na_values=[""])
    return caps.drop_duplicates("symbol").set_index("symbol")["market_cap"]


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
    p = roots(create=False).binance / interval / f"{symbol}-{interval}-{ym}.zip"
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.with_suffix(".missing").exists() and not p.exists():
        return None
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


def stage_crypto(start: str = CR_PULL_START, end: str = CR_PULL_END, workers: int = 8, need_1h: bool = True) -> None:
    check_not_holdout("crypto", end)
    R = roots()
    syms_path = R.binance / "usdt_symbols.json"
    if syms_path.exists():
        syms = json.loads(syms_path.read_text())
    else:
        prefixes = _s3_list("data/spot/monthly/klines/")
        syms = sorted({p.split("/")[-2] for p in prefixes if p.split("/")[-2].endswith("USDT")})
        syms_path.write_text(json.dumps(syms))
    log.info("crypto: %d USDT symbols listed in the bucket", len(syms))
    months = pd.period_range(start, end, freq="M").strftime("%Y-%m").tolist()
    t0 = time.time()

    def pull(sym, interval):
        frames = [f for f in (_kline_zip(sym, interval, ym) for ym in months) if f is not None]
        return sym, (pd.concat(frames, ignore_index=True) if frames else None)

    daily_path = R.binance / "klines_1d.parquet"
    if not daily_path.exists():
        frames = []
        with ThreadPoolExecutor(workers) as ex:
            for n, (sym, df) in enumerate(ex.map(lambda s: pull(s, "1d"), syms), 1):
                if df is not None:
                    frames.append(df)
                if n % 50 == 0:
                    log.info("crypto 1d: %d/%d symbols, %.0fs", n, len(syms), time.time() - t0)
        d1 = pd.concat(frames, ignore_index=True)
        d1 = d1[(d1["open_time"] >= start) & (d1["open_time"] <= pd.Timestamp(end) + pd.Timedelta(days=1))]
        d1.to_parquet(daily_path, index=False)
    else:
        d1 = pd.read_parquet(daily_path)
    log.info("crypto 1d: %d rows, %d symbols", len(d1), d1["symbol"].nunique())
    (R.binance / "pull_window.json").write_text(json.dumps({"start": start, "end": end}))
    if not need_1h:
        return
    uni_syms = sorted(crypto_universe_symbols(d1, start, end))
    log.info("crypto 1h: %d symbols ever in the universe", len(uni_syms))
    hourly_path = R.binance / "klines_1h_0100.parquet"
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


def stage_crypto_intraday(hours=(4, 12), start: str = CR_PULL_START, end: str = CR_PULL_END) -> None:
    """Hourly opens at the given UTC hours for the universe symbols, from the 1h zips the main
    pull cached (a zip not on disk is fetched the same way; none is in the holdout)."""
    check_not_holdout("crypto", end)
    R = roots()
    uni_syms = sorted(crypto_universe_symbols(load_crypto_1d(), start, end))
    months = pd.period_range(start, end, freq="M").strftime("%Y-%m").tolist()
    frames = {h: [] for h in hours}
    for n, sym in enumerate(uni_syms, 1):
        for ym in months:
            df = _kline_zip(sym, "1h", ym)
            if df is None:
                continue
            for h in hours:
                frames[h].append(df[df["open_time"].dt.hour == h][["open_time", "open", "symbol"]])
        if n % 50 == 0:
            log.info("crypto intraday opens: %d/%d symbols", n, len(uni_syms))
    for h in hours:
        pd.concat(frames[h], ignore_index=True).to_parquet(R.binance / f"klines_1h_{h:02d}00.parquet", index=False)


def load_crypto_hour_open(hour: int) -> pd.DataFrame | None:
    p = roots().binance / f"klines_1h_{hour:02d}00.parquet"
    return pd.read_parquet(p) if p.exists() else None


def crypto_base(sym: str) -> str:
    return sym[:-4]


def crypto_eligible_base(base: str) -> bool:
    if base in CR_STABLE or base in CR_WRAPPED:
        return False
    if CR_LEV_RE.search(base) and base not in {"JUP", "SYRUP"}:  # real tokens whose names end in UP
        return False
    return True


def crypto_universe_symbols(d1: pd.DataFrame, start: str, end: str) -> set[str]:
    panel = crypto_features(d1, start, end)
    return set(panel.loc[panel["in_universe"], "symbol"].unique())


# ================================================================ raw loaders
def load_equity_bars() -> pd.DataFrame:
    R = roots()
    parts = [pd.read_parquet(p) for p in sorted(R.yf.glob("batch_*.parquet"))]
    return pd.concat([p for p in parts if not p.empty], ignore_index=True)


def load_crypto_1d() -> pd.DataFrame:
    return pd.read_parquet(roots().binance / "klines_1d.parquet")


def load_crypto_o1() -> pd.DataFrame | None:
    p = roots().binance / "klines_1h_0100.parquet"
    return pd.read_parquet(p) if p.exists() else None


# ================================================================ feature panels (long form)
def _roll(g, col: str, n: int, how: str):
    r = getattr(g[col].rolling(n, min_periods=n), how)()
    return r.reset_index(level=0, drop=True)


def equity_features(px: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """Long panel of daily bars with features and eligibility flags (equities).

    The v1 columns are computed exactly as the v1 script did (same order of operations);
    `zscore_20`, `volume`, `med_vol_20_prev` are added for wave 1. Window-based features
    (vol_pctl_250, trailing returns, 250-day high) are added in `build_arrays`.
    """
    px = px.dropna(subset=["close"]).sort_values(["ticker", "date"]).reset_index(drop=True)
    px = px[(px["date"] >= start) & (px["date"] <= end)]
    # bars with a zero open/low (yfinance placeholder rows on no-trade days) are treated as missing
    px = px[(px["close"] > 0) & (px["adj_close"] > 0) & (px["open"] > 0) & (px["low"] > 0) & (px["high"] > 0)]
    g = px.groupby("ticker", sort=False)
    f = px["adj_close"] / px["close"]
    px["a_open"], px["a_high"], px["a_low"], px["a_close"] = px["open"] * f, px["high"] * f, px["low"] * f, px["adj_close"]
    px["dollar_vol"] = px["close"] * px["volume"]
    px["ret_1"] = np.log(px["a_close"]) - np.log(g["a_close"].shift(1))
    g = px.groupby("ticker", sort=False)
    px["rvol_20"] = _roll(g, "ret_1", 20, "std") * math.sqrt(EQ_ANN)
    px["rvol_20_prev"] = g["rvol_20"].shift(1)
    px["shock"] = px["ret_1"] / (px["rvol_20_prev"] / math.sqrt(EQ_ANN))
    px["mean_close_20"] = _roll(g, "a_close", 20, "mean")
    px["med_dv_20_prev"] = _roll(g, "dollar_vol", 20, "median")
    px["med_dv_20_prev"] = px.groupby("ticker", sort=False)["med_dv_20_prev"].shift(1)
    cal = pd.Index(sorted(px["date"].unique()))
    px["sidx"] = cal.get_indexer(px["date"])
    px["sidx_lag"] = px["sidx"] - px.groupby("ticker", sort=False)["sidx"].shift(EQ_HISTORY - 1)
    px["full_hist"] = px["sidx_lag"] == (EQ_HISTORY - 1)
    eta = (np.log(px["a_high"]) + np.log(px["a_low"])) / 2
    c = np.log(px["a_close"])
    eta_prev = eta.groupby(px["ticker"]).shift(1)
    c_prev = c.groupby(px["ticker"]).shift(1)
    px["ar_s2"] = (4 * (c_prev - eta_prev) * (c_prev - eta)).clip(lower=0)
    px["ar_spread"] = np.sqrt(_roll(px.groupby("ticker", sort=False), "ar_s2", 20, "mean"))
    px["ar_spread_prev"] = px.groupby("ticker", sort=False)["ar_spread"].shift(1)
    px = px.drop(columns=["ar_s2", "sidx_lag"])
    px["in_universe"] = (px["full_hist"] & (px["med_dv_20_prev"] >= EQ_DV_FLOOR) & (px["rvol_20"] > EQ_VOL_FLOOR)
                         & (px["close"] >= EQ_PRICE_FLOOR) & px["rvol_20_prev"].notna())
    # wave-1 additions (spec/04 zscore_20; volume for 1b's confirmation)
    g = px.groupby("ticker", sort=False)
    px["std_close_20"] = _roll(g, "a_close", 20, "std")
    px["zscore_20"] = (px["a_close"] - px["mean_close_20"]) / px["std_close_20"]
    px["med_vol_20_prev"] = g["volume"].shift(1).groupby(px["ticker"]).rolling(20, min_periods=20).median().reset_index(level=0, drop=True)
    return px.reset_index(drop=True)


def crypto_features(d1: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    px = d1.rename(columns={"open_time": "date"})[["date", "symbol", "open", "high", "low", "close", "volume", "quote_volume"]].copy()
    px["date"] = px["date"].dt.normalize()
    px = px[(px["date"] >= start) & (px["date"] <= end)]
    px = px[px["symbol"].map(lambda s: crypto_eligible_base(crypto_base(s)))]
    px = px[(px["close"] > 0) & (px["open"] > 0) & (px["low"] > 0) & (px["high"] > 0)].sort_values(["symbol", "date"]).reset_index(drop=True)
    px["ticker"] = px["symbol"]
    px["a_open"], px["a_high"], px["a_low"], px["a_close"] = px["open"], px["high"], px["low"], px["close"]
    px["dollar_vol"] = px["quote_volume"]
    g = px.groupby("ticker", sort=False)
    px["ret_1"] = np.log(px["a_close"]) - np.log(g["a_close"].shift(1))
    g = px.groupby("ticker", sort=False)
    px["rvol_20"] = _roll(g, "ret_1", 20, "std") * math.sqrt(CR_ANN)
    px["rvol_30"] = _roll(g, "ret_1", 30, "std") * math.sqrt(CR_ANN)
    px["rvol_20_prev"] = g["rvol_20"].shift(1)
    px["shock"] = px["ret_1"] / (px["rvol_20_prev"] / math.sqrt(CR_ANN))
    px["mean_close_20"] = _roll(g, "a_close", 20, "mean")
    px["med_dv_20_prev"] = _roll(g, "dollar_vol", 20, "median")
    px["med_dv_20_prev"] = px.groupby("ticker", sort=False)["med_dv_20_prev"].shift(1)
    px["qv_30"] = _roll(g, "dollar_vol", 30, "sum")
    cal = pd.Index(sorted(px["date"].unique()))
    px["sidx"] = cal.get_indexer(px["date"])
    lag = px["sidx"] - px.groupby("ticker", sort=False)["sidx"].shift(CR_HISTORY - 1)
    px["full_hist"] = lag == (CR_HISTORY - 1)
    eta = (np.log(px["a_high"]) + np.log(px["a_low"])) / 2
    c = np.log(px["a_close"])
    eta_prev = eta.groupby(px["ticker"]).shift(1)
    c_prev = c.groupby(px["ticker"]).shift(1)
    px["ar_s2"] = (4 * (c_prev - eta_prev) * (c_prev - eta)).clip(lower=0)
    px["ar_spread"] = np.sqrt(_roll(px.groupby("ticker", sort=False), "ar_s2", 20, "mean"))
    px["ar_spread_prev"] = px.groupby("ticker", sort=False)["ar_spread"].shift(1)
    px = px.drop(columns=["ar_s2"])
    base_ok = px["full_hist"] & px["qv_30"].notna() & (px["rvol_30"] > CR_VOL_FLOOR) & px["rvol_20_prev"].notna()
    px["rank_qv"] = px[base_ok].groupby("date")["qv_30"].rank(ascending=False, method="first")
    px["in_universe"] = base_ok & (px["rank_qv"] <= CR_TOP_N)
    px["top20"] = base_ok & (px["rank_qv"] <= 20)
    g = px.groupby("ticker", sort=False)
    px["std_close_20"] = _roll(g, "a_close", 20, "std")
    px["zscore_20"] = (px["a_close"] - px["mean_close_20"]) / px["std_close_20"]
    # volume confirmation on quote volume (the crypto liquidity measure)
    px["volume"] = px["quote_volume"]
    px["med_vol_20_prev"] = g["volume"].shift(1).groupby(px["ticker"]).rolling(20, min_periods=20).median().reset_index(level=0, drop=True)
    return px.reset_index(drop=True)


def equity_panel(start: str, end: str, use_cache: bool = True) -> pd.DataFrame:
    R = roots()
    p = R.cache / f"equity_panel_{start}_{end}_{PANEL_VERSION}.parquet"
    if use_cache and p.exists():
        return pd.read_parquet(p)
    px = equity_features(load_equity_bars(), start, end)
    px.to_parquet(p, index=False)
    return px


def crypto_panel(start: str, end: str, use_cache: bool = True) -> pd.DataFrame:
    R = roots()
    p = R.cache / f"crypto_panel_{start}_{end}_{PANEL_VERSION}.parquet"
    if use_cache and p.exists():
        return pd.read_parquet(p)
    px = crypto_features(load_crypto_1d(), start, end)
    px.to_parquet(p, index=False)
    return px


# ================================================================ as-of arrays (sessions x tickers)
def _wide(px: pd.DataFrame, col: str, cal: pd.Index, tickers: pd.Index) -> np.ndarray:
    return px.pivot(index="date", columns="ticker", values=col).reindex(index=cal, columns=tickers).to_numpy(dtype=float)


def shift_rows(a: np.ndarray, n: int) -> np.ndarray:
    """a[i+n] aligned at i (rows are sessions); NaN past the end. n < 0 looks back."""
    out = np.full_like(a, np.nan)
    if n > 0:
        out[:-n] = a[n:]
    elif n < 0:
        out[-n:] = a[:n]
    else:
        out[:] = a
    return out


def _rolling_max(a: np.ndarray, n: int) -> np.ndarray:
    return pd.DataFrame(a).rolling(n, min_periods=n).max().to_numpy()


def _midrank_pctl_cols(a: np.ndarray, window: int) -> np.ndarray:
    """spec/04 vol_pctl_250 (harness/features.py `_midrank_pctl`), per column, in wide form."""
    n, m = a.shape
    out = np.full((n, m), np.nan)
    if n < window:
        return out
    for j in range(m):
        col = a[:, j]
        if np.isnan(col).all():
            continue
        w = np.lib.stride_tricks.sliding_window_view(col, window)
        last = w[:, -1:]
        less = np.sum(w < last, axis=1)
        equal = np.sum(w == last, axis=1)
        valid = ~np.isnan(w).any(axis=1)
        out[window - 1:, j] = np.where(valid, (less + (equal + 1.0) / 2.0) / window, np.nan)
    return out


def build_arrays(px: pd.DataFrame, lane: str, o1: pd.DataFrame | None = None, hour_opens: dict | None = None) -> dict:
    """Wide as-of arrays: row i holds data through session i's close for every column.

    Every array a signal may read is listed here; `tests/screen/test_shift.py` perturbs
    bars after D and asserts the candidate and score matrices at D are unchanged.
    """
    # the v1 calendar: every date on which any name has a bar (NYSE sessions; every UTC day
    # for crypto, checked by `calendar_gaps`)
    cal = pd.Index(sorted(px["date"].unique()))
    tickers = pd.Index(sorted(px["ticker"].unique()))
    A: dict = {"cal": cal, "tickers": tickers, "lane": lane}
    for c in ["a_open", "a_high", "a_low", "a_close", "close", "shock", "mean_close_20", "rvol_20", "rvol_20_prev",
              "med_dv_20_prev", "ar_spread_prev", "dollar_vol", "zscore_20", "volume", "med_vol_20_prev"]:
        A[c] = _wide(px, c, cal, tickers)
    A["in_universe"] = _wide(px, "in_universe", cal, tickers) == 1.0
    A["top20"] = (_wide(px, "top20", cal, tickers) == 1.0) if "top20" in px else np.zeros_like(A["in_universe"])
    if o1 is not None:  # crypto: open of the 01:00 UTC 1h kline, aligned to the UTC day
        o1 = o1.assign(date=o1["open_time"].dt.normalize(), ticker=o1["symbol"]).rename(columns={"open": "o1"})
        o1 = o1.drop_duplicates(["date", "ticker"])
        A["o1"] = _wide(o1, "o1", cal, tickers)
    for key, df in (hour_opens or {}).items():  # crypto intraday horizons: o4, o12 (amendment A1)
        if df is None:
            continue
        df = df.assign(date=df["open_time"].dt.normalize(), ticker=df["symbol"]).rename(columns={"open": key}).drop_duplicates(["date", "ticker"])
        A[key] = _wide(df, key, cal, tickers)
    C = A["a_close"]
    with np.errstate(all="ignore"):
        A["vol_ratio_20"] = A["volume"] / A["med_vol_20_prev"]
        A["vol_pctl_250"] = _midrank_pctl_cols(A["dollar_vol"], 250)
        for n in (20, 21, 30, 60, 90):
            A[f"ret_{n}"] = C / shift_rows(C, -n) - 1.0
        A["high_250"] = _rolling_max(A["a_high"], 250)
        A["close_to_high_250"] = C / A["high_250"]
    return A


def equity_arrays(start: str, end: str, use_cache: bool = True) -> tuple[dict, dict]:
    """Arrays plus the universe masks {'smallcap': mask | 'uncapped': None} for the window."""
    px = equity_panel(start, end, use_cache)
    A = build_arrays(px, "equity")
    capmap = market_caps().reindex(A["tickers"])
    small = (capmap < EQ_CAP_USD).to_numpy() & capmap.notna().to_numpy()
    A["cap"] = capmap.to_numpy(dtype=float)
    A["panel"] = px
    return A, {"smallcap": small, "uncapped": None}


def crypto_arrays(start: str, end: str, use_cache: bool = True) -> dict:
    px = crypto_panel(start, end, use_cache)
    A = build_arrays(px, "crypto", load_crypto_o1(), {"o4": load_crypto_hour_open(4), "o12": load_crypto_hour_open(12)})
    A["panel"] = px
    return A


def calendar_gaps(A: dict) -> int:
    """Crypto: number of UTC days missing from the calendar (0 means every day has a bar)."""
    cal = A["cal"]
    return int(len(pd.date_range(cal[0], cal[-1], freq="D")) - len(cal))


def universe_size_stats(A: dict, cap_mask) -> dict:
    u = A["in_universe"] if cap_mask is None else (A["in_universe"] & cap_mask[None, :])
    n = u.sum(axis=1)
    return {"median_daily_universe": float(np.median(n)), "p10": float(np.percentile(n, 10)), "p90": float(np.percentile(n, 90)),
            "sessions": int(len(n)), "names_ever": int(u.any(axis=0).sum())}

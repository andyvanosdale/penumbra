#!/usr/bin/env python3
"""Screen 2: post-shock continuation, crypto first (issue #39).

Standalone like experiments/screen_free_data.py, whose data pull, universe, candidate
and cost code it reuses. Nothing here depends on harness/.

Stages (each caches under $PENUMBRA_DATA_ROOT/screen/ and is idempotent):

    python experiments/screen_free_data.py crypto            # spot 1d + 1h(01:00) klines 2018..2022
    python experiments/screen_continuation_crypto.py perp    # USD-M perpetual 1d, 1h, funding 2020..2022
    python experiments/screen_continuation_crypto.py run     # the screen; writes screen/processed/continuation/

Rule, costs and decision rules follow issue 39 and the pre-registration in
research_log/2026-09-30-continuation-crypto.md. No parameter here is fitted.
"""
from __future__ import annotations

import argparse
import io
import json
import logging
import math
import re
import sys
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import screen_free_data as s1  # noqa: E402

log = logging.getLogger("screen2")

RAW, PROC = s1.RAW, s1.PROC
BIN = s1.BIN                                   # spot klines (issue 15's layout)
PERP = RAW / "binance_um"                       # perpetual klines and funding
OUT = PROC / "continuation"
for d in (PERP, OUT):
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- locked parameters (issue 39)
K_SHOCK = 2.0
K_SHOCK_ALT = 3.0            # read only
K_Z20 = -2.0                 # read only: zscore_20 <= -2 band trigger
HOLD = 5                     # fixed exit at the 01:00 open on the 5th session after the fill session
HOLD_READS = [1, 3, 10]      # horizon read
STOP_RANGE_MULT = 1.5
ORDER_USD = 10_000.0
SPOT_START, SPOT_END = "2018-01-01", "2022-12-31"
PERP_START, PERP_END = "2020-01-01", "2022-12-31"
SPOT_TAKER = 0.0010          # per side
PERP_TAKER = 0.0005          # per side
TIER_TOP20 = 0.0005          # spread per side, top 20 by 30-day quote volume on D
TIER_OTHER = 0.0015
PLACEBO_LAG = 20
TOP_DAYS = 10
CR_ANN = 365
W = 16                       # sessions scanned after the fill session (10-session read + gaps)

UM_PREFIX = "data/futures/um/monthly"


# ================================================================ stage: perp (USD-M bucket)
def _um_zip(kind: str, symbol: str, interval: str | None, ym: str) -> pd.DataFrame | None:
    """One monthly file from the USD-M bucket; kind is 'klines' or 'fundingRate'."""
    if kind == "klines":
        rel = f"klines/{symbol}/{interval}/{symbol}-{interval}-{ym}.zip"
    else:
        rel = f"fundingRate/{symbol}/{symbol}-fundingRate-{ym}.zip"
    p = PERP / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    miss = p.with_suffix(".missing")
    if miss.exists() and not p.exists():
        return None
    if not p.exists():
        try:
            r = s1._http(f"{s1.BV}/{UM_PREFIX}/{rel}", tries=3)
        except Exception as e:  # noqa: BLE001
            if "404" in repr(e):
                miss.touch()
                return None
            raise
        p.write_bytes(r.content)
    with zipfile.ZipFile(p) as z:
        raw = z.read(z.namelist()[0])
    df = pd.read_csv(io.BytesIO(raw), header=None)
    if isinstance(df.iloc[0, 0], str):  # header row
        df = df.iloc[1:].reset_index(drop=True)
    if kind == "klines":
        df = df.iloc[:, :11].astype(float)
        df.columns = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume", "trades", "tb_base", "tb_quote"]
        ot = df["open_time"].astype("int64")
        ot = np.where(ot > 10**14, ot // 1000, ot)
        df["open_time"] = pd.to_datetime(ot, unit="ms")
    else:
        df = df.iloc[:, :3].astype(float)
        df.columns = ["calc_time", "funding_interval_hours", "funding_rate"]
        df["calc_time"] = pd.to_datetime(df["calc_time"].astype("int64"), unit="ms")
    df["symbol"] = symbol
    return df


def perp_symbols() -> list[str]:
    """USDT-quoted USD-M symbols in the bucket; delivery contracts and SETTLED symbols dropped."""
    p = PERP / "um_symbols.json"
    if p.exists():
        return json.loads(p.read_text())
    prefixes = s1._s3_list(f"{UM_PREFIX}/klines/")
    syms = sorted({x.split("/")[-2] for x in prefixes})
    syms = [s for s in syms if s.endswith("USDT") and "_" not in s and "SETTLED" not in s]
    p.write_text(json.dumps(syms))
    return syms


def strip_multiplier(sym: str) -> str:
    return re.sub(r"^\d+", "", sym)


def perp_months(sym: str, months: set[str]) -> list[str]:
    """Months (within the era) for which the bucket lists a 1d file; one listing per symbol."""
    keys = s1._http(f"{s1.S3}?prefix={UM_PREFIX}/klines/{sym}/1d/&max-keys=1000").text
    have = set(re.findall(rf"{sym}-1d-(\d{{4}}-\d{{2}})\.zip</Key>", keys))
    return sorted(have & months)


def stage_perp(workers: int = 12) -> None:
    syms = perp_symbols()
    months = set(pd.period_range(PERP_START, PERP_END, freq="M").strftime("%Y-%m"))
    log.info("perp: %d USDT perpetual symbols in the bucket", len(syms))
    mp = PERP / "um_months.json"
    if mp.exists():
        avail = json.loads(mp.read_text())
    else:
        with ThreadPoolExecutor(workers) as ex:
            avail = dict(zip(syms, ex.map(lambda s: perp_months(s, months), syms)))
        mp.write_text(json.dumps(avail))
    todo = {s: m for s, m in avail.items() if m}
    log.info("perp: %d symbols with 1d klines inside %s..%s; %d monthly files",
             len(todo), PERP_START, PERP_END, sum(len(m) for m in todo.values()))
    t0 = time.time()

    def pull(sym):
        ms = todo[sym]
        d1 = [f for f in (_um_zip("klines", sym, "1d", ym) for ym in ms) if f is not None]
        h1 = [f for f in (_um_zip("klines", sym, "1h", ym) for ym in ms) if f is not None]
        fr = [f for f in (_um_zip("fundingRate", sym, None, ym) for ym in ms) if f is not None]
        cat = lambda fs: pd.concat(fs, ignore_index=True) if fs else None
        return sym, cat(d1), cat(h1), cat(fr)

    D1, H1, FR = [], [], []
    with ThreadPoolExecutor(workers) as ex:
        for n, (sym, d1, h1, fr) in enumerate(ex.map(pull, sorted(todo)), 1):
            if d1 is not None:
                D1.append(d1)
            if h1 is not None:
                H1.append(h1)
            if fr is not None:
                FR.append(fr)
            if n % 20 == 0:
                log.info("perp: %d/%d symbols, %.0fs", n, len(todo), time.time() - t0)
    pd.concat(D1, ignore_index=True).to_parquet(PERP / "um_klines_1d.parquet", index=False)
    pd.concat(H1, ignore_index=True).to_parquet(PERP / "um_klines_1h.parquet", index=False)
    pd.concat(FR, ignore_index=True).to_parquet(PERP / "um_funding.parquet", index=False)
    log.info("perp done: %.0fs; 1d rows %d, 1h rows %d, funding rows %d",
             time.time() - t0, sum(len(x) for x in D1), sum(len(x) for x in H1), sum(len(x) for x in FR))


# ================================================================ panels and arrays
def _wide(df: pd.DataFrame, col: str, cal: pd.Index, tickers: pd.Index, tcol: str = "ticker") -> np.ndarray:
    return df.pivot(index="date", columns=tcol, values=col).reindex(index=cal, columns=tickers).to_numpy(dtype=float)


def build_perp_map(spot_tickers: pd.Index, perp_1d: pd.DataFrame) -> pd.DataFrame:
    """Spot pair -> USD-M perpetual symbol by stripping a leading numeric multiplier."""
    have = set(perp_1d["symbol"].unique())
    rows = []
    for s in spot_tickers:
        cands = sorted(p for p in have if strip_multiplier(p) == s)
        if not cands:
            rows.append({"spot": s, "perp": "", "multiplier": np.nan})
            continue
        plain = [p for p in cands if p == s]
        p = plain[0] if plain else cands[0]
        m = re.match(r"^(\d+)", p)
        rows.append({"spot": s, "perp": p, "multiplier": float(m.group(1)) if m else 1.0,
                     "alternatives": ",".join(c for c in cands if c != p)})
    return pd.DataFrame(rows)


def build(spot_1d: pd.DataFrame, spot_o1: pd.DataFrame, perp_1d: pd.DataFrame, perp_1h: pd.DataFrame,
          funding: pd.DataFrame) -> dict:
    px = s1.crypto_panel(spot_1d)
    g = px.groupby("ticker", sort=False)
    std20 = g["a_close"].rolling(20, min_periods=20).std(ddof=1).reset_index(level=0, drop=True)
    px["zscore_20"] = (px["a_close"] - px["mean_close_20"]) / std20
    cal = pd.Index(sorted(px["date"].unique()))
    tickers = pd.Index(sorted(px["ticker"].unique()))
    A = {"cal": cal, "tickers": tickers, "n_sess": len(cal), "n_tk": len(tickers)}
    for c in ["a_open", "a_high", "a_low", "a_close", "shock", "zscore_20", "rvol_20", "med_dv_20_prev", "ar_spread_prev"]:
        A["spot_" + c.replace("a_", "")] = _wide(px, c, cal, tickers)
    A["in_universe"] = _wide(px, "in_universe", cal, tickers) == 1.0
    A["top20"] = _wide(px, "top20", cal, tickers) == 1.0
    o1 = spot_o1.assign(date=spot_o1["open_time"].dt.normalize(), ticker=spot_o1["symbol"]).drop_duplicates(["date", "ticker"])
    A["spot_o1"] = _wide(o1, "open", cal, tickers)
    A["spot_range"] = A["spot_high"] - A["spot_low"]
    A["btc_rvol_20"] = A["spot_rvol_20"][:, tickers.get_loc("BTCUSDT")]
    # ---- perpetual, aligned to the spot ticker axis through the map
    pm = build_perp_map(tickers, perp_1d)
    A["perp_map"] = pm
    has = pm["perp"] != ""
    A["has_perp"] = has.to_numpy()
    A["mult"] = pm["multiplier"].fillna(1.0).to_numpy()
    p2s = dict(zip(pm.loc[has, "perp"], pm.loc[has, "spot"]))
    pd1 = perp_1d[perp_1d["symbol"].isin(p2s)].copy()
    pd1["date"] = pd1["open_time"].dt.normalize()
    pd1["ticker"] = pd1["symbol"].map(p2s)
    pd1 = pd1[(pd1["date"] >= SPOT_START) & (pd1["date"] <= PERP_END)]
    # a perpetual session or hour with zero quote volume (placeholder rows around listing/delisting) is a missing bar
    pd1 = pd1[(pd1["open"] > 0) & (pd1["high"] > 0) & (pd1["low"] > 0) & (pd1["close"] > 0) & (pd1["quote_volume"] > 0)].sort_values(["ticker", "date"])
    pd1["med_qv_20_prev"] = pd1.groupby("ticker", sort=False)["quote_volume"].rolling(20, min_periods=20).median().reset_index(level=0, drop=True)
    pd1["med_qv_20_prev"] = pd1.groupby("ticker", sort=False)["med_qv_20_prev"].shift(1)
    pd1 = pd1.drop_duplicates(["date", "ticker"])
    for c in ["open", "high", "low", "close", "med_qv_20_prev"]:
        A["perp_" + c] = _wide(pd1, c, cal, tickers)
    ph = perp_1h[perp_1h["symbol"].isin(p2s)].copy()
    ph["ticker"] = ph["symbol"].map(p2s)
    ph["date"] = ph["open_time"].dt.normalize()
    ph = ph[(ph["date"] >= SPOT_START) & (ph["date"] <= PERP_END)]
    ph["hour"] = ph["open_time"].dt.hour
    A["perp_o1"] = _wide(ph[(ph["hour"] == 1) & (ph["quote_volume"] > 0)].drop_duplicates(["date", "ticker"]), "open", cal, tickers)
    # hourly grids (hours since the first calendar day) for funding settlements and their marks
    t0 = cal[0]
    n_h = A["n_sess"] * 24
    ph["h"] = ((ph["open_time"] - t0) / pd.Timedelta(hours=1)).astype(int)
    ph = ph[(ph["h"] >= 0) & (ph["h"] < n_h)].drop_duplicates(["h", "ticker"])
    mark = np.full((n_h, A["n_tk"]), np.nan)
    mark[ph["h"].to_numpy(), tickers.get_indexer(ph["ticker"])] = ph["open"].to_numpy()
    fr = funding[funding["symbol"].isin(p2s)].copy()
    fr["ticker"] = fr["symbol"].map(p2s)
    fr["h"] = ((fr["calc_time"] - t0 + pd.Timedelta(minutes=30)) / pd.Timedelta(hours=1)).astype(int)  # settlement to the nearest hour
    fr = fr[(fr["h"] >= 0) & (fr["h"] < n_h)]
    A["funding_hours"] = sorted(int(h) for h in fr["calc_time"].dt.round("h").dt.hour.unique())
    fr = fr.groupby(["h", "ticker"], as_index=False)["funding_rate"].sum()
    rate = np.zeros((n_h, A["n_tk"]))
    rate[fr["h"].to_numpy(), tickers.get_indexer(fr["ticker"])] = fr["funding_rate"].to_numpy()
    A["perp_mark_h"] = mark
    A["perp_rate_h"] = rate
    return A


# ================================================================ the rule
def _shift(a: np.ndarray, n: int) -> np.ndarray:
    return s1._shift(a, n)


def simulate(A: dict, inst: str, hold: int = HOLD, trigger: str = "shock2", lag: int = 0) -> pd.DataFrame:
    """One row per candidate (filled or not). inst: 'spot' or 'perp'."""
    n_sess, n_tk = A["n_sess"], A["n_tk"]
    cal = A["cal"]
    shock = _shift(A["spot_shock"], -lag) if lag else A["spot_shock"]
    if trigger == "shock2":
        sig = shock <= -K_SHOCK
    elif trigger == "shock3":
        sig = shock <= -K_SHOCK_ALT
    elif trigger == "z20":
        sig = A["spot_zscore_20"] <= K_Z20
    else:
        raise ValueError(trigger)
    start, end = (PERP_START, PERP_END) if inst == "perp" else (SPOT_START, SPOT_END)
    era = np.asarray((cal >= start) & (cal <= end))
    cand = A["in_universe"] & sig & era[:, None]
    n_not_listed = 0
    if inst == "perp":
        cand &= A["has_perp"][None, :]
        listed = ~np.isnan(A["perp_close"])          # the perpetual has a (non-zero-volume) 1d bar on D
        n_not_listed = int((cand & ~listed).sum())
        cand &= listed
    si, tj = np.nonzero(cand)
    order = np.lexsort((tj, si))
    si, tj = si[order], tj[order]
    F = si + 1
    ok = F < n_sess
    si, tj, F = si[ok], tj[ok], F[ok]
    n = len(si)
    if inst == "spot":
        O1, Od, H, C = A["spot_o1"], A["spot_open"], A["spot_high"], A["spot_close"]
        mult = np.ones(n_tk)
    else:
        O1, Od, H, C = A["perp_o1"], A["perp_open"], A["perp_high"], A["perp_close"]
        mult = A["mult"]
    entry = O1[F, tj]
    rng = A["spot_range"][si, tj] * mult[tj]
    unfilled = np.isnan(entry) | np.isnan(rng) | (rng <= 0)
    stop = entry + STOP_RANGE_MULT * rng
    idx = F[:, None] + np.arange(1, W + 1)[None, :]
    inb = idx < n_sess
    idxc = np.minimum(idx, n_sess - 1)
    O1w, Odw, Hw, Cw = (X[idxc, tj[:, None]] for X in (O1, Od, H, C))
    valid = inb & ~np.isnan(Cw) & ~np.isnan(Odw) & ~np.isnan(Hw) & ~np.isnan(O1w)
    exit_k = np.full(n, -1); exit_type = np.full(n, "", dtype=object); exit_px = np.full(n, np.nan)
    cnt = np.zeros(n, dtype=int)
    done = unfilled.copy()
    for k in range(W):
        v = valid[:, k] & ~done
        cnt[v] += 1
        tm = v & (cnt == hold)                       # exit session: fill at its 01:00 open, no stop check there
        o, h = Odw[:, k], Hw[:, k]
        st_open = v & ~tm & (o >= stop)
        st_lvl = v & ~tm & ~st_open & (h >= stop)
        exit_k[tm] = k; exit_type[tm] = "time"; exit_px[tm] = O1w[tm, k]
        exit_k[st_open] = k; exit_type[st_open] = "stop_open"; exit_px[st_open] = o[st_open]
        exit_k[st_lvl] = k; exit_type[st_lvl] = "stop_level"; exit_px[st_lvl] = stop[st_lvl]
        done |= tm | st_open | st_lvl
    still = ~done
    if still.any():
        lastk = np.where(valid, np.arange(W)[None, :], -1).max(axis=1)
        has = still & (lastk >= 0)
        exit_k[has] = lastk[has]; exit_type[has] = "truncated"; exit_px[has] = Cw[has, lastk[has]]
        unfilled |= still & (lastk < 0)
    filled = ~unfilled
    # no re-entry while held: sequential per ticker on signal sessions
    keep = np.ones(n, dtype=bool)
    exit_sess = F + 1 + exit_k
    last_exit: dict[int, int] = {}
    for i in range(n):
        if not filled[i]:
            continue
        le = last_exit.get(tj[i], -1)
        if si[i] < le:
            keep[i] = False
            continue
        last_exit[tj[i]] = exit_sess[i]
    filled &= keep
    short_gross = np.where(filled, -(exit_px / entry - 1.0), np.nan)
    # ---- costs
    tier = np.where(A["top20"][si, tj], TIER_TOP20, TIER_OTHER)
    sigma_d = A["spot_rvol_20"][si, tj] / math.sqrt(CR_ANN)
    if inst == "spot":
        cost_tier = 2 * (SPOT_TAKER + tier)
        s = A["spot_ar_spread_prev"][si, tj]
        s = np.maximum(np.where(np.isnan(s), 0.0, s), tier)      # tier constants are full-spread floors (DECISIONS 2026-09-28)
        half = s / 2
        med = A["spot_med_dv_20_prev"][si, tj]
        slip_in = 0.5 * sigma_d * np.sqrt(ORDER_USD / (0.10 * med))
        slip_out = 0.5 * sigma_d * np.sqrt(ORDER_USD / med)
        cost_spec = (2 * half + slip_in) + (half + slip_out) + 2 * SPOT_TAKER
        cost_dec = cost_tier
        funding = np.zeros(n)
        vol_fallback = np.zeros(n, dtype=bool)
    else:
        med_perp = A["perp_med_qv_20_prev"][si, tj]
        med_spot = A["spot_med_dv_20_prev"][si, tj]
        # perpetual younger than 21 sessions on D (or a zero median): the spot median dollar volume stands in;
        # perpetual volume is normally the larger, so this overstates slippage (recorded per trade)
        vol_fallback = np.isnan(med_perp) | (med_perp <= 0)
        med = np.where(vol_fallback, med_spot, med_perp)
        slip_in = 0.5 * sigma_d * np.sqrt(ORDER_USD / (0.10 * med))
        slip_out = 0.5 * sigma_d * np.sqrt(ORDER_USD / med)
        cost_tier = 2 * PERP_TAKER + 2 * tier + slip_in + slip_out
        cost_spec = np.full(n, np.nan)
        cost_dec = cost_tier
        unfilled |= np.isnan(cost_dec)
        filled = ~unfilled & keep
        # funding: settlements with entry_time < t < exit_time (see the pre-registration)
        h_entry = F * 24 + 1
        x = np.minimum(exit_sess, n_sess - 1)
        h_exit = np.where(exit_type == "time", x * 24 + 1,
                 np.where(exit_type == "stop_open", x * 24,
                 np.where(exit_type == "stop_level", x * 24 + 1, x * 24 + 24)))   # truncated: last close, whole session
        funding = np.zeros(n)
        R, M = A["perp_rate_h"], A["perp_mark_h"]
        for i in np.nonzero(filled)[0]:
            hs = np.arange(h_entry[i] + 1, h_exit[i])
            if len(hs) == 0:
                continue
            r = R[hs, tj[i]]
            nz = r != 0
            if not nz.any():
                continue
            m = M[hs[nz], tj[i]]
            m = np.where(np.isnan(m), entry[i], m)
            funding[i] = float(np.sum(r[nz] * m / entry[i]))
    # ---- universe comparator on spot: entry 01:00 open on F to the exit price (01:00 open for time exits,
    #      session close for stops and truncations), equal weight over the names eligible on D
    univ = A["in_universe"]
    SO1, SC = A["spot_o1"], A["spot_close"]
    bench = np.full(n, np.nan)
    uni_n = np.zeros(n, dtype=int)
    for d in np.unique(si[filled]):
        rows = np.nonzero((si == d) & filled)[0]
        u = univ[d]
        p0 = SO1[d + 1, u]
        for k in np.unique(exit_k[rows]):
            for is_open in (True, False):
                r = rows[(exit_k[rows] == k) & ((exit_type[rows] == "time") == is_open)]
                if len(r) == 0:
                    continue
                xs = d + 2 + k
                if xs >= n_sess:
                    continue
                px_x = (SO1 if is_open else SC)[xs, u]
                with np.errstate(all="ignore"):
                    rr = px_x / p0 - 1.0
                bench[r] = np.nanmean(rr)
                uni_n[r] = int(np.sum(~np.isnan(rr)))
    short_net = short_gross - cost_dec + funding
    out = pd.DataFrame({
        "signal_date": cal[si], "ticker": A["tickers"][tj],
        "perp": A["perp_map"]["perp"].to_numpy()[tj] if inst == "perp" else "",
        "inst": inst, "trigger": trigger, "hold": hold, "lag": lag,
        "filled": filled, "unfilled_reason": np.where(unfilled, np.where(np.isnan(entry), "no_bar", np.where(np.isnan(cost_dec), "no_cost", "zero_range")), np.where(keep, "", "held")),
        "entry": entry, "stop": stop, "exit_type": exit_type, "exit_px": exit_px,
        "sessions_held": np.where(filled, cnt, np.nan),
        "short_gross": short_gross, "cost_tier": cost_tier, "cost_spec": cost_spec, "funding": funding,
        "bench": bench, "uni_n": uni_n,
        "short_net": short_net, "excess": bench + short_net,
        "excess_0": bench + short_gross + funding, "excess_nofund": bench + short_gross - cost_dec,
        "excess_spec": bench + short_gross - cost_spec,
        "vol_fallback": vol_fallback, "shock": A["spot_shock"][si, tj], "zscore_20": A["spot_zscore_20"][si, tj],
        "btc_rvol_20": A["btc_rvol_20"][si], "year": pd.DatetimeIndex(cal[si]).year, "top20": A["top20"][si, tj],
    })
    out["exit_date"] = np.where(filled, cal.to_numpy()[np.minimum(exit_sess, n_sess - 1)], np.datetime64("NaT"))
    out.attrs["perp_candidates_dropped_not_listed_on_D"] = n_not_listed
    return out


# ================================================================ statistics
def _z(daily: pd.Series) -> tuple[float, float, float, int]:
    """(z, day-mean, SE, days) over entry days."""
    daily = daily.dropna()
    if len(daily) < 2:
        return np.nan, np.nan, np.nan, len(daily)
    m, se = daily.mean(), daily.std(ddof=1) / math.sqrt(len(daily))
    return float(m / se), float(m), float(se), int(len(daily))


def summarize(tr: pd.DataFrame, col: str = "excess") -> dict:
    f = tr[tr["filled"]]
    daily = f.groupby("signal_date")[col].mean()
    contrib = f.groupby("signal_date")[col].sum()
    top = contrib.abs().nlargest(TOP_DAYS).index
    z, dm, se, nd = _z(daily)
    z_wo, _, _, nd_wo = _z(daily.drop(top))
    net_col = {"excess": "short_net", "excess_0": None, "excess_nofund": None, "excess_spec": None}[col]
    out = {
        "candidates": int(len(tr)), "trades": int(len(f)), "entry_days": nd,
        "mean_excess_bps": float(f[col].mean() * 1e4) if len(f) else np.nan,
        "median_excess_bps": float(f[col].median() * 1e4) if len(f) else np.nan,
        "hit_rate": float((f[col] > 0).mean()) if len(f) else np.nan,
        "daymean_bps": dm * 1e4 if nd else np.nan, "se_bps": se * 1e4 if nd else np.nan, "z": z,
        "z_wo_top10": z_wo, "days_wo_top10": nd_wo,
        "top10_share_abs_pnl": float(contrib.loc[top].abs().sum() / contrib.abs().sum()) if len(contrib) else np.nan,
        "mean_short_gross_bps": float(f["short_gross"].mean() * 1e4) if len(f) else np.nan,
        "mean_bench_bps": float(f["bench"].mean() * 1e4) if len(f) else np.nan,
        "mean_cost_tier_bps": float(f["cost_tier"].mean() * 1e4) if len(f) else np.nan,
        "mean_cost_spec_bps": float(f["cost_spec"].mean() * 1e4) if len(f) and f["cost_spec"].notna().any() else np.nan,
        "mean_funding_bps": float(f["funding"].mean() * 1e4) if len(f) else np.nan,
        "mean_short_net_bps": float(f["short_net"].mean() * 1e4) if len(f) else np.nan,
        "mean_sessions_held": float(f["sessions_held"].mean()) if len(f) else np.nan,
        "share_stop": float(f["exit_type"].str.startswith("stop").mean()) if len(f) else np.nan,
        "share_stop_open": float((f["exit_type"] == "stop_open").mean()) if len(f) else np.nan,
        "share_time": float((f["exit_type"] == "time").mean()) if len(f) else np.nan,
        "share_truncated": float((f["exit_type"] == "truncated").mean()) if len(f) else np.nan,
        "skipped_held": int((tr["unfilled_reason"] == "held").sum()),
        "unfilled_no_bar": int((tr["unfilled_reason"] == "no_bar").sum()),
        "unfilled_zero_range": int((tr["unfilled_reason"] == "zero_range").sum()),
        "vol_fallback_trades": int(f["vol_fallback"].sum()) if "vol_fallback" in f else 0,
        "perp_candidates_dropped_not_listed_on_D": int(tr.attrs.get("perp_candidates_dropped_not_listed_on_D", 0)),
    }
    if net_col:
        tot_net = f["short_net"].sum()
        out["funding_share_of_net"] = float(f["funding"].sum() / tot_net) if tot_net != 0 else np.nan
    return out


def per_year(tr: pd.DataFrame, col: str = "excess") -> pd.DataFrame:
    rows = []
    for y, g in tr.groupby("year"):
        s = summarize(g, col)
        rows.append({"year": int(y), "trades": s["trades"], "days": s["entry_days"], "mean_excess_bps": s["mean_excess_bps"],
                     "daymean_bps": s["daymean_bps"], "se_bps": s["se_bps"], "z": s["z"], "hit_rate": s["hit_rate"],
                     "mean_short_gross_bps": s["mean_short_gross_bps"], "mean_bench_bps": s["mean_bench_bps"],
                     "mean_funding_bps": s["mean_funding_bps"], "share_stop": s["share_stop"]})
    return pd.DataFrame(rows)


def fmt(x, nd=0):
    return "n/a" if x is None or (isinstance(x, float) and np.isnan(x)) else (f"{x:+.{nd}f}" if nd else f"{x:+.0f}")


# ================================================================ the screen
def stage_run() -> None:
    t0 = time.time()
    spot_1d = pd.read_parquet(BIN / "klines_1d.parquet")
    spot_o1 = pd.read_parquet(BIN / "klines_1h_0100.parquet")
    perp_1d = pd.read_parquet(PERP / "um_klines_1d.parquet")
    perp_1h = pd.read_parquet(PERP / "um_klines_1h.parquet")
    funding = pd.read_parquet(PERP / "um_funding.parquet")
    for df, name in [(spot_1d, "spot 1d"), (spot_o1, "spot 1h"), (perp_1d, "perp 1d"), (perp_1h, "perp 1h")]:
        assert df["open_time"].max() < pd.Timestamp("2023-01-01"), f"{name} carries post-2022 bars"
    assert funding["calc_time"].max() < pd.Timestamp("2023-01-01")
    A = build(spot_1d, spot_o1, perp_1d, perp_1h, funding)
    log.info("panel built: %d sessions x %d tickers, %d with a perpetual, %.0fs", A["n_sess"], A["n_tk"], int(A["has_perp"].sum()), time.time() - t0)
    A["perp_map"].to_csv(OUT / "spot_to_perp_map.csv", index=False)
    uni_2020 = A["in_universe"] & np.asarray((A["cal"] >= PERP_START) & (A["cal"] <= PERP_END))[:, None]
    ever = uni_2020.any(axis=0)
    no_perp = sorted(A["tickers"][ever & ~A["has_perp"]])
    meta = {
        "spec_commit": "3e2e6c11", "issue": 39, "run_at": pd.Timestamp.utcnow().isoformat(),
        "spot_symbols_after_exclusions": int(A["n_tk"]), "sessions": int(A["n_sess"]),
        "first_session": str(A["cal"][0].date()), "last_session": str(A["cal"][-1].date()),
        "spot_o1_coverage_of_universe_cells": float(np.mean(~np.isnan(A["spot_o1"][A["in_universe"]]))),
        "universe_2018_2022": s1.universe_size_stats({"in_universe": A["in_universe"]}, None),
        "universe_2020_2022": s1.universe_size_stats({"in_universe": uni_2020}, None),
        "pairs_ever_in_universe_2020_2022": int(ever.sum()),
        "pairs_with_perp": int((ever & A["has_perp"]).sum()), "pairs_without_perp": no_perp,
        "perp_symbols_mapped": int(A["has_perp"].sum()),
        "perp_o1_coverage_of_universe_cells_with_perp": float(np.mean(~np.isnan(A["perp_o1"][uni_2020 & A["has_perp"][None, :]]))),
        "funding_settlement_hours_utc": [int(h) for h in A["funding_hours"]],
    }
    log.info("meta: %s", {k: v for k, v in meta.items() if k != "pairs_without_perp"})

    runs: dict[str, pd.DataFrame] = {}
    runs["perp"] = simulate(A, "perp")
    runs["spot"] = simulate(A, "spot")
    runs["perp_placebo"] = simulate(A, "perp", lag=PLACEBO_LAG)
    runs["spot_placebo"] = simulate(A, "spot", lag=PLACEBO_LAG)
    for h in HOLD_READS:
        runs[f"perp_h{h}"] = simulate(A, "perp", hold=h)
        runs[f"spot_h{h}"] = simulate(A, "spot", hold=h)
    for trg in ["shock3", "z20"]:
        runs[f"perp_{trg}"] = simulate(A, "perp", trigger=trg)
        runs[f"spot_{trg}"] = simulate(A, "spot", trigger=trg)
    for k, v in runs.items():
        log.info("%s: %d candidates, %d filled", k, len(v), int(v["filled"].sum()))
    pd.concat([v.assign(run=k) for k, v in runs.items()]).to_parquet(RAW / "trades_continuation.parquet", index=False)

    # ---- headline summaries
    rows = []
    def add(run, inst, cost, col):
        s = summarize(runs[run], col)
        rows.append({"run": run, "instrument": inst, "cost": cost, **s})
    add("perp", "perp", "tier+funding", "excess")
    add("perp", "perp", "tier, zero funding", "excess_nofund")
    add("perp", "perp", "zero cost, with funding", "excess_0")
    add("spot", "spot", "tier", "excess")
    add("spot", "spot", "spec", "excess_spec")
    add("spot", "spot", "zero cost", "excess_0")
    add("perp_placebo", "perp", "tier+funding (placebo lag 20)", "excess")
    add("spot_placebo", "spot", "tier (placebo lag 20)", "excess")
    for h in HOLD_READS:
        add(f"perp_h{h}", "perp", f"tier+funding, hold {h}", "excess")
        add(f"spot_h{h}", "spot", f"tier, hold {h}", "excess")
    add("perp_shock3", "perp", "tier+funding, shock<=-3", "excess")
    add("spot_shock3", "spot", "tier, shock<=-3", "excess")
    add("perp_z20", "perp", "tier+funding, zscore_20<=-2", "excess")
    add("spot_z20", "spot", "tier, zscore_20<=-2", "excess")
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "results.csv", index=False)

    # ---- per year
    py = {}
    for run, col in [("perp", "excess"), ("perp", "excess_nofund"), ("spot", "excess"), ("spot", "excess_spec"), ("spot", "excess_0"),
                     ("perp_shock3", "excess"), ("perp_z20", "excess"), ("spot_shock3", "excess"), ("spot_z20", "excess")]:
        py[f"{run}/{col}"] = per_year(runs[run], col).assign(run=run, col=col)
    py_df = pd.concat(py.values(), ignore_index=True)
    py_df.to_csv(OUT / "per_year.csv", index=False)

    # ---- regime split: BTCUSDT rvol_20 on D vs its median over the instrument's era days
    reg = []
    for run, start, end in [("perp", PERP_START, PERP_END), ("spot", SPOT_START, SPOT_END)]:
        era = np.asarray((A["cal"] >= start) & (A["cal"] <= end))
        med = float(np.nanmedian(A["btc_rvol_20"][era]))
        tr = runs[run]
        for name, m in [("high vol", tr["btc_rvol_20"] > med), ("low vol", tr["btc_rvol_20"] <= med)]:
            s = summarize(tr[m], "excess")
            reg.append({"run": run, "regime": name, "btc_rvol_20_median": med, "trades": s["trades"], "days": s["entry_days"],
                        "mean_excess_bps": s["mean_excess_bps"], "daymean_bps": s["daymean_bps"], "se_bps": s["se_bps"], "z": s["z"], "hit_rate": s["hit_rate"]})
    reg_df = pd.DataFrame(reg)
    reg_df.to_csv(OUT / "regime.csv", index=False)

    # ---- decision rules, literally
    P = res[(res["run"] == "perp") & (res["cost"] == "tier+funding")].iloc[0]
    py_perp = py["perp/excess"].set_index("year")
    py_spot = py["spot/excess"].set_index("year")
    PL = res[res["run"] == "perp_placebo"].iloc[0]
    yrs_perp = {int(y): float(py_perp.loc[y, "mean_excess_bps"]) if y in py_perp.index else np.nan for y in (2020, 2021, 2022)}
    yrs_spot = {int(y): float(py_spot.loc[y, "mean_excess_bps"]) if y in py_spot.index else np.nan for y in range(2018, 2023)}
    overall_sign = np.sign(P["mean_excess_bps"])
    same_sign = sum(1 for v in yrs_spot.values() if not np.isnan(v) and np.sign(v) == overall_sign and v != 0)
    rules = {
        "1_mean_excess_ge_50bps": {"value_bps": float(P["mean_excess_bps"]), "pass": bool(P["mean_excess_bps"] >= 50)},
        "2_z_ge_2_and_z_wo_top10_ge_2": {"z": float(P["z"]), "z_wo_top10": float(P["z_wo_top10"]), "pass": bool(P["z"] >= 2.0 and P["z_wo_top10"] >= 2.0)},
        "3_positive_each_year": {"per_year_bps": yrs_perp, "pass": bool(all((not np.isnan(v)) and v > 0 for v in yrs_perp.values()))},
        "4_placebo_abs_z_lt_2": {"z": float(PL["z"]), "trades": int(PL["trades"]), "pass": bool(abs(PL["z"]) < 2.0)},
        "5_top10_share_lt_35pct": {"share": float(P["top10_share_abs_pnl"]), "pass": bool(P["top10_share_abs_pnl"] < 0.35)},
        "spot_same_sign_4_of_5_years": {"perp_sign": float(overall_sign), "spot_per_year_bps": yrs_spot, "years_same_sign": int(same_sign), "pass": bool(same_sign >= 4)},
    }
    rules["all_pass"] = bool(all(r["pass"] for r in rules.values()))
    meta["rules"] = rules
    meta["runtime_s"] = round(time.time() - t0)
    f = runs["perp"][runs["perp"]["filled"]]
    meta["perp_extremes"] = {
        "largest_excess": f.nlargest(5, "excess")[["signal_date", "ticker", "perp", "entry", "exit_px", "exit_type", "short_gross", "funding", "bench", "excess"]].to_dict("records"),
        "smallest_excess": f.nsmallest(5, "excess")[["signal_date", "ticker", "perp", "entry", "exit_px", "exit_type", "short_gross", "funding", "bench", "excess"]].to_dict("records"),
        "top10_days": f.groupby("signal_date")["excess"].agg(["sum", "count"]).assign(a=lambda d: d["sum"].abs()).nlargest(10, "a").drop(columns="a").reset_index().to_dict("records"),
    }
    (OUT / "meta.json").write_text(json.dumps(meta, indent=2, default=str))
    (OUT / "tables.md").write_text(tables_markdown(res, py_df, reg_df, meta))
    print((OUT / "tables.md").read_text())
    print(json.dumps(rules, indent=1, default=str))


def tables_markdown(res: pd.DataFrame, py: pd.DataFrame, reg: pd.DataFrame, meta: dict) -> str:
    L = ["# Screen 2: post-shock continuation, crypto — tables", "",
         "All return figures are basis points per trade. excess = universe return over the trade's window (spot, equal-weight, same-day eligible, long) + the short's net return (−price return − costs + funding); positive means the short beat the universe. z is day-clustered (mean over entry days of the daily mean excess over its standard error).", "",
         "## Headline", "",
         "| run | instrument | cost | candidates | trades | days | mean excess | median | hit | day-mean | SE | z | z w/o top 10 | top-10 share | short gross | universe | cost | funding | hold | stop share | trunc |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in res.iterrows():
        cost = r["mean_cost_spec_bps"] if r["cost"] == "spec" else (0.0 if "zero cost" in r["cost"] else r["mean_cost_tier_bps"])
        L.append(f"| {r['run']} | {r['instrument']} | {r['cost']} | {r['candidates']} | {r['trades']} | {r['entry_days']} | {fmt(r['mean_excess_bps'])} | {fmt(r['median_excess_bps'])} | {r['hit_rate']:.3f} | {fmt(r['daymean_bps'])} | {r['se_bps']:.0f} | {fmt(r['z'], 2)} | {fmt(r['z_wo_top10'], 2)} | {r['top10_share_abs_pnl']:.1%} | {fmt(r['mean_short_gross_bps'])} | {fmt(r['mean_bench_bps'])} | {cost:.0f} | {fmt(r['mean_funding_bps'])} | {r['mean_sessions_held']:.2f} | {r['share_stop']:.2f} | {r['share_truncated']:.3f} |")
    L += ["", "## Per year", "", "| run | quantity | year | trades | days | mean excess | day-mean | SE | z | hit | short gross | universe | funding | stop share |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in py.iterrows():
        L.append(f"| {r['run']} | {r['col']} | {int(r['year'])} | {int(r['trades'])} | {int(r['days'])} | {fmt(r['mean_excess_bps'])} | {fmt(r['daymean_bps'])} | {r['se_bps']:.0f} | {fmt(r['z'], 2)} | {r['hit_rate']:.3f} | {fmt(r['mean_short_gross_bps'])} | {fmt(r['mean_bench_bps'])} | {fmt(r['mean_funding_bps'])} | {r['share_stop']:.2f} |")
    L += ["", "## Regime split (BTCUSDT rvol_20 on D vs its era median)", "", "| run | regime | BTC rvol_20 median | trades | days | mean excess | day-mean | SE | z | hit |", "|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in reg.iterrows():
        L.append(f"| {r['run']} | {r['regime']} | {r['btc_rvol_20_median']:.3f} | {int(r['trades'])} | {int(r['days'])} | {fmt(r['mean_excess_bps'])} | {fmt(r['daymean_bps'])} | {r['se_bps']:.0f} | {fmt(r['z'], 2)} | {r['hit_rate']:.3f} |")
    L += ["", "## Decision rules (perpetual, 2020-01-01 → 2022-12-31; spot four-of-five)", "", "| rule | value | verdict |", "|---|---|---|"]
    R = meta["rules"]
    L.append(f"| 1. mean net excess ≥ +50 bps (tier + funding) | {R['1_mean_excess_ge_50bps']['value_bps']:+.0f} bps | {'PASS' if R['1_mean_excess_ge_50bps']['pass'] else 'FAIL'} |")
    L.append(f"| 2. z ≥ 2.0 and z without top 10 days ≥ 2.0 | {R['2_z_ge_2_and_z_wo_top10_ge_2']['z']:+.2f} / {R['2_z_ge_2_and_z_wo_top10_ge_2']['z_wo_top10']:+.2f} | {'PASS' if R['2_z_ge_2_and_z_wo_top10_ge_2']['pass'] else 'FAIL'} |")
    L.append(f"| 3. positive in 2020, 2021, 2022 | {', '.join(f'{y}: {v:+.0f}' for y, v in R['3_positive_each_year']['per_year_bps'].items())} | {'PASS' if R['3_positive_each_year']['pass'] else 'FAIL'} |")
    L.append(f"| 4. placebo (shock lagged 20) abs z < 2.0 | {R['4_placebo_abs_z_lt_2']['z']:+.2f} ({R['4_placebo_abs_z_lt_2']['trades']} trades) | {'PASS' if R['4_placebo_abs_z_lt_2']['pass'] else 'FAIL'} |")
    L.append(f"| 5. top-10-day share of abs P&L < 35% | {R['5_top10_share_lt_35pct']['share']:.1%} | {'PASS' if R['5_top10_share_lt_35pct']['pass'] else 'FAIL'} |")
    s = R["spot_same_sign_4_of_5_years"]
    L.append(f"| spot mirror same sign as the perpetual in ≥ 4 of 5 years | {', '.join(f'{y}: {v:+.0f}' for y, v in s['spot_per_year_bps'].items())} ({s['years_same_sign']} of 5 match sign {s['perp_sign']:+.0f}) | {'PASS' if s['pass'] else 'FAIL'} |")
    L.append(f"| **all** | | **{'PASS' if R['all_pass'] else 'FAIL'}** |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    if RAW is None:
        raise SystemExit("set PENUMBRA_DATA_ROOT (docs/environment.md)")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["perp", "run"])
    a = ap.parse_args()
    if a.stage == "perp":
        stage_perp()
    elif a.stage == "run":
        stage_run()

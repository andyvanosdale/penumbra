"""Intraday data layer of the screening engine (research_log/2026-10-07-intraday-wave.md).

Reads the Alpaca 5-minute IEX cache that `experiments/pull_alpaca_bars.py` wrote
(`$PENUMBRA_ALPACA_ROOT`, default `~/penumbra-data/alpaca`: `bars/5Min/<YYYY-MM>/batch_*.parquet`,
timestamps UTC at the bar's start, raw prices), one month at a time, and builds a per-session,
per-name table:

    the entry-rule price and lateness at each candidate clock time (open of the first
    regular-hours bar at or after T, within 15 minutes), the 09:30 open, the 09:55 / 14:55 /
    15:55 bars, the opening-range high, first-half-hour / through-12:00 / late-day / session
    volume, VWAP through 12:00, the regular-hours bar count, high and low, the same-session
    close (15:55 bar, else the last bar from 15:40 on).

`intraday_arrays` aligns that table to the wave-1 daily arrays (calendar x tickers; Alpaca's
dot-form class symbols mapped to the list's dash form), detects early closes, and computes the
coverage floor and the 20-session medians with data through F-1, skipping early-close sessions
and sessions without any bar. Row F of every array holds what was knowable on F at the stated
clock time; `tests/screen/test_intraday.py` perturbs later bars and asserts nothing moves.
"""
from __future__ import annotations

import logging
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from experiments.screen.data import shift_rows

log = logging.getLogger("screen.intraday")

PANEL_VERSION = "intraday-2"
TZ = "America/New_York"
RTH_START_MIN, RTH_END_MIN = 9 * 60 + 30, 15 * 60 + 55     # bar starts 09:30 .. 15:55 (the 15:55 bar ends 16:00)
EARLY_CLOSE_MIN = 13 * 60                                  # a 13:00 close; bars from 13:00 on are then extended hours
EARLY_CLOSE_PM_SHARE = 0.3                                 # early close when bars from 13:00 on are < 30% of the bars before 13:00 (all names)
MIN_SESSION_BARS = 1000                                    # fewer bars than this across all names: the cache has no coverage of that session
ENTRY_TIMES = ["09:35", "10:00", "10:30", "12:00", "15:30", "15:55"]
LATE_MAX_MIN = 15
CLOSE_FALLBACK_MIN = 15 * 60 + 40                          # same-session close: the 15:55 bar, else the last bar from 15:40 on
FLOOR_BARS = 60
FLOOR_WINDOW = 20
MED_WINDOW = 20
FIRST_MONTH = "2020-07"                                    # the cache's coverage starts 2020-07-27; earlier months are probes


def alpaca_root() -> Path:
    return Path(os.environ.get("PENUMBRA_ALPACA_ROOT", "~/penumbra-data/alpaca")).expanduser()


def to_minutes(t: str) -> int:
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def list_symbol(sym: pd.Series) -> pd.Series:
    """Alpaca's dot-form class symbols (BRK.B) to the list's dash form (BRK-B)."""
    return sym.str.replace(".", "-", regex=False)


# ---------------------------------------------------------------- one month -> session table
def load_month(ym: str, root: Path | None = None) -> pd.DataFrame:
    root = root or alpaca_root()
    files = sorted((root / "bars" / "5Min" / ym).glob("batch_*.parquet"))
    parts = [pd.read_parquet(f) for f in files]
    parts = [p for p in parts if len(p)]
    if not parts:
        return pd.DataFrame(columns=["symbol", "ts", "open", "high", "low", "close", "volume", "trade_count", "vwap"])
    df = pd.concat(parts, ignore_index=True)
    df["symbol"] = list_symbol(df["symbol"].astype(str))
    return df


def _first_bar_at_or_after(b: pd.DataFrame, t_min: int) -> pd.DataFrame:
    sub = b[(b["m"] >= t_min) & (b["m"] <= t_min + LATE_MAX_MIN)]
    first = sub.sort_values("m").drop_duplicates(["date", "symbol"], keep="first")
    return pd.DataFrame({"date": first["date"].to_numpy(), "symbol": first["symbol"].to_numpy(),
                         "px": first["open"].to_numpy(dtype=float), "late": (first["m"] - t_min).to_numpy(dtype=float)})


def _bar_at(b: pd.DataFrame, t_min: int, col: str) -> pd.Series:
    sub = b[b["m"] == t_min].drop_duplicates(["date", "symbol"])
    return sub.set_index(["date", "symbol"])[col].astype(float)


def session_table(bars: pd.DataFrame) -> pd.DataFrame:
    """Per (date, symbol) regular-hours summary of one month of 5-minute bars (timestamps UTC)."""
    if bars.empty:
        return pd.DataFrame()
    ts = pd.to_datetime(bars["ts"], utc=True).dt.tz_convert(TZ)
    m = (ts.dt.hour * 60 + ts.dt.minute).to_numpy()
    keep = (m >= RTH_START_MIN) & (m <= RTH_END_MIN)
    b = bars.loc[keep, ["symbol", "open", "high", "low", "close", "volume", "vwap"]].copy()
    b["m"] = m[keep]
    b["date"] = ts[keep].dt.tz_localize(None).dt.normalize().to_numpy()
    for c in ("open", "high", "low", "close", "volume", "vwap"):
        b[c] = pd.to_numeric(b[c], errors="coerce").astype(float)
    b = b.sort_values(["symbol", "date", "m"]).drop_duplicates(["symbol", "date", "m"], keep="last")
    # early closes (13:00): across all names, the bars from 13:00 on are a sliver of the morning's; those bars are
    # extended hours and are dropped. Also the total bar count per session, for the coverage check.
    per_date = b.groupby("date")["m"].agg(total="size", pm=lambda x: int((x >= EARLY_CLOSE_MIN).sum()))
    per_date["am"] = per_date["total"] - per_date["pm"]
    per_date["early_close"] = per_date["pm"] < EARLY_CLOSE_PM_SHARE * per_date["am"].clip(lower=1)
    early_dates = set(per_date.index[per_date["early_close"]])
    b = b[~(b["date"].isin(early_dates) & (b["m"] >= EARLY_CLOSE_MIN))]
    b["vwap"] = b["vwap"].where(b["vwap"].notna() & (b["vwap"] > 0), b["close"])
    b["pv"] = b["vwap"] * b["volume"]
    g = b.groupby(["date", "symbol"], sort=True)
    out = g.agg(n_rth=("m", "size"), v_rth=("volume", "sum"), hi_rth=("high", "max"), lo_rth=("low", "min"),
                last_m=("m", "max"), c_last=("close", "last"))
    # named bars
    out["o0930"] = _bar_at(b, to_minutes("09:30"), "open")
    out["c0955"] = _bar_at(b, to_minutes("09:55"), "close")
    out["c1455"] = _bar_at(b, to_minutes("14:55"), "close")
    out["c1555"] = _bar_at(b, to_minutes("15:55"), "close")
    # first half hour: six bars 09:30 .. 09:55; opening range high over 09:30 .. 09:50
    fhh = b[(b["m"] >= to_minutes("09:30")) & (b["m"] <= to_minutes("09:55"))]
    gf = fhh.groupby(["date", "symbol"])
    out["n_fhh"] = gf["m"].size()
    out["v_fhh"] = gf["volume"].sum()
    out["h_or"] = fhh[fhh["m"] <= to_minutes("09:50")].groupby(["date", "symbol"])["high"].max()
    # through 12:00: bars 09:30 .. 11:55
    am = b[b["m"] <= to_minutes("11:55")]
    ga = am.groupby(["date", "symbol"])
    out["v_1200"] = ga["volume"].sum()
    pv = ga["pv"].sum()
    with np.errstate(all="ignore"):
        out["vwap_1200"] = (pv / out["v_1200"]).where(out["v_1200"] > 0)
    # late day: bars 15:00 .. 15:55
    out["v_late"] = b[b["m"] >= to_minutes("15:00")].groupby(["date", "symbol"])["volume"].sum()
    # same-session close: the 15:55 bar, else the last bar starting at or after 15:40
    tail = b[b["m"] >= CLOSE_FALLBACK_MIN].sort_values("m").drop_duplicates(["date", "symbol"], keep="last")
    c_tail = tail.set_index(["date", "symbol"])["close"]
    out["c_close"] = out["c1555"].where(out["c1555"].notna(), c_tail)
    # entry-rule prices
    for t in ENTRY_TIMES:
        f = _first_bar_at_or_after(b, to_minutes(t)).set_index(["date", "symbol"])
        key = t.replace(":", "")
        out[f"px_{key}"] = f["px"]
        out[f"late_{key}"] = f["late"]
    for c in ("n_fhh", "v_fhh", "v_1200", "v_late"):
        out[c] = out[c].fillna(0)
    out["n_rth"] = out["n_rth"].astype(int)
    out["n_fhh"] = out["n_fhh"].astype(int)
    out = out.reset_index()
    out["early_close"] = out["date"].isin(early_dates)
    out["session_bars"] = out["date"].map(per_date["total"]).astype(int)
    return out


def _build_month(args) -> tuple[str, int, int]:
    ym, out_dir, root = args
    df = session_table(load_month(ym, root))
    p = Path(out_dir) / f"sessions_{ym}.parquet"
    df.to_parquet(p, index=False)
    return ym, int(len(df)), int(df["date"].nunique()) if len(df) else 0


def months_available(root: Path | None = None, first: str = FIRST_MONTH) -> list[str]:
    root = root or alpaca_root()
    return sorted(p.name for p in (root / "bars" / "5Min").iterdir() if p.is_dir() and p.name >= first)


def build_session_panel(out_dir: Path, months: list[str] | None = None, workers: int = 8, root: Path | None = None) -> pd.DataFrame:
    """Session tables for every month (parallel), cached as one parquet per month; returns the build log."""
    out_dir.mkdir(parents=True, exist_ok=True)
    months = months or months_available(root)
    todo = [(ym, str(out_dir), root) for ym in months if not (out_dir / f"sessions_{ym}.parquet").exists()]
    rows = []
    if todo:
        with ProcessPoolExecutor(workers) as ex:
            for ym, n, nd in ex.map(_build_month, todo):
                rows.append({"month": ym, "rows": n, "sessions": nd})
                log.info("sessions %s: %d name-sessions, %d sessions", ym, n, nd)
    return pd.DataFrame(rows)


def load_session_panel(out_dir: Path, months: list[str] | None = None) -> pd.DataFrame:
    files = sorted(out_dir.glob("sessions_*.parquet"))
    if months is not None:
        files = [f for f in files if f.stem.split("_", 1)[1] in months]
    parts = [pd.read_parquet(f) for f in files]
    parts = [p for p in parts if len(p)]
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


# ---------------------------------------------------------------- aligned arrays
SESSION_COLS = ["n_rth", "v_rth", "hi_rth", "lo_rth", "c_last", "last_m", "o0930", "c0955", "c1455", "c1555", "n_fhh", "v_fhh",
                "h_or", "v_1200", "vwap_1200", "v_late", "c_close"]


def _wide(px: pd.DataFrame, col: str, cal: pd.Index, tickers: pd.Index) -> np.ndarray:
    return px.pivot(index="date", columns="symbol", values=col).reindex(index=cal, columns=tickers).to_numpy(dtype=float)


def _rolling_prev(M: np.ndarray, rows: np.ndarray, window: int, how: str) -> np.ndarray:
    """Rolling statistic over the `window` rows of `rows` strictly before each row of `rows`, placed on
    the full calendar (NaN elsewhere). `how`: 'median' or 'min'."""
    out = np.full_like(M, np.nan)
    sub = pd.DataFrame(M[rows])
    r = getattr(sub.rolling(window, min_periods=window), how)().shift(1).to_numpy()
    out[rows] = r
    return out


def intraday_arrays(A: dict, panel: pd.DataFrame) -> dict:
    """Wide arrays on the daily calendar and tickers. Row F holds the session-F table; `floor_ok`,
    `med20_*` use the 20 fill-eligible sessions strictly before F; `elig_daily` is the daily universe
    at F-1; `elig_floor` adds the coverage floor."""
    cal, tickers = A["cal"], A["tickers"]
    panel = panel[panel["symbol"].isin(set(tickers))]
    I: dict = {"cal": cal, "tickers": tickers}
    for c in SESSION_COLS:
        I[c] = _wide(panel, c, cal, tickers)
    for t in ENTRY_TIMES:
        key = t.replace(":", "")
        I[f"px_{key}"] = _wide(panel, f"px_{key}", cal, tickers)
        I[f"late_{key}"] = _wide(panel, f"late_{key}", cal, tickers)
    n_rth = np.nan_to_num(I["n_rth"], nan=0.0)
    I["n_rth"] = n_rth
    per_date = panel.groupby("date")[["early_close", "session_bars"]].max().reindex(cal)
    I["session_bars"] = per_date["session_bars"].fillna(0).to_numpy(dtype=float)
    I["has_bars"] = I["session_bars"] >= MIN_SESSION_BARS
    I["early_close"] = I["has_bars"] & per_date["early_close"].fillna(False).to_numpy(dtype=bool)
    I["fill_session"] = I["has_bars"] & ~I["early_close"]
    rows = np.nonzero(I["fill_session"])[0]
    # coverage floor: >= FLOOR_BARS bars on each of the FLOOR_WINDOW fill sessions before F
    min_prev = _rolling_prev(n_rth, rows, FLOOR_WINDOW, "min")
    I["floor_ok"] = np.nan_to_num(min_prev, nan=-1.0) >= FLOOR_BARS
    I["med20_v_fhh"] = _rolling_prev(I["v_fhh"], rows, MED_WINDOW, "median")
    I["med20_v_1200"] = _rolling_prev(I["v_1200"], rows, MED_WINDOW, "median")
    # eligibility at F-1 (data through the previous session's close)
    I["elig_daily"] = shift_rows(A["in_universe"].astype(float), -1) == 1.0
    I["elig_floor"] = I["elig_daily"] & I["floor_ok"]
    with np.errstate(all="ignore"):
        I["f"] = A["a_close"] / A["close"]                      # raw -> adjusted basis, per session
    return I


def eligibility(I: dict, cap_mask: np.ndarray | None, floor: bool) -> np.ndarray:
    e = I["elig_floor"] if floor else I["elig_daily"]
    return e if cap_mask is None else (e & cap_mask[None, :])


def universe_stats(I: dict, cap_mask, era_mask: np.ndarray) -> dict:
    """Daily universe size with and without the floor over the era's fill sessions."""
    rows = era_mask & I["fill_session"]
    out = {}
    for name, floor in (("daily", False), ("floored", True)):
        n = eligibility(I, cap_mask, floor)[rows].sum(axis=1)
        out[name] = {"median": float(np.median(n)) if len(n) else np.nan, "p10": float(np.percentile(n, 10)) if len(n) else np.nan,
                     "p90": float(np.percentile(n, 90)) if len(n) else np.nan, "names_ever": int(eligibility(I, cap_mask, floor)[rows].any(axis=0).sum())}
    out["fill_sessions"] = int(rows.sum())
    out["early_close_sessions"] = int((era_mask & I["early_close"]).sum())
    out["sessions_without_bars"] = int((era_mask & ~I["has_bars"]).sum())
    return out


def fill_gap_stats(I: dict, elig: np.ndarray, era_mask: np.ndarray) -> dict:
    """Per entry time: share of eligible name-sessions filled, mean lateness (minutes), share late > 0."""
    rows = era_mask & I["fill_session"]
    out = {}
    for t in ENTRY_TIMES:
        key = t.replace(":", "")
        late = I[f"late_{key}"][rows][elig[rows]]
        n = late.size
        filled = ~np.isnan(late)
        out[t] = {"eligible_name_sessions": int(n), "filled_share": float(filled.mean()) if n else np.nan,
                  "mean_late_min": float(np.nanmean(late)) if filled.any() else np.nan,
                  "late_share": float((late[filled] > 0).mean()) if filled.any() else np.nan}
    return out

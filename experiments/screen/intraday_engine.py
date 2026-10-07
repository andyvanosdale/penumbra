"""Intraday event engine (research_log/2026-10-07-intraday-wave.md, "Common protocol").

A signal supplies a boolean candidate matrix on fill sessions F (row F: what was knowable on F
before the entry time). The engine ANDs it with the eligibility matrix (daily universe at F-1,
with the coverage floor for the session-shape signals), fills at the entry-rule price at the
signal's clock time, stores the return to every later exit (10:30, 12:00, the same-session
close, the next open, 1 / 5 / 21 sessions) with the same-day universe mean of the same quantity,
applies the no-re-entry rule at the decision horizon, charges the flat cost schedule, and
summarizes with the day-clustered z (`engine.event_summary`). Controls: the lag-20 stale-signal
placebo, the planted +50 bps, and for rank-type rows the random-slice placebo and a power
statement.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from experiments.screen import engine
from experiments.screen.data import shift_rows
from experiments.screen.intraday_data import ENTRY_TIMES, eligibility, to_minutes
from experiments.screen.v1rule import spec_cost

ERAS = {"dev": ("2020-08-01", "2022-06-30"), "confirm": ("2022-07-01", "2023-12-31")}
HALF_SPLIT = {"dev": "2021-07-16", "confirm": "2023-04-01"}
EXITS = ["1030", "1200", "close", "nopen", "1", "5", "21"]
EXIT_MIN = {"1030": to_minutes("10:30"), "1200": to_minutes("12:00"), "close": to_minutes("15:55")}   # intraday exits: the bar that starts here must start after the entry bar
EXIT_OFFSET = {"1030": 0, "1200": 0, "close": 0, "nopen": 1, "1": 1, "5": 5, "21": 21}                 # exit session offset
COST_LEVELS = ["0", "low", "base", "high", "spec"]
RANDOM_SEED = 20261007


def exits_for(entry: str) -> list[str]:
    """Exits defined for an entry time: every intraday exit strictly after the entry bar, then the daily ones."""
    t = to_minutes(entry)
    return [e for e in EXITS if e not in EXIT_MIN or EXIT_MIN[e] > t]


def exit_arrays(A: dict, I: dict) -> dict[str, np.ndarray]:
    """Exit prices in the raw-on-F basis (daily prices divided by the session factor f_F)."""
    f = I["f"]
    with np.errstate(all="ignore"):
        return {"1030": I["px_1030"], "1200": I["px_1200"], "close": I["c_close"],
                "nopen": shift_rows(A["a_open"], 1) / f, "1": shift_rows(A["a_close"], 1) / f,
                "5": shift_rows(A["a_close"], 5) / f, "21": shift_rows(A["a_close"], 21) / f}


def period_slices(dates: pd.Series, era_name: str) -> list[tuple[str, np.ndarray]]:
    d = pd.DatetimeIndex(dates)
    out = [("all", np.ones(len(d), dtype=bool))]
    for y in sorted(set(d.year)):
        out.append((str(y), np.asarray(d.year == y)))
    split = pd.Timestamp(HALF_SPLIT[era_name])
    out.append(("half1", np.asarray(d < split)))
    out.append(("half2", np.asarray(d >= split)))
    return out


class IntradaySpec:
    def __init__(self, name: str, direction: str, entry: str, horizon: str, comparator: str = "universe"):
        assert entry in ENTRY_TIMES and horizon in exits_for(entry)
        self.name, self.direction, self.entry, self.horizon, self.comparator = name, direction, entry, horizon, comparator

    @property
    def sign(self) -> float:
        return 1.0 if self.direction == "long" else -1.0

    @property
    def key(self) -> str:
        return self.entry.replace(":", "")


def intraday_trades(A: dict, I: dict, raw: np.ndarray, spec: IntradaySpec, elig: np.ndarray, era: tuple[str, str]) -> pd.DataFrame:
    """One row per candidate on an era fill session: entry, lateness, fwd_<exit>, uni_fwd_<exit>, excess_<exit>
    (sign-adjusted), cost_<level>, filled / held / traded."""
    cal = A["cal"]
    in_era, era_last = engine.era_rows(cal, era)
    fill_ok = in_era & I["fill_session"]
    cand = raw & elig & fill_ok[:, None]
    n_sess = cand.shape[0]
    E = I[f"px_{spec.key}"]
    comp = elig & ~np.isnan(E) & fill_ok[:, None]           # comparator: eligible names filled at the same time
    si, tj = np.nonzero(cand)
    order = np.lexsort((tj, si))
    si, tj = si[order], tj[order]
    n = len(si)
    entry = E[si, tj]
    X = exit_arrays(A, I)
    cols: dict[str, np.ndarray] = {}
    for ex in exits_for(spec.entry):
        off = EXIT_OFFSET[ex]
        with np.errstate(all="ignore"):
            fwd_all = X[ex] / E - 1.0
        if off:
            fwd_all[~(np.arange(n_sess) + off <= era_last), :] = np.nan
        um = np.where(comp, fwd_all, np.nan)
        uni_n = np.sum(~np.isnan(um), axis=1)
        with np.errstate(all="ignore"):
            uni = np.where(uni_n > 0, np.nansum(um, axis=1) / np.maximum(uni_n, 1), np.nan)
        cols[f"fwd_{ex}"] = fwd_all[si, tj]
        cols[f"uni_fwd_{ex}"] = uni[si] if spec.comparator == "universe" else np.zeros(n)
        cols[f"uni_n_{ex}"] = uni_n[si]
        cols[f"excess_{ex}"] = spec.sign * (cols[f"fwd_{ex}"] - cols[f"uni_fwd_{ex}"])
    H = spec.horizon
    filled = ~np.isnan(entry) & ~np.isnan(cols[f"fwd_{H}"]) & ~np.isnan(cols[f"uni_fwd_{H}"])
    keep = np.ones(n, dtype=bool)
    exit_sess = si + EXIT_OFFSET[H]
    last_exit: dict[int, int] = {}
    for i in range(n):
        if not filled[i]:
            continue
        if si[i] < last_exit.get(tj[i], -1):
            keep[i] = False
            continue
        last_exit[tj[i]] = int(exit_sess[i])
    traded = filled & keep
    med_dv = A["med_dv_20_prev"][si, tj]
    costs = engine.schedule_cost("equity", med_dv)
    out = pd.DataFrame({
        "signal_date": cal[si], "ticker": A["tickers"][tj], "fill": spec.entry, "direction": spec.direction,
        "entry": entry, "late_min": I[f"late_{spec.key}"][si, tj], "filled": filled, "held": filled & ~keep, "traded": traded,
        "med_dv": med_dv, "bucket": engine.bucket_label("equity", med_dv), **cols,
    })
    for k, v in costs.items():
        out[f"cost_{k}"] = v
    with np.errstate(all="ignore"):
        out["cost_spec"] = spec_cost(A, si, tj) if "ar_spread_prev" in A else np.nan
    out["year"] = pd.DatetimeIndex(out["signal_date"]).year
    return out


def intraday_report(tr: pd.DataFrame, spec: IntradaySpec, universe: str, era_name: str) -> pd.DataFrame:
    rows = []
    periods = period_slices(tr["signal_date"], era_name)
    for ex in exits_for(spec.entry):
        for cost in COST_LEVELS:
            for pname, m in periods:
                sub = tr[m]
                if sub.empty and pname != "all":
                    continue
                rows.append({"signal": spec.name, "lane": "equity", "universe": universe, "era": era_name, "fill": spec.entry,
                             "direction": spec.direction, "horizon": ex, "decision": ex == spec.horizon, "cost": cost, "period": pname,
                             **engine.event_summary(sub, ex, cost, spec.sign)})
    return pd.DataFrame(rows)


def fill_stats(tr: pd.DataFrame) -> dict:
    c = tr
    late = c["late_min"]
    return {"candidates": int(len(c)), "unfilled_share": float(late.isna().mean()) if len(c) else np.nan,
            "mean_late_min": float(late.mean()) if late.notna().any() else np.nan,
            "late_share": float((late.dropna() > 0).mean()) if late.notna().any() else np.nan}


def random_slice(raw: np.ndarray, pool: np.ndarray, seed: int = RANDOM_SEED) -> np.ndarray:
    """Per row, a uniformly random subset of `pool` of the same size as `raw`'s row."""
    rng = np.random.default_rng(seed)
    out = np.zeros_like(raw)
    k_rows = raw.sum(axis=1)
    for i in np.nonzero(k_rows)[0]:
        idx = np.nonzero(pool[i])[0]
        k = min(int(k_rows[i]), len(idx))
        if k:
            out[i, rng.choice(idx, size=k, replace=False)] = True
    return out


def controls(A: dict, I: dict, raw: np.ndarray, spec: IntradaySpec, elig: np.ndarray, era: tuple[str, str],
             actual: pd.DataFrame, pool: np.ndarray | None = None) -> dict:
    """Lag-20 placebo, planted +50 bps, and (rank-type rows) the random-slice placebo and the power statement."""
    H = spec.horizon
    lagged = shift_rows(raw.astype(float), -engine.PLACEBO_LAG) == 1.0
    pl = intraday_trades(A, I, lagged, spec, elig, era)
    out = {}
    for cost in ("0", "base"):
        s = engine.event_summary(pl, H, cost, spec.sign)
        out[f"placebo_z_{cost}"] = s["z"]; out[f"placebo_mean_net_{cost}"] = s["mean_net"]
    out["placebo_trades"] = int(pl["traded"].sum()); out["placebo_days"] = s["entry_days"]
    f = actual[actual["traded"] & actual[f"excess_{H}"].notna()]
    daily = (f[f"excess_{H}"] + engine.PLANTED_BPS / 1e4).groupby(f["signal_date"]).mean()
    base = f[f"excess_{H}"].groupby(f["signal_date"]).mean()
    out["planted_z_0"] = engine.zstats(daily)["z"]
    out["actual_z_0"] = engine.zstats(base)["z"]
    out["planted_shift"] = out["planted_z_0"] - out["actual_z_0"] if not (np.isnan(out["planted_z_0"]) or np.isnan(out["actual_z_0"])) else np.nan
    sb = engine.event_summary(actual, H, "base", spec.sign)
    out["power_days"] = sb["entry_days"]; out["power_se_bps"] = sb["se"] * 1e4 if sb["se"] == sb["se"] else np.nan
    out["power_required_net_bps_for_z3"] = 3.0 * out["power_se_bps"] if out["power_se_bps"] == out["power_se_bps"] else np.nan
    if pool is not None:
        rnd = intraday_trades(A, I, random_slice(raw, pool), spec, elig, era)
        s = engine.event_summary(rnd, H, "0", spec.sign)
        out["random_placebo_z_0"] = s["z"]; out["random_placebo_mean_net_0"] = s["mean_net"]; out["random_placebo_trades"] = int(rnd["traded"].sum())
    out.update({f"fill_{k}": v for k, v in fill_stats(actual).items()})
    return out


# ---------------------------------------------------------------- daily baselines (reported, not ledgered)
def daily_baseline(A: dict, raw_fill: np.ndarray, direction: str, elig: np.ndarray, era: tuple[str, str]) -> dict:
    """Fill at the daily open of F for the candidates on fill session F; exits at the same-session daily close
    and the next open; excess over the eligible universe; day-clustered z at zero and base cost."""
    sign = 1.0 if direction == "long" else -1.0
    cal = A["cal"]
    in_era, era_last = engine.era_rows(cal, era)
    O, C = A["a_open"], A["a_close"]
    cand = raw_fill & elig & in_era[:, None] & ~np.isnan(O)
    si, tj = np.nonzero(cand)
    out = {}
    with np.errstate(all="ignore"):
        paths = {"open_to_close": C / O - 1.0, "open_to_next_open": shift_rows(O, 1) / O - 1.0}
    paths["open_to_next_open"][~(np.arange(len(cal)) + 1 <= era_last), :] = np.nan
    med_dv = A["med_dv_20_prev"][si, tj]
    cost = engine.schedule_cost("equity", med_dv)["base"]
    for name, fwd in paths.items():
        um = np.where(elig & ~np.isnan(O), fwd, np.nan)
        with np.errstate(all="ignore"):
            uni = np.nanmean(um, axis=1)
        ex = sign * (fwd[si, tj] - uni[si])
        ok = ~np.isnan(ex)
        d0 = pd.Series(ex[ok]).groupby(cal[si[ok]]).mean()
        db = pd.Series(ex[ok] - cost[ok]).groupby(cal[si[ok]]).mean()
        out[name] = {"trades": int(ok.sum()), "days": int(len(d0)), "mean_gross_bps": float(np.mean(ex[ok]) * 1e4) if ok.any() else np.nan,
                     "z_0": engine.zstats(d0)["z"], "mean_net_base_bps": float(np.mean(ex[ok] - cost[ok]) * 1e4) if ok.any() else np.nan,
                     "z_base": engine.zstats(db)["z"]}
    return out

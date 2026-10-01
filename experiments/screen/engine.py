"""The screening engine: event mode, rank mode, costs, statistic, controls, reports.

Protocol: research_log/2026-10-01-wave-1-screen.md, "Common protocol" (transcribed from
proposals/2026-09-30-signal-screening-pivot.md section 6). Nothing here is fitted.

Event mode
    A signal supplies a raw candidate matrix (sessions x tickers, data through D's close).
    The engine ANDs it with the universe on D, fills at the next session's open (crypto:
    the 01:00 UTC open on D+1), exits at the same price type H sessions after the fill
    session, stores forward returns at 1, 5, 21 and 63 sessions with the same-day universe
    mean of each, applies the no-re-entry rule at the decision horizon, charges the flat
    cost schedule, and summarizes with the day-clustered z.

Rank mode (weekly, crypto)
    Rebalance D = every Sunday; data through D's close; fill at the 01:00 UTC open on
    D+1; one weekly observation per rebalance date. 1d: long/flat per pair vs buy-and-hold.
    1e: top decile by score, three overlapping 3-week tranches, vs the equal-weight
    universe eligible at each tranche's formation date.
"""
from __future__ import annotations

import math
import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd

from experiments.screen.data import shift_rows
from experiments.screen.v1rule import spec_cost

HORIZONS = [1, 5, 21, 63]
ORDER_USD = 10_000.0
PLACEBO_LAG = 20          # sessions (days for crypto rank mode)
PLANTED_BPS = 50
WEEK_DAYS = 7

ERAS = {
    "equity": {"dev": ("2010-01-01", "2020-12-31"), "confirm": ("2021-01-01", "2023-12-31")},
    "crypto": {"dev": ("2018-01-01", "2022-12-31"), "confirm": ("2023-01-01", "2024-12-31")},
}
# first day of the second half of each era
HALF_SPLIT = {
    "equity": {"dev": "2015-07-01", "confirm": "2022-07-01"},
    "crypto": {"dev": "2020-07-01", "confirm": "2024-01-01"},
}

# flat round-trip cost schedule (bps) by liquidity bucket: low / base / high
EQ_SCHEDULE = [(10_000_000.0, (10, 20, 40)), (1_000_000.0, (20, 40, 80)), (0.0, (40, 80, 160))]
CR_SCHEDULE = (40, 60, 100)
CR_ALT_BPS = 80
COST_LEVELS = {"equity": ["0", "low", "base", "high", "spec"], "crypto": ["0", "low", "base", "high", "alt80", "spec"]}


# ---------------------------------------------------------------- costs
def schedule_cost(lane: str, med_dv: np.ndarray) -> dict[str, np.ndarray]:
    """Round-trip cost fraction per candidate at each schedule level."""
    n = len(med_dv)
    out = {"0": np.zeros(n)}
    if lane == "crypto":
        for name, bps in zip(("low", "base", "high"), CR_SCHEDULE):
            out[name] = np.full(n, bps / 1e4)
        out["alt80"] = np.full(n, CR_ALT_BPS / 1e4)
        return out
    low = np.full(n, np.nan); base = np.full(n, np.nan); high = np.full(n, np.nan)
    for floor, (lo, ba, hi) in EQ_SCHEDULE:
        m = np.isnan(low) & (med_dv >= floor)
        low[m], base[m], high[m] = lo / 1e4, ba / 1e4, hi / 1e4
    out["low"], out["base"], out["high"] = low, base, high
    return out


def bucket_label(lane: str, med_dv: np.ndarray) -> np.ndarray:
    if lane == "crypto":
        return np.full(len(med_dv), "crypto")
    return np.where(med_dv >= 1e7, ">=10M", np.where(med_dv >= 1e6, "1-10M", "0.5-1M"))


# ---------------------------------------------------------------- statistic
def zstats(daily: pd.Series) -> dict:
    """Day-clustered mean, SE and z of a per-entry-day series."""
    d = daily.dropna()
    n = len(d)
    if n < 2:
        return {"days": n, "daymean": float(d.mean()) if n else np.nan, "se": np.nan, "z": np.nan}
    se = float(d.std(ddof=1) / math.sqrt(n))
    return {"days": n, "daymean": float(d.mean()), "se": se, "z": float(d.mean() / se) if se > 0 else np.nan}


def top10_stats(daily_sum: pd.Series, daily_mean: pd.Series) -> dict:
    """Share of absolute P&L from the 10 largest entry days and the z without them."""
    if daily_sum.empty:
        return {"top10_share": np.nan, "z_wo_top10": np.nan}
    top = daily_sum.abs().nlargest(10).index
    tot = daily_sum.abs().sum()
    return {"top10_share": float(daily_sum.loc[top].abs().sum() / tot) if tot > 0 else np.nan,
            "z_wo_top10": zstats(daily_mean.drop(top, errors="ignore"))["z"]}


# ---------------------------------------------------------------- eras
def era_rows(cal: pd.Index, era: tuple[str, str]) -> tuple[np.ndarray, int]:
    """Boolean mask of sessions inside the era and the index of the era's last session."""
    start, end = pd.Timestamp(era[0]), pd.Timestamp(era[1])
    m = (cal >= start) & (cal <= end)
    idx = np.nonzero(m)[0]
    return m, (int(idx[-1]) if len(idx) else -1)


def period_slices(dates: pd.Series, lane: str, era_name: str) -> list[tuple[str, np.ndarray]]:
    """('all', mask), one per year, and the two halves of the era."""
    d = pd.DatetimeIndex(dates)
    out = [("all", np.ones(len(d), dtype=bool))]
    for y in sorted(set(d.year)):
        out.append((str(y), (d.year == y).to_numpy()))
    split = pd.Timestamp(HALF_SPLIT[lane][era_name])
    out.append(("half1", (d < split).to_numpy()))
    out.append(("half2", (d >= split).to_numpy()))
    return out


# ================================================================ event mode
@dataclass
class EventSpec:
    name: str
    direction: str      # "long" | "short"
    horizon: int        # decision horizon (sessions)

    @property
    def sign(self) -> float:
        return 1.0 if self.direction == "long" else -1.0


def _fill_prices(A: dict, fill: str) -> tuple[np.ndarray, int]:
    O, C = A["a_open"], A["a_close"]
    if fill == "next_open":
        return (A["o1"] if (A["lane"] == "crypto" and "o1" in A) else O), 1
    if fill == "close":
        return C, 0
    if fill == "next_close":
        return C, 1
    raise ValueError(fill)


def event_trades(A: dict, raw_cand: np.ndarray, spec: EventSpec, cap_mask: np.ndarray | None,
                 era: tuple[str, str], fill: str = "next_open") -> pd.DataFrame:
    """One row per candidate on an era session. Columns: fwd_h, uni_fwd_h, excess_h (sign-adjusted),
    cost_<level>, traded (filled, not held, decision-horizon label inside the era)."""
    univ = A["in_universe"] if cap_mask is None else (A["in_universe"] & cap_mask[None, :])
    in_era, era_last = era_rows(A["cal"], era)
    cand = univ & raw_cand & in_era[:, None]
    n_sess = cand.shape[0]
    P, off = _fill_prices(A, fill)
    si, tj = np.nonzero(cand)
    order = np.lexsort((tj, si))
    si, tj = si[order], tj[order]
    F = si + off
    n = len(si)
    entry = np.where(F < n_sess, P[np.minimum(F, n_sess - 1), tj], np.nan)
    cols: dict[str, np.ndarray] = {}
    for h in HORIZONS:
        fwd_all = shift_rows(P, off + h) / shift_rows(P, off) - 1.0
        # era boundary: an exit session after the era's last session is a null label
        last_ok = np.arange(n_sess) + off + h <= era_last
        fwd_all[~last_ok, :] = np.nan
        um = np.where(univ, fwd_all, np.nan)
        uni_n = np.sum(~np.isnan(um), axis=1)
        with np.errstate(all="ignore"):
            uni = np.where(uni_n > 0, np.nansum(um, axis=1) / np.maximum(uni_n, 1), np.nan)
        cols[f"fwd_{h}"] = fwd_all[si, tj]
        cols[f"uni_fwd_{h}"] = uni[si]
        cols[f"uni_n_{h}"] = uni_n[si]
        cols[f"excess_{h}"] = spec.sign * (cols[f"fwd_{h}"] - cols[f"uni_fwd_{h}"])
    H = spec.horizon
    filled = ~np.isnan(entry) & ~np.isnan(cols[f"fwd_{H}"]) & ~np.isnan(cols[f"uni_fwd_{H}"])
    # no re-entry while held: a name held at D's close (exit session F+H > D) is skipped
    keep = np.ones(n, dtype=bool)
    exit_sess = F + H
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
    costs = schedule_cost(A["lane"], med_dv)
    out = pd.DataFrame({
        "signal_date": A["cal"][si], "ticker": A["tickers"][tj], "fill": fill, "direction": spec.direction,
        "entry": entry, "filled": filled, "held": filled & ~keep, "traded": traded,
        "med_dv": med_dv, "bucket": bucket_label(A["lane"], med_dv), "shock": A["shock"][si, tj],
        **cols,
    })
    for k, v in costs.items():
        out[f"cost_{k}"] = v
    with np.errstate(all="ignore"):
        out["cost_spec"] = spec_cost(A, si, tj)
    out["year"] = pd.DatetimeIndex(out["signal_date"]).year
    return out


def event_summary(tr: pd.DataFrame, h: int, cost: str, sign: float = 1.0) -> dict:
    """Statistics of the net excess at horizon h and cost level `cost` over the traded rows."""
    f = tr[tr["traded"] & tr[f"excess_{h}"].notna()]
    c = f[f"cost_{cost}"].to_numpy() if cost != "0" else np.zeros(len(f))
    ex = f[f"excess_{h}"].to_numpy()
    net = pd.Series(ex - c, index=f.index)
    daily_mean = net.groupby(f["signal_date"]).mean()
    daily_sum = net.groupby(f["signal_date"]).sum()
    zs = zstats(daily_mean)
    own = sign * f[f"fwd_{h}"]
    out = {
        "candidates": int(len(tr)), "filled": int(tr["filled"].sum()), "held": int(tr["held"].sum()),
        "trades": int(len(f)), "entry_days": zs["days"],
        "mean_net": float(net.mean()) if len(f) else np.nan, "median_net": float(net.median()) if len(f) else np.nan,
        "hit_rate": float((net > 0).mean()) if len(f) else np.nan,
        "mean_gross_excess": float(ex.mean()) if len(f) else np.nan,
        "winsorized_gross_excess": float(pd.Series(ex).clip(*np.nanquantile(ex, [0.01, 0.99])).mean()) if len(f) > 1 else np.nan,
        "mean_cand_ret": float(own.mean()) if len(f) else np.nan,
        "mean_uni_ret": float((sign * f[f"uni_fwd_{h}"]).mean()) if len(f) else np.nan,
        "mean_cost": float(c.mean()) if len(f) else np.nan,
        "daymean": zs["daymean"], "se": zs["se"], "z": zs["z"],
        **top10_stats(daily_sum, daily_mean),
    }
    return out


def event_report(trades_by_fill: dict[str, pd.DataFrame], spec: EventSpec, lane: str, era_name: str,
                 universe: str) -> pd.DataFrame:
    rows = []
    for fill, tr in trades_by_fill.items():
        horizons = HORIZONS if fill == "next_open" else [spec.horizon]
        levels = COST_LEVELS[lane] if fill == "next_open" else ["0", "base"]
        periods = period_slices(tr["signal_date"], lane, era_name)
        for h in horizons:
            for cost in levels:
                for pname, m in periods:
                    sub = tr[m]
                    if sub.empty and pname != "all":
                        continue
                    rows.append({"signal": spec.name, "lane": lane, "universe": universe, "era": era_name, "fill": fill,
                                 "horizon": h, "decision": h == spec.horizon, "cost": cost, "period": pname,
                                 **event_summary(sub, h, cost, spec.sign)})
    return pd.DataFrame(rows)


def event_controls(A: dict, raw_cand: np.ndarray, spec: EventSpec, cap_mask, era: tuple[str, str],
                   actual: pd.DataFrame) -> dict:
    """Stale-signal placebo (rule lagged 20 sessions, universe on D) and the planted +50 bps control."""
    lagged = shift_rows(raw_cand.astype(float), -PLACEBO_LAG) == 1.0
    pl = event_trades(A, lagged, spec, cap_mask, era)
    out = {}
    for cost in ("0", "base"):
        s = event_summary(pl, spec.horizon, cost, spec.sign)
        out[f"placebo_z_{cost}"] = s["z"]; out[f"placebo_mean_net_{cost}"] = s["mean_net"]
    out["placebo_trades"] = int(pl["traded"].sum()); out["placebo_days"] = s["entry_days"]
    f = actual[actual["traded"] & actual[f"excess_{spec.horizon}"].notna()]
    daily = (f[f"excess_{spec.horizon}"] + PLANTED_BPS / 1e4).groupby(f["signal_date"]).mean()
    base = f[f"excess_{spec.horizon}"].groupby(f["signal_date"]).mean()
    out["planted_z_0"] = zstats(daily)["z"]
    out["actual_z_0"] = zstats(base)["z"]
    out["planted_shift"] = out["planted_z_0"] - out["actual_z_0"] if not (np.isnan(out["planted_z_0"]) or np.isnan(out["actual_z_0"])) else np.nan
    return out


# ================================================================ rank mode (weekly, crypto)
def weekly_dates(A: dict, era: tuple[str, str]) -> pd.DatetimeIndex:
    """Every Sunday (UTC day) inside the era that is on the calendar."""
    cal = A["cal"]
    start, end = pd.Timestamp(era[0]), pd.Timestamp(era[1])
    d = cal[(cal >= start) & (cal <= end)]
    return pd.DatetimeIndex([x for x in d if x.dayofweek == 6])


def _at(A: dict, key: str, dates: pd.DatetimeIndex, offset_days: int) -> np.ndarray:
    """Array (len(dates) x tickers) of A[key] on date + offset; NaN when the date is off the calendar."""
    idx = A["cal"].get_indexer(dates + pd.Timedelta(days=offset_days))
    out = np.full((len(dates), A[key].shape[1]), np.nan)
    ok = idx >= 0
    out[ok] = A[key][idx[ok]]
    return out


def week_returns(A: dict, dates: pd.DatetimeIndex, w: int, era_end: str) -> np.ndarray:
    """Return from the 01:00 UTC open on D+1+7w to the 01:00 UTC open on D+8+7w, per name.
    A name whose end bar is missing is liquidated at its last close inside the week; a week
    whose end falls after the era's last day is null."""
    P = A["o1"] if "o1" in A else A["a_open"]
    s0 = _at_prices(A, P, dates, 1 + WEEK_DAYS * w)
    s1 = _at_prices(A, P, dates, 1 + WEEK_DAYS * (w + 1))
    # liquidation fallback: last available close strictly inside the week
    C = A["a_close"]
    fallback = np.full_like(s1, np.nan)
    for k in range(WEEK_DAYS, 0, -1):
        c = _at_prices(A, C, dates, WEEK_DAYS * w + k)
        fallback = np.where(np.isnan(fallback), c, fallback)
    end_px = np.where(np.isnan(s1), fallback, s1)
    r = end_px / s0 - 1.0
    too_late = (dates + pd.Timedelta(days=1 + WEEK_DAYS * (w + 1))) > pd.Timestamp(era_end)
    r[np.asarray(too_late), :] = np.nan
    return r


def _at_prices(A: dict, M: np.ndarray, dates: pd.DatetimeIndex, offset_days: int) -> np.ndarray:
    idx = A["cal"].get_indexer(dates + pd.Timedelta(days=offset_days))
    out = np.full((len(dates), M.shape[1]), np.nan)
    ok = idx >= 0
    out[ok] = M[idx[ok]]
    return out


def ts_mom_weekly(A: dict, position: np.ndarray, pair: str, era: tuple[str, str], lag_days: int = 0) -> pd.DataFrame:
    """1d: long/flat one pair per week against buy-and-hold. `position` is the signal's
    sessions x tickers boolean matrix (data through D). Returns one row per rebalance date."""
    dates = weekly_dates(A, era)
    j = int(A["tickers"].get_loc(pair))
    idx = A["cal"].get_indexer(dates - pd.Timedelta(days=lag_days))
    pos = np.where(idx >= 0, position[np.maximum(idx, 0), j], False).astype(float)
    r = week_returns(A, dates, 0, era[1])[:, j]
    prev = np.concatenate([[0.0], pos[:-1]])
    switch = np.abs(pos - prev)
    costs = schedule_cost("crypto", np.full(len(dates), np.nan))
    rows = {"date": dates, "pos": pos, "switch": switch, "bh": r}
    for level, c in costs.items():
        rows[f"strat_{level}"] = pos * r - (c / 2.0) * switch
        rows[f"diff_{level}"] = rows[f"strat_{level}"] - r
    df = pd.DataFrame(rows)
    df["year"] = df["date"].dt.year
    df["valid"] = ~np.isnan(r)
    return df


def xs_mom_weekly(A: dict, scores: np.ndarray, era: tuple[str, str], hold_weeks: int = 3, lag_days: int = 0) -> pd.DataFrame:
    """1e: each Sunday form the top decile of the eligible universe by `scores` (data through D),
    hold three weeks; `hold_weeks` tranches are live each week. One row per rebalance date:
    the mean over live tranches of (tranche week return - universe week return - cost at formation)."""
    dates = weekly_dates(A, era)
    nd = len(dates)
    univ = _at(A, "in_universe", dates, 0) == 1.0
    sidx = A["cal"].get_indexer(dates - pd.Timedelta(days=lag_days))
    sc = np.full((nd, scores.shape[1]), np.nan)
    ok = sidx >= 0
    sc[ok] = scores[sidx[ok]]
    sc = np.where(univ, sc, np.nan)
    # top decile per formation date
    top = np.zeros_like(univ)
    k_arr = np.zeros(nd, dtype=int)
    for i in range(nd):
        valid = ~np.isnan(sc[i])
        n = int(valid.sum())
        if n == 0:
            continue
        k = int(math.ceil(n / 10))
        k_arr[i] = k
        order = np.argsort(-np.where(valid, sc[i], -np.inf), kind="stable")
        top[i, order[:k]] = True
    wr = [week_returns(A, dates, w, era[1]) for w in range(hold_weeks)]
    costs = schedule_cost("crypto", np.full(nd, np.nan))
    tranche_ret = np.full((nd, hold_weeks), np.nan)   # tranche formed at i, week w
    uni_ret = np.full((nd, hold_weeks), np.nan)
    with np.errstate(all="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # all-NaN weeks are null by design
        for w in range(hold_weeks):
            tr_w = np.where(top, wr[w], np.nan)
            un_w = np.where(univ, wr[w], np.nan)
            tranche_ret[:, w] = np.nanmean(tr_w, axis=1)
            uni_ret[:, w] = np.nanmean(un_w, axis=1)
    # observation at week i: tranches formed at i (w=0), i-1 (w=1), i-2 (w=2)
    rows = {"date": dates, "n_eligible": (~np.isnan(sc)).sum(axis=1), "k": k_arr}
    gross = np.full(nd, np.nan); uni = np.full(nd, np.nan); live = np.zeros(nd, dtype=int)
    for i in range(nd):
        g, u, m = [], [], 0
        for w in range(hold_weeks):
            f = i - w
            if f < 0 or np.isnan(tranche_ret[f, w]) or np.isnan(uni_ret[f, w]):
                continue
            g.append(tranche_ret[f, w]); u.append(uni_ret[f, w]); m += 1
        if m:
            gross[i], uni[i], live[i] = float(np.mean(g)), float(np.mean(u)), m
    rows["tranches"] = live
    rows["port"] = gross
    rows["uni"] = uni
    new_tranche = np.array([not np.isnan(tranche_ret[i, 0]) for i in range(nd)])
    for level, c in costs.items():
        # the new tranche pays its round trip at formation; the observation averages over live tranches
        cost_week = np.where(live > 0, c * new_tranche / np.maximum(live, 1), np.nan)
        rows[f"diff_{level}"] = gross - uni - cost_week
        rows[f"port_{level}"] = gross - cost_week
    df = pd.DataFrame(rows)
    df["year"] = df["date"].dt.year
    df["valid"] = ~np.isnan(gross)
    return df


def rank_summary(wk: pd.DataFrame, cost: str) -> dict:
    v = wk[wk["valid"]]
    diff = v[f"diff_{cost}"]
    zs = zstats(diff)
    out = {"weeks": zs["days"], "mean_weekly_diff": zs["daymean"], "se": zs["se"], "z": zs["z"],
           "ann_excess": 52 * zs["daymean"] if zs["days"] else np.nan,
           "hit_rate": float((diff > 0).mean()) if len(v) else np.nan,
           **top10_stats(diff, diff)}
    strat_col = f"strat_{cost}" if f"strat_{cost}" in v else f"port_{cost}"
    comp_col = "bh" if "bh" in v else "uni"
    for name, col in (("strat", strat_col), ("comp", comp_col)):
        r = v[col].dropna()
        if len(r) > 1:
            eq = (1 + r).cumprod()
            out[f"ann_ret_{name}"] = float(eq.iloc[-1] ** (52 / len(r)) - 1)
            out[f"ann_vol_{name}"] = float(r.std(ddof=1) * math.sqrt(52))
            out[f"sharpe_{name}"] = out[f"ann_ret_{name}"] / out[f"ann_vol_{name}"] if out[f"ann_vol_{name}"] > 0 else np.nan
            out[f"max_dd_{name}"] = float((eq / eq.cummax() - 1).min())
        else:
            out[f"ann_ret_{name}"] = out[f"ann_vol_{name}"] = out[f"sharpe_{name}"] = out[f"max_dd_{name}"] = np.nan
    if "pos" in v:
        out["time_in_market"] = float(v["pos"].mean()) if len(v) else np.nan
        out["switches_per_year"] = float(v["switch"].sum() / max(len(v), 1) * 52)
        out["round_trips_per_year"] = out["switches_per_year"] / 2
    else:
        out["round_trips_per_year"] = 52 / 3
    return out


def rank_report(wk: pd.DataFrame, name: str, universe: str, era_name: str) -> pd.DataFrame:
    rows = []
    for cost in COST_LEVELS["crypto"]:
        if f"diff_{cost}" not in wk:
            continue
        for pname, m in period_slices(wk["date"], "crypto", era_name):
            sub = wk[m]
            if sub.empty and pname != "all":
                continue
            rows.append({"signal": name, "lane": "crypto", "universe": universe, "era": era_name, "cost": cost,
                         "period": pname, **rank_summary(sub, cost)})
    return pd.DataFrame(rows)


def rank_controls(actual: pd.DataFrame, placebo: pd.DataFrame) -> dict:
    out = {}
    for cost in ("0", "base"):
        out[f"placebo_z_{cost}"] = rank_summary(placebo, cost)["z"]
        out[f"placebo_ann_excess_{cost}"] = rank_summary(placebo, cost)["ann_excess"]
    v = actual[actual["valid"]]
    out["actual_z_0"] = zstats(v["diff_0"])["z"]
    out["planted_z_0"] = zstats(v["diff_0"] + PLANTED_BPS / 1e4)["z"]
    out["planted_shift"] = out["planted_z_0"] - out["actual_z_0"]
    out["placebo_weeks"] = int(placebo["valid"].sum())
    return out

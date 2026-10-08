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

HORIZONS = [1, 5, 21, 63, 126, 252]
INTRADAY = {"i04": "o4", "i12": "o12"}   # crypto: 01:00 UTC fill -> 04:00 / 12:00 UTC hourly open on D+1
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
        out.append((str(y), np.asarray(d.year == y)))
    split = pd.Timestamp(HALF_SPLIT[lane][era_name])
    out.append(("half1", np.asarray(d < split)))
    out.append(("half2", np.asarray(d >= split)))
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
    if A["lane"] == "crypto" and fill == "next_open" and "o1" in A:
        # intraday horizons on D+1: from the 01:00 UTC open to the 04:00 / 12:00 UTC open, same universe comparator
        for lab, key in INTRADAY.items():
            if key not in A:
                continue
            with np.errstate(all="ignore"):
                fwd_all = shift_rows(A[key], 1) / shift_rows(A["o1"], 1) - 1.0
            fwd_all[~(np.arange(n_sess) + 1 <= era_last), :] = np.nan
            um = np.where(univ, fwd_all, np.nan)
            uni_n = np.sum(~np.isnan(um), axis=1)
            with np.errstate(all="ignore"):
                uni = np.where(uni_n > 0, np.nansum(um, axis=1) / np.maximum(uni_n, 1), np.nan)
            cols[f"fwd_{lab}"] = fwd_all[si, tj]; cols[f"uni_fwd_{lab}"] = uni[si]; cols[f"uni_n_{lab}"] = uni_n[si]
            cols[f"excess_{lab}"] = spec.sign * (cols[f"fwd_{lab}"] - cols[f"uni_fwd_{lab}"])
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


def horizons_in(tr: pd.DataFrame) -> list:
    """Horizon labels present in a trades frame: the session grid plus any intraday labels."""
    return [h for h in HORIZONS if f"excess_{h}" in tr] + [lab for lab in INTRADAY if f"excess_{lab}" in tr]


def event_summary(tr: pd.DataFrame, h, cost: str, sign: float = 1.0) -> dict:
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
        horizons = horizons_in(tr) if fill == "next_open" else [spec.horizon]
        levels = COST_LEVELS[lane] if fill == "next_open" else ["0", "base"]
        periods = period_slices(tr["signal_date"], lane, era_name)
        for h in horizons:
            for cost in levels:
                for pname, m in periods:
                    sub = tr[m]
                    if sub.empty and pname != "all":
                        continue
                    rows.append({"signal": spec.name, "lane": lane, "universe": universe, "era": era_name, "fill": fill, "direction": spec.direction,
                                 "horizon": str(h), "decision": h == spec.horizon, "cost": cost, "period": pname,
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


# ================================================================ rank mode (equities; wave 2)
# Protocol: research_log/2026-10-08-wave-2-rank.md. Monthly (2a, 2b) or weekly (2d) long baskets
# of the top (or bottom) decile / quintile of a score, filled at the next open after D and held to
# the next open after the next D, against the equal-weight ranked set. Every constant below is a
# locked number from the pre-registration.
RANDOM_SEED = 20261008
RANDOM_DRAWS = 200
PLACEBO_LAG_LONG = 250
RANK_MIN_PERIODS = {"dev": {12: 120, 52: 520}, "confirm": {12: 30, 52: 140}}
Z_EX2020 = 1.5
Z_GATE_DEV, Z_GATE_CONFIRM, Z_POOLED_MIN, NET_PP_MIN = 2.0, 1.0, 2.5, 5.0
NW_LAGS = {12: 3, 52: 4}
PLANTED_BAR_BPS = {12: 42, 52: 10}
MDE80_MULT = 2.8416
MDE80_UNDERPOWERED_PP = 12.0
FAMILY_N = 9
RANDOM_RANK_MIN, RANDOM_RANK_OF = 191, 201
TOP_SHARE = 0.05
MIN_K = 10
MIRROR_Z, LAG250_Z, AUTOCORR_FLAG = 2.0, 2.0, 0.3
YEARS_POSITIVE_MIN = 7
EQ_RANK_LEVELS = ["0", "low", "base", "high"]
SIGMA_LOCKED = {12: 0.05, 52: 0.025}


@dataclass
class RankSpec:
    name: str                    # "2a-v1"
    ppy: int                     # 12 monthly, 52 weekly
    side: str                    # "top" | "bottom": the end of the ranking held long
    div: int                     # 10 decile, 5 quintile
    hold: int = 1                # periods a tranche is held (2a V3: 3 overlapping tranches)
    liq_floor: float | None = None   # 2d: med_dv_20_prev floor on the ranked set
    subset_top_half: bool = False    # 2b V3: rank within the top half of a second score
    comparator: str = "ranked"       # "ranked" | "full" (2b V3: the full ranked set, as V1)


# ---------------------------------------------------------------- rebalance dates and fills
def monthly_dates(cal: pd.Index) -> np.ndarray:
    """Indices of the last session of each calendar month on the session calendar."""
    d = pd.DatetimeIndex(cal)
    key = d.year * 100 + d.month
    last = pd.Series(np.arange(len(d))).groupby(key).max()
    return last.to_numpy()


def weekly_session_dates(cal: pd.Index) -> np.ndarray:
    """Indices of the last session of each ISO week (Monday to Sunday) on the session calendar."""
    d = pd.DatetimeIndex(cal)
    iso = d.isocalendar()
    key = iso["year"].to_numpy() * 100 + iso["week"].to_numpy()
    last = pd.Series(np.arange(len(d))).groupby(key).max()
    return last.to_numpy()


def rank_fills(cal: pd.Index, ppy: int, era: tuple[str, str]) -> pd.DataFrame:
    """One row per rebalance date D inside the era: D, the fill session (D + 1 session) and the
    exit session (the session after the next rebalance date). `valid` is False when the exit
    session is after the era's last session (the wave-1 boundary rule) or does not exist."""
    idx_all = monthly_dates(cal) if ppy == 12 else weekly_session_dates(cal)
    in_era, era_last = era_rows(cal, era)
    n = len(cal)
    rows = []
    for p, i in enumerate(idx_all):
        if not in_era[i]:
            continue
        nxt = idx_all[p + 1] if p + 1 < len(idx_all) else None
        F = i + 1
        E = nxt + 1 if nxt is not None else None
        ok = F < n and E is not None and E < n and E <= era_last
        rows.append({"D_idx": int(i), "fill_idx": int(F) if F < n else -1, "exit_idx": int(E) if (E is not None and E < n) else -1,
                     "date": cal[i], "fill_date": cal[F] if F < n else pd.NaT,
                     "exit_date": cal[E] if (E is not None and E < n) else pd.NaT, "valid": bool(ok)})
    df = pd.DataFrame(rows)
    df["year"] = pd.DatetimeIndex(df["fill_date"]).year
    df["month"] = pd.DatetimeIndex(df["fill_date"]).month
    return df


def _last_valid_rows(block: np.ndarray) -> np.ndarray:
    """Last non-NaN value per column of a (rows x cols) block; NaN when none."""
    if block.shape[0] == 0:
        return np.full(block.shape[1], np.nan)
    return pd.DataFrame(block).ffill().iloc[-1].to_numpy()


def holding_returns(A: dict, fills: pd.DataFrame, price: str = "open") -> tuple[np.ndarray, np.ndarray]:
    """Per period and name: the return from the fill-session open to the exit-session open
    (`price="close"`: from the close on D to the close on the next D, the bounce diagnostic).
    A name with no bar at the exit is marked at its last close inside the period (`liq` True);
    a name with no bar at the fill is NaN. Invalid periods are NaN throughout."""
    O, C = A["a_open"], A["a_close"]
    P, N = len(fills), O.shape[1]
    R = np.full((P, N), np.nan)
    liq = np.zeros((P, N), dtype=bool)
    for i, r in enumerate(fills.itertuples(index=False)):
        if not r.valid:
            continue
        if price == "open":
            s0, s1 = O[r.fill_idx], O[r.exit_idx]
            fb = _last_valid_rows(C[r.fill_idx:r.exit_idx])
        else:
            s0, s1 = C[r.D_idx], C[r.exit_idx - 1]
            fb = _last_valid_rows(C[r.D_idx + 1:r.exit_idx - 1])
        end = np.where(np.isnan(s1), fb, s1)
        liq[i] = np.isnan(s1) & ~np.isnan(fb)
        with np.errstate(all="ignore"):
            R[i] = end / s0 - 1.0
    return R, liq


# ---------------------------------------------------------------- baskets
def rank_basket(score: np.ndarray, ranked: np.ndarray, side: str, div: int) -> tuple[np.ndarray, int, int]:
    """Top (or bottom) ceil(n/div) of the ranked set by score, ties at the cutoff included.
    Returns (basket mask, realized k, n). k under MIN_K is a skipped observation (empty basket)."""
    valid = ranked & ~np.isnan(score)
    n = int(valid.sum())
    k0 = int(math.ceil(n / div))
    if k0 < MIN_K:
        return np.zeros_like(ranked), 0, n
    s = np.where(valid, score, np.nan)
    if side == "top":
        order = np.argsort(-s, kind="stable")
        cutoff = s[order[k0 - 1]]
        basket = valid & (s >= cutoff)
    else:
        order = np.argsort(s, kind="stable")
        cutoff = s[order[k0 - 1]]
        basket = valid & (s <= cutoff)
    return basket, int(basket.sum()), n


def ranked_sets(A: dict, cap_mask, fills: pd.DataFrame, score: np.ndarray, spec: RankSpec, score2: np.ndarray | None = None):
    """Per period: the ranked set (eligible, scorable, floored), the formation score row, the
    comparator set and the basket of the actual row and of its mirror."""
    univ = A["in_universe"] if cap_mask is None else (A["in_universe"] & cap_mask[None, :])
    D = fills["D_idx"].to_numpy()
    P, N = len(fills), univ.shape[1]
    sc = score[D]
    elig = univ[D]
    if spec.liq_floor is not None:
        with np.errstate(invalid="ignore"):
            elig = elig & (A["med_dv_20_prev"][D] >= spec.liq_floor)
    ranked_full = elig & ~np.isnan(sc)
    ranked = ranked_full.copy()
    if spec.subset_top_half:
        s2 = score2[D]
        ranked = ranked & ~np.isnan(s2)
        for i in range(P):
            m = ranked[i]
            if m.any():
                med = np.median(s2[i][m])
                ranked[i] = m & (s2[i] >= med)
    comp = ranked_full if spec.comparator == "full" else ranked
    basket = np.zeros((P, N), dtype=bool); mirror = np.zeros((P, N), dtype=bool)
    k = np.zeros(P, dtype=int); n = np.zeros(P, dtype=int)
    other = "bottom" if spec.side == "top" else "top"
    for i in range(P):
        basket[i], k[i], n[i] = rank_basket(sc[i], ranked[i], spec.side, spec.div)
        mirror[i], _, _ = rank_basket(sc[i], ranked[i], other, spec.div)
    return {"ranked": ranked, "comp": comp, "basket": basket, "mirror": mirror, "k": k, "n": n, "score": sc, "D": D}


def _nanmean_rows(R: np.ndarray, mask: np.ndarray) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return np.nanmean(np.where(mask, R, np.nan), axis=1)


def _quintiles(close_row: np.ndarray, ranked_row: np.ndarray) -> np.ndarray:
    """Within-day quintile (1..5) of `close` among the ranked set; 0 outside it."""
    q = np.zeros(len(close_row), dtype=int)
    m = ranked_row & ~np.isnan(close_row)
    n = int(m.sum())
    if n == 0:
        return q
    r = pd.Series(close_row[m]).rank(method="average").to_numpy() / n
    q[m] = np.minimum(5, np.ceil(5 * r)).astype(int)
    return q


def _matched(r: np.ndarray, held: np.ndarray, comp: np.ndarray, q: np.ndarray) -> float:
    held = held & ~np.isnan(r)
    if not held.any():
        return np.nan
    qm = np.full(6, np.nan)
    for qq in range(1, 6):
        m = comp & (q == qq) & ~np.isnan(r)
        if m.any():
            qm[qq] = float(r[m].mean())
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return float(np.nanmean(qm[q[held]]))


def aggregate_periods(fills: pd.DataFrame, R: np.ndarray, liq: np.ndarray, sets: dict, basket: np.ndarray,
                      rt: dict[str, np.ndarray], hold: int, close_at_D: np.ndarray | None = None) -> pd.DataFrame:
    """One row per rebalance date: basket and comparator returns, entering names, turnover, cost
    at each level (entering names pay their round trip; the first period the whole basket) and
    the net difference. `hold` > 1 averages over the live tranches (the 1e construction): the
    tranche formed at t enters against the tranche formed `hold` periods earlier and its cost is
    spread over the live tranches. With `close_at_D` the price-matched comparator is computed."""
    P, N = R.shape
    comp = sets["comp"]
    k = basket.sum(axis=1)
    prev = np.zeros_like(basket)
    if P > hold:
        prev[hold:] = basket[:-hold]
    entering = basket & ~prev
    n_ent = entering.sum(axis=1)
    with np.errstate(all="ignore"):
        tau = np.where(k > 0, n_ent / np.maximum(k, 1), np.nan)
    cost_tr = {lvl: np.where(k > 0, np.nansum(np.where(entering, rt[lvl], 0.0), axis=1) / np.maximum(k, 1), 0.0) for lvl in rt}
    q = None
    if close_at_D is not None:
        q = np.stack([_quintiles(close_at_D[i], comp[i]) for i in range(P)])
    if hold == 1:
        port = _nanmean_rows(R, basket)
        uni = _nanmean_rows(R, comp)
        live = (k > 0).astype(int)
        match = np.array([_matched(R[i], basket[i], comp[i], q[i]) if (q is not None and k[i] > 0) else np.nan for i in range(P)])
        cost = cost_tr
        unfilled = (basket & np.isnan(R)).sum(axis=1)
        liquidated = (basket & liq).sum(axis=1)
    else:
        tr = np.full((P, hold), np.nan); un = np.full((P, hold), np.nan); mt = np.full((P, hold), np.nan)
        for w in range(hold):
            Rw = np.full_like(R, np.nan)
            Rw[:P - w] = R[w:]
            tr[:, w] = _nanmean_rows(Rw, basket)
            un[:, w] = _nanmean_rows(Rw, comp)
            if q is not None:
                mt[:, w] = [_matched(Rw[i], basket[i], comp[i], q[i]) if k[i] > 0 else np.nan for i in range(P)]
        port = np.full(P, np.nan); uni = np.full(P, np.nan); match = np.full(P, np.nan); live = np.zeros(P, dtype=int)
        for t in range(P):
            g, u, m = [], [], []
            for w in range(hold):
                f = t - w
                if f < 0 or np.isnan(tr[f, w]) or np.isnan(un[f, w]):
                    continue
                g.append(tr[f, w]); u.append(un[f, w]); m.append(mt[f, w])
            if g:
                port[t], uni[t], live[t] = float(np.mean(g)), float(np.mean(u)), len(g)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", RuntimeWarning)
                    match[t] = float(np.nanmean(m))
        new_live = ~np.isnan(tr[:, 0])
        cost = {lvl: np.where(live > 0, cost_tr[lvl] * new_live / np.maximum(live, 1), 0.0) for lvl in rt}
        unfilled = (basket & np.isnan(R)).sum(axis=1)
        liquidated = (basket & liq).sum(axis=1)
    df = pd.DataFrame({"date": fills["date"].to_numpy(), "fill_date": fills["fill_date"].to_numpy(), "exit_date": fills["exit_date"].to_numpy(),
                       "year": fills["year"].to_numpy(), "month": fills["month"].to_numpy(),
                       "n": sets["n"], "k": k, "entering": n_ent, "tau": tau, "live": live, "unfilled": unfilled, "liquidated": liquidated,
                       "port": port, "uni": uni, "match": match})
    for lvl in rt:
        df[f"cost_{lvl}"] = cost[lvl]
        df[f"diff_{lvl}"] = port - uni - cost[lvl]
        df[f"mdiff_{lvl}"] = port - match - cost[lvl]
    df["valid"] = ~np.isnan(port) & ~np.isnan(uni) & (live > 0)
    return df


def random_baskets(sets: dict, k: np.ndarray, tau: np.ndarray, hold: int, seed: int) -> np.ndarray:
    """One random-slice draw: each date holds k_t names of the ranked set, keeping a held name
    (from the basket formed `hold` periods earlier) with probability 1 - tau_t, dropping names that
    left the ranked set, trimming uniformly when k falls and refilling uniformly from the unheld
    ranked names. One default_rng(seed) per draw."""
    rng = np.random.default_rng(seed)
    ranked = sets["ranked"]
    P, N = ranked.shape
    B = np.zeros((P, N), dtype=bool)
    for t in range(P):
        kt = int(k[t])
        if kt <= 0:
            continue
        held = (B[t - hold] & ranked[t]) if t - hold >= 0 else np.zeros(N, dtype=bool)
        idx = np.nonzero(held)[0]
        keep = idx[rng.random(len(idx)) >= tau[t]] if len(idx) else idx
        if len(keep) > kt:
            keep = rng.choice(keep, kt, replace=False)
        pool = np.nonzero(ranked[t])[0]
        pool = np.setdiff1d(pool, keep, assume_unique=True)
        need = kt - len(keep)
        fill = rng.choice(pool, min(need, len(pool)), replace=False) if need > 0 else np.array([], dtype=int)
        B[t, keep] = True
        B[t, fill] = True
    return B


# ---------------------------------------------------------------- statistic
def nw_se(d: np.ndarray, L: int) -> float:
    """Newey-West standard error of the mean with Bartlett weights, autocovariances at ddof 0."""
    T = len(d)
    if T < 2:
        return np.nan
    x = d - d.mean()
    s = float((x * x).sum() / T)
    for j in range(1, L + 1):
        if j >= T:
            break
        s += 2.0 * (1.0 - j / (L + 1.0)) * float((x[j:] * x[:-j]).sum() / T)
    return math.sqrt(s / T) if s > 0 else np.nan


def rank_zstats(d: np.ndarray, ppy: int) -> dict:
    d = np.asarray(d, dtype=float)
    d = d[~np.isnan(d)]
    T = len(d)
    out = {"periods": T, "mean_diff_period": np.nan, "se": np.nan, "z_plain": np.nan, "z_nw": np.nan, "z_gate": np.nan,
           "ann_excess": np.nan, "mde80_pp": np.nan}
    if T < 2:
        if T == 1:
            out["mean_diff_period"] = float(d[0]); out["ann_excess"] = ppy * float(d[0])
        return out
    m = float(d.mean())
    se = float(d.std(ddof=1) / math.sqrt(T))
    se_nw = nw_se(d, NW_LAGS[ppy])
    zp = m / se if se > 0 else np.nan
    zn = m / se_nw if (se_nw is not None and se_nw > 0) else np.nan
    out.update({"mean_diff_period": m, "se": se, "z_plain": zp, "z_nw": zn,
                "z_gate": float(np.nanmin([zp, zn])) if not (np.isnan(zp) and np.isnan(zn)) else np.nan,
                "ann_excess": ppy * m, "mde80_pp": ppy * MDE80_MULT * se * 100.0})
    return out


def _ann_path(r: pd.Series, ppy: int, prefix: str) -> dict:
    r = r.dropna()
    if len(r) < 2:
        return {f"ann_ret_{prefix}": np.nan, f"vol_{prefix}": np.nan, f"maxdd_{prefix}": np.nan}
    eq = (1 + r).cumprod()
    return {f"ann_ret_{prefix}": float(eq.iloc[-1] ** (ppy / len(r)) - 1), f"vol_{prefix}": float(r.std(ddof=1) * math.sqrt(ppy)),
            f"maxdd_{prefix}": float((eq / eq.cummax() - 1).min())}


def top_share_rows(d: pd.Series) -> pd.Index:
    """Index labels of the ceil(TOP_SHARE x T) periods with the largest d_t."""
    n = int(math.ceil(TOP_SHARE * len(d)))
    return d.nlargest(n).index if n > 0 else d.index[:0]


def rank_summary_equity(wk: pd.DataFrame, cost: str, ppy: int) -> dict:
    """Statistics of the net difference at one cost level over the valid rows of a period table."""
    v = wk[wk["valid"]]
    d = v[f"diff_{cost}"]
    zs = rank_zstats(d.to_numpy(), ppy)
    k = v["k"].to_numpy(dtype=float)
    tw = float(np.sum(k * d.to_numpy()) / np.sum(k)) if len(v) and np.sum(k) > 0 else np.nan
    top = top_share_rows(d)
    tot = float(d.abs().sum()) if len(v) else 0.0
    turn = v["tau"] / np.maximum(v["live"], 1)
    out = {**zs, "k_median": float(v["k"].median()) if len(v) else np.nan, "n_eligible_median": float(v["n"].median()) if len(v) else np.nan,
           "trade_weighted_mean": tw, "hit_rate": float((d > 0).mean()) if len(v) else np.nan,
           "turnover_oneway_ann": float(turn.mean() * ppy) if len(v) else np.nan,
           "cost_drag_ann": float(v[f"cost_{cost}"].mean() * ppy) if len(v) else np.nan,
           **_ann_path(v["port"] - v[f"cost_{cost}"], ppy, "strat"), **_ann_path(v["uni"], ppy, "uni"),
           "top5pct_share": float(d.loc[top].abs().sum() / tot) if tot > 0 else np.nan,
           "z_wo_top5pct": rank_zstats(d.drop(top).to_numpy(), ppy)["z_gate"],
           "flag_autocorr": bool(abs(zs["z_plain"] - zs["z_nw"]) > AUTOCORR_FLAG) if not np.isnan(zs["z_nw"]) else False,
           "flag_size_concentrated": bool(abs(tw - zs["mean_diff_period"]) > zs["se"]) if not np.isnan(zs["se"]) else False}
    # rename to the schema's names
    out["vol_strat"], out["vol_uni"] = out.pop("vol_strat"), out.pop("vol_uni")
    return out


def period_slices_rank(wk: pd.DataFrame, era_name: str, lane: str = "equity") -> list[tuple[str, np.ndarray]]:
    """('all', mask), one per fill year, the two halves (split on D), without the top 5% of
    periods at base, without January fills and without calendar-2020 fills."""
    d = pd.DatetimeIndex(wk["date"])
    out = [("all", np.ones(len(wk), dtype=bool))]
    for y in sorted(set(wk["year"].dropna().astype(int))):
        out.append((str(y), (wk["year"] == y).to_numpy()))
    split = pd.Timestamp(HALF_SPLIT[lane][era_name])
    out.append(("half1", np.asarray(d < split)))
    out.append(("half2", np.asarray(d >= split)))
    v = wk[wk["valid"]]
    top = top_share_rows(v["diff_base"])
    out.append(("ex_top5pct", ~wk.index.isin(top)))
    out.append(("ex_jan", (wk["month"] != 1).to_numpy()))
    out.append(("ex_2020", (wk["year"] != 2020).to_numpy()))
    return out


def rule4_columns(wk: pd.DataFrame, cost: str, ppy: int, era_name: str) -> dict:
    """The full-era rule-4 quantities at one cost level: halves, years positive, z without 2020,
    the 2020 contribution to z, z without January fills."""
    v = wk[wk["valid"]]
    d = v[f"diff_{cost}"]
    split = pd.Timestamp(HALF_SPLIT["equity"][era_name])
    dd = pd.DatetimeIndex(v["date"])
    h1 = d[np.asarray(dd < split)]; h2 = d[np.asarray(dd >= split)]
    yearly = d.groupby(v["year"]).mean()
    zs = rank_zstats(d.to_numpy(), ppy)
    sd = d.std(ddof=1) if len(d) > 1 else np.nan
    contrib = float(d[v["year"] == 2020].sum() / (sd * math.sqrt(len(d)))) if (sd and sd > 0) else np.nan
    return {"half1_excess": ppy * float(h1.mean()) if len(h1) else np.nan, "half2_excess": ppy * float(h2.mean()) if len(h2) else np.nan,
            "years_positive": int((yearly > 0).sum()), "years_total": int(len(yearly)),
            "z_ex2020": rank_zstats(d[v["year"] != 2020].to_numpy(), ppy)["z_gate"], "z_contrib_2020": contrib,
            "z_ex_jan": rank_zstats(d[v["month"] != 1].to_numpy(), ppy)["z_gate"], "z_all": zs["z_gate"]}


# ---------------------------------------------------------------- the row
def rank_equity(A: dict, cap_mask, spec: RankSpec, score: np.ndarray, era: tuple[str, str], era_name: str,
                score2: np.ndarray | None = None, fills: pd.DataFrame | None = None, R: np.ndarray | None = None,
                liq: np.ndarray | None = None, matched: bool = True) -> dict:
    """The actual row and its mirror as period tables, with the formation sets. `fills`, `R` and
    `liq` can be passed in (built once per lane and frequency)."""
    if fills is None:
        fills = rank_fills(A["cal"], spec.ppy, era)
    if R is None:
        R, liq = holding_returns(A, fills)
    sets = ranked_sets(A, cap_mask, fills, score, spec, score2)
    D = sets["D"]
    rt = {lvl: v.reshape(len(D), -1) for lvl, v in schedule_cost("equity", A["med_dv_20_prev"][D].ravel()).items()}
    close_at_D = A["close"][D] if matched else None
    wk = aggregate_periods(fills, R, liq, sets, sets["basket"], rt, spec.hold, close_at_D)
    mirror = aggregate_periods(fills, R, liq, sets, sets["mirror"], rt, spec.hold)
    return {"fills": fills, "R": R, "liq": liq, "sets": sets, "rt": rt, "periods": wk, "mirror": mirror}


def rank_ladder(sets: dict, R: np.ndarray, fills: pd.DataFrame, ppy: int) -> pd.DataFrame:
    """Decile ladder (1 = highest score) of the one-period excess over the comparator at zero cost."""
    P, N = R.shape
    rows = []
    comp_ret = _nanmean_rows(R, sets["comp"])
    dec = np.zeros((P, N), dtype=int)
    for i in range(P):
        m = sets["ranked"][i] & ~np.isnan(sets["score"][i])
        n = int(m.sum())
        if n < 10:
            continue
        r = pd.Series(-sets["score"][i][m]).rank(method="first").to_numpy() / n
        dec[i, m] = np.minimum(10, np.ceil(10 * r)).astype(int)
    for dd in range(1, 11):
        pr = _nanmean_rows(R, dec == dd)
        diff = pr - comp_ret
        diff = diff[fills["valid"].to_numpy() & ~np.isnan(diff)]
        zs = rank_zstats(diff, ppy)
        rows.append({"decile": dd, "periods": zs["periods"], "ann_excess": zs["ann_excess"], "z_gate": zs["z_gate"], "mean_period": zs["mean_diff_period"]})
    return pd.DataFrame(rows)


def rank_controls_equity(res: dict, spec: RankSpec, A: dict, cap_mask, score: np.ndarray, era: tuple[str, str], era_name: str,
                         score2: np.ndarray | None = None, draws: int = RANDOM_DRAWS, shock_key: str = "shock") -> tuple[dict, pd.DataFrame]:
    """Mirror, random slice (draws), lag 250 and lag 20 placebos, planted controls, price-matched
    comparator, 1a long-avoid overlay, the bounce diagnostic (weekly rows). Returns the control
    dict and the per-draw table."""
    ppy = spec.ppy
    wk, mirror, sets, fills, R, liq, rt = res["periods"], res["mirror"], res["sets"], res["fills"], res["R"], res["liq"], res["rt"]
    v = wk[wk["valid"]]
    act = rank_zstats(v["diff_0"].to_numpy(), ppy)
    act_base = rank_zstats(v["diff_base"].to_numpy(), ppy)
    out: dict = {"actual_z0": act["z_gate"], "actual_ann_excess_0": act["ann_excess"], "actual_z_base": act_base["z_gate"],
                 "actual_ann_excess_base": act_base["ann_excess"], "periods": act["periods"]}
    # mirror slice, long, zero cost
    mv = mirror[mirror["valid"]]
    mz = rank_zstats(mv["diff_0"].to_numpy(), ppy)
    out.update({"mirror_z": mz["z_gate"], "mirror_ann_excess": mz["ann_excess"], "mirror_periods": mz["periods"]})
    # planted controls at zero cost (z_plain shift = X / SE)
    X = PLANTED_BAR_BPS[ppy] / 1e4
    out["planted_bar_bps"] = PLANTED_BAR_BPS[ppy]
    out["planted_bar_shift"] = rank_zstats((v["diff_0"] + X).to_numpy(), ppy)["z_plain"] - act["z_plain"]
    out["planted_50_shift"] = rank_zstats((v["diff_0"] + PLANTED_BPS / 1e4).to_numpy(), ppy)["z_plain"] - act["z_plain"]
    out["planted_bar_expected"] = X / act["se"] if act["se"] else np.nan
    # random slice: count-matched, turnover-matched draws
    k, tau = sets["basket"].sum(axis=1), wk["tau"].fillna(0.0).to_numpy()
    rows = []
    for i in range(draws):
        B = random_baskets(sets, k, tau, spec.hold, RANDOM_SEED + i)
        dfr = aggregate_periods(fills, R, liq, sets, B, rt, spec.hold)
        vr = dfr[dfr["valid"]]
        z0 = rank_zstats(vr["diff_0"].to_numpy(), ppy); zb = rank_zstats(vr["diff_base"].to_numpy(), ppy)
        rows.append({"draw": i, "seed": RANDOM_SEED + i, "periods": z0["periods"], "z0": z0["z_gate"], "ann_excess_0": z0["ann_excess"],
                     "z_base": zb["z_gate"], "ann_excess_base": zb["ann_excess"], "turnover_oneway_ann": float((vr["tau"] / np.maximum(vr["live"], 1)).mean() * ppy) if len(vr) else np.nan})
    rnd = pd.DataFrame(rows)
    if len(rnd):
        ex = rnd["ann_excess_base"].to_numpy()
        out["random_rank"] = int(1 + np.sum(ex < act_base["ann_excess"]))   # ascending rank among itself and the draws
        out["random_pctile_excess"] = float(np.mean(ex < act_base["ann_excess"]))
        out["random_pctile_z"] = float(np.mean(rnd["z_base"].to_numpy() < act_base["z_gate"]))
        out["random_median_z0"] = float(rnd["z0"].median()); out["random_median_ann_excess_0"] = float(rnd["ann_excess_0"].median())
        out["random_engine_check"] = bool(abs(out["random_median_z0"]) <= 0.5 and abs(out["random_median_ann_excess_0"]) * 100 <= 1.0)
        out["random_draws"] = int(len(rnd))
    # lag placebos: the score as of D - lag, ranked set and k as of D
    for lag, key in ((PLACEBO_LAG_LONG, "lag250"), (PLACEBO_LAG, "lag20")):
        sc_l = shift_rows(score, -lag)
        s2_l = shift_rows(score2, -lag) if score2 is not None else None
        pl = rank_equity(A, cap_mask, spec, sc_l, era, era_name, s2_l, fills, R, liq, matched=False)
        pv = pl["periods"][pl["periods"]["valid"]]
        pz = rank_zstats(pv["diff_0"].to_numpy(), ppy)
        out[f"{key}_z0"] = pz["z_gate"]; out[f"{key}_ann_excess"] = pz["ann_excess"]; out[f"{key}_periods"] = pz["periods"]
        if key == "lag250":
            on = v[v["date"].isin(pv["date"])]
            out["actual_on_lag250_dates_z"] = rank_zstats(on["diff_0"].to_numpy(), ppy)["z_gate"]
            out["actual_on_lag250_dates_ann_excess"] = rank_zstats(on["diff_0"].to_numpy(), ppy)["ann_excess"]
    # price-matched comparator at base
    pm = rank_zstats(v["mdiff_base"].to_numpy(), ppy)
    out["price_matched_excess"] = pm["ann_excess"]; out["price_matched_z"] = pm["z_gate"]
    D = sets["D"]
    ratios = []
    for i in range(len(D)):
        b = sets["basket"][i]; c = sets["comp"][i]
        if b.any() and c.any():
            cb, cc = A["close"][D[i]][b], A["close"][D[i]][c]
            ratios.append(float(np.nanmedian(cb) / np.nanmedian(cc)))
    out["price_ratio_top_uni"] = float(np.median(ratios)) if ratios else np.nan
    # 1a long-avoid overlay: names with shock <= -2 on D dropped at formation
    with np.errstate(invalid="ignore"):
        avoid = A[shock_key][D] <= -2.0
    ov = aggregate_periods(fills, R, liq, sets, sets["basket"] & ~avoid, rt, spec.hold)
    ovv = ov[ov["valid"]]
    oz = rank_zstats(ovv["diff_base"].to_numpy(), ppy)
    out.update({"overlay_1a_z_base": oz["z_gate"], "overlay_1a_ann_excess_base": oz["ann_excess"], "overlay_1a_dropped_mean": float((sets["basket"] & avoid).sum(axis=1).mean())})
    # bounce diagnostic (weekly rows): signal-close fill against the next-open fill
    if ppy == 52:
        Rc, liqc = holding_returns(A, fills, price="close")
        cl = aggregate_periods(fills, Rc, liqc, sets, sets["basket"], rt, spec.hold)
        cv = cl[cl["valid"]]
        cz = rank_zstats(cv["diff_0"].to_numpy(), ppy)
        out["close_fill_mean_period"] = cz["mean_diff_period"]; out["close_fill_z0"] = cz["z_gate"]
        gap = (cz["mean_diff_period"] - act["mean_diff_period"]) * 1e4 if not np.isnan(cz["mean_diff_period"]) else np.nan
        out["bounce_gap_bps"] = gap; out["bounce_flag"] = bool(gap >= 20.0) if not np.isnan(gap) else False
    out["skipped_periods"] = int((wk["k"] == 0).sum()); out["unfilled_total"] = int(wk["unfilled"].sum()); out["liquidated_total"] = int(wk["liquidated"].sum())
    return out, rnd


def rank_report_equity(res: dict, ctl: dict, spec: RankSpec, universe: str, era_name: str, lane: str = "equity") -> pd.DataFrame:
    """results_<tag>.csv: one row per cost level and period slice with the schema's columns; the
    control columns are the full-era values repeated on every row."""
    wk = res["periods"]; ppy = spec.ppy
    sig, variant = spec.name.split("-", 1)
    ctl_cols = {c: ctl.get(c, np.nan) for c in ("mirror_z", "mirror_ann_excess", "price_matched_excess", "price_ratio_top_uni", "random_pctile_z",
                                                "random_pctile_excess", "random_rank", "lag250_z0", "lag250_ann_excess", "lag250_periods",
                                                "actual_on_lag250_dates_z", "lag20_z0", "planted_bar_shift", "planted_50_shift")}
    rows = []
    for cost in EQ_RANK_LEVELS:
        r4 = rule4_columns(wk, cost, ppy, era_name)
        for pname, m in period_slices_rank(wk, era_name, lane):
            sub = wk[m]
            if sub["valid"].sum() == 0 and pname != "all":
                continue
            s = rank_summary_equity(sub, cost, ppy)
            rows.append({"signal": sig, "variant": variant, "lane": lane, "universe": universe, "era": era_name, "cost": cost, "period": pname,
                         **{c: s[c] for c in ("periods", "k_median", "n_eligible_median", "mean_diff_period", "se", "z_plain", "z_nw", "z_gate", "ann_excess",
                                               "mde80_pp", "trade_weighted_mean", "hit_rate", "turnover_oneway_ann", "cost_drag_ann", "ann_ret_strat", "ann_ret_uni",
                                               "vol_strat", "vol_uni", "maxdd_strat", "maxdd_uni", "top5pct_share", "z_wo_top5pct")},
                         **{c: r4[c] for c in ("half1_excess", "half2_excess", "years_positive", "z_ex2020", "z_contrib_2020", "z_ex_jan")},
                         **ctl_cols, "family_n": FAMILY_N, "p_sidak": np.nan, "verdict": ""})
    return pd.DataFrame(rows)


def p_one_sided(z: float) -> float:
    return float(0.5 * math.erfc(z / math.sqrt(2))) if not np.isnan(z) else np.nan


def p_sidak(p: float, n: int = FAMILY_N) -> float:
    return float(1 - (1 - p) ** n) if not np.isnan(p) else np.nan


def verdict_rank(row: dict, universe: str, ppy: int) -> str:
    """The pre-registered verdict algorithm on a dev row (the 'all' row at base cost with the
    high-cost net and the control columns merged in); the first rule that fires is the verdict."""
    T = row["periods"]
    if T < RANK_MIN_PERIODS["dev"][ppy]:
        return "insufficient"
    net = row["ann_excess"] * 100; net_high = row["ann_excess_high"] * 100
    if not (row["z_gate"] >= Z_GATE_DEV and net >= NET_PP_MIN and net_high > 0):
        return f"null (underpowered below {row['mde80_pp']:.0f} pp)" if row["mde80_pp"] > MDE80_UNDERPOWERED_PP else "null"
    if row["random_rank"] < RANDOM_RANK_MIN:
        return "null"
    if row["mirror_z"] >= MIRROR_Z:
        return "artifact"
    sign = np.sign(row["ann_excess"])
    conds = [row["years_positive"] >= YEARS_POSITIVE_MIN,
             np.sign(row["half1_excess"]) == sign, np.sign(row["half2_excess"]) == sign,
             np.sign(row["z_wo_top5pct"]) == sign, np.sign(row["z_ex_jan"]) == sign,
             row["z_ex2020"] >= Z_EX2020,
             np.sign(row["price_matched_excess"]) == sign and abs(row["price_matched_excess"]) >= 0.5 * abs(row["ann_excess"])]
    if not all(bool(c) for c in conds):
        return "artifact"
    if row["lag250_z0"] >= LAG250_Z:
        return "characteristic"
    return "confirm" if universe == "uncapped" else "diagnostic-pass"


def verdict_rank_confirm(dev: dict, conf: dict, ppy: int) -> str:
    """The confirm gate for a dev `confirm` row. `graduate` is not awarded in this wave (C8)."""
    if conf["periods"] < RANK_MIN_PERIODS["confirm"][ppy]:
        return "insufficient"
    pooled = (dev["z_gate"] * math.sqrt(dev["periods"]) + conf["z_gate"] * math.sqrt(conf["periods"])) / math.sqrt(dev["periods"] + conf["periods"])
    ok = (np.sign(conf["ann_excess"]) == np.sign(dev["ann_excess"]) and conf["z_gate"] >= Z_GATE_CONFIRM and pooled >= Z_POOLED_MIN
          and conf["years_positive"] >= 2)
    return "confirm (gate passed, C8 pending)" if ok else "fails confirm"

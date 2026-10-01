"""The v1 mean-reversion rule (spec/05), ported verbatim from `experiments/screen_free_data.py`.

Kept as its own module so the refactor can be proven: `python -m experiments.screen regress`
runs this through the new data layer and compares every headline cell with the original
script run on the same data. Nothing in here is used by the wave-1 signals, whose event
mode (fixed horizon, no stop, no target) is in `engine.py`.
"""
from __future__ import annotations

import math
import warnings

import numpy as np
import pandas as pd

from experiments.screen.data import CR_ANN, EQ_ANN, shift_rows

# locked parameters (spec/05, spec/06)
K_SHOCK = 2.0
TIME_STOP_SESSIONS = 10
STOP_RANGE_MULT = 1.5
ORDER_USD = 10_000.0
FWD_H = 5
COST_LEVELS_BPS = [0, 50, 100]
EQ_SPREAD_FLOOR = 0.0025
EQ_TICK = 0.01
CR_TAKER = 0.0010
CR_SPREAD_FLOOR_TOP20 = 0.0005
CR_SPREAD_FLOOR_OTHER = 0.0015
FILLS = ["close", "next_open", "next_close"]
W = 16  # sessions scanned after the fill session


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
    """Run the v1 rule for one fill convention. Returns one row per candidate (filled or not)."""
    O, H, L, C = A["a_open"], A["a_high"], A["a_low"], A["a_close"]
    if A["lane"] == "crypto" and fill == "next_open" and "o1" in A:
        O = A["o1"]
    n_sess, n_tk = C.shape
    univ = A["in_universe"] if cap_mask is None else (A["in_universe"] & cap_mask[None, :])
    cand = univ & (A["shock"] <= -K_SHOCK)
    off = 0 if fill == "close" else 1
    si_all, tj_all = np.nonzero(cand)
    order = np.lexsort((tj_all, si_all))
    si_all, tj_all = si_all[order], tj_all[order]
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
    idx = F[:, None] + np.arange(1, W + 1)[None, :]
    inb = idx < n_sess
    idxc = np.minimum(idx, n_sess - 1)
    Ow, Hw, Lw, Cw = (X[idxc, tj[:, None]] for X in (O, H, L, C))
    valid = inb & ~np.isnan(Cw) & ~np.isnan(Ow)
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
        if fill == "close":
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
    open_still = ~done
    if open_still.any():
        lastk = np.where(valid, np.arange(W)[None, :], -1).max(axis=1)
        has = open_still & (lastk >= 0)
        exit_k[has] = lastk[has]; exit_type[has] = "truncated"; exit_px[has] = Cw[has, lastk[has]]
        none = open_still & (lastk < 0)
        unfilled |= none
    filled = ~unfilled
    keep = np.ones(n, dtype=bool)
    exit_sess = F + 1 + exit_k
    last_exit: dict[int, int] = {}
    for i in range(n):
        if not filled[i]:
            continue
        t = tj[i]
        le = last_exit.get(t, -1)
        if si[i] < le:
            keep[i] = False
            continue
        last_exit[t] = exit_sess[i]
    filled &= keep
    gross = np.where(filled, exit_px / entry - 1.0, np.nan)
    if fill == "close":
        P = C; base_off = 0
    elif fill == "next_open":
        P = O; base_off = 1
    else:
        P = C; base_off = 1
    fwd_all = shift_rows(P, base_off + FWD_H) / shift_rows(P, base_off) - 1.0
    um = np.where(univ, fwd_all, np.nan)
    with np.errstate(all="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # days with an empty universe are NaN
        uni_fwd = np.nanmean(um, axis=1)
        uni_n = np.sum(~np.isnan(um), axis=1)
    fwd5 = fwd_all[si, tj]
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


def _se(daily: pd.Series) -> tuple[float, float]:
    daily = daily.dropna()
    if len(daily) < 2:
        return np.nan, np.nan
    return float(daily.mean()), float(daily.std(ddof=1) / math.sqrt(len(daily)))


def summarize(tr: pd.DataFrame, cost_bps) -> dict:
    per_trade = cost_bps in ("spec", "tier")
    c = tr["cost_" + cost_bps] if per_trade else cost_bps / 1e4
    f = tr[tr["filled"]].copy()
    f["net"] = f["gross"] - (c[tr["filled"]] if per_trade else c)
    f["net_minus_bench"] = f["net"] - f["bench"]
    cand = tr.copy()
    cand["fwd5_net_excess"] = cand["fwd5"] - cand["uni_fwd5"] - c
    d_net = f.groupby("signal_date")["net_minus_bench"].mean()
    d_f5 = cand.dropna(subset=["fwd5_net_excess"]).groupby("signal_date")["fwd5_net_excess"].mean()
    z_net, nd_net = _z(d_net)
    z_f5, nd_f5 = _z(d_f5)
    dm_net, se_net = _se(d_net)
    dm_f5, se_f5 = _se(d_f5)
    return {
        "daymean_net_minus_bench": dm_net, "se_net": se_net, "daymean_fwd5_excess": dm_f5, "se_fwd5": se_f5,
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


def headline_markdown(res: pd.DataFrame) -> str:
    lines = []
    fmt = lambda x: "n/a" if pd.isna(x) else f"{x * 1e4:+.0f}"  # noqa: E731
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


def run_v1(A: dict, market: str, universe: str, cap_mask) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    trades = {fill: simulate(A, fill, cap_mask) for fill in FILLS}
    return report(trades, market, universe), trades

"""Extreme-movers counts and lift study (proposal section 4; pre-registration
"Extreme-movers counts study"). Hypothesis material, not a result.

Event: for horizon h, the move starting on session D has ratio_h = close_{D+h-1} / close_{D-1}
(adjusted closes). The name must be universe-eligible on D-1. A name counts once per
calendar year (year of D) per threshold. Lifts: for the 63-session 5x group, the within-day
percentile rank of each as-of feature at D-1 among the universe on D-1, taken at the first
qualifying D per name-year (the same unit as the counts).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from experiments.screen.data import shift_rows
from experiments.screen.engine import era_rows

UP = {1: 2.0, 21: 3.0, 63: 5.0, 252: 10.0}
DOWN = {1: 0.5, 21: 1.0 / 3.0, 63: 0.2, 252: 0.1}
LIFT_H = 63
LIFT_GROUPS = {"up5x63": (5.0, True), "down80_63": (0.2, False)}   # (threshold, up?)
LIFT_FEATURES = ["close", "med_dv_20_prev", "rvol_20", "close_to_high_250", "ret_20", "ret_60",
                 "vol_pctl_250", "zscore_20", "shock", "cap"]


def _events(A: dict, univ: np.ndarray, in_era: np.ndarray, era_last: int, h: int, thr: float, up: bool) -> np.ndarray:
    C = A["a_close"]
    with np.errstate(all="ignore"):
        ratio = shift_rows(C, h - 1) / shift_rows(C, -1)
    elig_prev = shift_rows(univ.astype(float), -1) == 1.0
    ok_rows = in_era & (np.arange(C.shape[0]) + h - 1 <= era_last)
    with np.errstate(invalid="ignore"):
        hit = (ratio >= thr) if up else (ratio <= thr)
    return hit & elig_prev & ok_rows[:, None]


def counts(A: dict, cap_mask, era: tuple[str, str], universe: str) -> pd.DataFrame:
    univ = A["in_universe"] if cap_mask is None else (A["in_universe"] & cap_mask[None, :])
    in_era, era_last = era_rows(A["cal"], era)
    years = pd.DatetimeIndex(A["cal"]).year
    rows = []
    for kind, table in (("up", UP), ("down", DOWN)):
        for h, thr in table.items():
            E = _events(A, univ, in_era, era_last, h, thr, kind == "up")
            for y in sorted(set(years[in_era])):
                m = (years == y) & in_era
                rows.append({"universe": universe, "year": int(y), "kind": kind, "horizon": h, "threshold": thr,
                             "names": int(E[m].any(axis=0).sum()), "event_days": int(E[m].sum()),
                             "names_eligible": int(univ[m].any(axis=0).sum()),
                             "label": f"{'x' if kind == 'up' else '-'}{thr:.3g}/{h}d"})
    df = pd.DataFrame(rows)
    df["rate"] = df["names"] / df["names_eligible"].replace(0, np.nan)
    return df


def _pctl_within_day(M: np.ndarray, univ: np.ndarray) -> np.ndarray:
    X = pd.DataFrame(np.where(univ, M, np.nan))
    return X.rank(axis=1, pct=True).to_numpy()


def lifts(A: dict, cap_mask, era: tuple[str, str], universe: str) -> pd.DataFrame:
    return pd.concat([_lifts_group(A, cap_mask, era, universe, g) for g in LIFT_GROUPS], ignore_index=True)


def _lifts_group(A: dict, cap_mask, era: tuple[str, str], universe: str, group: str) -> pd.DataFrame:
    thr, up = LIFT_GROUPS[group]
    univ = A["in_universe"] if cap_mask is None else (A["in_universe"] & cap_mask[None, :])
    in_era, era_last = era_rows(A["cal"], era)
    E = _events(A, univ, in_era, era_last, LIFT_H, thr, up)
    years = pd.DatetimeIndex(A["cal"]).year
    # first qualifying D per name-year
    first = np.zeros_like(E)
    for y in sorted(set(years[in_era])):
        rows = np.nonzero(years == y)[0]
        sub = E[rows]
        has = sub.any(axis=0)
        fi = sub.argmax(axis=0)
        first[rows[fi[has]], np.nonzero(has)[0]] = True
    di, tj = np.nonzero(first)
    prev = di - 1
    out = []
    for f in LIFT_FEATURES:
        if f == "cap":
            if "cap" not in A:
                continue
            M = np.broadcast_to(A["cap"][None, :], univ.shape)
        else:
            M = A[f]
        P = _pctl_within_day(M, univ)
        p = P[prev, tj]
        p = p[~np.isnan(p)]
        n = len(p)
        out.append({"universe": universe, "group": group, "feature": f, "events": int(n),
                    "share_top_quintile": float((p >= 0.8).mean()) if n else np.nan,
                    "share_bottom_quintile": float((p <= 0.2).mean()) if n else np.nan,
                    "lift_top": float((p >= 0.8).mean() / 0.2) if n else np.nan,
                    "lift_bottom": float((p <= 0.2).mean() / 0.2) if n else np.nan,
                    "median_pctl": float(np.median(p)) if n else np.nan})
    return pd.DataFrame(out)


def counts_markdown(df: pd.DataFrame) -> str:
    lines = []
    for uni, g in df.groupby("universe", sort=False):
        labels = list(dict.fromkeys(g["label"]))
        lines.append(f"\n**{uni}: names per year (eligible on D−1) at each threshold; names eligible that year in the last column**\n")
        lines.append("| year | " + " | ".join(labels) + " | eligible |")
        lines.append("|" + "---|" * (len(labels) + 2))
        for y, gy in g.groupby("year"):
            cells = [str(int(gy.loc[gy["label"] == lab, "names"].iloc[0])) for lab in labels]
            lines.append(f"| {y} | " + " | ".join(cells) + f" | {int(gy['names_eligible'].iloc[0])} |")
        tot = g.groupby("label", sort=False)["names"].sum()
        lines.append("| total | " + " | ".join(str(int(tot[lab])) for lab in labels) + " | |")
    return "\n".join(lines)


def lifts_markdown(df: pd.DataFrame) -> str:
    lines = []
    names = {"up5x63": "5× over 63 sessions", "down80_63": "−80% over 63 sessions"}
    for (uni, grp), g in df.groupby(["universe", "group"], sort=False):
        n = int(g["events"].max()) if len(g) else 0
        lines.append(f"\n**{uni}: {names[grp]}, {n} name-years; within-day percentile of the feature at D−1 among the universe on D−1**\n")
        lines.append("| feature | lift top quintile | lift bottom quintile | median percentile | n |")
        lines.append("|---|---|---|---|---|")
        for _, r in g.iterrows():
            lines.append(f"| {r['feature']} | {r['lift_top']:.2f} | {r['lift_bottom']:.2f} | {r['median_pctl']:.2f} | {int(r['events'])} |")
    return "\n".join(lines)

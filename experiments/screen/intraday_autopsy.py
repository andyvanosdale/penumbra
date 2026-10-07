"""i8, autopsy intraday (research_log/2026-10-07-intraday-wave.md, "Autopsy, intraday").

Pass 1: for the one-session 2x movers and -50% movers of the dev era (adjusted daily closes,
universe-eligible on D-1, first qualifying D per name-year), the lift ratios of four intraday
features at D-1 among the universe-eligible names with the feature on D-1. Hypothesis material.

Pass 2: the locked selection (top three features by max lift >= 1.5 per group, from the
`uncapped` table) becomes fixed rules: a name is a candidate on D when the feature's within-day
percentile among the universe-eligible names with the feature on D is >= 0.8 (top) or <= 0.2
(bottom); fill at 09:35 on D+1, decision the same-session close. In-sample in dev by
construction; only the confirm era is evidence.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from experiments.screen import engine
from experiments.screen.data import shift_rows

GROUPS = {"up2x1": (2.0, True), "down50_1": (0.5, False)}      # ratio_1 threshold, up?
GROUP_DIRECTION = {"up2x1": "long", "down50_1": "short"}
FEATURES = ["fhh_ret", "fhh_vol_share", "close_loc", "late_vol_share"]
LIFT_MIN = 1.5
MAX_PER_DIRECTION = 3
ENTRY = "09:35"
HORIZON = "close"


def features(I: dict) -> dict[str, np.ndarray]:
    """The four intraday features of a session (row D holds session D's)."""
    with np.errstate(all="ignore"):
        rng = I["hi_rth"] - I["lo_rth"]
        return {"fhh_ret": I["c0955"] / I["o0930"] - 1.0,
                "fhh_vol_share": np.where(I["v_rth"] > 0, I["v_fhh"] / I["v_rth"], np.nan),
                "close_loc": np.where(rng > 0, (I["c_last"] - I["lo_rth"]) / rng, np.nan),
                "late_vol_share": np.where(I["v_rth"] > 0, I["v_late"] / I["v_rth"], np.nan)}


def pctl_within_day(M: np.ndarray, univ: np.ndarray) -> np.ndarray:
    X = pd.DataFrame(np.where(univ & ~np.isnan(M), M, np.nan))
    return X.rank(axis=1, pct=True).to_numpy()


def mover_events(A: dict, univ: np.ndarray, era: tuple[str, str], group: str) -> np.ndarray:
    """First qualifying D per name-year: ratio_1 = a_close_D / a_close_{D-1} meets the group's threshold,
    name universe-eligible on D-1, D in the era."""
    thr, up = GROUPS[group]
    C = A["a_close"]
    in_era, _ = engine.era_rows(A["cal"], era)
    with np.errstate(all="ignore"):
        ratio = C / shift_rows(C, -1)
    elig_prev = shift_rows(univ.astype(float), -1) == 1.0
    with np.errstate(invalid="ignore"):
        hit = (ratio >= thr) if up else (ratio <= thr)
    E = hit & elig_prev & in_era[:, None]
    years = pd.DatetimeIndex(A["cal"]).year
    first = np.zeros_like(E)
    for y in sorted(set(years[in_era])):
        rows = np.nonzero(years == y)[0]
        sub = E[rows]
        has = sub.any(axis=0)
        fi = sub.argmax(axis=0)
        first[rows[fi[has]], np.nonzero(has)[0]] = True
    return first


def counts(A: dict, univ: np.ndarray, era: tuple[str, str], universe: str) -> pd.DataFrame:
    in_era, _ = engine.era_rows(A["cal"], era)
    years = pd.DatetimeIndex(A["cal"]).year
    rows = []
    for group in GROUPS:
        E = mover_events(A, univ, era, group)
        for y in sorted(set(years[in_era])):
            m = (years == y) & in_era
            rows.append({"universe": universe, "group": group, "year": int(y), "names": int(E[m].any(axis=0).sum()),
                         "names_eligible": int(univ[m].any(axis=0).sum())})
    return pd.DataFrame(rows)


def lifts(A: dict, I: dict, univ: np.ndarray, era: tuple[str, str], universe: str) -> pd.DataFrame:
    """Lift ratios of each feature at D-1 among the universe on D-1 (names with the feature), per group."""
    F = features(I)
    out = []
    for group in GROUPS:
        E = mover_events(A, univ, era, group)
        di, tj = np.nonzero(E)
        prev = di - 1
        ok = prev >= 0
        di, tj, prev = di[ok], tj[ok], prev[ok]
        for f in FEATURES:
            P = pctl_within_day(F[f], univ)
            p = P[prev, tj]
            p = p[~np.isnan(p)]
            n = len(p)
            out.append({"universe": universe, "group": group, "feature": f, "events": int(n), "events_total": int(len(di)),
                        "share_top_quintile": float((p >= 0.8).mean()) if n else np.nan,
                        "share_bottom_quintile": float((p <= 0.2).mean()) if n else np.nan,
                        "lift_top": float((p >= 0.8).mean() / 0.2) if n else np.nan,
                        "lift_bottom": float((p <= 0.2).mean() / 0.2) if n else np.nan,
                        "median_pctl": float(np.median(p)) if n else np.nan})
    return pd.DataFrame(out)


def select_features(lift_table: pd.DataFrame, universe: str, group: str) -> list[dict]:
    g = lift_table[(lift_table["universe"] == universe) & (lift_table["group"] == group)].copy()
    g["lift"] = g[["lift_top", "lift_bottom"]].max(axis=1)
    g["side"] = np.where(g["lift_top"] >= g["lift_bottom"], "top", "bottom")
    g = g[g["lift"] >= LIFT_MIN].sort_values(["lift", "events", "feature"], ascending=[False, False, True])
    return [{"feature": r["feature"], "side": r["side"], "lift": float(r["lift"]), "events": int(r["events"])}
            for _, r in g.head(MAX_PER_DIRECTION).iterrows()]


def rule_name(group: str, feature: str) -> str:
    return f"i8-{'up' if group == 'up2x1' else 'down'}-{feature}"


def rule_matrix(A: dict, I: dict, feature: str, side: str, univ: np.ndarray) -> np.ndarray:
    """Candidates on the fill session F = D+1: the feature's within-day percentile on D among the
    universe-eligible names with the feature on D in the selected quintile."""
    P = pctl_within_day(features(I)[feature], univ)
    with np.errstate(invalid="ignore"):
        on_D = (P >= 0.8) if side == "top" else (P <= 0.2)
    return shift_rows(on_D.astype(float), -1) == 1.0


def extra_metrics(A: dict, I: dict, tr: pd.DataFrame, elig: np.ndarray, era: tuple[str, str], group: str) -> dict:
    """Match rate per fill session, the hit rate for the original one-session move among traded candidates
    (a_close_F / a_close_{F-1}), and the universe base rate of the same move."""
    thr, up = GROUPS[group]
    in_era, _ = engine.era_rows(A["cal"], era)
    rows = in_era & I["fill_session"]
    n_elig = elig.sum(axis=1).astype(float)
    cand_per_day = tr.groupby("signal_date").size().reindex(A["cal"][rows], fill_value=0).to_numpy()
    with np.errstate(all="ignore"):
        match = np.where(n_elig[rows] > 0, cand_per_day / n_elig[rows], np.nan)
        ratio = A["a_close"] / shift_rows(A["a_close"], -1)
    f = tr[tr["traded"]]
    idx_r = A["cal"].get_indexer(pd.DatetimeIndex(f["signal_date"]))
    idx_c = A["tickers"].get_indexer(f["ticker"])
    own = ratio[idx_r, idx_c]
    hit = (own >= thr) if up else (own <= thr)
    with np.errstate(invalid="ignore"):
        m = ((ratio >= thr) if up else (ratio <= thr)) & elig & rows[:, None]
    denom = (elig & ~np.isnan(ratio) & rows[:, None]).sum(axis=1)
    with np.errstate(all="ignore"):
        base = np.where(denom > 0, m.sum(axis=1) / denom, np.nan)
    br = float(np.nanmean(base)) if np.isfinite(base).any() else np.nan
    return {"match_rate_per_day": float(np.nanmean(match)) if np.isfinite(match).any() else np.nan,
            "hits": int(np.nansum(hit)), "hit_original_move": float(np.nanmean(hit)) if len(f) else np.nan,
            "universe_base_rate": br, "lift_realized": float(np.nanmean(hit) / br) if len(f) and br and br > 0 else np.nan}


def counts_markdown(df: pd.DataFrame) -> str:
    lines = []
    for uni, g in df.groupby("universe", sort=False):
        lines.append(f"\n**{uni}: one-session movers per year (eligible on D−1); names eligible that year in the last column**\n")
        lines.append("| year | ×2 / 1 session | −50% / 1 session | eligible |")
        lines.append("|---|---|---|---|")
        for y, gy in g.groupby("year"):
            up = int(gy.loc[gy["group"] == "up2x1", "names"].iloc[0]); dn = int(gy.loc[gy["group"] == "down50_1", "names"].iloc[0])
            lines.append(f"| {y} | {up} | {dn} | {int(gy['names_eligible'].iloc[0])} |")
        tot = g.groupby("group")["names"].sum()
        lines.append(f"| total | {int(tot.get('up2x1', 0))} | {int(tot.get('down50_1', 0))} | |")
    return "\n".join(lines)


def lifts_markdown(df: pd.DataFrame) -> str:
    lines = []
    names = {"up2x1": "×2 in one session", "down50_1": "−50% in one session"}
    for (uni, grp), g in df.groupby(["universe", "group"], sort=False):
        n = int(g["events_total"].max()) if len(g) else 0
        lines.append(f"\n**{uni}: {names[grp]}, {n} name-years; within-day percentile of the intraday feature at D−1 among the universe on D−1**\n")
        lines.append("| feature | lift top quintile | lift bottom quintile | median percentile | n |")
        lines.append("|---|---|---|---|---|")
        for _, r in g.iterrows():
            lines.append(f"| {r['feature']} | {r['lift_top']:.2f} | {r['lift_bottom']:.2f} | {r['median_pctl']:.2f} | {int(r['events'])} |")
    return "\n".join(lines)

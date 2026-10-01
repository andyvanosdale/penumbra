"""Autopsy to rule (pre-registration amendment A2): the top-lift features of the extreme-movers
study turned into fixed-threshold prospective rules.

Selection reads the committed lift table (dev era). A rule fires on D when the feature's
within-day percentile among the universe on D is >= 0.8 (lift from the top quintile) or
<= 0.2 (bottom quintile): the same rank the lift used, with data through D's close. The
rules are run through the event engine like any catalog signal. A dev result here is
in-sample by construction (the features were chosen on the dev era); only the confirm era
is evidence.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from experiments.screen import engine
from experiments.screen.movers import _pctl_within_day

LIFT_MIN = 1.5
MAX_PER_DIRECTION = 3
EXCLUDED = {"cap"}          # today's cap is not an as-of feature
GROUP_DIRECTION = {"up5x63": "long", "down80_63": "short"}
GROUP_MOVE = {"up5x63": ("ge", 4.0), "down80_63": ("le", -0.8)}   # the original move as a 63-session return
DECISION_H = 63


def select_features(lifts: pd.DataFrame, universe: str, group: str) -> list[dict]:
    """The locked selection: top three by max(lift_top, lift_bottom) >= 1.5, cap excluded,
    ties by event count then name. Returns [{feature, side, lift, events}]."""
    g = lifts[(lifts["universe"] == universe) & (lifts["group"] == group) & ~lifts["feature"].isin(EXCLUDED)].copy()
    g["lift"] = g[["lift_top", "lift_bottom"]].max(axis=1)
    g["side"] = np.where(g["lift_top"] >= g["lift_bottom"], "top", "bottom")
    g = g[g["lift"] >= LIFT_MIN].sort_values(["lift", "events", "feature"], ascending=[False, False, True])
    return [{"feature": r["feature"], "side": r["side"], "lift": float(r["lift"]), "events": int(r["events"])}
            for _, r in g.head(MAX_PER_DIRECTION).iterrows()]


def rule_matrix(A: dict, feature: str, side: str, cap_mask) -> np.ndarray:
    """Candidate matrix: universe-eligible on D and the feature's within-day percentile among
    the universe on D in the selected quintile."""
    univ = A["in_universe"] if cap_mask is None else (A["in_universe"] & cap_mask[None, :])
    P = _pctl_within_day(A[feature], univ)
    with np.errstate(invalid="ignore"):
        return (P >= 0.8) if side == "top" else (P <= 0.2)


def rule_name(group: str, feature: str) -> str:
    return f"a2r-{'up' if group == 'up5x63' else 'down'}-{feature}"


def extra_metrics(A: dict, tr: pd.DataFrame, cap_mask, era: tuple[str, str], group: str) -> dict:
    """Match rate per day, hit rate for the original move among traded candidates, and the
    universe base rate of the same move (mean over era sessions)."""
    univ = A["in_universe"] if cap_mask is None else (A["in_universe"] & cap_mask[None, :])
    in_era, era_last = era_rows = engine.era_rows(A["cal"], era)
    n_univ = univ.sum(axis=1).astype(float)
    cand_per_day = tr.groupby("signal_date").size().reindex(A["cal"][in_era], fill_value=0).to_numpy()
    with np.errstate(all="ignore"):
        match = np.where(n_univ[in_era] > 0, cand_per_day / n_univ[in_era], np.nan)
    op, thr = GROUP_MOVE[group]
    f = tr[tr["traded"] & tr["fwd_63"].notna()]
    own = f["fwd_63"]
    hit = (own >= thr) if op == "ge" else (own <= thr)
    # universe base rate: share of the universe on D whose 63-session open-to-open return from D+1 meets the move
    P, off = engine._fill_prices(A, "next_open")
    with np.errstate(all="ignore"):
        fwd = engine.shift_rows(P, off + DECISION_H) / engine.shift_rows(P, off) - 1.0
    ok_rows = in_era & (np.arange(len(A["cal"])) + off + DECISION_H <= era_last)
    m = (fwd >= thr) if op == "ge" else (fwd <= thr)
    m = m & univ & ok_rows[:, None]
    denom = (univ & ~np.isnan(fwd) & ok_rows[:, None]).sum(axis=1)
    with np.errstate(all="ignore"):
        base = np.where(denom > 0, m.sum(axis=1) / denom, np.nan)
    return {"match_rate_per_day": float(np.nanmean(match)), "hit_original_move": float(hit.mean()) if len(f) else np.nan,
            "hits": int(hit.sum()), "universe_base_rate": float(np.nanmean(base)),
            "lift_realized": float(hit.mean() / np.nanmean(base)) if len(f) and np.nanmean(base) > 0 else np.nan}

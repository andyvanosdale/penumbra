"""1c Slide-cohort momentum, short / long-avoid leg: zscore_20 <= -2, |shock| < 1 and top-half
250-session dollar-volume percentile (spec/04 vol_pctl_250 >= 0.5). 21-session time stop."""
from __future__ import annotations

import numpy as np

NAME, MODE, DIRECTION, HORIZON = "1c-short", "event", "short", 21
UNIVERSES = ["smallcap", "uncapped", "crypto"]
Z_K = 2.0
SHOCK_MAX = 1.0
VOL_PCTL_MIN = 0.5


def candidates(A: dict) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        return (A["zscore_20"] <= -Z_K) & (np.abs(A["shock"]) < SHOCK_MAX) & (A["vol_pctl_250"] >= VOL_PCTL_MIN)

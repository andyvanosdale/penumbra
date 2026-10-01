"""1c Slide-cohort momentum, long leg (the mirror winners cohort): zscore_20 >= +2 and
|shock| < 1 (the catalog's long leg carries no volume condition). 21-session time stop."""
from __future__ import annotations

import numpy as np

NAME, MODE, DIRECTION, HORIZON = "1c-long", "event", "long", 21
UNIVERSES = ["smallcap", "uncapped", "crypto"]
Z_K = 2.0
SHOCK_MAX = 1.0


def candidates(A: dict) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        return (A["zscore_20"] >= Z_K) & (np.abs(A["shock"]) < SHOCK_MAX)

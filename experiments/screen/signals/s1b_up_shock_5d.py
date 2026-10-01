"""1b Up-shock continuation (long), 5-session variant: shock >= +2.0 on volume >= 2x the
median of the 20 volumes ending D-1."""
from __future__ import annotations

import numpy as np

NAME, MODE, DIRECTION, HORIZON = "1b-5d", "event", "long", 5
UNIVERSES = ["smallcap", "uncapped", "crypto"]
K_SHOCK = 2.0
VOL_MULT = 2.0


def candidates(A: dict) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        return (A["shock"] >= K_SHOCK) & (A["vol_ratio_20"] >= VOL_MULT)

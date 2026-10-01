"""1a Post-shock continuation (short / long-avoid): shock <= -2.0 on D, 5-session time stop."""
from __future__ import annotations

import numpy as np

NAME, MODE, DIRECTION, HORIZON = "1a", "event", "short", 5
UNIVERSES = ["smallcap", "uncapped", "crypto"]
K_SHOCK = 2.0


def candidates(A: dict) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        return A["shock"] <= -K_SHOCK

"""The v1 candidate rule (spec/05): shock <= -2.0. Event mode is the v1 exit model in
`v1rule.py`; this module exists for the regression and the shift test."""
from __future__ import annotations

import numpy as np

NAME, MODE, DIRECTION, HORIZON = "v1", "v1", "long", 5
UNIVERSES = ["smallcap", "uncapped", "crypto"]
K_SHOCK = 2.0


def candidates(A: dict) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        return A["shock"] <= -K_SHOCK

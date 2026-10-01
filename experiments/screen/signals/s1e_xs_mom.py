"""1e Crypto cross-sectional momentum: among the eligible top-100 on D, rank by the trailing
3-week return (close_D / close_{D-21} - 1); long the top decile equal-weight, hold 3 weeks,
a new tranche every week."""
from __future__ import annotations

import numpy as np

NAME, MODE = "1e", "rank"
UNIVERSES = ["crypto"]
HORIZON = 7
HOLD_WEEKS = 3


def scores(A: dict) -> np.ndarray:
    return np.array(A["ret_21"], dtype=float)

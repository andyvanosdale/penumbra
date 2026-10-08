"""2a 12-1 momentum (rank mode, equities): score ret_12_1 = a_close[D-21] / a_close[D-252] - 1;
long the top decile (V1), top quintile (V2), or the decile held three months in three
overlapping tranches (V3), monthly at the next open after each month-end."""
from __future__ import annotations

import numpy as np

NAME, MODE, LANE = "2a", "rank", "equity"
UNIVERSES = ["uncapped", "smallcap"]
HORIZON = 21
PPY = 12
SIDE = "top"
PRIOR_PP = 3.0
VARIANTS = {"v1": {"div": 10, "hold": 1}, "v2": {"div": 5, "hold": 1}, "v3": {"div": 10, "hold": 3}}


def scores(A: dict, variant: str = "v1") -> np.ndarray:
    return np.array(A["ret_12_1"], dtype=float)

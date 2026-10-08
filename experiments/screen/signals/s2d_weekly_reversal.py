"""2d Weekly reversal, liquid names (rank mode, equities): score ret_5 = a_close[D] / a_close[D-5]
- 1 among names with med_dv_20_prev >= USD 10M; long the bottom decile (V1), bottom quintile
(V2), or the bottom decile ranked on sessions D-6 to D-1 (V3, D excluded), weekly at the next
open after each ISO week-end."""
from __future__ import annotations

import numpy as np

from experiments.screen.data import shift_rows

NAME, MODE, LANE = "2d", "rank", "equity"
UNIVERSES = ["uncapped", "smallcap"]
HORIZON = 5
PPY = 52
SIDE = "bottom"
LIQ_FLOOR = 1e7
PRIOR_PP = 7.8
VARIANTS = {"v1": {"div": 10}, "v2": {"div": 5}, "v3": {"div": 10}}


def scores(A: dict, variant: str = "v1") -> np.ndarray:
    r5 = np.array(A["ret_5"], dtype=float)
    return shift_rows(r5, -1) if variant == "v3" else r5

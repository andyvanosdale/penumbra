"""2b 52-week-high proximity (rank mode, equities): score close / max(close over the 250 sessions
ending D) on split-adjusted closes (George and Hwang); long the top decile (V1), top quintile
(V2), or the top decile among the names in the top half of the 2a score on D (V3), monthly."""
from __future__ import annotations

import numpy as np

NAME, MODE, LANE = "2b", "rank", "equity"
UNIVERSES = ["uncapped", "smallcap"]
HORIZON = 21
PPY = 12
SIDE = "top"
PRIOR_PP = 2.0
VARIANTS = {"v1": {"div": 10}, "v2": {"div": 5}, "v3": {"div": 10, "subset_top_half": True, "comparator": "full"}}


def scores(A: dict, variant: str = "v1") -> np.ndarray:
    return np.array(A["close_to_max_close_250"], dtype=float)


def subset_scores(A: dict) -> np.ndarray:
    """V3's second score: the names in its top half on D form the ranked set."""
    return np.array(A["ret_12_1"], dtype=float)

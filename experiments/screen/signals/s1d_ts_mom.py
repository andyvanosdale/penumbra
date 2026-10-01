"""1d Crypto time-series momentum: long the pair for the week when its trailing 30-day and
90-day returns (closes through D) are both positive; flat otherwise. Weekly at the 01:00 UTC
open on D+1; comparator buy-and-hold of the same pair."""
from __future__ import annotations

import numpy as np

NAME, MODE = "1d", "rank"
UNIVERSES = ["BTCUSDT", "ETHUSDT"]
HORIZON = 7


def position(A: dict) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        return (A["ret_30"] > 0) & (A["ret_90"] > 0)

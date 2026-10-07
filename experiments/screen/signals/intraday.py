"""The intraday wave's signals (research_log/2026-10-07-intraday-wave.md, "Signals").

Each row is an `IntradaySignal`: `candidates(A, I, elig)` returns a boolean matrix on fill
sessions F from the daily arrays `A` (data through F-1 where used) and the intraday arrays `I`
(bars that closed before the entry time), ANDed by the engine with `elig`. Rank-type rows also
expose `pool(A, I, elig)`, the set of names the slice was drawn from, for the random-slice
placebo. `tests/screen/test_intraday.py` perturbs the bars after the entry bar on F and every
bar on later sessions and asserts each matrix at F is unchanged.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

from experiments.screen.data import shift_rows
from experiments.screen.signals import s1a_post_shock, s1b_up_shock_5d

K_GAP = 2.0
K_VOL = 2.0
VWAP_PREMIUM = 0.02
ANN = 252


@dataclass(frozen=True)
class IntradaySignal:
    NAME: str
    DIRECTION: str          # "long" | "short"
    ENTRY: str              # clock time ET
    HORIZON: str            # decision exit: "close" | "nopen" | ...
    FLOOR: bool             # scored on the floored universe
    RANK: bool              # a cross-sectional slice (random-slice placebo, power statement)
    _cand: Callable
    _pool: Callable | None = None
    COMPARATOR: str = "universe"
    UNIVERSES: tuple = ("smallcap", "uncapped")
    MODE: str = "intraday"

    def candidates(self, A: dict, I: dict, elig: np.ndarray) -> np.ndarray:
        return self._cand(A, I, elig)

    def pool(self, A: dict, I: dict, elig: np.ndarray) -> np.ndarray:
        return self._pool(A, I, elig) if self._pool else elig


# ---------------------------------------------------------------- shared features (row F, knowable before the entry)
def gap_sigma(A: dict, I: dict) -> np.ndarray:
    """ln(o(09:30) x f_F / a_close_{F-1}) / (rvol_20_{F-1} / sqrt(252))."""
    with np.errstate(all="ignore"):
        g = np.log(I["o0930"] * I["f"] / shift_rows(A["a_close"], -1))
        return g / (shift_rows(A["rvol_20"], -1) / math.sqrt(ANN))


def overnight_return(A: dict, I: dict) -> np.ndarray:
    with np.errstate(all="ignore"):
        return np.log(I["o0930"] * I["f"] / shift_rows(A["a_close"], -1))


def r_fhh(I: dict) -> np.ndarray:
    with np.errstate(all="ignore"):
        return I["c0955"] / I["o0930"] - 1.0


def r_1500(I: dict) -> np.ndarray:
    with np.errstate(all="ignore"):
        return I["c1455"] / I["o0930"] - 1.0


def top_k(score: np.ndarray, pool: np.ndarray, frac: float, bottom: bool = False) -> np.ndarray:
    """Per row, the k = ceil(n * frac) highest (lowest) scores among `pool`; stable sort."""
    s = np.where(pool & ~np.isnan(score), score, np.nan)
    out = np.zeros(score.shape, dtype=bool)
    for i in range(score.shape[0]):
        valid = ~np.isnan(s[i])
        n = int(valid.sum())
        if n == 0:
            continue
        k = int(math.ceil(n * frac))
        key = np.where(valid, s[i], np.inf if bottom else -np.inf)
        order = np.argsort(key if bottom else -key, kind="stable")
        out[i, order[:k]] = True
    return out


def quintile(score: np.ndarray, pool: np.ndarray) -> np.ndarray:
    """Per row, quintile 1..5 by percentile rank among `pool` (NaN outside)."""
    s = pd.DataFrame(np.where(pool & ~np.isnan(score), score, np.nan))
    p = s.rank(axis=1, pct=True).to_numpy()
    with np.errstate(invalid="ignore"):
        return np.ceil(p * 5)


# ---------------------------------------------------------------- rules
def _i1(A, I, elig):
    with np.errstate(all="ignore"):
        return (I["n_fhh"] == 6) & (I["c0955"] > I["h_or"]) & (I["v_fhh"] >= K_VOL * I["med20_v_fhh"])


def _i2_up(A, I, elig):
    with np.errstate(invalid="ignore"):
        return gap_sigma(A, I) >= K_GAP


def _i2_down(A, I, elig):
    with np.errstate(invalid="ignore"):
        return gap_sigma(A, I) <= -K_GAP


def _fhh_pool(A, I, elig):
    return elig & ~np.isnan(r_fhh(I))


def _i3_top(A, I, elig):
    return top_k(r_fhh(I), _fhh_pool(A, I, elig), 0.1)


def _i3_bottom(A, I, elig):
    return top_k(r_fhh(I), _fhh_pool(A, I, elig), 0.1, bottom=True)


def _r1500_pool(A, I, elig):
    return elig & ~np.isnan(r_1500(I))


def _i4(A, I, elig):
    return top_k(r_1500(I), _r1500_pool(A, I, elig), 0.1)


def _i5_all(A, I, elig):
    return elig & ~np.isnan(I["px_1555"])


def _i5_pool(A, I, elig):
    return elig & ~np.isnan(I["px_1555"]) & ~np.isnan(overnight_return(A, I))


def _i5_q(q):
    def f(A, I, elig):
        with np.errstate(invalid="ignore"):
            return quintile(overnight_return(A, I), _i5_pool(A, I, elig)) == q
    return f


def _next_day(daily_rule):
    """Wave-1 candidates on D, filled on F = D+1."""
    def f(A, I, elig):
        return shift_rows(daily_rule(A).astype(float), -1) == 1.0
    return f


def _i7(A, I, elig):
    with np.errstate(all="ignore"):
        return (I["px_1200"] >= (1 + VWAP_PREMIUM) * I["vwap_1200"]) & (I["v_1200"] >= K_VOL * I["med20_v_1200"])


INTRADAY = {s.NAME: s for s in [
    IntradaySignal("i1", "long", "10:00", "close", True, False, _i1),
    IntradaySignal("i2-up", "long", "09:35", "close", False, False, _i2_up),
    IntradaySignal("i2-down", "short", "09:35", "close", False, False, _i2_down),
    IntradaySignal("i3-top", "long", "10:00", "close", True, True, _i3_top, _fhh_pool),
    IntradaySignal("i3-bottom", "short", "10:00", "close", True, True, _i3_bottom, _fhh_pool),
    IntradaySignal("i4", "long", "15:30", "close", True, True, _i4, _r1500_pool),
    IntradaySignal("i5-all", "long", "15:55", "nopen", False, False, _i5_all, COMPARATOR="zero"),
    IntradaySignal("i5-q5", "long", "15:55", "nopen", False, True, _i5_q(5), _i5_pool),
    IntradaySignal("i5-q4", "long", "15:55", "nopen", False, True, _i5_q(4), _i5_pool),
    IntradaySignal("i5-q3", "long", "15:55", "nopen", False, True, _i5_q(3), _i5_pool),
    IntradaySignal("i5-q2", "long", "15:55", "nopen", False, True, _i5_q(2), _i5_pool),
    IntradaySignal("i5-q1", "long", "15:55", "nopen", False, True, _i5_q(1), _i5_pool),
    IntradaySignal("i6-1a-0935", "short", "09:35", "close", False, False, _next_day(s1a_post_shock.candidates)),
    IntradaySignal("i6-1a-1030", "short", "10:30", "close", False, False, _next_day(s1a_post_shock.candidates)),
    IntradaySignal("i6-1b-0935", "long", "09:35", "close", False, False, _next_day(s1b_up_shock_5d.candidates)),
    IntradaySignal("i6-1b-1030", "long", "10:30", "close", False, False, _next_day(s1b_up_shock_5d.candidates)),
    IntradaySignal("i7", "short", "12:00", "close", True, False, _i7),
]}

LEDGERED = [n for n in INTRADAY if n not in ("i5-q4", "i5-q3", "i5-q2")]   # q2-q4 are reported from the same run, not ledgered


def load(name: str) -> IntradaySignal:
    if name not in INTRADAY:
        raise KeyError(f"unknown intraday signal {name!r}; known: {sorted(INTRADAY)}")
    return INTRADAY[name]

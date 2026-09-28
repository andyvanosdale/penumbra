"""Labeler (plan §3.3) — ███ QUARANTINED ███.

This is the ONLY component permitted to look into the future. It must never be
importable from feature-building code. Enforcement:

  * It reads via store.get_prices_oracle() (the future-aware path).
  * tests/test_features_no_lookahead.py asserts that features.py imports nothing
    from this module and never references the oracle.

Label definition (plan §2 / §10.4):
  Given (ticker, decision_date), look forward `horizon` trading days. Compute the
  ticker's return and its sector ETF's return over that window. The *excess
  return* is (ticker_return - benchmark_return). The binary label is 1 if the
  excess return exceeds `threshold`, else 0.

Entry convention: a signal generated at the close of `decision_date` is filled at
that close. We hold `horizon` trading days and measure close-to-close. Costs are
applied separately by the evaluator, not baked into the label.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from legacy.universe import benchmark_for
from legacy.store import PITStore

DEFAULT_HORIZON = 5        # trading days (plan §2)
DEFAULT_THRESHOLD = 0.02   # 2% excess vs sector (plan §2)


@dataclass
class LabelResult:
    ticker: str
    decision_date: str
    horizon: int
    threshold: float
    ticker_return: Optional[float]
    benchmark_return: Optional[float]
    excess_return: Optional[float]
    label: Optional[int]          # None if the forward window is incomplete
    benchmark: str


class Labeler:
    """Future-aware. Construct once per backtest; it caches the oracle frame."""

    def __init__(
        self,
        store: PITStore,
        horizon: int = DEFAULT_HORIZON,
        threshold: float = DEFAULT_THRESHOLD,
    ):
        self.store = store
        self.horizon = horizon
        self.threshold = threshold
        # Pre-load full history once and precompute the horizon-forward return for
        # every (ticker, date) so label() is an O(1) lookup. fwd[d] = P[d+h]/P[d]-1;
        # the last `horizon` dates are NaN (incomplete forward window).
        frame = store.get_prices_oracle()
        self._fwd: dict[str, pd.Series] = {}
        for tkr, grp in frame.groupby("ticker"):
            s = grp.sort_values("date").set_index("date")["adj_close"]
            s = s.where(s != 0)  # guard divide-by-zero
            fwd = s.shift(-self.horizon) / s - 1.0
            self._fwd[tkr] = fwd

    def _fwd_return(self, ticker: str, decision_date: str) -> Optional[float]:
        fwd = self._fwd.get(ticker)
        if fwd is None or decision_date not in fwd.index:
            return None
        v = fwd.loc[decision_date]
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return None  # not enough future data — leave unlabeled, don't guess
        return float(v)

    def label(self, ticker: str, decision_date) -> LabelResult:
        """label(ticker, timestamp) -> binary_outcome  (plan §3.3 signature)."""
        decision_date = (
            decision_date if isinstance(decision_date, str)
            else pd.Timestamp(decision_date).strftime("%Y-%m-%d")
        )
        bench = benchmark_for(ticker)
        r_t = self._fwd_return(ticker, decision_date)
        r_b = self._fwd_return(bench, decision_date)
        if r_t is None or r_b is None:
            return LabelResult(ticker, decision_date, self.horizon,
                               self.threshold, r_t, r_b, None, None, bench)
        excess = r_t - r_b
        return LabelResult(
            ticker, decision_date, self.horizon, self.threshold,
            r_t, r_b, excess, int(excess > self.threshold), bench,
        )

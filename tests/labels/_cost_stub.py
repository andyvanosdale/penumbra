"""Stand-in for issue 7's cost model, for the labeler tests only.

It implements exactly the interface issue 7 is building in `harness/costs.py`
(`LegType`, `LegCost`, `CostModel.leg`, `CostInputs`) with trivially checkable
numbers: the spread is the input half-spread (2x on the entry leg), slippage a
flat 10 bps, no fee. Replace with `harness.costs` once issue 7 merges.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

LegType = Literal["entry", "exit_target", "exit_stop", "exit_time", "exit_delist",
                  "exit_era_end"]

STUB_SLIPPAGE = 0.001


@dataclass(frozen=True)
class CostInputs:
    lane: str
    symbol: str
    signal_date: str
    half_spread_est: float = 0.0025
    close_unadj_d: float = 100.0
    rvol_20_d: float = 0.5
    median_dollar_volume: float = 5_000_000.0
    top20_by_quote_volume: bool = False


@dataclass(frozen=True)
class LegCost:
    spread: float
    slippage: float
    fee: float
    floor_bound: bool

    @property
    def total(self) -> float:
        return self.spread + self.slippage + self.fee


class CostModel:
    def __init__(self, lane, stress=None, multiplier=1.0):
        self.lane = lane
        self.stress = stress
        self.multiplier = multiplier
        self.calls: list[tuple[str, str, float]] = []

    def leg(self, inputs: CostInputs, leg: LegType, order_notional: float) -> LegCost:
        self.calls.append((inputs.symbol, leg, order_notional))
        spread = inputs.half_spread_est * (2.0 if leg == "entry" else 1.0) * self.multiplier
        return LegCost(spread=spread, slippage=STUB_SLIPPAGE * self.multiplier, fee=0.0,
                       floor_bound=inputs.half_spread_est <= 0.0025)

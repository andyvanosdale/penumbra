"""Transaction-cost & slippage model (plan §3.5 / §6.5).

Cost realism from day one. A signal is a round trip (enter + exit), so the total
cost charged against an excess return is applied for both legs:

    total_cost = 2 * (half_spread + commission + slippage)

Everything is expressed as a fraction of notional (so it subtracts directly from
a return). Defaults are deliberately conservative for liquid large caps; smaller
caps should use wider spreads and larger slippage (plan §6.5).
"""

from __future__ import annotations

from dataclasses import dataclass

BPS = 1e-4


@dataclass(frozen=True)
class CostModel:
    spread_bps: float = 4.0        # full bid/ask spread; we pay half per leg
    commission_bps: float = 1.0    # per leg
    slippage_bps: float = 2.0      # per leg (own-order market impact)

    def per_leg(self) -> float:
        return (self.spread_bps / 2.0 + self.commission_bps
                + self.slippage_bps) * BPS

    def round_trip(self) -> float:
        """Total cost as a fraction of notional for a full enter+exit cycle."""
        return 2.0 * self.per_leg()

    def net_of_costs(self, gross_return: float) -> float:
        """Apply round-trip costs to a gross (excess) return."""
        return gross_return - self.round_trip()


DEFAULT_COSTS = CostModel()

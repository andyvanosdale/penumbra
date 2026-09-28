"""Crypto branch of the cost formula: taker fee and the top-20/other spread
floor tiers (spec/06 Costs). Synthetic inputs only -- no crypto data work
(issue 7 scope note: the crypto lane may be removed by the pre-build screen)."""

from __future__ import annotations

import math

from harness.costs import CostInputs, CostModel


def _inputs(top20: bool) -> CostInputs:
    return CostInputs(
        lane="crypto",
        symbol="BTCUSDT",
        signal_date="2024-01-10",
        half_spread_est=0.0001,  # 1 bp, below both crypto floors
        close_unadj_d=50_000.0,
        rvol_20_d=0.8,
        median_dollar_volume=5_000_000.0,
        top20_by_quote_volume=top20,
    )


def test_top_tier_floor():
    """The 0.05% tier constant is a full-spread floor (PM ruling, penumbra-specs
    PR #10); the per-side charge is half of it."""

    model = CostModel("crypto")
    leg = model.leg(_inputs(top20=True), "exit_target", 10_000.0)
    assert leg.floor_bound is True
    assert math.isclose(leg.spread, 0.0005 / 2.0, rel_tol=1e-9)


def test_other_tier_floor():
    model = CostModel("crypto")
    leg = model.leg(_inputs(top20=False), "exit_target", 10_000.0)
    assert leg.floor_bound is True
    assert math.isclose(leg.spread, 0.0015 / 2.0, rel_tol=1e-9)


def test_taker_fee_per_side_both_legs():
    model = CostModel("crypto")
    entry = model.leg(_inputs(top20=True), "entry", 10_000.0)
    exit_ = model.leg(_inputs(top20=True), "exit_target", 10_000.0)
    assert math.isclose(entry.fee, 0.0010, rel_tol=1e-9)
    assert math.isclose(exit_.fee, 0.0010, rel_tol=1e-9)


def test_crypto_annualization_uses_sqrt_365():
    model = CostModel("crypto")
    inputs = _inputs(top20=True)
    order_notional = 10_000.0
    leg = model.leg(inputs, "exit_target", order_notional)

    sigma_d = inputs.rvol_20_d / math.sqrt(365)
    participation = order_notional / inputs.median_dollar_volume
    expected_slippage = 0.5 * sigma_d * math.sqrt(participation)
    assert math.isclose(leg.slippage, expected_slippage, rel_tol=1e-9)

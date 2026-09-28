"""CostModel.leg: the tick-aware floor, square-root participation slippage, the
entry-leg spread and participation multipliers, and the three stress cases
(spec/06 Costs)."""

from __future__ import annotations

import math

import pytest

from config.params import STRESS_CASES
from harness.costs import CostInputs, CostModel


def _inputs(**overrides) -> CostInputs:
    base = dict(
        lane="smallcap",
        symbol="100001",
        signal_date="2024-01-10",
        half_spread_est=0.006,  # 60 bps, above every floor used below
        close_unadj_d=50.0,
        rvol_20_d=0.40,
        median_dollar_volume=1_000_000.0,
        top20_by_quote_volume=None,
    )
    base.update(overrides)
    return CostInputs(**base)


def test_tick_floor_binds_for_a_low_priced_stock():
    """A USD 3 stock: one tick / close = 0.01 / 3 = 0.333%, above the 0.25%
    floor, so the tick floor binds."""

    model = CostModel("smallcap")
    inputs = _inputs(close_unadj_d=3.0, half_spread_est=0.001)  # 10 bps, below either floor
    leg = model.leg(inputs, "exit_target", order_notional=10_000.0)
    expected_floor = 0.01 / 3.0
    assert expected_floor > 0.0025
    assert leg.floor_bound is True
    assert math.isclose(leg.spread, expected_floor, rel_tol=1e-9)


def test_percentage_floor_binds_for_a_higher_priced_stock():
    model = CostModel("smallcap")
    inputs = _inputs(close_unadj_d=50.0, half_spread_est=0.001)  # tick/close = 0.0002 < 0.25%
    leg = model.leg(inputs, "exit_target", order_notional=10_000.0)
    assert leg.floor_bound is True
    assert math.isclose(leg.spread, 0.0025, rel_tol=1e-9)


def test_floor_not_bound_when_estimate_exceeds_it():
    model = CostModel("smallcap")
    inputs = _inputs(close_unadj_d=50.0, half_spread_est=0.01)  # 100 bps, above 0.25% and above tick floor
    leg = model.leg(inputs, "exit_target", order_notional=10_000.0)
    assert leg.floor_bound is False
    assert math.isclose(leg.spread, 0.01, rel_tol=1e-9)


def test_square_root_participation_slippage():
    model = CostModel("smallcap")
    inputs = _inputs(rvol_20_d=0.5, median_dollar_volume=2_000_000.0)
    order_notional = 20_000.0
    leg = model.leg(inputs, "exit_target", order_notional=order_notional)

    sigma_d = 0.5 / math.sqrt(252)
    participation = order_notional / 2_000_000.0  # exit: full median
    expected_slippage = 0.5 * sigma_d * math.sqrt(participation)
    assert math.isclose(leg.slippage, expected_slippage, rel_tol=1e-9)


def test_entry_leg_spread_and_participation_multipliers():
    model = CostModel("smallcap")
    inputs = _inputs()  # half_spread_est well above the floor, so the floor never binds
    order_notional = 10_000.0

    entry = model.leg(inputs, "entry", order_notional)
    exit_ = model.leg(inputs, "exit_target", order_notional)

    assert math.isclose(entry.spread, 2.0 * exit_.spread, rel_tol=1e-9)
    # participation_entry = notional / (median * 0.10) = 10 x participation_exit,
    # so slippage scales by sqrt(10).
    assert math.isclose(entry.slippage, exit_.slippage * math.sqrt(10.0), rel_tol=1e-9)


def test_equity_fee_is_zero():
    model = CostModel("smallcap")
    inputs = _inputs()
    leg = model.leg(inputs, "entry", 10_000.0)
    assert leg.fee == 0.0


@pytest.mark.parametrize("case", STRESS_CASES, ids=[c.name for c in STRESS_CASES])
def test_each_stress_case(case):
    baseline_model = CostModel("smallcap")
    stressed_model = CostModel("smallcap", stress=case)
    inputs = _inputs()
    order_notional = 10_000.0

    base = baseline_model.leg(inputs, "exit_target", order_notional)
    stressed = stressed_model.leg(inputs, "exit_target", order_notional)

    assert math.isclose(stressed.spread, base.spread * float(case.spread_multiplier), rel_tol=1e-9)
    assert math.isclose(stressed.slippage, base.slippage * float(case.slippage_multiplier), rel_tol=1e-9)
    assert math.isclose(stressed.fee, base.fee + float(case.fixed_bps_per_leg), rel_tol=1e-9)


def test_multiplier_scales_every_component():
    inputs = _inputs()
    order_notional = 10_000.0
    base = CostModel("smallcap").leg(inputs, "entry", order_notional)
    scaled = CostModel("smallcap", multiplier=3.0).leg(inputs, "entry", order_notional)

    assert math.isclose(scaled.spread, base.spread * 3.0, rel_tol=1e-9)
    assert math.isclose(scaled.slippage, base.slippage * 3.0, rel_tol=1e-9)
    assert math.isclose(scaled.total, base.total * 3.0, rel_tol=1e-9)


def test_negative_order_notional_rejected():
    model = CostModel("smallcap")
    with pytest.raises(ValueError):
        model.leg(_inputs(), "entry", -1.0)


def test_nonpositive_median_dollar_volume_rejected():
    model = CostModel("smallcap")
    with pytest.raises(ValueError):
        model.leg(_inputs(median_dollar_volume=0.0), "entry", 10_000.0)


def test_unknown_lane_rejected():
    with pytest.raises(ValueError):
        CostModel("not_a_lane")

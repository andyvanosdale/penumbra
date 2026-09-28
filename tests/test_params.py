"""Cross-checks config/params.py against the locked-parameter tables in
spec/01, spec/05, spec/06 and spec/07 (see spec/DECISIONS.md "Parameters
re-locked" for the consolidated list)."""

from __future__ import annotations

from decimal import Decimal

from config import params


def test_strategy_rule_spec05():
    assert params.SPEC05.k == Decimal("2.0")
    assert params.SPEC05.time_stop_sessions == 10
    assert params.SPEC05.order_size_usd == Decimal("10000")
    assert params.SPEC05.lane_capital_usd == Decimal("200000")


def test_universe_spec01():
    assert params.SPEC01.small_cap_ceiling_usd == Decimal("2000000000")
    assert params.SPEC01.liquidity_floor_equities_usd == Decimal("500000")
    assert params.SPEC01.vol_floor_equities == Decimal("0.40")
    assert params.SPEC01.crypto_vol_floor == Decimal("0.20")
    assert params.SPEC01.price_floor_equities_usd == Decimal("2.00")
    assert params.SPEC01.crypto_n == 100


def test_costs_spec06():
    assert params.SPEC06_EQUITY.spread_floor_pct == Decimal("0.0025")
    assert params.SPEC06_CRYPTO.spread_floor_top_tier_pct == Decimal("0.0005")
    assert params.SPEC06_CRYPTO.spread_floor_other_pct == Decimal("0.0015")
    assert params.SPEC06_CRYPTO.taker_fee_per_side == Decimal("0.0010")

    stress_by_name = {c.name: c for c in params.STRESS_CASES}
    assert len(params.STRESS_CASES) == 3
    assert stress_by_name["spread_x2"].spread_multiplier == Decimal("2")
    assert stress_by_name["slippage_x2"].slippage_multiplier == Decimal("2")
    assert stress_by_name["fixed_10bps_per_leg"].fixed_bps_per_leg == Decimal("0.0010")


def test_evaluation_spec07():
    assert params.SPEC07.drawdown_budget == Decimal("0.25")
    assert params.SPEC07.min_entry_days == 100
    assert params.SPEC07.min_trades == 500
    assert params.SPEC07.net_share_of_gross_floor == Decimal("0.5")
    assert params.SPEC07.z_threshold == Decimal("3.0")
    assert params.SPEC07.z_threshold_stress == Decimal("2.0")
    assert params.SPEC07.mean_return_ci_confidence == Decimal("0.95")
    assert params.SPEC07.regime_vol_window_days == 20
    assert params.SPEC07.regime_proxy_equities == "SPY"
    assert params.SPEC07.regime_proxy_crypto == "BTCUSDT"


def test_labels_spec04():
    assert params.SPEC04.horizon_days == (5, 21, 63, 252)
    assert params.SPEC04.cohort_zscore_threshold == Decimal("-2.0")
    assert params.SPEC04.cohort_shock_share_floor == Decimal("0.5")


def test_benchmark_quintile_bins():
    assert params.SPEC05.benchmark_quintile_bins == 5


def test_controls():
    by_kind = {c.kind: c for c in params.CONTROLS}
    placebo = by_kind["placebo"]
    assert placebo.lag_days == 20
    assert placebo.z_threshold == Decimal("2.0")
    assert placebo.z_condition == "abs_below"

    positive_control = by_kind["positive_control"]
    assert positive_control.planted_return == Decimal("0.005")
    assert positive_control.z_threshold == Decimal("3.0")
    assert positive_control.z_condition == "at_least"


def test_benchmark_seed_scheme():
    assert params.BENCHMARK_SEED_SCHEME.seed_fields == (
        "configuration_hash",
        "lane",
        "era",
        "i",
    )
    assert params.SPEC05.benchmark_draws == 1000


def test_all_locked_params_wires_every_group():
    all_params = params.ALL_LOCKED_PARAMS
    assert all_params.universe is params.SPEC01
    assert all_params.strategy is params.SPEC05
    assert all_params.benchmark_seed_scheme is params.BENCHMARK_SEED_SCHEME
    assert all_params.costs_equities is params.SPEC06_EQUITY
    assert all_params.costs_crypto is params.SPEC06_CRYPTO
    assert all_params.stress_cases is params.STRESS_CASES
    assert all_params.labels is params.SPEC04
    assert all_params.evaluation is params.SPEC07
    assert all_params.controls is params.CONTROLS

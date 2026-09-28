"""Every locked parameter from spec/01, spec/05, spec/06 and spec/07, as frozen
data. This module is the single input to `harness.runrecord.config_hash`
(spec/03 "Run record") along with `config/eras.py`; nothing here may change
except by a spec change with a decision-log entry (spec/DECISIONS.md
"Parameters re-locked").

Decimals are exact: every monetary and percentage value is a `Decimal`
constructed from a literal string, never a float that could round.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


# --- spec/01 "Lanes and universe" -------------------------------------------
# "Parameters (locked)" table, plus the eligibility-window constants named in
# the body text (250-day equity history, 30-day crypto window) and the
# delisting haircuts ("Delisting while a position is open").
@dataclass(frozen=True)
class UniverseParams:
    small_cap_ceiling_usd: Decimal
    liquidity_floor_equities_usd: Decimal
    liquidity_floor_window_days: int
    vol_floor_equities: Decimal
    vol_floor_window_days: int
    price_floor_equities_usd: Decimal
    equities_full_history_days: int
    crypto_n: int
    crypto_quote: str
    crypto_vol_floor: Decimal
    crypto_vol_floor_window_days: int
    crypto_full_history_days: int
    crypto_volume_ranking_window_days: int
    delisting_haircut_nasdaq: Decimal
    delisting_haircut_nyse_amex: Decimal


SPEC01 = UniverseParams(
    small_cap_ceiling_usd=Decimal("2000000000"),
    liquidity_floor_equities_usd=Decimal("500000"),
    liquidity_floor_window_days=20,
    vol_floor_equities=Decimal("0.40"),
    vol_floor_window_days=20,
    price_floor_equities_usd=Decimal("2.00"),
    equities_full_history_days=250,
    crypto_n=100,
    crypto_quote="USDT",
    crypto_vol_floor=Decimal("0.20"),
    crypto_vol_floor_window_days=30,
    crypto_full_history_days=30,
    crypto_volume_ranking_window_days=30,
    delisting_haircut_nasdaq=Decimal("0.45"),
    delisting_haircut_nyse_amex=Decimal("0.70"),
)


# --- spec/05 "Strategy rule" -------------------------------------------------
# "Parameters (locked)" table, plus the benchmark draw count and the crypto
# entry-hour and no-bar-closure constants named in the rule body.
@dataclass(frozen=True)
class StrategyParams:
    k: Decimal
    time_stop_sessions: int
    target_window_days: int
    hard_stop_range_multiplier: Decimal
    order_size_usd: Decimal
    lane_capital_usd: Decimal
    capped_variant_positions: int
    no_bar_closure_sessions: int
    crypto_entry_hour_utc: int
    benchmark_draws: int
    benchmark_quintile_bins: int


SPEC05 = StrategyParams(
    k=Decimal("2.0"),
    time_stop_sessions=10,
    target_window_days=20,
    hard_stop_range_multiplier=Decimal("1.5"),
    order_size_usd=Decimal("10000"),
    lane_capital_usd=Decimal("200000"),
    capped_variant_positions=20,
    no_bar_closure_sessions=5,
    crypto_entry_hour_utc=1,
    benchmark_draws=1000,
    # "the same rvol_20 quintile of the day's universe as that candidate"
    # (spec/05 Benchmark): a quintile is 5 bins by definition.
    benchmark_quintile_bins=5,
)


@dataclass(frozen=True)
class BenchmarkSeedScheme:
    description: str
    seed_fields: tuple[str, ...]


BENCHMARK_SEED_SCHEME = BenchmarkSeedScheme(
    description=(
        "Draw i of the 1,000-draw random-entry benchmark is seeded "
        "deterministically from the ordered tuple (configuration hash, lane, "
        "era, i); a draw is never re-seeded (spec/05 Benchmark)."
    ),
    seed_fields=("configuration_hash", "lane", "era", "i"),
)


# --- spec/06 "Costs" ----------------------------------------------------------
# The cost model's locked table, split by lane group since equities and
# crypto differ; the three cost-stress cases ("Cost stress").
@dataclass(frozen=True)
class EquityCostParams:
    spread_window_days: int
    spread_floor_pct: Decimal
    tick_size_usd: Decimal
    slippage_coefficient: Decimal
    entry_spread_multiplier: Decimal
    entry_participation_base: Decimal
    fee_per_side: Decimal


SPEC06_EQUITY = EquityCostParams(
    spread_window_days=20,
    spread_floor_pct=Decimal("0.0025"),
    tick_size_usd=Decimal("0.01"),
    slippage_coefficient=Decimal("0.5"),
    entry_spread_multiplier=Decimal("2"),
    entry_participation_base=Decimal("0.10"),
    fee_per_side=Decimal("0"),
)


@dataclass(frozen=True)
class CryptoCostParams:
    spread_window_days: int
    spread_floor_top_tier_pct: Decimal
    spread_floor_other_pct: Decimal
    top_tier_rank: int
    slippage_coefficient: Decimal
    entry_spread_multiplier: Decimal
    entry_participation_base: Decimal
    taker_fee_per_side: Decimal


SPEC06_CRYPTO = CryptoCostParams(
    spread_window_days=20,
    spread_floor_top_tier_pct=Decimal("0.0005"),
    spread_floor_other_pct=Decimal("0.0015"),
    top_tier_rank=20,
    slippage_coefficient=Decimal("0.5"),
    entry_spread_multiplier=Decimal("2"),
    entry_participation_base=Decimal("0.10"),
    taker_fee_per_side=Decimal("0.0010"),
)


@dataclass(frozen=True)
class StressCase:
    name: str
    spread_multiplier: Decimal
    slippage_multiplier: Decimal
    fixed_bps_per_leg: Decimal
    stop_fills_at_low: bool


STRESS_CASES = (
    StressCase(
        name="spread_x2",
        spread_multiplier=Decimal("2"),
        slippage_multiplier=Decimal("1"),
        fixed_bps_per_leg=Decimal("0"),
        stop_fills_at_low=True,
    ),
    StressCase(
        name="slippage_x2",
        spread_multiplier=Decimal("1"),
        slippage_multiplier=Decimal("2"),
        fixed_bps_per_leg=Decimal("0"),
        stop_fills_at_low=True,
    ),
    StressCase(
        name="fixed_10bps_per_leg",
        spread_multiplier=Decimal("1"),
        slippage_multiplier=Decimal("1"),
        fixed_bps_per_leg=Decimal("0.0010"),
        stop_fills_at_low=True,
    ),
)


# --- spec/04 "Features and labels" (Labels; referenced by spec/07 Evaluation) -
# The forward-return horizons and the cohort-split threshold are reported
# diagnostics, not decision inputs, but they are locked text: a change to
# either changes what the horizon curve and the cohort split mean.
@dataclass(frozen=True)
class LabelParams:
    horizon_days: tuple[int, ...]
    cohort_zscore_threshold: Decimal  # spec/07 Cohort split: zscore_20 <= this
    cohort_shock_share_floor: Decimal  # shock's share of the 20-day z


SPEC04 = LabelParams(
    horizon_days=(5, 21, 63, 252),
    cohort_zscore_threshold=Decimal("-2.0"),
    cohort_shock_share_floor=Decimal("0.5"),
)


# --- spec/07 "Evaluation" ------------------------------------------------------
# The decision rule's locked thresholds and the two controls ("Controls").
@dataclass(frozen=True)
class EvaluationParams:
    z_threshold: Decimal
    z_threshold_stress: Decimal
    min_entry_days: int
    min_trades: int
    net_share_of_gross_floor: Decimal
    drawdown_budget: Decimal
    bootstrap_resamples: int
    top_pnl_days_excluded: int
    mean_return_ci_confidence: Decimal
    regime_vol_window_days: int
    regime_proxy_equities: str
    regime_proxy_crypto: str
    # Condition 5 ("net return positive ... in each half of the era") needs a
    # split rule the spec does not name. Reading, flagged for PM confirmation
    # in the PR description: the era's lane trading days in date order, split
    # at the midpoint by count (not by calendar date), consistent with every
    # other window in spec/05-07 being counted in lane trading days.
    era_half_split: str


SPEC07 = EvaluationParams(
    z_threshold=Decimal("3.0"),
    z_threshold_stress=Decimal("2.0"),
    min_entry_days=100,
    min_trades=500,
    net_share_of_gross_floor=Decimal("0.5"),
    drawdown_budget=Decimal("0.25"),
    bootstrap_resamples=10000,
    top_pnl_days_excluded=10,
    mean_return_ci_confidence=Decimal("0.95"),
    regime_vol_window_days=20,
    regime_proxy_equities="SPY",
    regime_proxy_crypto="BTCUSDT",
    era_half_split="trading_day_midpoint",
)


@dataclass(frozen=True)
class ControlDefinition:
    name: str
    kind: str  # "placebo" or "positive_control"
    lag_days: int | None
    planted_return: Decimal | None
    z_threshold: Decimal
    z_condition: str  # "abs_below" or "at_least"


CONTROLS = (
    ControlDefinition(
        name="stale_signal_placebo",
        kind="placebo",
        lag_days=20,
        planted_return=None,
        z_threshold=Decimal("2.0"),
        z_condition="abs_below",
    ),
    ControlDefinition(
        name="planted_effect_positive_control",
        kind="positive_control",
        lag_days=None,
        planted_return=Decimal("0.005"),
        z_threshold=Decimal("3.0"),
        z_condition="at_least",
    ),
)


# --- Aggregate ----------------------------------------------------------------
@dataclass(frozen=True)
class LockedParams:
    universe: UniverseParams
    strategy: StrategyParams
    benchmark_seed_scheme: BenchmarkSeedScheme
    costs_equities: EquityCostParams
    costs_crypto: CryptoCostParams
    stress_cases: tuple[StressCase, ...]
    labels: LabelParams
    evaluation: EvaluationParams
    controls: tuple[ControlDefinition, ...]


ALL_LOCKED_PARAMS = LockedParams(
    universe=SPEC01,
    strategy=SPEC05,
    benchmark_seed_scheme=BENCHMARK_SEED_SCHEME,
    costs_equities=SPEC06_EQUITY,
    costs_crypto=SPEC06_CRYPTO,
    stress_cases=STRESS_CASES,
    labels=SPEC04,
    evaluation=SPEC07,
    controls=CONTROLS,
)

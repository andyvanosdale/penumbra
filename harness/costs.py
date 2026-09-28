"""Per-lane cost model (spec/06 Costs; spec/01 for the participation denominator).

Every fill is a marketable order and pays spread and slippage on both legs; equities
pay no fee, crypto pays a taker fee per side (spec/06). This module is the only
consumer, alongside the universe builder and the feature builder, of
`harness.store.reader.AsOfReader` (`docs/architecture.md`, "Import rules"); it never
imports `harness.store.oracle`.

## Spec ambiguity flagged for the PA: where the spread floor applies

spec/06 says, in one cell: "Half of the Abdi-Ranaldo (2017) close-high-low spread
estimate over the 20 lane trading days ending D-1, with negative two-day estimates
set to zero before averaging; the estimate is floored at max(0.25%, one tick / D's
unadjusted close)". "The estimate is floored" could mean the *full* (round-trip) AR
estimate is floored before halving (giving an effective per-side floor of 0.125% for
equities), or the *half-spread* (the per-side quantity, already named earlier in the
same sentence, and the one the table's own column, "Spread (per side)", is about) is
floored directly at 0.25%.

This module floors the half-spread directly (0.25% per side, not 0.125%): the column
header is "Spread (per side)", so every clause inside that cell, including the floor,
most naturally describes the per-side number; and it is the more conservative
reading (it can only raise modeled costs, never understate them). `CostInputs.
half_spread_est` is therefore computed unfloored (half the AR estimate, negatives
zeroed before averaging) and `CostModel.leg` applies the floor to it directly, before
the entry leg's 2x multiplier. Flagged for the PA to confirm or correct.
"""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass
from typing import Callable, Literal, Mapping, Sequence

import numpy as np
import pandas as pd

from config.params import SPEC01, SPEC06_CRYPTO, SPEC06_EQUITY, StressCase
from harness.store import AsOfReader, calendar_for_lane
from harness.store.reader import iso_date

LegType = Literal["entry", "exit_target", "exit_stop", "exit_time", "exit_delist", "exit_era_end"]

# spec/02 Trading calendars: "Annualization uses sqrt(252) for equities and sqrt(365)
# for crypto."
_EQUITY_ANNUALIZATION = math.sqrt(252)
_CRYPTO_ANNUALIZATION = math.sqrt(365)

_LANE_MARKET = {"smallcap": "us_equity", "discovered": "us_equity", "crypto": "binance_spot"}

# Calendar days of history fetched before D to build the 20/21/30-session windows.
# Equity lanes see roughly 5 sessions per 7 calendar days even net of holidays, so 200
# calendar days comfortably covers a 30-session window; crypto trades every day, so it
# is trivially enough there too.
_CALENDAR_LOOKBACK_DAYS = 200

# The RVOL window is 20 days ending D (spec/04 `rvol_20`); 21 closes give 20 returns.
_RVOL_SESSIONS = 21


def _lane_market(lane: str) -> str:
    try:
        return _LANE_MARKET[lane]
    except KeyError:
        raise ValueError(f"unknown lane {lane!r}; expected one of {sorted(_LANE_MARKET)}")


def abdi_ranaldo_spread(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> float:
    """Abdi & Ranaldo (2017) close-high-low round-trip spread estimator.

    Abdi, B. F. and Ranaldo, A. (2017), "A Simple Estimation of Bid-Ask Spreads
    from Daily Close, High, and Low Prices", Review of Financial Studies 30(12),
    4437-4480. With the log mid-range eta_t = (ln H_t + ln L_t) / 2 and the log
    close c_t = ln(Close_t), the paper's two-day spread estimator is

        S_t^2 = 4 (c_t - eta_t)(c_t - eta_{t+1})

    for each pair of consecutive sessions (t, t+1). The round-trip spread
    estimate is s = sqrt(mean(S_t^2)) over the sample, with any negative S_t^2
    set to zero before averaging (spec/06: "negative two-day estimates set to
    zero before averaging").

    `high`, `low`, `close` are equal-length, date-ordered arrays covering the
    window; every consecutive pair is used, so N sessions give N-1 estimates.
    Callers pass the split-and-dividend-adjusted series (spec/06: costs read the
    same as-of-D adjusted series as features), since a raw split discontinuity
    would otherwise show up as a large but spurious two-day spread.
    """
    high = np.asarray(high, dtype=float)
    low = np.asarray(low, dtype=float)
    close = np.asarray(close, dtype=float)
    if not (len(high) == len(low) == len(close)):
        raise ValueError("high, low and close must be the same length")
    if len(high) < 2:
        raise ValueError("need at least two sessions to form one two-day pair")
    eta = (np.log(high) + np.log(low)) / 2.0
    c = np.log(close)
    s2 = 4.0 * (c[:-1] - eta[:-1]) * (c[:-1] - eta[1:])
    s2 = np.clip(s2, 0.0, None)
    return float(np.sqrt(np.mean(s2)))


@dataclass(frozen=True)
class LegCost:
    spread: float
    slippage: float
    fee: float
    floor_bound: bool

    @property
    def total(self) -> float:
        return self.spread + self.slippage + self.fee


@dataclass(frozen=True)
class CostInputs:
    """Everything a leg's cost depends on, all as of signal day D."""

    lane: str
    symbol: str
    signal_date: str
    half_spread_est: float
    close_unadj_d: float
    rvol_20_d: float
    median_dollar_volume: float
    top20_by_quote_volume: bool | None


class CostModel:
    """The lane's cost model: spread, slippage and fees for one leg of one trade."""

    def __init__(self, lane: str, stress: StressCase | None = None, multiplier: float = 1.0):
        self.lane = lane
        self.stress = stress
        self.multiplier = multiplier
        self._is_crypto = lane == "crypto"
        if lane not in _LANE_MARKET:
            raise ValueError(f"unknown lane {lane!r}; expected one of {sorted(_LANE_MARKET)}")
        self._params = SPEC06_CRYPTO if self._is_crypto else SPEC06_EQUITY

    def _spread_floor(self, inputs: CostInputs) -> float:
        if self._is_crypto:
            top20 = bool(inputs.top20_by_quote_volume)
            floor = SPEC06_CRYPTO.spread_floor_top_tier_pct if top20 else SPEC06_CRYPTO.spread_floor_other_pct
            return float(floor)
        if inputs.close_unadj_d <= 0:
            raise ValueError(f"non-positive close_unadj_d for {inputs.symbol} on {inputs.signal_date}")
        tick_floor = float(SPEC06_EQUITY.tick_size_usd) / inputs.close_unadj_d
        return max(float(SPEC06_EQUITY.spread_floor_pct), tick_floor)

    def leg(self, inputs: CostInputs, leg: LegType, order_notional: float) -> LegCost:
        """The modeled spread, slippage and fee for one leg (spec/06 Costs)."""
        p = self._params
        is_entry = leg == "entry"
        entry_mult = float(p.entry_spread_multiplier) if is_entry else 1.0
        participation_base = float(p.entry_participation_base) if is_entry else 1.0

        floor = self._spread_floor(inputs)
        floor_bound = inputs.half_spread_est <= floor
        floored_half_spread = max(inputs.half_spread_est, floor)
        spread = floored_half_spread * entry_mult

        annualization = _CRYPTO_ANNUALIZATION if self._is_crypto else _EQUITY_ANNUALIZATION
        sigma_d = inputs.rvol_20_d / annualization
        participation_denom = inputs.median_dollar_volume * participation_base
        if participation_denom <= 0:
            raise ValueError(
                f"non-positive participation denominator for {inputs.symbol} on "
                f"{inputs.signal_date} (median_dollar_volume={inputs.median_dollar_volume!r})"
            )
        participation = order_notional / participation_denom
        if participation < 0:
            raise ValueError(f"negative order_notional for {inputs.symbol} on {inputs.signal_date}")
        slippage = float(p.slippage_coefficient) * sigma_d * math.sqrt(participation)

        fee = float(p.taker_fee_per_side) if self._is_crypto else 0.0

        if self.stress is not None:
            spread *= float(self.stress.spread_multiplier)
            slippage *= float(self.stress.slippage_multiplier)
            fee += float(self.stress.fixed_bps_per_leg)

        spread *= self.multiplier
        slippage *= self.multiplier
        fee *= self.multiplier

        return LegCost(spread=spread, slippage=slippage, fee=fee, floor_bound=floor_bound)

    def breakeven_multiple(
        self,
        net_fn: Callable[[float], float],
        *,
        lo: float = 0.0,
        hi: float = 8.0,
        tol: float = 1e-6,
        max_expand: int = 50,
        max_iter: int = 200,
    ) -> float:
        """Root-find the cost multiplier at which `net_fn(multiplier)` is zero.

        `net_fn` is supplied by the caller (the evaluator, issue 11): it reruns
        the lane's net return with this model's costs scaled by the given
        multiplier and returns that net return. Bisection, expanding the
        bracket [lo, hi] outward while both endpoints have the same sign, since
        `net_fn` is expected to be monotone in the multiplier (more cost scales
        down net return) but its exact shape is the caller's business, not
        this module's.
        """
        f_lo, f_hi = net_fn(lo), net_fn(hi)
        expansions = 0
        while f_lo * f_hi > 0 and expansions < max_expand:
            hi *= 2.0
            f_hi = net_fn(hi)
            expansions += 1
        if f_lo * f_hi > 0:
            raise ValueError(
                "breakeven_multiple: no sign change in net_fn found within the "
                f"expanded bracket [{lo}, {hi}]"
            )
        if f_lo == 0.0:
            return lo
        if f_hi == 0.0:
            return hi
        for _ in range(max_iter):
            mid = (lo + hi) / 2.0
            f_mid = net_fn(mid)
            if abs(f_mid) < tol or (hi - lo) < tol:
                return mid
            if f_lo * f_mid <= 0:
                hi, f_hi = mid, f_mid
            else:
                lo, f_lo = mid, f_mid
        return (lo + hi) / 2.0


def _lookback_date(d: str, days: int) -> str:
    return (dt.date.fromisoformat(d) - dt.timedelta(days=days)).isoformat()


def _crypto_top20(reader: AsOfReader, rank_window: Sequence[str], as_of: str) -> Mapping[str, bool]:
    """Which `binance_spot` symbols are top 20 by trailing 30-day quote volume as of D.

    spec/06: the crypto floor tier is "top 20 by trailing 30-day quote volume
    as-of D"; spec/01 gives the 30-day ranking window as the same one used for
    universe eligibility (`SPEC01.crypto_volume_ranking_window_days`).
    `dollar_volume` on a crypto daily bar is the kline quote volume (spec/04).
    """
    start, end = rank_window[0], rank_window[-1]
    bars = reader.panel("binance_spot", None, start, end, as_of=as_of, adjust="none")
    if bars.empty:
        return {}
    windowed = bars[bars["date"].isin(rank_window)]
    volume_by_symbol = windowed.groupby("symbol")["dollar_volume"].sum().sort_values(ascending=False)
    top_n = int(SPEC06_CRYPTO.top_tier_rank)
    top_symbols = set(volume_by_symbol.index[:top_n])
    return {s: (s in top_symbols) for s in volume_by_symbol.index}


def cost_inputs(reader: AsOfReader, lane: str, symbols: Sequence[str], dates: Sequence) -> pd.DataFrame:
    """One row of `CostInputs` fields per (symbol, D), read as of D only.

    For each D, three lane-trading-day windows are built from the lane's
    calendar (`harness.store.calendar_for_lane`), sessions sorted ascending
    with D itself last:

    - the spread/median window: the 20 sessions immediately before D (indices
      D-20 .. D-1 by session offset), used for `half_spread_est` (paired
      consecutive-session AR estimates (s_1,s_2), (s_2,s_3), ..., (s_19,s_20)
      over those 20 sessions -- 19 pairs) and `median_dollar_volume`;
    - the RVOL window: the 21 sessions ending at and including D (D-20 .. D),
      giving the 20 one-day log returns spec/04's `rvol_20` averages;
    - for `crypto` only, the 30 sessions ending at and including D, used to
      rank every `binance_spot` symbol by trailing quote volume for the
      spread-floor tier (spec/06; spec/01 for the window length).

    Every store read passes `as_of=D`, and every read's date range ends at or
    before D, so nothing dated after D is ever fetched (the leakage invariant
    this module's test asserts via `harness.testing.invariance.perturbations`).
    Bars are read with `adjust="split_div"`: within an as-of-D panel a bar
    dated exactly D is unaffected by adjustment (no action can be dated in
    (D, D]), so the same read gives both the adjusted series for the spread
    and RVOL windows and D's own unadjusted close (`close_unadj_d`).
    """
    market = _lane_market(lane)
    calendar_name = calendar_for_lane(lane)
    is_crypto = lane == "crypto"
    p = SPEC06_CRYPTO if is_crypto else SPEC06_EQUITY
    spread_window_days = int(p.spread_window_days)
    symbols = list(symbols)
    dates = sorted({iso_date(d) for d in dates})

    min_sessions = max(_RVOL_SESSIONS, spread_window_days + 1)
    if is_crypto:
        min_sessions = max(min_sessions, int(SPEC01.crypto_volume_ranking_window_days))

    rows: list[dict] = []
    for D in dates:
        window_start = _lookback_date(D, _CALENDAR_LOOKBACK_DAYS)
        sessions = sorted(reader.calendar(calendar_name, window_start, D, as_of=D)["date"].tolist())
        if not sessions or sessions[-1] != D:
            raise ValueError(f"{D!r} is not a {calendar_name} lane trading day known as-of itself")
        if len(sessions) < min_sessions:
            raise ValueError(
                f"only {len(sessions)} {calendar_name} sessions known before {D} "
                f"(need >= {min_sessions}); widen the cost_inputs lookback"
            )
        spread_window = sessions[:-1][-spread_window_days:]
        rvol_window = sessions[-_RVOL_SESSIONS:]

        top20_by_symbol: Mapping[str, bool] = {}
        if is_crypto:
            rank_window = sessions[-int(SPEC01.crypto_volume_ranking_window_days):]
            top20_by_symbol = _crypto_top20(reader, rank_window, D)

        for symbol in symbols:
            bars = reader.panel(market, [symbol], window_start, D, as_of=D, adjust="split_div")
            bars = bars.sort_values("date").reset_index(drop=True)

            window_bars = bars[bars["date"].isin(spread_window)].sort_values("date")
            if len(window_bars) != len(spread_window):
                missing = sorted(set(spread_window) - set(window_bars["date"]))
                raise ValueError(f"{symbol} missing bars on {missing} in the spread window ending {D}")
            spread_est = abdi_ranaldo_spread(
                window_bars["high"].to_numpy(float),
                window_bars["low"].to_numpy(float),
                window_bars["close"].to_numpy(float),
            )
            half_spread_est = spread_est / 2.0
            median_dollar_volume = float(window_bars["dollar_volume"].median())

            rvol_bars = bars[bars["date"].isin(rvol_window)].sort_values("date")
            if len(rvol_bars) != len(rvol_window):
                missing = sorted(set(rvol_window) - set(rvol_bars["date"]))
                raise ValueError(f"{symbol} missing bars on {missing} in the RVOL window ending {D}")
            closes = rvol_bars["close"].to_numpy(float)
            log_rets = np.diff(np.log(closes))
            annualization = _CRYPTO_ANNUALIZATION if is_crypto else _EQUITY_ANNUALIZATION
            rvol_20_d = float(np.std(log_rets, ddof=1) * annualization)

            d_bar = bars[bars["date"] == D]
            if d_bar.empty:
                raise ValueError(f"{symbol} has no bar on signal day {D}")
            close_unadj_d = float(d_bar["close"].iloc[0])

            rows.append(
                {
                    "lane": lane,
                    "symbol": symbol,
                    "signal_date": D,
                    "half_spread_est": half_spread_est,
                    "close_unadj_d": close_unadj_d,
                    "rvol_20_d": rvol_20_d,
                    "median_dollar_volume": median_dollar_volume,
                    "top20_by_quote_volume": (top20_by_symbol.get(symbol, False) if is_crypto else None),
                }
            )

    return pd.DataFrame(
        rows,
        columns=[
            "lane", "symbol", "signal_date", "half_spread_est", "close_unadj_d",
            "rvol_20_d", "median_dollar_volume", "top20_by_quote_volume",
        ],
    )


# --------------------------------------------------------------------- reporting

# spec/06: "the mean cost per side in basis points for entry legs, target exits,
# stop exits and time-stop exits." Delisting and era-end closures are not named in
# that sentence but are reported too, under their own labels, for completeness.
LEG_REPORT_LABELS = {
    "entry": "entry",
    "exit_target": "target",
    "exit_stop": "stop",
    "exit_time": "time_stop",
    "exit_delist": "delist",
    "exit_era_end": "era_end",
}


def cost_report(trades: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Per-lane, per-year cost reporting (spec/06 Costs, "Acceptance").

    `trades` is a per-leg frame (`docs/costs.md` documents the columns): one
    row per leg of a trade, with `lane`, `symbol`, `entry_date` (the trade's
    signal date, used to bucket by year), `leg` (a `LegType`), `notional` (the
    leg's order notional), `spread`, `slippage` and `fee` (fractions of
    notional, as `LegCost` gives them) and `floor_bound`.

    Returns a dict of frames, keyed:

    - `cost_distribution`: `describe()` of the per-leg total cost in basis
      points, by (lane, year).
    - `floor_bound_share`: the share of legs on which the spread floor bound,
      by (lane, year).
    - `mean_cost_bps_by_leg`: the mean total cost per side in basis points, by
      (lane, year, leg) -- leg relabeled per `LEG_REPORT_LABELS`.
    - `component_sums`: each component's summed cost in notional currency
      (`spread_cost`, `slippage_cost`, `fee_cost`) by (lane, year); the
      evaluator divides these by its own gross-return sum to get each
      component's share of gross (spec/06: "each cost component's share of
      gross").
    """
    required = {"lane", "symbol", "entry_date", "leg", "notional", "spread", "slippage", "fee", "floor_bound"}
    missing = required - set(trades.columns)
    if missing:
        raise ValueError(f"cost_report: trades is missing columns {sorted(missing)}")

    df = trades.copy()
    df["year"] = pd.to_datetime(df["entry_date"]).dt.year
    df["total"] = df["spread"] + df["slippage"] + df["fee"]
    df["total_bps"] = df["total"] * 10_000.0

    cost_distribution = (
        df.groupby(["lane", "year"])["total_bps"]
        .describe()
        .rename(columns=lambda c: f"total_bps_{c}")
        .reset_index()
    )

    floor_bound_share = (
        df.groupby(["lane", "year"])["floor_bound"].mean().rename("floor_bound_share").reset_index()
    )

    df["leg_label"] = df["leg"].map(LEG_REPORT_LABELS).fillna(df["leg"])
    mean_cost_bps_by_leg = (
        df.groupby(["lane", "year", "leg_label"])["total_bps"]
        .mean()
        .rename("mean_cost_bps")
        .reset_index()
    )

    df["spread_cost"] = df["spread"] * df["notional"]
    df["slippage_cost"] = df["slippage"] * df["notional"]
    df["fee_cost"] = df["fee"] * df["notional"]
    component_sums = (
        df.groupby(["lane", "year"])[["spread_cost", "slippage_cost", "fee_cost"]].sum().reset_index()
    )

    return {
        "cost_distribution": cost_distribution,
        "floor_bound_share": floor_bound_share,
        "mean_cost_bps_by_leg": mean_cost_bps_by_leg,
        "component_sums": component_sums,
    }

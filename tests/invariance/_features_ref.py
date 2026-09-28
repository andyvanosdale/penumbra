"""Reference implementations of a few spec/04 features, for the feature
invariance test only.

`harness/features.py` (issue 8) does not exist yet. These are deliberately
small, written only to prove `harness.testing.invariance` catches a leaky
window, and are not meant to be reused by the real feature builder. Issue 8
must call `assert_feature_invariance` on its own module.

Annualization here is fixed at sqrt(252) regardless of lane, for simplicity;
the real feature builder is lane-dependent (spec/02 Trading calendars).
"""

from __future__ import annotations

import datetime as dt
import math
from typing import Any

import numpy as np
import pandas as pd

ANNUALIZATION = math.sqrt(252)


def _asof(bars: pd.DataFrame, D) -> pd.DataFrame:
    """Bars dated on or before D, sorted by date. Every reference feature
    filters through this before touching a window, rather than trusting that
    its caller already trimmed the frame — the whole point of the invariance
    test is to catch a feature that skips this step."""

    return bars[bars["date"] <= D].sort_values("date").reset_index(drop=True)


def ret_1(asof: pd.DataFrame) -> float:
    if len(asof) < 2:
        return float("nan")
    c = asof["close"].to_numpy()
    return float(np.log(c[-1] / c[-2]))


def _log_returns(asof: pd.DataFrame) -> np.ndarray:
    c = asof["close"].to_numpy()
    if len(c) < 2:
        return np.array([])
    return np.log(c[1:] / c[:-1])


def rvol_20(asof: pd.DataFrame) -> float:
    rets = _log_returns(asof)
    if len(rets) < 20:
        return float("nan")
    return float(np.std(rets[-20:], ddof=1) * ANNUALIZATION)


def rvol_20_prev(asof: pd.DataFrame) -> float:
    """rvol_20 as of D-1: the same computation with today's row dropped."""

    return rvol_20(asof.iloc[:-1])


def shock(asof: pd.DataFrame) -> float:
    r1 = ret_1(asof)
    prev_vol = rvol_20_prev(asof)
    if math.isnan(r1) or math.isnan(prev_vol) or prev_vol == 0:
        return float("nan")
    daily_prev_vol = prev_vol / ANNUALIZATION
    return float(r1 / daily_prev_vol)


def zscore_20(asof: pd.DataFrame) -> float:
    window = asof["close"].tail(20)
    if len(window) < 20:
        return float("nan")
    std = window.std(ddof=1)
    if std == 0:
        return float("nan")
    return float((window.iloc[-1] - window.mean()) / std)


def vol_pctl_250(asof: pd.DataFrame) -> float:
    window = asof["dollar_volume"].tail(250)
    if len(window) < 250:
        return float("nan")
    rank = int((window.to_numpy() <= window.iloc[-1]).sum())
    return float(rank) / 250.0


def dd_from_20d_high(asof: pd.DataFrame) -> float:
    window = asof["high"].tail(20)
    if len(window) < 20:
        return float("nan")
    return float(asof["close"].iloc[-1] / window.max() - 1.0)


def filing_2d(asof_bars: pd.DataFrame, events: pd.DataFrame | None, D) -> bool:
    """True when an events row has `available_at` on D-1 or D-2 lane trading
    days (spec/04). D-1/D-2 are read off the bars calendar, not calendar-day
    arithmetic, so a Friday filing (available_at rolls to the following
    Monday) is handled correctly."""

    if len(asof_bars) < 2 or events is None or events.empty:
        return False
    trading_days = asof_bars["date"].to_numpy()
    lookback = set(trading_days[-3:-1]) if len(trading_days) >= 3 else set(trading_days[:-1])
    knowable = events[events["available_at"] <= D]
    return bool(knowable["available_at"].isin(lookback).any())


def compute_features(bars: pd.DataFrame, events: pd.DataFrame | None, D) -> dict[str, Any]:
    asof = _asof(bars, D)
    return {
        "ret_1": ret_1(asof),
        "rvol_20": rvol_20(asof),
        "rvol_20_prev": rvol_20_prev(asof),
        "shock": shock(asof),
        "zscore_20": zscore_20(asof),
        "vol_pctl_250": vol_pctl_250(asof),
        "dd_from_20d_high": dd_from_20d_high(asof),
        "filing_2d": filing_2d(asof, events, D),
    }


# --- Mutants: each is a deliberately leaky variant that must fail the
# feature invariance test. ---------------------------------------------------


def compute_features_center_window(bars: pd.DataFrame, events: pd.DataFrame | None, D) -> dict[str, Any]:
    """BROKEN: rvol_20 and zscore_20 use `rolling(..., center=True)` over the
    *full*, untrimmed bars frame, so the window at D reaches past D into
    future rows. Named in the issue 18 acceptance criteria."""

    full = bars.sort_values("date").reset_index(drop=True)
    close = full["close"]
    rets = pd.Series(np.log(close.to_numpy()[1:] / close.to_numpy()[:-1]))
    rvol = rets.rolling(20, center=True).std(ddof=1) * ANNUALIZATION
    # rets[i] is the return landing on full["date"][i+1]; align accordingly.
    rvol_by_date = pd.Series(rvol.to_numpy(), index=full["date"].iloc[1:].to_numpy())
    close_by_date = close.set_axis(full["date"])
    close_roll = close_by_date.rolling(20, center=True)
    zscore_by_date = (close_by_date - close_roll.mean()) / close_roll.std(ddof=1)

    out = compute_features(bars, events, D)
    out["rvol_20"] = float(rvol_by_date.get(D, float("nan")))
    out["zscore_20"] = float(zscore_by_date.get(D, float("nan")))
    r1 = out["ret_1"]
    if not math.isnan(out["rvol_20"]) and out["rvol_20"] != 0 and not math.isnan(r1):
        out["shock"] = float(r1 / (out["rvol_20"] / ANNUALIZATION))
    else:
        out["shock"] = float("nan")
    return out


def compute_features_rvol_prev_window_ends_d_plus_1(bars: pd.DataFrame, events: pd.DataFrame | None, D) -> dict[str, Any]:
    """BROKEN: rvol_20_prev is computed over the window ending D+1 instead of
    D-1, i.e. it reads one bar past the decision date."""

    full = bars.sort_values("date").reset_index(drop=True)
    dates = full["date"].to_numpy()
    pos = np.searchsorted(dates, D)
    if pos + 1 >= len(dates):
        return compute_features(bars, events, D)
    leaky_asof = full.iloc[: pos + 2]  # includes D and D+1
    leaky_rvol_prev = rvol_20(leaky_asof)

    out = compute_features(bars, events, D)
    out["rvol_20_prev"] = leaky_rvol_prev
    r1 = out["ret_1"]
    if not math.isnan(leaky_rvol_prev) and leaky_rvol_prev != 0 and not math.isnan(r1):
        out["shock"] = float(r1 / (leaky_rvol_prev / ANNUALIZATION))
    else:
        out["shock"] = float("nan")
    return out


def filing_2d_calendar_day_approximation(bars: pd.DataFrame, filings: pd.DataFrame, D) -> bool:
    """BROKEN: derives `available_at` as filing_date + 1 CALENDAR day instead
    of the next lane trading day. For a Friday filing this lands on a
    Saturday, which never equals a (weekday) trading day, so the filing is
    silently dropped from every filing_2d check it should have set. This is a
    correctness bug in the available_at rule, not a leakage-under-perturbation
    one (the miscomputed date never depends on anything dated after D), so it
    is exercised by a direct comparison against the reference rather than
    through `assert_feature_invariance`; see the test module docstring."""

    asof = _asof(bars, D)
    if len(asof) < 2 or filings.empty:
        return False
    trading_days = asof["date"].to_numpy()
    lookback = set(trading_days[-3:-1]) if len(trading_days) >= 3 else set(trading_days[:-1])
    approx_available_at = filings["filing_date"].map(lambda d: d + dt.timedelta(days=1))
    knowable = approx_available_at[approx_available_at <= D]
    return bool(knowable.isin(lookback).any())

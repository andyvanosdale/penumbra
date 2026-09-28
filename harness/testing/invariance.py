"""Reusable leakage-invariance machinery (spec/02 Leakage tests).

Two of the three leakage tests are generic across every feature and every exit
rule: recompute the same quantity after perturbing or deleting everything
dated after the decision date, and check nothing moves. This module is that
machinery. It has no opinion about what a feature or an exit level is; the
caller supplies a `compute` or `levels` callable and this module drives it
through a fixed set of perturbations.

`harness/features.py` (issue 8) and `harness/labels.py` (issues 9, 10) are not
built yet. Until they land, `tests/invariance/` exercises this module against
small reference implementations of a few spec/04 features and a reference
exit-level function, written in the test module only. Issues 8, 9 and 10 must
call `assert_feature_invariance` and `assert_exit_invariance` on the real
modules when they land.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence

import numpy as np
import pandas as pd

DateLike = Any

_MULTIPLY_RANGE = (0.5, 1.5)
_SHOCK_FACTORS = (0.1, 10.0)  # -90% and +900%, spec/02 "extreme shock"


@dataclass(frozen=True)
class Position:
    """A position filled the lane trading day after its signal day.

    `fill_price` is the entry fill price (spec/05: equities fill at the open of
    the next lane trading day), carried as data rather than re-derived from
    `bars` so that `levels()` is not forced to read the fill bar at all.
    """

    signal_date: DateLike
    fill_date: DateLike
    fill_price: float


def _is_number_dtype(series: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series)


def _numeric_columns(df: pd.DataFrame, exclude: Sequence[str]) -> list[str]:
    return [c for c in df.columns if c not in exclude and _is_number_dtype(df[c])]


def _delete_after(df: pd.DataFrame | None, date_col: str, D: DateLike, rng: np.random.Generator) -> pd.DataFrame | None:
    if df is None:
        return None
    return df[df[date_col] <= D].reset_index(drop=True).copy()


def _multiply_after(df: pd.DataFrame | None, date_col: str, D: DateLike, rng: np.random.Generator) -> pd.DataFrame | None:
    if df is None:
        return None
    out = df.copy()
    mask = out[date_col] > D
    n = int(mask.sum())
    if n == 0:
        return out
    cols = _numeric_columns(out, exclude=[date_col])
    factors = rng.uniform(_MULTIPLY_RANGE[0], _MULTIPLY_RANGE[1], size=n)
    for c in cols:
        out.loc[mask, c] = out.loc[mask, c].to_numpy() * factors
    return out


def _shock_after(df: pd.DataFrame | None, date_col: str, D: DateLike, rng: np.random.Generator) -> pd.DataFrame | None:
    if df is None:
        return None
    out = df.copy()
    mask = out[date_col] > D
    n = int(mask.sum())
    if n == 0:
        return out
    cols = _numeric_columns(out, exclude=[date_col])
    factors = rng.choice(_SHOCK_FACTORS, size=n)
    for c in cols:
        out.loc[mask, c] = out.loc[mask, c].to_numpy() * factors
    return out


def _shuffle_after(df: pd.DataFrame | None, date_col: str, D: DateLike, rng: np.random.Generator) -> pd.DataFrame | None:
    if df is None:
        return None
    out = df.copy()
    mask = out[date_col] > D
    idx = out.index[mask]
    if len(idx) <= 1:
        return out
    perm = rng.permutation(idx)
    cols = [c for c in out.columns if c != date_col]
    out.loc[idx, cols] = df.loc[perm, cols].to_numpy()
    return out


def perturbations(
    bars: pd.DataFrame,
    events: pd.DataFrame | None,
    D: DateLike,
    rng: np.random.Generator,
    *,
    date_col: str = "date",
    event_date_col: str = "available_at",
) -> Iterator[tuple[str, pd.DataFrame, pd.DataFrame | None]]:
    """Yield named (bars, events) variants perturbing everything dated after D.

    Every row with `date_col <= D` in `bars`, and `event_date_col <= D` in
    `events`, is bit-identical across every variant. Rows dated after D are, in
    turn:

    - `deleted`: dropped entirely.
    - `multiplied`: every numeric column scaled by an independent random factor
      per row (uniform in [0.5, 1.5]); the same factor is used across all of a
      row's numeric columns so OHLC ordering and positivity survive.
    - `shocked`: every numeric column scaled by an extreme per-row factor (0.1
      or 10.0, i.e. -90% or +900%), again shared across a row's columns.
    - `shuffled`: whole rows (every column but the date) are permuted among the
      dates after D, so the same values appear but attached to different
      dates.

    `events` may be `None` (no event stream to perturb, e.g. exit invariance),
    in which case the yielded events variant is always `None`.
    """

    variants = (
        ("deleted", _delete_after),
        ("multiplied", _multiply_after),
        ("shocked", _shock_after),
        ("shuffled", _shuffle_after),
    )
    for name, fn in variants:
        new_bars = fn(bars, date_col, D, rng)
        new_events = fn(events, event_date_col, D, rng)
        yield name, new_bars, new_events


def sample_dates(dates: Sequence[DateLike], n: int, rng: np.random.Generator, *, edge_window: int = 3) -> list[DateLike]:
    """A seeded sample of up to `n` dates from `dates`, biased to include the
    first and last `edge_window` dates (feature and exit windows are most
    likely to break at their edges) plus a random draw of the remainder.
    """

    ordered = sorted(dates)
    if len(ordered) <= n:
        return ordered
    edges = list(dict.fromkeys(ordered[:edge_window] + ordered[-edge_window:]))
    remaining = [d for d in ordered if d not in set(edges)]
    extra = max(n - len(edges), 0)
    if extra and remaining:
        chosen = rng.choice(len(remaining), size=min(extra, len(remaining)), replace=False)
        edges.extend(remaining[i] for i in chosen)
    return sorted(dict.fromkeys(edges))


def _values_equal(a: Any, b: Any) -> bool:
    a_na, b_na = pd.isna(a), pd.isna(b)
    if a_na or b_na:
        return bool(a_na) and bool(b_na)
    return bool(a == b)


def assert_feature_invariance(
    compute: Callable[[pd.DataFrame, pd.DataFrame | None, DateLike], Mapping[str, Any]],
    bars: pd.DataFrame,
    events: pd.DataFrame | None,
    samples: Iterable[DateLike],
    rng: np.random.Generator,
) -> None:
    """Assert every value `compute(bars, events, D)` gives is unchanged when
    everything dated after D is perturbed or deleted, for every D in
    `samples`. NaN-aware and bit-exact: no tolerance, since a leaky window can
    hide inside one. Raises `AssertionError` naming the feature, D and the
    perturbation on the first mismatch.
    """

    for D in samples:
        baseline = compute(bars, events, D)
        for pname, bars_variant, events_variant in perturbations(bars, events, D, rng):
            try:
                got = compute(bars_variant, events_variant, D)
            except Exception as exc:  # noqa: BLE001 - a crash IS an invariance failure
                raise AssertionError(
                    f"compute(...) at D={D!r} raised {exc!r} under perturbation {pname!r} "
                    "(it depends on data dated after D that this perturbation removed or changed)"
                ) from exc
            for feature, base_val in baseline.items():
                new_val = got.get(feature)
                if not _values_equal(base_val, new_val):
                    raise AssertionError(
                        f"feature {feature!r} at D={D!r} changed under perturbation "
                        f"{pname!r}: {base_val!r} -> {new_val!r}"
                    )


def _protect_fill_open(bars_variant: pd.DataFrame, original_bars: pd.DataFrame, position: Position, date_col: str) -> pd.DataFrame:
    """Restore the fill bar's open in `bars_variant` to its original value.

    The fill bar (`position.fill_date`) is dated after the signal day, so
    every other perturbation touches it. Its open is left alone because it is
    definitionally the entry fill price the stop is defined from (spec/05:
    entry fill - 1.5 x the signal day's range); perturbing it would make even
    a correct `levels()` implementation that re-derives the fill price from
    `bars` disagree with itself. When the fill bar's row is deleted entirely
    (the `deleted` variant) there is nothing to restore: a correct `levels()`
    must get the fill price from `position.fill_price`, not from `bars`, so
    that variant is left as-is on purpose.
    """

    mask = bars_variant[date_col] == position.fill_date
    if not mask.any():
        return bars_variant
    orig_mask = original_bars[date_col] == position.fill_date
    if not orig_mask.any():
        return bars_variant
    out = bars_variant.copy()
    out.loc[mask, "open"] = original_bars.loc[orig_mask, "open"].to_numpy()
    return out


def assert_exit_invariance(
    levels: Callable[[pd.DataFrame, Position], tuple[float, float]],
    bars: pd.DataFrame,
    fills: Iterable[Position],
    rng: np.random.Generator,
    *,
    date_col: str = "date",
) -> None:
    """Assert `levels(bars, position)` gives the same (target, stop) pair when
    every bar dated `position.fill_date` (D+1) and later is perturbed or
    deleted, for every position in `fills`.

    Every bar is perturbed except the fill bar's open (see
    `_protect_fill_open`); the entry fill price is fixed at entry (spec/05)
    and this is the invariant under test, not a hole in the perturbation.
    Raises `AssertionError` naming the position and the perturbation on the
    first mismatch.
    """

    for position in fills:
        baseline = levels(bars, position)
        for pname, bars_variant, _ in perturbations(bars, None, position.signal_date, rng, date_col=date_col):
            bars_variant = _protect_fill_open(bars_variant, bars, position, date_col)
            try:
                got = levels(bars_variant, position)
            except Exception as exc:  # noqa: BLE001 - a crash IS an invariance failure
                raise AssertionError(
                    f"levels(...) for position signal_date={position.signal_date!r} "
                    f"fill_date={position.fill_date!r} raised {exc!r} under perturbation "
                    f"{pname!r} (it depends on a bar after the signal day that this "
                    "perturbation removed or changed)"
                ) from exc
            if not _values_equal(got[0], baseline[0]) or not _values_equal(got[1], baseline[1]):
                raise AssertionError(
                    f"exit levels for position signal_date={position.signal_date!r} "
                    f"fill_date={position.fill_date!r} changed under perturbation "
                    f"{pname!r}: target/stop {baseline!r} -> {got!r}"
                )

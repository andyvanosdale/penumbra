"""Reference exit-level function for the exit invariance test only.

`harness/labels.py` (issues 9, 10) does not exist yet. This is a small
stand-in proving `harness.testing.invariance.assert_exit_invariance` catches
the two mutants named in the issue 18 acceptance criteria. Issues 9 and 10
must call `assert_exit_invariance` on their own module.
"""

from __future__ import annotations

from harness.testing import Position


def levels_reference(bars, position: Position) -> tuple[float, float]:
    """spec/05 locked parameters: target = mean of the 20 closes ending at the
    signal day D; hard stop = entry fill price - 1.5 x D's (high - low), both
    fixed at entry and computed only from data dated on or before D."""

    D = position.signal_date
    asof = bars[bars["date"] <= D].sort_values("date")
    target = float(asof["close"].tail(20).mean())
    row_d = asof[asof["date"] == D].iloc[0]
    stop = float(position.fill_price - 1.5 * (row_d["high"] - row_d["low"]))
    return target, stop


# --- Mutants: each is a deliberately leaky variant that must fail the exit
# invariance test. ------------------------------------------------------------


def levels_mutant_fill_day_range(bars, position: Position) -> tuple[float, float]:
    """BROKEN: the stop's range comes from the fill bar (D+1) instead of the
    signal day D. Named in the issue 18 acceptance criteria."""

    D = position.signal_date
    asof = bars[bars["date"] <= D].sort_values("date")
    target = float(asof["close"].tail(20).mean())
    fill_rows = bars[bars["date"] == position.fill_date]
    row_fill = fill_rows.iloc[0]
    stop = float(position.fill_price - 1.5 * (row_fill["high"] - row_fill["low"]))
    return target, stop


def levels_mutant_rolling_target(bars, position: Position) -> tuple[float, float]:
    """BROKEN: the target is the 20-day mean of closes ending at the *last*
    bar in the frame, not the signal day D, so it keeps moving as bars after D
    arrive instead of being fixed at entry."""

    D = position.signal_date
    full = bars.sort_values("date")
    target = float(full["close"].tail(20).mean())
    asof = full[full["date"] <= D]
    row_d = asof[asof["date"] == D].iloc[0]
    stop = float(position.fill_price - 1.5 * (row_d["high"] - row_d["low"]))
    return target, stop

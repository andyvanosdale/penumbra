"""Exit invariance (spec/02 Leakage tests, spec/05 Strategy rule).

`harness/labels.py` (issues 9, 10) does not exist yet, so this exercises
`harness.testing.invariance.assert_exit_invariance` against a reference
target/stop level function (`tests/invariance/_exits_ref.py`) and against
deliberately broken variants the acceptance criteria name. Issues 9 and 10
must call `assert_exit_invariance` on the real exit simulator.
"""

from __future__ import annotations

import numpy as np
import pytest

from harness.testing import Position, assert_exit_invariance, sample_dates
from tests.invariance._exits_ref import (
    levels_mutant_fill_day_range,
    levels_mutant_rolling_target,
    levels_reference,
)
from tests.invariance._synth import build_panel

pytestmark = pytest.mark.leakage


def _fills_for(bars, rng, n=6) -> list[Position]:
    """Positions filled the trading day after a sampled signal day, holding
    entries near the 20-day target window's edge and near the end of the
    series (so the fill day and the following bars actually exist)."""

    dates = bars["date"].tolist()
    # Need 20 bars ending at D for the target window, and a D+1 to fill on.
    eligible = dates[19:-1]
    edge_indices = (19, 20, 21, len(dates) - 3, len(dates) - 2)
    edge_dates = [dates[i] for i in edge_indices if 19 <= i < len(dates) - 1]
    samples = set(sample_dates(eligible, n, rng)) | set(edge_dates)

    by_date = bars.set_index("date")
    fills = []
    for D in sorted(samples):
        idx = dates.index(D)
        fill_date = dates[idx + 1]
        fill_price = float(by_date.loc[fill_date, "open"])
        fills.append(Position(signal_date=D, fill_date=fill_date, fill_price=fill_price))
    return fills


@pytest.fixture(scope="module")
def panel():
    return build_panel(lanes=("smallcap", "crypto"), names_per_lane=2, seed=7)


def test_reference_levels_are_invariant(panel):
    for name in panel:
        rng = np.random.default_rng(hash((name.lane, name.symbol, "exit")) % (2**32))
        fills = _fills_for(name.bars, rng)
        assert_exit_invariance(levels_reference, name.bars, fills, rng)


def test_fill_day_range_mutant_fails_invariance(panel):
    name = panel[0]
    rng = np.random.default_rng(3)
    fills = _fills_for(name.bars, rng)
    with pytest.raises(AssertionError, match="perturbation"):
        assert_exit_invariance(levels_mutant_fill_day_range, name.bars, fills, rng)


def test_rolling_target_mutant_fails_invariance(panel):
    name = panel[0]
    rng = np.random.default_rng(4)
    fills = _fills_for(name.bars, rng)
    with pytest.raises(AssertionError, match="perturbation"):
        assert_exit_invariance(levels_mutant_rolling_target, name.bars, fills, rng)

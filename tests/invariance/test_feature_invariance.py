"""Feature invariance (spec/02 Leakage tests, spec/04 Features and labels).

`harness/features.py` (issue 8) does not exist yet, so this exercises
`harness.testing.invariance.assert_feature_invariance` against a small
reference implementation of a few spec/04 features with the trickiest
windows (`tests/invariance/_features_ref.py`), and against deliberately
broken variants of it that the acceptance criteria name. Issue 8 must call
`assert_feature_invariance` on the real feature builder.

The filing_2d "+1 calendar day" mutant is checked separately, by direct
comparison against the reference rather than through
`assert_feature_invariance`: a filing date approximated by calendar-day
arithmetic is either right or wrong entirely from data on or before D — it
never depends on anything dated after D, so it is a correctness bug in the
available_at rule, not a case the leakage-invariance machinery (which only
perturbs data after D) can expose.
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import pytest

from harness.testing import assert_feature_invariance, sample_dates
from tests.invariance._features_ref import (
    compute_features,
    compute_features_center_window,
    compute_features_rvol_prev_window_ends_d_plus_1,
    filing_2d,
    filing_2d_calendar_day_approximation,
)
from tests.invariance._synth import build_panel, gbm_bars

pytestmark = pytest.mark.leakage

# Window sizes used by the reference features (20-day rvol/zscore/dd, 250-day
# vol_pctl); sampling near these edges is where an off-by-one leak hides.
_WINDOW_EDGE_INDICES = (19, 20, 21, 249, 250, 251)


def _samples_for(bars, rng, n=6) -> list:
    dates = bars["date"].tolist()
    samples = set(sample_dates(dates, n, rng))
    samples.update(dates[i] for i in _WINDOW_EDGE_INDICES if 0 <= i < len(dates))
    return sorted(samples)


@pytest.fixture(scope="module")
def panel():
    return build_panel(lanes=("smallcap", "crypto"), names_per_lane=2, seed=42)


def test_reference_features_are_invariant(panel):
    for name in panel:
        rng = np.random.default_rng(hash((name.lane, name.symbol)) % (2**32))
        samples = _samples_for(name.bars, rng)
        assert_feature_invariance(compute_features, name.bars, name.events, samples, rng)


def test_center_window_mutant_fails_invariance(panel):
    name = panel[0]
    rng = np.random.default_rng(1)
    samples = _samples_for(name.bars, rng)
    with pytest.raises(AssertionError, match="perturbation"):
        assert_feature_invariance(compute_features_center_window, name.bars, name.events, samples, rng)


def test_rvol_20_prev_window_ending_d_plus_1_mutant_fails_invariance(panel):
    name = panel[0]
    rng = np.random.default_rng(2)
    samples = _samples_for(name.bars, rng)
    with pytest.raises(AssertionError, match="perturbation"):
        assert_feature_invariance(
            compute_features_rvol_prev_window_ends_d_plus_1, name.bars, name.events, samples, rng
        )


def test_filing_2d_calendar_day_approximation_misses_a_friday_filing():
    """A filing on a Friday, accepted after the close: the correct
    available_at is the following Monday (the next lane trading day, spec/02
    & spec/04). The calendar-day approximation instead lands on Saturday,
    which is never a trading day, so it can never match a D-1/D-2 lookback
    and the flag silently misses a filing it should have caught."""

    dates = [
        dt.date(2020, 1, 3),  # Friday: the filing
        dt.date(2020, 1, 6),  # Monday: true available_at
        dt.date(2020, 1, 7),  # Tuesday: D, so D-1 = Monday
        dt.date(2020, 1, 8),  # Wednesday: D, so D-2 = Monday
    ]
    bars = gbm_bars(dates, seed=0)
    events = pd.DataFrame(
        [{"filing_date": dates[0], "available_at": dates[1], "eventcodes": "23"}]
    )

    for D in (dates[2], dates[3]):
        asof_bars = bars[bars["date"] <= D]
        correct = filing_2d(asof_bars, events, D)
        broken = filing_2d_calendar_day_approximation(bars, events, D)
        assert correct is True, f"reference filing_2d should be True at D={D}"
        assert broken is False, f"calendar-day approximation should miss the filing at D={D}"

"""Direct tests of `harness.testing.invariance.perturbations` — the shared
machinery every other test in this package relies on."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from harness.testing.invariance import perturbations
from tests.invariance._synth import build_panel

pytestmark = pytest.mark.leakage


def _bars_and_events():
    panel = build_panel(lanes=("smallcap",), names_per_lane=1, seed=1)
    name = panel[0]
    return name.bars, name.events


def test_rows_on_or_before_d_are_untouched_in_every_variant():
    bars, events = _bars_and_events()
    rng = np.random.default_rng(0)
    D = bars["date"].iloc[100]
    before = bars[bars["date"] <= D].reset_index(drop=True)
    for _, bars_variant, _ in perturbations(bars, events, D, rng):
        got = bars_variant[bars_variant["date"] <= D].reset_index(drop=True)
        pd.testing.assert_frame_equal(got, before)


def test_deleted_variant_drops_rows_after_d():
    bars, events = _bars_and_events()
    rng = np.random.default_rng(0)
    D = bars["date"].iloc[100]
    for name, bars_variant, _ in perturbations(bars, events, D, rng):
        if name == "deleted":
            assert (bars_variant["date"] <= D).all()
            return
    raise AssertionError("no 'deleted' variant yielded")


def test_multiplied_and_shocked_variants_change_rows_after_d():
    bars, events = _bars_and_events()
    rng = np.random.default_rng(0)
    D = bars["date"].iloc[100]
    after = bars["date"] > D
    for name, bars_variant, _ in perturbations(bars, events, D, rng):
        if name in ("multiplied", "shocked"):
            changed = bars_variant.loc[after, "close"].to_numpy() != bars.loc[after, "close"].to_numpy()
            assert changed.any(), f"{name} left every close after D unchanged"


def test_shuffled_variant_keeps_the_same_dates_and_values_after_d():
    bars, events = _bars_and_events()
    rng = np.random.default_rng(0)
    D = bars["date"].iloc[100]
    for name, bars_variant, _ in perturbations(bars, events, D, rng):
        if name == "shuffled":
            after = bars_variant["date"] > D
            assert set(bars_variant.loc[after, "date"]) == set(bars.loc[after, "date"])
            assert sorted(bars_variant.loc[after, "close"]) == sorted(bars.loc[after, "close"])
            return
    raise AssertionError("no 'shuffled' variant yielded")


def test_events_may_be_none():
    bars, _ = _bars_and_events()
    rng = np.random.default_rng(0)
    D = bars["date"].iloc[100]
    for _, _, events_variant in perturbations(bars, None, D, rng):
        assert events_variant is None

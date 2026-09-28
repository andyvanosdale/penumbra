"""`harness.universe.sanity_report` (spec/01 Parameters: target universe size,
persistent excursions flagged not dropped)."""

from __future__ import annotations

import pandas as pd
import pytest

from harness import universe


def _membership(rows: list[tuple[str, str, str]]) -> pd.DataFrame:
    """rows: (lane, date, symbol)."""
    return pd.DataFrame(rows, columns=["lane", "date", "symbol"])


def _dates(n: int, start: int = 0) -> list[str]:
    return [f"2021-01-{d:02d}" for d in range(start + 1, start + 1 + n)]


def test_in_range_size_is_not_flagged():
    dates = _dates(3)
    rows = [("smallcap", d, f"S{i}") for d in dates for i in range(600)]  # inside 500-1500
    report = universe.sanity_report(_membership(rows))
    assert not report["out_of_range"].any()
    assert not report["persistent_excursion"].any()
    assert (report["n"] == 600).all()


def test_out_of_range_is_flagged_but_present():
    dates = _dates(3)
    rows = [("smallcap", d, f"S{i}") for d in dates for i in range(10)]  # far below 500
    report = universe.sanity_report(_membership(rows))
    assert report["out_of_range"].all()
    assert len(report) == 3, "excursions are flagged, never dropped from the report"


def test_short_excursion_is_not_persistent():
    dates = _dates(universe.PERSISTENT_SESSIONS - 1)
    rows = [("smallcap", d, f"S{i}") for d in dates for i in range(10)]
    report = universe.sanity_report(_membership(rows))
    assert report["out_of_range"].all()
    assert not report["persistent_excursion"].any()


def test_run_at_or_above_the_threshold_is_persistent():
    dates = _dates(universe.PERSISTENT_SESSIONS)
    rows = [("smallcap", d, f"S{i}") for d in dates for i in range(10)]
    report = universe.sanity_report(_membership(rows))
    assert report["persistent_excursion"].all()


def test_persistence_is_per_lane_and_does_not_bridge_a_return_to_range():
    dates = _dates(universe.PERSISTENT_SESSIONS + 4)
    rows = []
    for i, d in enumerate(dates):
        n = 10 if i < 5 else 700  # a short excursion, then back in range
        rows += [("smallcap", d, f"S{j}") for j in range(n)]
    report = universe.sanity_report(_membership(rows)).set_index("date")
    assert report.loc[dates[0], "out_of_range"]
    assert not report.loc[dates[0], "persistent_excursion"], "run is shorter than the threshold"
    assert not report.loc[dates[-1], "out_of_range"]


def test_unranged_lane_is_never_flagged():
    rows = [("crypto", d, f"S{i}") for d in _dates(3) for i in range(5)]
    report = universe.sanity_report(_membership(rows))
    assert not report["out_of_range"].any()
    assert report["low"].isna().all() and report["high"].isna().all()


def test_custom_ranges_are_honored():
    rows = [("smallcap", d, f"S{i}") for d in _dates(1) for i in range(5)]
    report = universe.sanity_report(_membership(rows), ranges={"smallcap": (0, 10)})
    assert not report["out_of_range"].any()

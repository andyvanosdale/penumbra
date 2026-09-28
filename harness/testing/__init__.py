"""Reusable leakage-invariance machinery (spec/02 Leakage tests).

See `harness.testing.invariance` for the implementation.
"""

from __future__ import annotations

from .invariance import (
    Position,
    assert_exit_invariance,
    assert_feature_invariance,
    perturbations,
    sample_dates,
)

__all__ = [
    "Position",
    "assert_exit_invariance",
    "assert_feature_invariance",
    "perturbations",
    "sample_dates",
]

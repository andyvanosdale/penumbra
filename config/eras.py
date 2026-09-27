"""Locked era split (plan §6.1). Do not edit without a research-log entry.

The holdout era must be touched exactly once, at the very end. These dates are
imported everywhere rather than hard-coded so the discipline is enforced in one
place.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass


@dataclass(frozen=True)
class Era:
    name: str
    start: _dt.date
    end: _dt.date  # inclusive

    def contains(self, d: _dt.date) -> bool:
        return self.start <= d <= self.end


# Development: explore freely, build features, tune.
DEVELOPMENT = Era("development", _dt.date(2015, 1, 1), _dt.date(2020, 12, 31))
# Validation: peek sparingly, only to confirm a locked design.
VALIDATION = Era("validation", _dt.date(2021, 1, 1), _dt.date(2022, 12, 31))
# Holdout: touch ONCE, at the very end.
HOLDOUT = Era("holdout", _dt.date(2023, 1, 1), _dt.date(2100, 1, 1))

ERAS = {e.name: e for e in (DEVELOPMENT, VALIDATION, HOLDOUT)}


def era_for(d: _dt.date) -> str:
    for era in (DEVELOPMENT, VALIDATION, HOLDOUT):
        if era.contains(d):
            return era.name
    raise ValueError(f"date {d} falls outside all defined eras")

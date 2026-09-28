"""Per-lane era bounds (spec/03-eras-and-holdout.md). Locked; changed only by a
spec change with a decision-log entry, never in response to a result.

`legacy/eras.py` keeps the old news-project split (2015/2021/2023) for the
day-of-week plumbing test only; it is not read from here.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass

LANES = ("smallcap", "discovered", "crypto")

_ERA_NAMES = ("dev", "validation", "holdout")


@dataclass(frozen=True)
class Era:
    name: str
    start: _dt.date
    end: _dt.date | None  # inclusive; None means open-ended (unfixed holdout end)

    def contains(self, d: _dt.date) -> bool:
        if self.end is None:
            return self.start <= d
        return self.start <= d <= self.end


# spec/03 era table. Equities (smallcap, discovered) share one split; crypto has
# its own. The holdout end is None until fixed and logged by an unlocked run
# (spec/03 "Holdout").
_EQUITY_ERAS = {
    "dev": Era("dev", _dt.date(2010, 1, 1), _dt.date(2020, 12, 31)),
    "validation": Era("validation", _dt.date(2021, 1, 1), _dt.date(2023, 12, 31)),
    "holdout": Era("holdout", _dt.date(2024, 1, 1), None),
}

_CRYPTO_ERAS = {
    "dev": Era("dev", _dt.date(2018, 1, 1), _dt.date(2022, 12, 31)),
    "validation": Era("validation", _dt.date(2023, 1, 1), _dt.date(2024, 12, 31)),
    "holdout": Era("holdout", _dt.date(2025, 1, 1), None),
}

_ERAS_BY_LANE = {
    "smallcap": _EQUITY_ERAS,
    "discovered": _EQUITY_ERAS,
    "crypto": _CRYPTO_ERAS,
}

HOLDOUT_START = {lane: eras["holdout"].start for lane, eras in _ERAS_BY_LANE.items()}


def era(lane: str, name: str) -> Era:
    """The named era (`dev`, `validation` or `holdout`) for `lane`."""
    try:
        lane_eras = _ERAS_BY_LANE[lane]
    except KeyError:
        raise ValueError(f"unknown lane {lane!r}; expected one of {LANES}") from None
    try:
        return lane_eras[name]
    except KeyError:
        raise ValueError(f"unknown era {name!r}; expected one of {_ERA_NAMES}") from None


def era_for(lane: str, date: _dt.date) -> str:
    """The name of the era `date` falls in, for `lane`."""
    lane_eras = _ERAS_BY_LANE[lane] if lane in _ERAS_BY_LANE else None
    if lane_eras is None:
        raise ValueError(f"unknown lane {lane!r}; expected one of {LANES}")
    for name in _ERA_NAMES:
        if lane_eras[name].contains(date):
            return name
    raise ValueError(f"date {date} falls outside all defined eras for lane {lane!r}")

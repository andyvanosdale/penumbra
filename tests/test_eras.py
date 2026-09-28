"""spec/03-eras-and-holdout.md era table, asserted date by date."""

from __future__ import annotations

import datetime as _dt

import pytest

from config import eras


def test_lanes():
    assert eras.LANES == ("smallcap", "discovered", "crypto")


@pytest.mark.parametrize("lane", ["smallcap", "discovered"])
def test_equity_era_bounds(lane):
    dev = eras.era(lane, "dev")
    assert dev.start == _dt.date(2010, 1, 1)
    assert dev.end == _dt.date(2020, 12, 31)

    validation = eras.era(lane, "validation")
    assert validation.start == _dt.date(2021, 1, 1)
    assert validation.end == _dt.date(2023, 12, 31)

    holdout = eras.era(lane, "holdout")
    assert holdout.start == _dt.date(2024, 1, 1)
    assert holdout.end is None


def test_crypto_era_bounds():
    dev = eras.era("crypto", "dev")
    assert dev.start == _dt.date(2018, 1, 1)
    assert dev.end == _dt.date(2022, 12, 31)

    validation = eras.era("crypto", "validation")
    assert validation.start == _dt.date(2023, 1, 1)
    assert validation.end == _dt.date(2024, 12, 31)

    holdout = eras.era("crypto", "holdout")
    assert holdout.start == _dt.date(2025, 1, 1)
    assert holdout.end is None


def test_holdout_start():
    assert eras.HOLDOUT_START == {
        "smallcap": _dt.date(2024, 1, 1),
        "discovered": _dt.date(2024, 1, 1),
        "crypto": _dt.date(2025, 1, 1),
    }


@pytest.mark.parametrize(
    "lane,date,expected",
    [
        ("smallcap", _dt.date(2010, 1, 1), "dev"),
        ("smallcap", _dt.date(2020, 12, 31), "dev"),
        ("smallcap", _dt.date(2021, 1, 1), "validation"),
        ("smallcap", _dt.date(2023, 12, 31), "validation"),
        ("smallcap", _dt.date(2024, 1, 1), "holdout"),
        ("smallcap", _dt.date(2100, 1, 1), "holdout"),
        ("discovered", _dt.date(2021, 1, 1), "validation"),
        ("crypto", _dt.date(2018, 1, 1), "dev"),
        ("crypto", _dt.date(2022, 12, 31), "dev"),
        ("crypto", _dt.date(2023, 1, 1), "validation"),
        ("crypto", _dt.date(2024, 12, 31), "validation"),
        ("crypto", _dt.date(2025, 1, 1), "holdout"),
    ],
)
def test_era_for(lane, date, expected):
    assert eras.era_for(lane, date) == expected


def test_era_for_rejects_gap_date():
    # 2009-12-31 is before every lane's dev era starts.
    with pytest.raises(ValueError):
        eras.era_for("smallcap", _dt.date(2009, 12, 31))


def test_era_rejects_unknown_lane():
    with pytest.raises(ValueError):
        eras.era("mid_cap", "dev")


def test_era_rejects_unknown_name():
    with pytest.raises(ValueError):
        eras.era("smallcap", "test")


def test_era_contains_is_inclusive_both_ends():
    dev = eras.era("smallcap", "dev")
    assert dev.contains(dev.start)
    assert dev.contains(dev.end)
    assert not dev.contains(dev.end + _dt.timedelta(days=1))


def test_open_ended_holdout_contains_far_future():
    holdout = eras.era("crypto", "holdout")
    assert holdout.contains(_dt.date(2099, 1, 1))

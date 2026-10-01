"""Leakage guard for the screening signals (proposal section 8, item 3).

Perturb every bar after D; the candidate (or score / position) matrix at and before D must
not change, for every signal in the registry, through the real feature panel and arrays.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from experiments.screen import data, signals
from tests.screen._synth import crypto_klines, equity_bars, perturb_after

EVENT = ["v1", "1a", "1b-5d", "1b-21d", "1c-short", "1c-long"]
RANK = ["1d", "1e"]


def _matrix(sig, A):
    if sig.MODE in ("event", "v1"):
        return sig.candidates(A).astype(float)
    if hasattr(sig, "position"):
        return sig.position(A).astype(float)
    return sig.scores(A)


def _same_through(cut_row: int, M1, M2):
    a, b = M1[: cut_row + 1], M2[: cut_row + 1]
    assert a.shape == b.shape
    assert np.array_equal(np.isnan(a), np.isnan(b))
    assert np.allclose(np.nan_to_num(a), np.nan_to_num(b), rtol=0, atol=0)


@pytest.fixture(scope="module")
def equity_pair():
    bars = equity_bars()
    cut = pd.Timestamp(sorted(bars["date"].unique())[330])
    A1 = data.build_arrays(data.equity_features(bars, "2019-01-01", "2021-12-31"), "equity")
    A2 = data.build_arrays(data.equity_features(perturb_after(bars, cut), "2019-01-01", "2021-12-31"), "equity")
    return cut, A1, A2


@pytest.fixture(scope="module")
def crypto_pair():
    d1, h1 = crypto_klines()
    cut = pd.Timestamp("2020-01-15")
    A1 = data.build_arrays(data.crypto_features(d1, "2019-01-01", "2021-12-31"), "crypto", h1)
    A2 = data.build_arrays(data.crypto_features(perturb_after(d1, cut, date_col="open_time"), "2019-01-01", "2021-12-31"), "crypto",
                           perturb_after(h1, cut + pd.Timedelta(hours=1), date_col="open_time"))
    return cut, A1, A2


@pytest.mark.parametrize("name", EVENT + RANK)
def test_signal_matrix_at_D_is_unchanged_by_bars_after_D_equity(name, equity_pair):
    cut, A1, A2 = equity_pair
    sig = signals.load(name)
    row = A1["cal"].get_loc(cut)
    M1, M2 = _matrix(sig, A1), _matrix(sig, A2)
    _same_through(row, M1, M2)
    # the perturbation did reach the arrays after D (the test is not vacuous)
    assert not np.allclose(np.nan_to_num(A1["a_close"][row + 1:]), np.nan_to_num(A2["a_close"][row + 1:]))


@pytest.mark.parametrize("name", EVENT + RANK)
def test_signal_matrix_at_D_is_unchanged_by_bars_after_D_crypto(name, crypto_pair):
    cut, A1, A2 = crypto_pair
    sig = signals.load(name)
    row = A1["cal"].get_loc(cut)
    _same_through(row, _matrix(sig, A1), _matrix(sig, A2))
    assert np.array_equal(A1["in_universe"][: row + 1], A2["in_universe"][: row + 1])
    assert not np.allclose(np.nan_to_num(A1["o1"][row + 2:]), np.nan_to_num(A2["o1"][row + 2:]))


def test_universe_and_features_at_D_are_unchanged_by_bars_after_D(equity_pair):
    cut, A1, A2 = equity_pair
    row = A1["cal"].get_loc(cut)
    for key in ("in_universe", "shock", "zscore_20", "vol_pctl_250", "vol_ratio_20", "ret_21", "ret_30", "ret_90",
                "med_dv_20_prev", "close_to_high_250"):
        _same_through(row, np.asarray(A1[key], dtype=float), np.asarray(A2[key], dtype=float))


def test_every_signal_fires_on_the_synthetic_panel(equity_pair, crypto_pair):
    """Guards against a shift test that passes because the matrix is all False."""
    _, A, _ = equity_pair
    for name in EVENT:
        assert signals.load(name).candidates(A).sum() > 0, name
    _, C, _ = crypto_pair
    assert signals.load("1d").position(C).sum() > 0
    assert np.isfinite(signals.load("1e").scores(C)).sum() > 0


def test_registry_modules_declare_the_interface():
    for name in EVENT + RANK:
        sig = signals.load(name)
        assert sig.NAME == name and sig.MODE in ("event", "rank", "v1") and sig.UNIVERSES
        if sig.MODE in ("event", "v1"):
            assert sig.DIRECTION in ("long", "short") and sig.HORIZON in (5, 21)

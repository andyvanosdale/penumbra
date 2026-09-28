"""breakeven_multiple: a root-find on the multiplier where the lane's net
return is zero (spec/06 Costs, "the breakeven cost multiple")."""

from __future__ import annotations

import math

import pytest

from harness.costs import CostModel


def test_linear_net_function_root():
    # net(m) = 0.02 - 0.004 * m: gross return 2%, modeled cost 0.4% at m=1,
    # so net crosses zero at m = 5.
    def net_fn(m: float) -> float:
        return 0.02 - 0.004 * m

    model = CostModel("smallcap")
    root = model.breakeven_multiple(net_fn)
    assert math.isclose(root, 5.0, rel_tol=1e-4)


def test_root_already_inside_default_bracket_hi():
    def net_fn(m: float) -> float:
        return 1.0 - 0.5 * m  # root at m = 2

    model = CostModel("crypto")
    root = model.breakeven_multiple(net_fn)
    assert math.isclose(root, 2.0, rel_tol=1e-4)


def test_expands_bracket_when_root_is_far_out():
    def net_fn(m: float) -> float:
        return 100.0 - m  # root at m = 100, outside the default hi=8 bracket

    model = CostModel("smallcap")
    root = model.breakeven_multiple(net_fn)
    assert math.isclose(root, 100.0, rel_tol=1e-4)


def test_no_sign_change_raises():
    def net_fn(m: float) -> float:
        return 5.0 + m  # always positive

    model = CostModel("smallcap")
    with pytest.raises(ValueError):
        model.breakeven_multiple(net_fn, max_expand=5)

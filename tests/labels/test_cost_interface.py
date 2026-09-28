"""The labeler's cost Protocol (`harness.labels.CostModelLike`) matches the real
cost model (`harness/costs.py`, issue 7) exactly: the leg types, the `leg`
signature and the `LegCost` fields. The labeler never imports `harness.costs`,
so this test is what keeps the two from drifting."""

from __future__ import annotations

import dataclasses
import inspect
import typing

from harness import costs, labels


def test_leg_types_match():
    assert typing.get_args(labels.LegType) == typing.get_args(costs.LegType)
    assert set(labels.EXIT_LEG.values()) | {"entry"} == set(typing.get_args(costs.LegType))


def test_leg_signature_matches():
    proto = inspect.signature(labels.CostModelLike.leg)
    real = inspect.signature(costs.CostModel.leg)
    assert list(proto.parameters) == list(real.parameters) == ["self", "inputs", "leg",
                                                               "order_notional"]


def test_leg_cost_fields_match():
    proto = typing.get_type_hints(labels.LegCostLike)
    real = {f.name: f.type for f in dataclasses.fields(costs.LegCost)}
    assert list(proto) == list(real) == ["spread", "slippage", "fee", "floor_bound"]


def test_the_real_model_satisfies_the_protocol_structurally():
    model = costs.CostModel("smallcap")
    inputs = costs.CostInputs("smallcap", "1", "2021-03-01", 0.004, 100.0, 0.6, 5e6, None)
    leg = model.leg(inputs, "entry", 10_000.0)
    for name in typing.get_type_hints(labels.LegCostLike):
        assert hasattr(leg, name)

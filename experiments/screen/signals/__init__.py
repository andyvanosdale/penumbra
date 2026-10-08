"""One module per signal. Each module exposes:

    NAME        ledger name ("1a", "1b-5d", ...)
    MODE        "event" | "rank"
    DIRECTION   "long" | "short" (event mode)
    HORIZON     decision horizon in sessions (event mode)
    UNIVERSES   universes the signal runs on
    candidates(A) -> bool matrix (event mode): the raw rule on the as-of arrays, data
                     through D's close in row D; the engine ANDs it with the universe
    scores(A) / position(A) (rank mode); scores(A, variant) for the wave-2 equity rank
                     signals, with LANE = "equity", PPY, SIDE, VARIANTS and PRIOR_PP

A signal reads only the arrays `data.build_arrays` provides. `tests/screen/test_shift.py`
perturbs every bar after D and asserts the matrix at D is unchanged, for every module here.
"""
from __future__ import annotations

import importlib

REGISTRY = {
    "v1": "experiments.screen.signals.v1_reversal",
    "1a": "experiments.screen.signals.s1a_post_shock",
    "1b-5d": "experiments.screen.signals.s1b_up_shock_5d",
    "1b-21d": "experiments.screen.signals.s1b_up_shock_21d",
    "1c-short": "experiments.screen.signals.s1c_slide_short",
    "1c-long": "experiments.screen.signals.s1c_slide_long",
    "1d": "experiments.screen.signals.s1d_ts_mom",
    "1e": "experiments.screen.signals.s1e_xs_mom",
    "2a": "experiments.screen.signals.s2a_mom_12_1",
    "2b": "experiments.screen.signals.s2b_high_52w",
    "2d": "experiments.screen.signals.s2d_weekly_reversal",
}


def load(name: str):
    if name not in REGISTRY:
        raise KeyError(f"unknown signal {name!r}; known: {sorted(REGISTRY)}")
    return importlib.import_module(REGISTRY[name])

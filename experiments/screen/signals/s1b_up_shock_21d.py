"""1b Up-shock continuation (long), 21-session variant: same candidates as 1b-5d."""
from __future__ import annotations

from experiments.screen.signals.s1b_up_shock_5d import candidates  # noqa: F401

NAME, MODE, DIRECTION, HORIZON = "1b-21d", "event", "long", 21
UNIVERSES = ["smallcap", "uncapped", "crypto"]

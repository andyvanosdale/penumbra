"""Feature builder (plan §3.2).

    build_features(ticker, timestamp) -> feature_vector

STRICTLY FORBIDDEN from accessing any data with knowledge_date > timestamp. This
is the chokepoint where lookahead bias would otherwise enter, so this module:

  * reads ONLY via the store's as-of paths (known_bar / get_known_prices),
    always with as_of = timestamp;
  * does NOT import harness.labels and does NOT call store.get_prices_oracle().

It currently computes a single, deliberately uninformative calendar feature
("is it Monday"). This serves as a negative control: a harness that finds an edge
in it has a bug.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from harness.store import PITStore

# Feature schema is explicit so the model wrapper and tests agree on column order.
FEATURE_NAMES = ["is_monday"]


def build_features(
    store: PITStore, ticker: str, timestamp
) -> Optional[dict]:
    """Return a feature dict for (ticker, timestamp), or None if not buildable.

    'is_monday' is a calendar feature with no plausible predictive content. We
    still require that the bar for `timestamp` is actually KNOWN as of
    `timestamp` (i.e. the ticker traded that day and the row exists in the
    point-in-time store) so the feature path exercises the real as-of read.
    """
    ts = pd.Timestamp(timestamp)
    as_of = ts.strftime("%Y-%m-%d")

    # Require that THIS day's bar is actually known as of this day (the ticker
    # traded and the row is in the point-in-time store). Uses the as-of read path,
    # so it is structurally impossible to consult future data here.
    if store.known_bar(ticker, as_of, as_of) is None:
        return None  # ticker did not trade on this date (or isn't knowable yet)

    return {"is_monday": 1.0 if ts.weekday() == 0 else 0.0}


def features_to_vector(feat: dict) -> list[float]:
    """Deterministic ordering matching FEATURE_NAMES."""
    return [float(feat[name]) for name in FEATURE_NAMES]

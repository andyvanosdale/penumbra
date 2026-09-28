"""Read-time price adjustment (spec/02 Store; docs/store.md "Adjustment").

Prices are stored unadjusted. The series in the basis of date B multiplies a bar
dated t by

    M(t, B) = P(B) / P(t),   P(x) = product of f_a over adjusting actions dated <= x

For t < B that is the product of the factors of actions with t < action date <= B,
which is the spec's rule for the as-of-B series. Actions dated after B are never
applied, because the as-of reader never fetches them. For t > B (the labeler's
oracle read, converting later bars into the entry date's basis) the same expression
divides by the factors of actions in (B, t].

Factors:

- split, `value` = shares after / shares before (2.0 for a 2-for-1):
  f = 1 / value on open, high, low and close; volume is multiplied by `value`.
- dividend (cash), `value` = amount per share:
  f = 1 - value / close_{ex-1}, where close_{ex-1} is the unadjusted close of the
  symbol's last bar dated before the ex-date. Volume is unchanged. This is the
  standard CRSP-style convention; the spec gives no formula (flagged in the PR for
  issue 16).

`dollar_volume` is never adjusted (spec/04: dollar volume uses the unadjusted
series). No other action type adjusts prices.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

ADJUST_MODES = ("none", "split", "split_div")
SPLIT = "split"
DIVIDEND = "dividend"
PRICE_COLUMNS = ("open", "high", "low", "close")


def adjusting_actions(mode: str) -> tuple[str, ...]:
    if mode not in ADJUST_MODES:
        raise ValueError(f"adjust must be one of {ADJUST_MODES}, got {mode!r}")
    return {"none": (), "split": (SPLIT,), "split_div": (SPLIT, DIVIDEND)}[mode]


def action_factors(actions: pd.DataFrame) -> pd.DataFrame:
    """Per-action price factor `f` and volume factor `vf`.

    `actions` has columns symbol, date, action, value and, for dividends,
    prev_close (the unadjusted close of the last bar before the ex-date).
    """
    out = actions[["symbol", "date", "action"]].copy()
    value = actions["value"].astype(float)
    f = pd.Series(1.0, index=actions.index)
    vf = pd.Series(1.0, index=actions.index)

    is_split = actions["action"] == SPLIT
    if (is_split & ~(value > 0)).any():
        bad = actions.loc[is_split & ~(value > 0)]
        raise ValueError(f"split with non-positive ratio: {bad.to_dict('records')}")
    f[is_split] = 1.0 / value[is_split]
    vf[is_split] = value[is_split]

    is_div = actions["action"] == DIVIDEND
    if is_div.any():
        prev = actions.loc[is_div, "prev_close"].astype(float)
        # A dividend with no earlier bar in the store has nothing to adjust.
        fd = (1.0 - value[is_div] / prev).where(prev.notna(), 1.0)
        if (fd <= 0).any():
            bad = actions.loc[is_div][fd <= 0]
            raise ValueError(f"dividend at or above the prior close: {bad.to_dict('records')}")
        f[is_div] = fd
    out["f"] = f
    out["vf"] = vf
    return out


def apply(bars: pd.DataFrame, factors: pd.DataFrame, basis: str,
          time_column: str = "date") -> pd.DataFrame:
    """Return `bars` expressed in the basis of date `basis`.

    `bars` has symbol, `time_column` and the price and volume columns; `factors`
    is `action_factors(...)` restricted to the actions the caller may apply.
    Rows are returned in their input order.
    """
    out = bars.copy()
    if out.empty or factors.empty:
        return out
    t = out[time_column].astype(str).str.slice(0, 10).to_numpy()
    price_mult = np.ones(len(out))
    vol_mult = np.ones(len(out))
    sym = out["symbol"].to_numpy()
    for s, fa in factors.sort_values("date").groupby("symbol", sort=False):
        idx = np.flatnonzero(sym == s)
        if idx.size == 0:
            continue
        dates = fa["date"].to_numpy(dtype=str)
        # Cumulative products P(x) over actions dated <= x; cum[0] = empty product.
        cum_f = np.concatenate([[1.0], np.cumprod(fa["f"].to_numpy(dtype=float))])
        cum_v = np.concatenate([[1.0], np.cumprod(fa["vf"].to_numpy(dtype=float))])
        k_t = np.searchsorted(dates, t[idx], side="right")
        k_b = np.searchsorted(dates, np.array([basis[:10]]), side="right")[0]
        price_mult[idx] = cum_f[k_b] / cum_f[k_t]
        vol_mult[idx] = cum_v[k_b] / cum_v[k_t]
    for c in PRICE_COLUMNS:
        if c in out:
            out[c] = out[c].astype(float) * price_mult
    if "volume" in out:
        out["volume"] = out["volume"].astype(float) * vol_mult
    return out

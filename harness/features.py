"""Feature builder (spec/04 Features and Flags; issue 8).

`build_features(reader, lane, dates, symbols=None, eligible=None)` computes the
fourteen spec/04 features and the `filing_2d` flag as-of each date in `dates`, for
`symbols` in `lane` (`None` = every symbol the store carries for the lane's market
in the window). Reads go through `harness.store.reader.AsOfReader` only: never the
oracle (`harness.store.oracle`), never `harness.labels` (`tests/test_architecture.py`
enforces this).

Conventions (spec/04):

- A window of n days ends at and includes D unless a feature says otherwise; days
  are the lane's trading days (`harness.store.calendar_for_lane`), not calendar
  days. A name with a missing bar anywhere inside a window on D makes that feature
  NaN at D; it is never forward-filled.
- Standard deviations are sample (n - 1).
- Price features use the split-and-dividend-adjusted series (`adjust="split_div"`).
  Per `docs/architecture.md` ("Adjustment", consequence 1), every feature here is
  scale-invariant, so one `panel` read per (lane, era) — adjusted as of the panel's
  last date — gives the same feature values as reading each D as of D; only bars
  dated on or before each D are ever used for that D's features, so no feature ever
  reads a row with `available_at` after D. `tests/features/test_scale_invariance.py`
  is the required proof.
- Annualization is sqrt(252) for equity lanes (`nyse` calendar) and sqrt(365) for
  crypto (`utc` calendar).
- "Today's return" (used by `sector_rel_ret_1` and `ret_per_vol`) is the simple
  return close_D / close_{D-1} - 1; `ret_1` is the 1-day *log* return. The spec's
  Conventions section defines both, and the features table uses each by name.

`sector_rel_ret_1`'s "eligible equities" (spec/01 Eligibility) is issue 6's universe
builder, built in parallel. This module takes it as the `eligible` parameter: a
DataFrame with `date` and `symbol` columns (the shape `AsOfReader.lane_membership`
returns), naming the eligible names on each date. When `eligible` is omitted, this
module falls back to "every symbol with a valid return on D" as a local stand-in —
flagged in the PR description for the PA to replace with the real universe once
issue 6 lands.
"""

from __future__ import annotations

import bisect
import datetime as dt
from typing import Mapping, Sequence

import numpy as np
import pandas as pd

from config.params import SPEC01
from harness.store.calendar import calendar_for_lane
from harness.store.reader import AsOfReader, iso_date

ANNUALIZATION = {"nyse": 252.0, "utc": 365.0}
LANE_MARKET = {"smallcap": "us_equity", "discovered": "us_equity", "crypto": "binance_spot"}
EQUITY_LANES = ("smallcap", "discovered")

RVOL_WINDOW = 20
ZSCORE_WINDOW = 20
# spec/01 Eligibility fixes an equity's full-history requirement at 250 lane
# trading days "so every feature window is full" — the same 250 spec/04 uses
# for vol_pctl_250 and dist_52w_low. Sourced from config/params.py (the
# locked-parameter source of truth) rather than a second literal.
VOL_PCTL_WINDOW = SPEC01.equities_full_history_days
DIST_52W_WINDOW = SPEC01.equities_full_history_days
DD_20D_WINDOW = 20
RANGE_REL_WINDOW = 20
CLOSE_LOC_LAG = 2
FILING_LOOKBACK = 2  # D-1 and D-2

# The longest lookback any feature needs, in lane trading sessions ending at D.
LOOKBACK_SESSIONS = max(VOL_PCTL_WINDOW, DIST_52W_WINDOW, RVOL_WINDOW + 1)

KEY_COLUMNS = ("lane", "market", "symbol", "date")
FEATURE_COLUMNS = (
    "ret_1", "rvol_20", "rvol_20_prev", "shock", "zscore_20", "vol_pctl_250",
    "sector_rel_ret_1", "dist_52w_low", "dd_from_20d_high", "close_loc", "gap",
    "range_rel_20", "ret_per_vol", "close_loc_chg_2",
)
FLAG_COLUMNS = ("filing_2d",)


class FeatureError(ValueError):
    pass


def _dates_arg(dates) -> list[str]:
    if isinstance(dates, (str, dt.date, dt.datetime, pd.Timestamp)):
        dates = [dates]
    out = sorted({iso_date(d) for d in dates})
    if not out:
        raise FeatureError("dates must be non-empty")
    return out


def _symbols_arg(symbols) -> list[str] | None:
    if symbols is None:
        return None
    if isinstance(symbols, str):
        return [symbols]
    return list(symbols)


def _session_span(sessions: list[str], d_min: str, d_max: str) -> list[str]:
    """Sessions in `sessions` covering [start of the D_min lookback, d_max]."""
    hi = bisect.bisect_right(sessions, d_max)
    lo_d_min = bisect.bisect_right(sessions, d_min) - 1
    if lo_d_min < 0:
        raise FeatureError(f"no session on or before {d_min} in the fetched calendar")
    lo = max(0, lo_d_min - LOOKBACK_SESSIONS + 1)
    return sessions[lo:hi]


def _full_window(cnt: pd.Series, window: int) -> pd.Series:
    return cnt == window


def _roll(s: pd.Series, window: int, how: str, ddof: int = 1) -> pd.Series:
    """Rolling `how` over `window` sessions, NaN unless every session has a value."""
    r = s.rolling(window)
    cnt = r.count()
    if how == "mean":
        val = r.mean()
    elif how == "std":
        val = r.std(ddof=ddof)
    elif how == "min":
        val = r.min()
    elif how == "max":
        val = r.max()
    else:
        raise ValueError(how)
    return val.where(_full_window(cnt, window))


def _midrank_pctl(s: pd.Series, window: int) -> pd.Series:
    """Rolling rank of the window's last value, divided by `window`.

    Ties share the mean rank of the tied group (the midrank convention: rank(x) =
    count(v < x) + (count(v == x) + 1) / 2), so a value tied for the top of a
    window of 250 does not score a full 1.0 on its own. NaN unless every session
    in the window has a value.
    """
    def midrank(x: np.ndarray) -> float:
        if np.isnan(x).any():
            return np.nan
        last = x[-1]
        less = float(np.sum(x < last))
        equal = float(np.sum(x == last))
        return (less + (equal + 1.0) / 2.0) / window

    return s.rolling(window).apply(midrank, raw=True)


def _reindexed(bars: pd.DataFrame, sessions: list[str]) -> pd.DataFrame:
    return bars.set_index("date").reindex(pd.Index(sessions, name="date"))


def _per_symbol_features(bars_sym: pd.DataFrame, sessions: list[str], ann: float) -> pd.DataFrame:
    b = _reindexed(bars_sym, sessions)
    close, open_, high, low = b["close"], b["open"], b["high"], b["low"]
    dollar_volume = b["dollar_volume"]

    log_ret_1 = np.log(close / close.shift(1))
    simple_ret_1 = close / close.shift(1) - 1.0

    rvol_20 = _roll(log_ret_1, RVOL_WINDOW, "std") * np.sqrt(ann)
    rvol_20_prev = rvol_20.shift(1)
    shock = log_ret_1 / (rvol_20_prev / np.sqrt(ann))

    mean_close_20 = _roll(close, ZSCORE_WINDOW, "mean")
    std_close_20 = _roll(close, ZSCORE_WINDOW, "std")
    zscore_20 = (close - mean_close_20) / std_close_20

    vol_pctl_250 = _midrank_pctl(dollar_volume, VOL_PCTL_WINDOW)

    min_low_250 = _roll(low, DIST_52W_WINDOW, "min")
    dist_52w_low = close / min_low_250 - 1.0

    max_high_20 = _roll(high, DD_20D_WINDOW, "max")
    dd_from_20d_high = close / max_high_20 - 1.0

    hl_range = high - low
    close_loc = ((close - low) / hl_range).where(hl_range != 0, 0.5)
    close_loc = close_loc.where(close.notna() & high.notna() & low.notna())

    gap = open_ / close.shift(1) - 1.0
    range_rel_20 = hl_range / _roll(hl_range, RANGE_REL_WINDOW, "mean")
    ret_per_vol = simple_ret_1 / (vol_pctl_250 + 0.01)
    close_loc_chg_2 = close_loc - close_loc.shift(CLOSE_LOC_LAG)

    out = pd.DataFrame({
        "ret_1": log_ret_1,
        "rvol_20": rvol_20,
        "rvol_20_prev": rvol_20_prev,
        "shock": shock,
        "zscore_20": zscore_20,
        "vol_pctl_250": vol_pctl_250,
        "dist_52w_low": dist_52w_low,
        "dd_from_20d_high": dd_from_20d_high,
        "close_loc": close_loc,
        "gap": gap,
        "range_rel_20": range_rel_20,
        "ret_per_vol": ret_per_vol,
        "close_loc_chg_2": close_loc_chg_2,
        "_simple_ret_1": simple_ret_1,
    }, index=b.index)
    out.index.name = "date"
    return out


def _filing_2d(events: pd.DataFrame, sessions: list[str], dates: list[str],
              symbols: Sequence[str]) -> pd.DataFrame:
    """True when a symbol has an EVENTS row `available_at` on D-1 or D-2."""
    avail_by_symbol: dict[str, set[str]] = {s: set() for s in symbols}
    if not events.empty:
        for sym, avail in zip(events["symbol"], events["available_at"]):
            avail_by_symbol.setdefault(sym, set()).add(avail)

    rows = []
    for d in dates:
        i = bisect.bisect_left(sessions, d)
        if i >= len(sessions) or sessions[i] != d:
            raise FeatureError(f"{d} is not a session in the fetched calendar")
        lookback = sessions[max(0, i - FILING_LOOKBACK):i]
        for s in symbols:
            flag = any(prior in avail_by_symbol.get(s, ()) for prior in lookback)
            rows.append((s, d, flag))
    return pd.DataFrame(rows, columns=["symbol", "date", "filing_2d"])


def _eligible_lookup(eligible: pd.DataFrame | None) -> dict[str, set[str]] | None:
    if eligible is None:
        return None
    if not {"date", "symbol"}.issubset(eligible.columns):
        raise FeatureError("eligible must have 'date' and 'symbol' columns")
    lookup: dict[str, set[str]] = {}
    for d, sym in zip(eligible["date"].astype(str), eligible["symbol"]):
        lookup.setdefault(d, set()).add(sym)
    return lookup


def _sector_rel_ret_1(per_symbol: dict[str, pd.DataFrame], sectors: Mapping[str, str],
                      dates: list[str], symbols: Sequence[str],
                      eligible_by_date: dict[str, set[str]] | None) -> pd.DataFrame:
    """Today's return minus the equal-weight return of eligible sector peers.

    "Eligible" (spec/01) gates who is *averaged*, not whether the name itself
    gets a value: a name outside the eligible set (or with no `eligible` given
    at all, the fallback in the module docstring) still gets a
    `sector_rel_ret_1` computed against its eligible peers, excluding itself
    from that average only when it is itself one of them.
    """
    rows = []
    for d in dates:
        own_by_symbol: dict[str, float] = {}
        for s in symbols:
            r = per_symbol[s].at[d, "_simple_ret_1"] if d in per_symbol[s].index else np.nan
            if not pd.isna(r):
                own_by_symbol[s] = r
        eligible_here = eligible_by_date.get(d, set()) if eligible_by_date is not None else None
        by_sector: dict[str, list[float]] = {}
        for s, r in own_by_symbol.items():
            sector = sectors.get(s)
            if sector is None:
                continue
            if eligible_here is None or s in eligible_here:
                by_sector.setdefault(sector, []).append((s, r))

        for s in symbols:
            sector = sectors.get(s)
            own = own_by_symbol.get(s, np.nan)
            value = np.nan
            if sector is not None and not pd.isna(own):
                group = by_sector.get(sector, [])
                group_sum = sum(r for _, r in group)
                group_n = len(group)
                is_member = any(x == s for x, _ in group)
                peer_sum = group_sum - own if is_member else group_sum
                peer_n = group_n - 1 if is_member else group_n
                if peer_n > 0:
                    value = own - peer_sum / peer_n
            rows.append((s, d, value))
    return pd.DataFrame(rows, columns=["symbol", "date", "sector_rel_ret_1"])


def build_features(reader: AsOfReader, lane: str, dates, symbols=None,
                   eligible: pd.DataFrame | None = None) -> pd.DataFrame:
    """Compute the spec/04 features and flags for `lane`, as of each date in `dates`.

    `symbols` is `None` (every symbol the store carries for the lane's market over
    the window) or an explicit list. `eligible` is the equities universe used by
    `sector_rel_ret_1` (spec/01); see the module docstring for its shape and the
    fallback used when it is omitted.

    Returns a DataFrame keyed by (lane, market, symbol, date), one column per
    feature and flag.
    """
    if lane not in LANE_MARKET:
        raise FeatureError(f"lane must be one of {sorted(LANE_MARKET)}, got {lane!r}")
    market = LANE_MARKET[lane]
    calendar_name = calendar_for_lane(lane)
    ann = ANNUALIZATION[calendar_name]
    date_list = _dates_arg(dates)
    d_min, d_max = date_list[0], date_list[-1]
    as_of = d_max

    wide_start = iso_date(dt.date.fromisoformat(d_min) - dt.timedelta(days=1500))
    cal = reader.calendar(calendar_name, wide_start, d_max, as_of)
    sessions = sorted(cal["date"].tolist())
    missing = sorted(set(date_list) - set(sessions))
    if missing:
        raise FeatureError(f"not {calendar_name} sessions: {missing}")
    span = _session_span(sessions, d_min, d_max)
    panel_start = span[0]

    req_symbols = _symbols_arg(symbols)
    panel = reader.panel(market, req_symbols, panel_start, d_max, as_of, adjust="split_div")
    resolved_symbols = sorted(panel["symbol"].unique()) if req_symbols is None else req_symbols

    per_symbol: dict[str, pd.DataFrame] = {}
    for s in resolved_symbols:
        bars_sym = panel[panel["symbol"] == s]
        per_symbol[s] = _per_symbol_features(bars_sym, span, ann)

    frames = []
    for s in resolved_symbols:
        f = per_symbol[s].loc[per_symbol[s].index.isin(date_list)].drop(columns=["_simple_ret_1"])
        f = f.reset_index().rename(columns={"index": "date"})
        f.insert(0, "symbol", s)
        frames.append(f)
    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(
        columns=["symbol", "date", *FEATURE_COLUMNS])

    if lane in EQUITY_LANES:
        events = reader.events(market, resolved_symbols or None, panel_start, d_max, as_of)
        filing = _filing_2d(events, span, date_list, resolved_symbols)
        out = out.merge(filing, on=["symbol", "date"], how="left")
        out["filing_2d"] = out["filing_2d"].astype("boolean")

        sym_attrs = reader.symbols(market, resolved_symbols or None, as_of)
        sectors = dict(zip(sym_attrs["symbol"], sym_attrs["sector"]))
        eligible_by_date = _eligible_lookup(eligible)
        sector_rel = _sector_rel_ret_1(per_symbol, sectors, date_list, resolved_symbols,
                                       eligible_by_date)
        out = out.merge(sector_rel, on=["symbol", "date"], how="left")
    else:
        out["filing_2d"] = pd.array([pd.NA] * len(out), dtype="boolean")
        out["sector_rel_ret_1"] = np.nan

    out.insert(0, "market", market)
    out.insert(0, "lane", lane)
    out = out[list(KEY_COLUMNS) + list(FEATURE_COLUMNS) + list(FLAG_COLUMNS)]
    return out.sort_values(["symbol", "date"]).reset_index(drop=True)

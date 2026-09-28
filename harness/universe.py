"""Per-lane universe builders (spec/01 Lanes and universe; issue 6).

Scope of this module: the `UniverseBuilder` interface and the two equity lane
builders, `smallcap` and `discovered`. The `crypto` builder is deferred: issue 15
(the pre-build screen) may remove the crypto lane by spec change before its
universe rule is built (docs/architecture.md, "Build order"). `BUILDERS` is a
lane-name registry so a `CryptoBuilder` can slot in later without changing the
interface or the callers.

All reads go through `harness.store.reader.AsOfReader`. Every screen a builder
computes for a date D is a strictly backward-looking (causal) function of bars
dated <= D: rolling windows, medians and standard deviations are computed with
pandas `rolling`, which by construction only look at the current and earlier
rows of a chronologically sorted series. This is what `docs/architecture.md`
means by "windowed panel read for efficiency": one `panel`/`marketcap`/`listing`
read spans the whole date range a build() call is asked for, `as_of` set to the
last requested date, and every table this module reads (`bars_daily`,
`marketcap`, `listing`, `symbols`) has `available_at` equal to its own row's
date (or, for `symbols`, the first listing date), so a single read with
`as_of = max(dates)` returns exactly the rows a per-date `as_of = D` read would
return for each D individually — the SQL `available_at <= as_of` filter adds no
visibility beyond the date-range filter already gives, because these tables are
never restated after the fact in this store. The per-D screen values are then
computed from that panel without ever looking past D, which the invariance test
in `tests/universe/` checks directly (perturbing every bar after D leaves D's
membership unchanged).

Missing bars are never forward-filled (spec/02 Trading calendars): a
(symbol, session) slot with no bar counts as absent for both the 250-day
completeness check and every rolling window that touches it.
"""

from __future__ import annotations

import json
from typing import Mapping, Protocol, Sequence

import numpy as np
import pandas as pd

from harness.store.calendar import calendar_for_lane
from harness.store.reader import AsOfReader, iso_date
from harness.store.writer import upsert

EQUITY_MARKET = "us_equity"
EQUITY_LANES = ("smallcap", "discovered")

# spec/01 Eligibility.
ELIGIBLE_CATEGORIES = (
    "Domestic Common Stock",
    "Domestic Common Stock Primary Class",
    "Domestic Common Stock Secondary Class",
)
ELIGIBLE_EXCHANGES = ("NYSE", "NASDAQ", "NYSEMKT", "NYSEARCA", "BATS")

# spec/01 Eligibility / Point-in-time construction.
HISTORY_SESSIONS = 250   # full bar history required, lane trading days ending at D
LIQUIDITY_WINDOW = 20    # lane trading days ending D-1, for the dollar-volume median
VOL_WINDOW = 20          # lane trading days ending D, for realized vol
EQUITY_ANNUALIZATION = 252 ** 0.5

# TODO(PA): replace with config.params once PR 24 merges (issue 17). Values below
# are spec/01 Parameters: Small-cap ceiling, Liquidity floor (equities), Vol floor
# (equities), Price floor (equities).
SMALLCAP_CEILING = 2_000_000_000.0   # USD market cap, DAILY dated D
LIQUIDITY_FLOOR = 500_000.0          # USD median daily dollar volume, 20 sessions ending D-1
VOL_FLOOR = 0.40                     # 20-day annualized realized vol
PRICE_FLOOR = 2.00                   # unadjusted close on D

# A read this early returns nothing before the store's actual history; it exists
# so listing events and calendar sessions from long before the requested window
# are still picked up (a symbol's listing date, or the 250-day lookback, can sit
# well before the earliest date a caller asks to build).
EARLIEST_CALENDAR_DATE = "1900-01-01"

# spec/01 Parameters: target universe size per lane per day (a sanity check, not
# a filter). Crypto is out of scope for this module (issue 15 may remove the
# lane before its own builder and range are built).
TARGET_SIZE_RANGES: dict[str, tuple[int, int]] = {
    "smallcap": (500, 1500),
    "discovered": (600, 2000),
}

# "Persistent" excursions (spec/01: "Persistent sizes outside the range are
# flagged, not silently accepted") are not otherwise defined by the spec. This
# module defines persistent as at least this many consecutive lane trading
# sessions, among the dates `sanity_report` is given, with the size outside its
# target range. Flagged in the PR for issue 6 as an operational choice, not a
# locked parameter.
PERSISTENT_SESSIONS = 20


class UniverseBuilder(Protocol):
    """Common interface for every lane's universe builder.

    `dates` are lane trading sessions (per `harness.store.calendar_for_lane`);
    passing a date the lane's calendar doesn't carry as a session is an error.
    """

    def build(self, reader: AsOfReader, lane: str, dates: Sequence[str]) -> pd.DataFrame:
        """Return one row per (lane, market, symbol, date) admitted on that date.

        Columns: `lane`, `market`, `symbol`, `date`, `screen_values` (a dict of
        the screen values that admitted the name; JSON-encoded by
        `write_lane_membership`, not here, so callers can inspect it as data).
        """
        ...


def _check_lane(lane: str, expected: str) -> None:
    if lane != expected:
        raise ValueError(f"{expected} builder called with lane={lane!r}")


def _validate_dates(dates: Sequence[str]) -> list[str]:
    if not dates:
        raise ValueError("dates must be non-empty")
    return sorted({iso_date(d) for d in dates})


def _empty_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=["lane", "market", "symbol", "date", "screen_values"])


def _lane_sessions(reader: AsOfReader, calendar_name: str, end: str) -> list[str]:
    """Every session of `calendar_name` in the store's history up to `end`."""
    df = reader.calendar(calendar_name, EARLIEST_CALENDAR_DATE, end, end)
    return df["date"].tolist()


def _window_sessions(sessions: list[str], dates: list[str]) -> list[str]:
    """The lane trading sessions from `HISTORY_SESSIONS` before `dates[0]` to `dates[-1]`.

    Raises if a requested date is not itself a session of the lane's calendar.
    """
    index = {d: i for i, d in enumerate(sessions)}
    missing = [d for d in dates if d not in index]
    if missing:
        raise ValueError(f"dates are not lane trading sessions: {missing[:5]}")
    start_i = max(0, index[dates[0]] - (HISTORY_SESSIONS - 1))
    end_i = index[dates[-1]]
    return sessions[start_i:end_i + 1]


def _equity_screen_frame(reader: AsOfReader, dates: list[str]) -> pd.DataFrame:
    """Per (symbol, date) eligibility and screen values for every date in `dates`.

    One row per (symbol, date) for every equity symbol with any bar in the
    lookback window, whether or not it turns out eligible; callers filter.
    """
    calendar_name = calendar_for_lane("smallcap")  # smallcap and discovered share nyse
    sessions = _lane_sessions(reader, calendar_name, dates[-1])
    window_sessions = _window_sessions(sessions, dates)
    window_start, d_max = window_sessions[0], dates[-1]

    bars = reader.panel(EQUITY_MARKET, None, window_start, d_max, as_of=d_max, adjust="none")
    if bars.empty:
        return _empty_screen_columns()
    bars_adj = reader.panel(EQUITY_MARKET, None, window_start, d_max, as_of=d_max,
                            adjust="split_div")
    marketcap = reader.marketcap(EQUITY_MARKET, None, window_start, d_max, as_of=d_max)
    listing = reader.listing(EQUITY_MARKET, None, EARLIEST_CALENDAR_DATE, d_max, as_of=d_max)
    attrs = reader.symbols(EQUITY_MARKET, None, d_max)

    symbols_list = sorted(bars["symbol"].unique())
    grid = pd.MultiIndex.from_product([symbols_list, window_sessions],
                                      names=["symbol", "date"]).to_frame(index=False)
    grid = grid.merge(bars[["market", "symbol", "date", "close", "dollar_volume"]],
                      on=["symbol", "date"], how="left")
    grid = grid.merge(bars_adj[["symbol", "date", "close"]].rename(columns={"close": "close_adj"}),
                      on=["symbol", "date"], how="left")
    grid["market"] = grid["market"].fillna(EQUITY_MARKET)

    grid["present"] = grid["close"].notna()
    grid["bar_count_250"] = grid.groupby("symbol")["present"].transform(
        lambda s: s.rolling(HISTORY_SESSIONS, min_periods=HISTORY_SESSIONS).sum())
    grid["complete_250"] = grid["bar_count_250"] == HISTORY_SESSIONS

    # Liquidity floor: median dollar volume over the 20 sessions ending D-1
    # (spec/01 Point-in-time construction), so the signal day's own volume never
    # qualifies a name. Computed as the rolling-20 median ending at each row,
    # then shifted one session so row D holds the window ending D-1.
    grid["_dv_median_20"] = grid.groupby("symbol")["dollar_volume"].transform(
        lambda s: s.rolling(LIQUIDITY_WINDOW, min_periods=LIQUIDITY_WINDOW).median())
    grid["dv_median_20_prev"] = grid.groupby("symbol")["_dv_median_20"].shift(1)
    grid.drop(columns=["_dv_median_20"], inplace=True)

    # 20-day annualized realized vol on the split-and-dividend-adjusted series
    # (spec/04 Conventions); scale-invariant to the panel's as-of basis constant,
    # so the log return is identical whether computed per-D or from one panel
    # (docs/architecture.md, "Adjustment").
    grid["_log_ret"] = grid.groupby("symbol")["close_adj"].transform(
        lambda s: np.log(s / s.shift(1)))
    grid["rvol_20"] = (grid.groupby("symbol")["_log_ret"]
                       .transform(lambda s: s.rolling(VOL_WINDOW, min_periods=VOL_WINDOW)
                                  .std(ddof=1)) * EQUITY_ANNUALIZATION)
    grid.drop(columns=["_log_ret"], inplace=True)

    if not marketcap.empty:
        grid = grid.merge(marketcap[["symbol", "date", "marketcap"]], on=["symbol", "date"],
                          how="left")
    else:
        grid["marketcap"] = np.nan

    attrs = attrs[["symbol", "category", "exchange"]] if not attrs.empty else \
        pd.DataFrame(columns=["symbol", "category", "exchange"])
    grid = grid.merge(attrs, on="symbol", how="left")
    grid["category_ok"] = grid["category"].isin(ELIGIBLE_CATEGORIES)
    grid["exchange_ok"] = grid["exchange"].isin(ELIGIBLE_EXCHANGES)

    min_listed = (listing[listing["event"] == "listed"].groupby("symbol")["date"].min()
                 if not listing.empty else pd.Series(dtype=object))
    min_delisted = (listing[listing["event"] == "delisted"].groupby("symbol")["date"].min()
                   if not listing.empty else pd.Series(dtype=object))
    sym_listing = pd.DataFrame({"symbol": symbols_list})
    sym_listing["min_listed"] = sym_listing["symbol"].map(min_listed)
    sym_listing["min_delisted"] = sym_listing["symbol"].map(min_delisted)
    grid = grid.merge(sym_listing, on="symbol", how="left")
    # spec/02 Store: listed on D = a `listed` event on or before D and no
    # `delisted` event on or before D (harness.store.reader.AsOfReader.listed).
    grid["listed_on_d"] = (grid["min_listed"].notna() & (grid["date"] >= grid["min_listed"])
                           & (grid["min_delisted"].isna() | (grid["date"] < grid["min_delisted"])))

    grid["eligible"] = (grid["category_ok"] & grid["exchange_ok"] & grid["listed_on_d"]
                       & grid["complete_250"])
    grid["has_marketcap"] = grid["marketcap"].notna()
    grid["smallcap_cap_ok"] = grid["has_marketcap"] & (grid["marketcap"] < SMALLCAP_CEILING)
    grid["liquidity_ok"] = grid["dv_median_20_prev"] > LIQUIDITY_FLOOR
    grid["vol_ok"] = grid["rvol_20"] > VOL_FLOOR
    grid["price_ok"] = grid["close"] >= PRICE_FLOOR

    return grid[grid["date"].isin(dates)].reset_index(drop=True)


def _empty_screen_columns() -> pd.DataFrame:
    cols = ["market", "symbol", "date", "close", "marketcap", "dv_median_20_prev", "rvol_20",
           "eligible", "has_marketcap", "smallcap_cap_ok", "liquidity_ok", "vol_ok", "price_ok"]
    return pd.DataFrame(columns=cols)


def _screen_values(row: pd.Series) -> dict:
    def _num(v):
        return None if pd.isna(v) else float(v)
    return {
        "marketcap": _num(row.get("marketcap")),
        "dollar_volume_median_20": _num(row.get("dv_median_20_prev")),
        "rvol_20": _num(row.get("rvol_20")),
        "close": _num(row.get("close")),
    }


def _membership_frame(admitted: pd.DataFrame, lane: str) -> pd.DataFrame:
    if admitted.empty:
        return _empty_frame()
    out = pd.DataFrame({
        "lane": lane,
        "market": admitted["market"],
        "symbol": admitted["symbol"],
        "date": admitted["date"],
        "screen_values": admitted.apply(_screen_values, axis=1),
    })
    return out.reset_index(drop=True)


class SmallcapBuilder:
    """`smallcap`: eligible, below the small-cap ceiling, liquid, volatile, priced.

    spec/01: "A name with no Sharadar DAILY market-cap row as-of D is ineligible
    for `smallcap`" — `has_marketcap` gates this lane; a present marketcap must
    also be below `SMALLCAP_CEILING`.
    """

    LANE = "smallcap"

    def build(self, reader: AsOfReader, lane: str, dates: Sequence[str]) -> pd.DataFrame:
        _check_lane(lane, self.LANE)
        dates = _validate_dates(dates)
        frame = _equity_screen_frame(reader, dates)
        if frame.empty:
            return _empty_frame()
        admitted = frame[frame["eligible"] & frame["smallcap_cap_ok"] & frame["liquidity_ok"]
                         & frame["vol_ok"] & frame["price_ok"]]
        return _membership_frame(admitted, self.LANE)


class DiscoveredBuilder:
    """`discovered`: eligible, liquid, volatile, priced; no cap limit.

    spec/01 gives `discovered` no market-cap condition at all, so a name missing
    a DAILY row and a name above the small-cap ceiling are both eligible here
    (subject to the shared screens), and a `smallcap` member may also appear in
    `discovered` — the spec says the two lanes are never pooled into one model,
    not that their membership is disjoint. Flagged in the PR for issue 6: read
    literally, the lane table gives no de-duplication rule between the two
    equity lanes, and this builder does not invent one.
    """

    LANE = "discovered"

    def build(self, reader: AsOfReader, lane: str, dates: Sequence[str]) -> pd.DataFrame:
        _check_lane(lane, self.LANE)
        dates = _validate_dates(dates)
        frame = _equity_screen_frame(reader, dates)
        if frame.empty:
            return _empty_frame()
        admitted = frame[frame["eligible"] & frame["liquidity_ok"] & frame["vol_ok"]
                         & frame["price_ok"]]
        return _membership_frame(admitted, self.LANE)


# Lane -> builder. A `CryptoBuilder` slots in here once issue 15's screen decides
# the lane survives; nothing else in this module or its callers needs to change.
BUILDERS: dict[str, UniverseBuilder] = {
    "smallcap": SmallcapBuilder(),
    "discovered": DiscoveredBuilder(),
}


def write_lane_membership(conn, snapshot_id: str, frame: pd.DataFrame) -> int:
    """Write a builder's output frame into `lane_membership` (harness.store.writer).

    `frame` is a `build()` result: `screen_values` holds a dict, JSON-encoded
    here. `available_at` is the row's own date (docs/store.md: `lane_membership`
    `available_at` is the date).
    """
    if frame.empty:
        return 0
    rows = [
        {
            "lane": r["lane"],
            "market": r["market"],
            "symbol": r["symbol"],
            "date": r["date"],
            "screen_values": json.dumps(r["screen_values"], sort_keys=True),
            "available_at": r["date"],
        }
        for r in frame.to_dict("records")
    ]
    return upsert(conn, "lane_membership", snapshot_id, rows)


def sanity_report(membership: pd.DataFrame, ranges: Mapping[str, tuple[int, int]] | None = None,
                  persistent_sessions: int = PERSISTENT_SESSIONS) -> pd.DataFrame:
    """Universe size per (lane, date), flagged against `ranges` (spec/01 Parameters).

    `membership` is one or more builders' concatenated output (or the stored
    `lane_membership` rows): anything with `lane`, `date` and one row per member.
    A lane outside `ranges` is reported with no target and never flagged.

    Returns a frame with `lane`, `date`, `n`, `low`, `high`, `out_of_range` and
    `persistent_excursion`. Excursions outside the range are never dropped, only
    flagged; a run's caller decides what to do with a flagged row.
    `persistent_excursion` marks a row that is part of a run of at least
    `persistent_sessions` *consecutive rows in `membership`'s own date sequence*
    with `out_of_range` set — the caller is expected to pass one row per lane
    trading session with no gaps (a full era's dates), since this function has
    no calendar of its own to detect a gap.
    """
    ranges = TARGET_SIZE_RANGES if ranges is None else ranges
    sizes = (membership.groupby(["lane", "date"]).size().rename("n").reset_index()
             .sort_values(["lane", "date"]).reset_index(drop=True))
    ranged = sizes["lane"].isin(ranges)
    sizes["low"] = sizes["lane"].map(lambda l: ranges.get(l, (np.nan, np.nan))[0])
    sizes["high"] = sizes["lane"].map(lambda l: ranges.get(l, (np.nan, np.nan))[1])
    sizes["out_of_range"] = ranged & ((sizes["n"] < sizes["low"]) | (sizes["n"] > sizes["high"]))

    run_id = sizes.groupby("lane")["out_of_range"].transform(lambda s: (s != s.shift()).cumsum())
    run_len = sizes.groupby(["lane", run_id])["out_of_range"].transform("size")
    sizes["persistent_excursion"] = sizes["out_of_range"] & (run_len >= persistent_sessions)
    return sizes

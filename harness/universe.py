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
last requested date, not per-date `as_of = D`. This is correct by construction,
not by assumption: `harness.store.schema.AVAILABLE_ON_DATE` lists `bars_daily`,
`marketcap` and `listing` (along with `calendar`, `actions` and
`lane_membership`) as tables whose writer refuses any row whose `available_at`
differs from its own date (`docs/store.md`, "Availability invariant"), so a row
dated t <= D is always known by D regardless of what `as_of` a read used to
fetch it — a single `as_of = max(dates)` read returns exactly the rows a
per-date `as_of = D` read would for each requested D. `tests/universe/` pins
this: a row that violates the invariant can't be written at all, and a call
asked for extra, later dates leaves an earlier date's result unchanged even
when every table carries ordinary (compliant) rows dated after it. The per-D
screen values are computed from that one panel without ever looking past D,
which the invariance tests also check directly by perturbing every bar (and,
separately, every market-cap row and listing event) dated after D and
confirming D's membership doesn't move.

`symbols` and `exchange_on` (see "Equity eligibility" below) are the two
exceptions to the windowed-read design: `symbols.available_at` is a symbol's
first listing date, not "this row's own date", so it's fetched once with
`as_of = max(dates)` for the (non-point-in-time) `category` only; `exchange`
is point-in-time and fetched once per requested date instead.

Missing bars are never forward-filled (spec/02 Trading calendars): a
(symbol, session) slot with no bar counts as absent for both the 250-day
completeness check and every rolling window that touches it.
"""

from __future__ import annotations

import json
from typing import Mapping, Protocol, Sequence

import numpy as np
import pandas as pd

from config.params import SPEC01
from harness.store.calendar import calendar_for_lane
from harness.store.reader import AsOfReader, iso_date
from harness.store.writer import upsert

EQUITY_MARKET = "us_equity"
EQUITY_LANES = ("smallcap", "discovered")

# spec/01 Eligibility. `category` is a TICKERS current value, allowlisted like
# `sector` (spec/04; PM ruling on issue 6's Q4) — read as-is, no point-in-time
# reconstruction. `exchange` is point-in-time; see `_exchange_frame` below.
ELIGIBLE_CATEGORIES = (
    "Domestic Common Stock",
    "Domestic Common Stock Primary Class",
    "Domestic Common Stock Secondary Class",
)
ELIGIBLE_EXCHANGES = ("NYSE", "NASDAQ", "NYSEMKT", "NYSEARCA", "BATS")

# spec/01 Parameters, from config/params.py (issue 17, PR 24) — the single
# input to the run's configuration hash (spec/03 Run record). Decimal ->
# float: every value here feeds arithmetic against float bars and market caps.
HISTORY_SESSIONS = SPEC01.equities_full_history_days   # 250 lane trading days ending at D
LIQUIDITY_WINDOW = SPEC01.liquidity_floor_window_days  # 20 lane trading days ending D-1
VOL_WINDOW = SPEC01.vol_floor_window_days              # 20 lane trading days ending D
SMALLCAP_CEILING = float(SPEC01.small_cap_ceiling_usd)         # USD market cap, DAILY dated D
LIQUIDITY_FLOOR = float(SPEC01.liquidity_floor_equities_usd)   # USD median dollar volume
VOL_FLOOR = float(SPEC01.vol_floor_equities)                   # 20-day annualized realized vol
PRICE_FLOOR = float(SPEC01.price_floor_equities_usd)           # unadjusted close on D
# spec/02 Trading calendars: "Annualization uses sqrt(252) for equities" — a
# calendar convention, not one of config/params.py's locked parameters.
EQUITY_ANNUALIZATION = 252 ** 0.5

# A read this early returns nothing before the store's actual history; it exists
# so listing events and calendar sessions from long before the requested window
# are still picked up (a symbol's listing date, or the 250-day lookback, can sit
# well before the earliest date a caller asks to build).
EARLIEST_CALENDAR_DATE = "1900-01-01"
# A sentinel later than any real date, for "no listed/delisted event exists"
# (see its use in _equity_screen_frame).
NO_EVENT = "9999-12-31"

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


def _exchange_frame(reader: AsOfReader, market: str, symbols: Sequence[str],
                    dates: list[str], as_of: str) -> pd.DataFrame:
    """Per (symbol, date) exchange, via `AsOfReader.exchange_on` (spec/01
    Eligibility; PM ruling on issue 6's Q4, penumbra-specs PR 10): the most
    recent ACTIONS listing or exchange-change event on or before the date,
    falling back to the TICKERS current `exchange`. One call per requested
    date, since `exchange_on` takes a single date, not a window."""
    frames = []
    for d in dates:
        ex = reader.exchange_on(market, symbols, d, as_of)
        if not ex.empty:
            frames.append(ex[["symbol", "exchange"]].assign(date=d))
    if not frames:
        return pd.DataFrame(columns=["symbol", "date", "exchange"])
    return pd.concat(frames, ignore_index=True)


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

    # category is allowlisted like sector (spec/04): a current TICKERS value,
    # read as-is (PM ruling on issue 6's Q4). exchange is point-in-time.
    cat_attrs = (attrs[["symbol", "category"]] if not attrs.empty
                else pd.DataFrame(columns=["symbol", "category"]))
    grid = grid.merge(cat_attrs, on="symbol", how="left")
    grid["category_ok"] = grid["category"].isin(ELIGIBLE_CATEGORIES)

    exchange_frame = _exchange_frame(reader, EQUITY_MARKET, symbols_list, dates, d_max)
    grid = grid.merge(exchange_frame, on=["symbol", "date"], how="left")
    grid["exchange_ok"] = grid["exchange"].isin(ELIGIBLE_EXCHANGES)

    min_listed = (listing[listing["event"] == "listed"].groupby("symbol")["date"].min()
                 if not listing.empty else pd.Series(dtype=object))
    min_delisted = (listing[listing["event"] == "delisted"].groupby("symbol")["date"].min()
                   if not listing.empty else pd.Series(dtype=object))
    sym_listing = pd.DataFrame({"symbol": symbols_list})
    # A symbol with no listed/delisted event maps to NaN; comparing a string
    # "date" column against a float NaN array raises under pandas' pyarrow-
    # backed string dtype (it did in CI, not locally, since that comparison's
    # behavior is dtype-backend dependent). NO_EVENT is a sentinel date after
    # any real one, so "never listed" and "never delisted" are plain string
    # comparisons against a string, valid on every dtype backend: a symbol
    # with no listed event never satisfies `date >= min_listed`, and one with
    # no delisted event always satisfies `date < min_delisted`.
    sym_listing["min_listed"] = sym_listing["symbol"].map(min_listed).fillna(NO_EVENT)
    sym_listing["min_delisted"] = sym_listing["symbol"].map(min_delisted).fillna(NO_EVENT)
    grid = grid.merge(sym_listing, on="symbol", how="left")
    # spec/02 Store: listed on D = a `listed` event on or before D and no
    # `delisted` event on or before D (harness.store.reader.AsOfReader.listed).
    grid["listed_on_d"] = ((grid["date"] >= grid["min_listed"])
                           & (grid["date"] < grid["min_delisted"]))

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
    `discovered` — confirmed on PR 32's review: the size targets fit
    `discovered` being a superset, and "never pooled into one model" (spec/01,
    `DECISIONS.md`) means the lanes are reported separately, not that their
    membership is disjoint.
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

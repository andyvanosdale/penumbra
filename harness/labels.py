"""The quarantined labeler (spec/04 Labels; spec/05 steps 5-7; spec/03 Era
boundaries; spec/01 Delisting while a position is open; spec/06).

The labeler is the only component that reads prices after the signal date, and it
reads them only through `harness.store.oracle.OracleReader`, whose reads are
bounded by the era's last trading day and by the holdout unlock. Only the
backtester imports this module (tests/test_architecture.py); its output meets the
features there and nowhere else.

For every candidate it simulates the committed rule's entry and exit, charges
both legs through the cost model, and stores the realized gross and net exit
return (the net return is the decision quantity), the forward returns at the
spec/04 horizons, the ex-post `news`/`noise` bucket and the delisting treatment.

Price basis (spec/05 "Corporate actions during an open position";
docs/architecture.md "Adjustment", consequence 2). The target and the stop are
fixed in the price basis of the signal day D. Every later bar is read with
`adjust='split_div', basis=D`, i.e. divided by the factors of the actions dated in
(D, t]. A split therefore neither triggers the stop nor moves the target, the
share count scales with the split, and a cash dividend paid while the position is
open is credited to the return through the dividend-adjusted basis: the
exit price in D's basis is the unadjusted price divided by (1 - div / close_ex-1),
which is the price plus the dividend reinvested at the ex-date close. The credit
is reported separately as `dividend_credit` (gross in the split_div basis minus
gross in the split-only basis).

Costs come through `CostModelLike`, the interface issue 7's `harness/costs.py`
implements. Nothing here imports `harness.costs`: the backtester constructs the
model (with the stress case) and passes it in, and each candidate row carries the
model's own inputs object in `cost_inputs`.
"""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

import numpy as np
import pandas as pd

from config.params import SPEC01, SPEC04, SPEC05
from harness.levels import hard_stop_level, market_for_lane
from harness.store.calendar import calendar_for_lane
from harness.store.oracle import OracleReader
from harness.store.reader import iso_date

# --- Cost interface (issue 7, harness/costs.py) --------------------------------

LegType = Literal["entry", "exit_target", "exit_stop", "exit_time", "exit_delist",
                  "exit_era_end"]


class LegCostLike(Protocol):
    """Per-leg cost, each component a fraction of the leg's order notional."""
    spread: float
    slippage: float
    fee: float
    floor_bound: bool


class CostModelLike(Protocol):
    def leg(self, inputs: Any, leg: LegType, order_notional: float) -> LegCostLike: ...


# --- Locked parameters -----------------------------------------------------------

ORDER_SIZE = float(SPEC05.order_size_usd)
TIME_STOP_SESSIONS = SPEC05.time_stop_sessions
NO_BAR_CLOSURE_SESSIONS = SPEC05.no_bar_closure_sessions
CRYPTO_ENTRY_HOUR = SPEC05.crypto_entry_hour_utc
HORIZONS = tuple(SPEC04.horizon_days)
HAIRCUT_NASDAQ = float(SPEC01.delisting_haircut_nasdaq)
HAIRCUT_NYSE = float(SPEC01.delisting_haircut_nyse_amex)
DEFAULT_CRYPTO_LOT = 1e-8

# spec/01: exits at the last close.
LAST_CLOSE_REASONS = frozenset({"acquisitionby", "mergerto", "voluntarydelisting"})
# spec/01: exits at a haircut of the last close, by the listing exchange.
HAIRCUT_REASONS = frozenset({"bankruptcyliquidation", "regulatorydelisting"})
HAIRCUT_BY_EXCHANGE = {"NASDAQ": HAIRCUT_NASDAQ, "NYSE": HAIRCUT_NYSE,
                       "NYSEMKT": HAIRCUT_NYSE, "NYSE AMERICAN": HAIRCUT_NYSE,
                       "NYSE MKT": HAIRCUT_NYSE, "AMEX": HAIRCUT_NYSE}

# Bucket window, lane sessions around D (spec/04 Labels).
BUCKET_BEFORE, BUCKET_AFTER = 2, 4

EXIT_LEG: dict[str, LegType] = {
    "stop": "exit_stop", "target": "exit_target", "time": "exit_time",
    "delist": "exit_delist", "no_bar_delist": "exit_delist", "era_end": "exit_era_end",
}

REQUIRED_COLUMNS = ("symbol", "signal_date", "target_level", "stop_range", "cost_inputs")

# Unfilled reasons.
UNFILLED_ZERO_RANGE = "zero_range"
UNFILLED_NO_BAR = "no_bar_on_fill_day"
UNFILLED_NO_SESSION = "no_fill_session_in_era"
UNFILLED_NO_LEVELS = "levels_missing"

# Flags.
FLAG_ERA_TRUNCATED = "era_truncated"
FLAG_HELD_AT_LAST_CLOSE = "held_at_last_close"
FLAG_POST_DELIST_PRICE = "post_delisting_price"
FLAG_EXCHANGE_UNMAPPED = "haircut_exchange_unmapped"
FLAG_REASON_UNKNOWN = "delist_reason_unknown"
FLAG_NO_BAR_AT_ERA_END = "no_bar_at_era_end"
FLAG_BUCKET_TRUNCATED = "bucket_window_truncated"
FLAG_DELIST_ON_FILL = "delisted_by_fill_session"

OUTPUT_COLUMNS = (
    "symbol", "signal_date", "status", "unfilled_reason",
    "target_level", "stop_range", "stop_level",
    "entry_date", "entry_price", "entry_price_unadj", "shares", "entry_notional",
    "entry_leg", "entry_spread", "entry_slippage", "entry_fee", "entry_floor_bound",
    "exit_date", "exit_price", "exit_price_unadj", "exit_shares", "exit_notional",
    "exit_reason", "exit_leg", "exit_spread", "exit_slippage", "exit_fee",
    "exit_floor_bound", "sessions_held",
    "delist_reason", "delist_exchange", "haircut",
    "era_truncated", "flags",
    "gross", "dividend_credit", "net",
    *[f"fwd_{h}" for h in HORIZONS],
    "bucket", "eventcodes",
)


def _flags_str(flags: list[str]) -> str:
    return "|".join(dict.fromkeys(flags))


@dataclass
class _Series:
    """One candidate's bars from the fill session on, in three bases."""
    adj: pd.DataFrame        # split_div, basis D
    split: pd.DataFrame      # split only, basis D
    unadj: pd.DataFrame      # none

    def __post_init__(self):
        for name in ("adj", "split", "unadj"):
            setattr(self, name, getattr(self, name).set_index("date"))

    def has(self, d: str) -> bool:
        return d in self.adj.index

    def last_on_or_before(self, d: str) -> str | None:
        idx = self.adj.index[self.adj.index <= d]
        return idx[-1] if len(idx) else None

    def unadj_factor(self, d: str) -> float:
        """Unadjusted price / split_div basis-D price for the bar dated d."""
        return float(self.unadj.at[d, "close"]) / float(self.adj.at[d, "close"])

    def split_to_adj(self, d: str) -> float:
        """split-only basis-D price / split_div basis-D price for the bar dated d."""
        return float(self.split.at[d, "close"]) / float(self.adj.at[d, "close"])

    def split_multiple(self, d: str) -> float:
        """unadjusted / split-only basis-D price: S(t) / S(D) (docs/labels.md)."""
        return float(self.unadj.at[d, "close"]) / float(self.split.at[d, "close"])


@dataclass
class _Exit:
    date: str
    price: float           # split_div basis D
    reason: str
    price_date: str        # the bar whose basis converts `price` to unadjusted
    flags: list[str] = field(default_factory=list)
    delist_reason: str | None = None
    delist_exchange: str | None = None
    haircut: float | None = None


def _delist_value(series: _Series, delist: dict | None, lane: str, until: str
                  ) -> tuple[float, str, list[str], float | None]:
    """spec/01 delisting treatment. Returns (price in basis D, price bar, flags, haircut).

    `until` is the last date whose bar may serve as the last close.
    """
    flags: list[str] = []
    ref_date = delist["date"] if delist is not None else until
    last = series.last_on_or_before(min(ref_date, until))
    last_close = float(series.adj.at[last, "close"])
    if delist is None:
        # Bars stopped with no delisting record: held at the last close, flagged.
        return last_close, last, [FLAG_HELD_AT_LAST_CLOSE], None
    if lane == "crypto":
        return last_close, last, flags, None
    reason = delist.get("reason")
    if reason in LAST_CLOSE_REASONS:
        return last_close, last, flags, None
    if reason not in HAIRCUT_REASONS:
        # A delisting whose reason is not one spec/01 names: the conservative
        # (haircut) treatment, flagged for the report.
        flags.append(FLAG_REASON_UNKNOWN)
    # A post-delisting price in the store replaces the haircut: the first bar
    # dated after the delisting date.
    after = series.adj.index[series.adj.index > delist["date"]]
    if len(after):
        return float(series.adj.at[after[0], "close"]), after[0], flags + [FLAG_POST_DELIST_PRICE], None
    exchange = (delist.get("exchange") or "").upper()
    haircut = HAIRCUT_BY_EXCHANGE.get(exchange)
    if haircut is None:
        flags.append(FLAG_EXCHANGE_UNMAPPED)
        haircut = min(HAIRCUT_NASDAQ, HAIRCUT_NYSE)
    return haircut * last_close, last, flags, haircut


def _simulate(series: _Series, sessions: list[str], fill_idx: int, target: float,
              stop: float, delist: dict | None, lane: str, era_last: str,
              stop_at_low: bool) -> tuple[_Exit, int]:
    """Walk the sessions after the fill session (spec/05 step 6). Returns the exit
    and the number of bar sessions held after the fill session."""
    bar_sessions = 0
    missing = 0
    pending: str | None = None  # "target" or "time": exit at the next open
    fill_date = sessions[fill_idx]

    def delist_exit(on: str, reason: str) -> _Exit:
        price, pdate, flags, haircut = _delist_value(series, delist, lane, on)
        return _Exit(on, price, reason, pdate, flags,
                     delist.get("reason") if delist else None,
                     delist.get("exchange") if delist else None, haircut)

    if delist is not None and delist["date"] <= fill_date:
        # Delisted by the fill session: closed on the first session after it.
        nxt = sessions[fill_idx + 1] if fill_idx + 1 < len(sessions) else fill_date
        ex = delist_exit(nxt, "delist")
        ex.flags.append(FLAG_DELIST_ON_FILL)
        return ex, 0

    for t in sessions[fill_idx + 1:]:
        if delist is not None and t > delist["date"]:
            # Past the delisting date (a non-session delisting date): any bar here
            # is a post-delisting price, never a tradable session.
            return delist_exit(t, "delist"), bar_sessions
        has_bar = series.has(t)
        if has_bar:
            missing = 0
            bar = series.adj.loc[t]
            o, lo, c = float(bar["open"]), float(bar["low"]), float(bar["close"])
            if pending is not None:
                return _Exit(t, o, pending, t), bar_sessions
            bar_sessions += 1
            # 1. Hard stop: gap-through fills at the open; otherwise at the level,
            #    or at the low in a stress case (spec/06 Cost stress).
            if o <= stop:
                return _Exit(t, o, "stop", t), bar_sessions
            if lo < stop:
                return _Exit(t, lo if stop_at_low else stop, "stop", t), bar_sessions
            if delist is not None and t >= delist["date"]:
                return delist_exit(t, "delist"), bar_sessions
            if t == era_last:
                return _Exit(t, c, "era_end", t, [FLAG_ERA_TRUNCATED]), bar_sessions
            # 2. Target on the close, filled at the next open.
            if c >= target:
                pending = "target"
            # 3. Time stop after the 10th session with a bar after the fill.
            elif bar_sessions >= TIME_STOP_SESSIONS:
                pending = "time"
        else:
            if delist is not None and t >= delist["date"]:
                return delist_exit(t, "delist"), bar_sessions
            # A session with no bar evaluates no exit and does not advance the
            # time stop; the fifth in a row closes the position (spec/05).
            missing += 1
            if missing >= NO_BAR_CLOSURE_SESSIONS:
                return delist_exit(t, "no_bar_delist"), bar_sessions
            if t == era_last:
                last = series.last_on_or_before(t)
                return _Exit(t, float(series.adj.at[last, "close"]), "era_end", last,
                             [FLAG_ERA_TRUNCATED, FLAG_NO_BAR_AT_ERA_END]), bar_sessions
    # The fill session is the era's last session: closed at that close.
    return (_Exit(fill_date, float(series.adj.at[fill_date, "close"]), "era_end", fill_date,
                  [FLAG_ERA_TRUNCATED]), bar_sessions)


def _forward(series: _Series, sessions: list[str], fill_idx: int, entry: float,
             delist: dict | None, lane: str, era_last: str) -> dict[str, float | None]:
    """Forward returns from the entry fill to the close h lane sessions after the
    fill session, in basis D. Null past the era's last trading day (spec/03). A
    name delisted by the horizon is valued by the delisting treatment; a name with
    no bar on the horizon session is held at its last close (spec/01)."""
    out: dict[str, float | None] = {}
    for h in HORIZONS:
        i = fill_idx + h
        if i >= len(sessions) or sessions[i] > era_last:
            out[f"fwd_{h}"] = None
            continue
        s = sessions[i]
        if delist is not None and delist["date"] <= s:
            price = _delist_value(series, delist, lane, s)[0]
        else:
            price = float(series.adj.at[series.last_on_or_before(s), "close"])
        out[f"fwd_{h}"] = price / entry - 1.0
    return out


def _leg(cost_model: CostModelLike, inputs: Any, leg: LegType, notional: float, prefix: str
         ) -> dict[str, Any]:
    lc = cost_model.leg(inputs, leg, notional)
    return {f"{prefix}_leg": leg, f"{prefix}_spread": float(lc.spread),
            f"{prefix}_slippage": float(lc.slippage), f"{prefix}_fee": float(lc.fee),
            f"{prefix}_floor_bound": bool(lc.floor_bound)}


def _leg_total(row: dict, prefix: str) -> float:
    return row[f"{prefix}_spread"] + row[f"{prefix}_slippage"] + row[f"{prefix}_fee"]


def label(oracle: OracleReader, candidates: pd.DataFrame, lane: str, era_last_date,
          cost_model: CostModelLike, stress=None, *, lot_size: float = DEFAULT_CRYPTO_LOT
          ) -> pd.DataFrame:
    """Label every candidate: one row per candidate, OUTPUT_COLUMNS.

    `candidates` has REQUIRED_COLUMNS: `target_level` and `stop_range` in D's
    split-and-dividend-adjusted basis (from `harness.levels.entry_levels`), and
    `cost_inputs`, the cost model's inputs object for the candidate. `stress` is a
    `config.params.StressCase` or None; only its `stop_fills_at_low` is read here
    (the cost model applies its multipliers). Every read is bounded by
    `era_last_date` and by the oracle's own bounds and holdout lock.
    """
    missing = [c for c in REQUIRED_COLUMNS if c not in candidates.columns]
    if missing:
        raise ValueError(f"candidates lack columns {missing}")
    era_last = iso_date(era_last_date)
    market = market_for_lane(lane)
    cal_name = calendar_for_lane(lane)
    stop_at_low = bool(getattr(stress, "stop_fills_at_low", False))
    if candidates.empty:
        return pd.DataFrame(columns=list(OUTPUT_COLUMNS))

    signal_dates = [iso_date(d) for d in candidates["signal_date"]]
    first = (dt.date.fromisoformat(min(signal_dates)) - dt.timedelta(days=15)).isoformat()
    # This read is the first to touch the era bound, so an era past the oracle's
    # bound or into a locked holdout is refused before anything is labeled.
    sessions = oracle.calendar(cal_name, first, era_last)["date"].tolist()
    if not sessions:
        raise ValueError(f"no {cal_name} sessions between {first} and {era_last}")
    # The boundary the rule compares against is the era's last session on or
    # before `era_last_date` (the date itself may be a weekend or holiday).
    era_last = sessions[-1]
    pos = {d: i for i, d in enumerate(sessions)}

    rows = []
    for cand, D in zip(candidates.to_dict("records"), signal_dates):
        rows.append(_label_one(oracle, cand, D, lane, market, sessions, pos, era_last,
                               cost_model, stop_at_low, lot_size))
    return pd.DataFrame(rows, columns=list(OUTPUT_COLUMNS))


def _bucket(oracle: OracleReader, market: str, symbol: str, sessions: list[str],
            d_idx: int, lane: str) -> dict[str, Any]:
    """spec/04: `news` if an EVENTS row has a filing date in [D-2, D+4] lane
    sessions, else `noise`. Crypto has no EVENTS and is always `noise`."""
    if lane == "crypto":
        return {"bucket": "noise", "eventcodes": None, "_flags": []}
    lo = sessions[max(d_idx - BUCKET_BEFORE, 0)]
    hi_idx = d_idx + BUCKET_AFTER
    flags = []
    if hi_idx >= len(sessions):
        hi_idx = len(sessions) - 1
        flags.append(FLAG_BUCKET_TRUNCATED)
    ev = oracle.events(market, [symbol], lo, sessions[hi_idx])
    if ev.empty:
        return {"bucket": "noise", "eventcodes": None, "_flags": flags}
    codes = sorted({c for s in ev["eventcodes"].dropna() for c in str(s).split("|") if c})
    return {"bucket": "news", "eventcodes": "|".join(codes), "_flags": flags}


def _label_one(oracle: OracleReader, cand: dict, D: str, lane: str, market: str,
               sessions: list[str], pos: dict[str, int], era_last: str,
               cost_model: CostModelLike, stop_at_low: bool, lot_size: float) -> dict:
    sym = str(cand["symbol"])
    target = float(cand["target_level"])
    stop_range = float(cand["stop_range"])
    row: dict[str, Any] = {c: None for c in OUTPUT_COLUMNS}
    row.update(symbol=sym, signal_date=D, target_level=target, stop_range=stop_range,
               era_truncated=False)
    if D not in pos:
        raise ValueError(f"signal date {D} for {sym} is not a {lane} session in the era")
    d_idx = pos[D]
    b = _bucket(oracle, market, sym, sessions, d_idx, lane)
    flags: list[str] = b.pop("_flags")
    row.update(b)

    def unfilled(reason: str) -> dict:
        row.update(status="unfilled", unfilled_reason=reason, flags=_flags_str(flags))
        return row

    if not (math.isfinite(target) and math.isfinite(stop_range)):
        return unfilled(UNFILLED_NO_LEVELS)
    if stop_range <= 0:
        return unfilled(UNFILLED_ZERO_RANGE)

    # --- Entry (spec/05 step 5) --------------------------------------------------
    if lane == "crypto":
        fill_date = (dt.date.fromisoformat(D) + dt.timedelta(days=1)).isoformat()
    else:
        fill_date = sessions[d_idx + 1] if d_idx + 1 < len(sessions) else None
    if fill_date is None or fill_date > era_last or fill_date not in pos:
        return unfilled(UNFILLED_NO_SESSION)
    fill_idx = pos[fill_date]
    read_end = sessions[min(fill_idx + max(HORIZONS), len(sessions) - 1)]
    series = _Series(
        oracle.bars(market, [sym], fill_date, read_end, adjust="split_div", basis=D),
        oracle.bars(market, [sym], fill_date, read_end, adjust="split", basis=D),
        oracle.bars(market, [sym], fill_date, read_end, adjust="none"))
    if lane == "crypto":
        ts = f"{fill_date}T{CRYPTO_ENTRY_HOUR:02d}:00:00.000Z"
        k = oracle.hourly(market, [sym], fill_date, fill_date)
        k = k[k["ts"] == ts]
        if k.empty or not series.has(fill_date):
            return unfilled(UNFILLED_NO_BAR)
        entry_unadj = float(k["open"].iloc[0])
        entry = entry_unadj  # Binance has no corporate actions.
        shares = math.floor(ORDER_SIZE / entry_unadj / lot_size + 1e-9) * lot_size
    else:
        if not series.has(fill_date):
            return unfilled(UNFILLED_NO_BAR)
        entry = float(series.adj.at[fill_date, "open"])
        entry_unadj = float(series.unadj.at[fill_date, "open"])
        # Order sizing uses the unadjusted series (spec/02 Store).
        shares = float(math.floor(ORDER_SIZE / entry_unadj))
    entry_notional = shares * entry_unadj
    stop = hard_stop_level(entry, stop_range)
    row.update(status="filled", entry_date=fill_date, entry_price=entry,
               entry_price_unadj=entry_unadj, shares=shares, entry_notional=entry_notional,
               stop_level=stop)
    row.update(_leg(cost_model, cand["cost_inputs"], "entry", entry_notional, "entry"))

    # --- Exit (spec/05 step 6; spec/01; spec/03) ----------------------------------
    lst = oracle.listing(market, [sym], fill_date, read_end)
    dl = lst[lst["event"] == "delisted"]
    delist = dl.iloc[0].to_dict() if not dl.empty else None
    ex, held = _simulate(series, sessions, fill_idx, target, stop, delist, lane, era_last,
                         stop_at_low)
    flags += ex.flags
    exit_unadj = ex.price * series.unadj_factor(ex.price_date)
    exit_shares = shares * series.split_multiple(fill_date) / series.split_multiple(ex.price_date)
    exit_notional = exit_shares * exit_unadj
    row.update(exit_date=ex.date, exit_price=ex.price, exit_price_unadj=exit_unadj,
               exit_shares=exit_shares, exit_notional=exit_notional, exit_reason=ex.reason,
               sessions_held=held, delist_reason=ex.delist_reason,
               delist_exchange=ex.delist_exchange, haircut=ex.haircut,
               era_truncated=FLAG_ERA_TRUNCATED in ex.flags)
    row.update(_leg(cost_model, cand["cost_inputs"], EXIT_LEG[ex.reason], exit_notional, "exit"))

    # Gross: entry fill to exit fill in basis D, dividends credited. Net charges
    # each leg's cost fractions on that leg's notional, per unit of entry notional.
    gross = ex.price / entry - 1.0
    gross_split = (ex.price * series.split_to_adj(ex.price_date)) / \
        (entry * series.split_to_adj(fill_date)) - 1.0
    row["gross"] = gross
    row["dividend_credit"] = gross - gross_split
    row["net"] = (gross - _leg_total(row, "entry")
                  - _leg_total(row, "exit") * exit_notional / entry_notional
                  if entry_notional > 0 else float("nan"))
    row.update(_forward(series, sessions, fill_idx, entry, delist, lane, era_last))
    row["flags"] = _flags_str(flags)
    return row


def forward_null_counts(labels: pd.DataFrame) -> pd.DataFrame:
    """Per horizon: filled candidates, null forward returns (censored at the era
    boundary, spec/03), and non-null. Reported alongside the horizon curve."""
    filled = labels[labels["status"] == "filled"]
    rows = []
    for h in HORIZONS:
        col = filled[f"fwd_{h}"]
        rows.append({"horizon": h, "filled": len(filled), "null": int(col.isna().sum()),
                     "non_null": int(col.notna().sum())})
    return pd.DataFrame(rows, columns=["horizon", "filled", "null", "non_null"])

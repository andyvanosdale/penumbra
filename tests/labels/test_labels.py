"""The quarantined labeler (issue 9): entries, every exit path, delisting, corporate
actions, era censoring, the ex-post bucket and costs per leg.

Exit-path scenarios use one name at a flat 100 (open = close = 100, low 99.5), a
signal-day range of 2 so the hard stop sits at fill - 3 = 97, and a target of 105;
then one session is edited to trigger the path under test.
"""

from __future__ import annotations

import math

import pandas as pd
import pytest

from config.params import STRESS_CASES
from harness.labels import (OUTPUT_COLUMNS, UNFILLED_NO_BAR, UNFILLED_NO_LEVELS,
                            UNFILLED_NO_SESSION, UNFILLED_ZERO_RANGE, forward_null_counts,
                            label)
from harness.store.oracle import HoldoutLockedError, OracleBoundError, OracleReader
from tests.fixtures import store as fx
from tests.fixtures.label_store import SNAPSHOT, flat, scenario_store, sessions_between
from tests.labels._cost_stub import STUB_SLIPPAGE, CostInputs, CostModel

SYM = "100100"
SESSIONS = sessions_between("2021-06-01", "2021-08-31")
D_IDX = 20
D = SESSIONS[D_IDX]
F = D_IDX + 1              # fill session index
FILL = SESSIONS[F]
TARGET, RANGE = 105.0, 2.0
STOP = 100.0 - 1.5 * RANGE  # 97
HOLDOUT = "2024-01-01"


def s(k: int) -> str:
    """The k-th session after the fill session."""
    return SESSIONS[F + k]


def after(k: int) -> list[str]:
    """Every session after the k-th session after the fill."""
    return SESSIONS[F + k + 1:]


def candidates(sym=SYM, dates=(D,), target=TARGET, rng=RANGE, lane="smallcap"):
    return pd.DataFrame([dict(symbol=sym, signal_date=d, target_level=target, stop_range=rng,
                              cost_inputs=CostInputs(lane, sym, d)) for d in dates])


def run(bars=None, *, edits=None, drop=(), listing=(), actions=(), events=(), era_last=None,
        cands=None, stress=None, sessions=SESSIONS, oracle_last=None):
    b = flat(sessions) if bars is None else bars
    for d, v in (edits or {}).items():
        b[d] = v
    for d in drop:
        b.pop(d, None)
    conn = scenario_store(sessions, {SYM: b}, listing=listing, actions=actions, events=events)
    era_last = era_last or sessions[-1]
    oracle = OracleReader(conn, SNAPSHOT, oracle_last or era_last, HOLDOUT)
    cm = CostModel("smallcap", stress)
    out = label(oracle, candidates() if cands is None else cands, "smallcap", era_last, cm,
                stress)
    return out, cm


def one(**kw) -> dict:
    out, _ = run(**kw)
    assert len(out) == 1
    return out.iloc[0].to_dict()


# --- Entry ------------------------------------------------------------------------

def test_entry_at_next_open_and_shares_rounded_down():
    r = one(edits={FILL: (103.0, 103.5, 102.5, 103.0)})
    assert r["status"] == "filled" and r["entry_date"] == FILL
    assert r["entry_price"] == 103.0
    assert r["shares"] == math.floor(10_000 / 103.0) == 97
    assert r["entry_notional"] == pytest.approx(97 * 103.0)
    assert r["stop_level"] == pytest.approx(103.0 - 3.0)
    assert list(r) == list(OUTPUT_COLUMNS)


def test_unfilled_cases():
    r = one(drop=[FILL])
    assert (r["status"], r["unfilled_reason"]) == ("unfilled", UNFILLED_NO_BAR)
    r = one(cands=candidates(rng=0.0))
    assert (r["status"], r["unfilled_reason"]) == ("unfilled", UNFILLED_ZERO_RANGE)
    r = one(cands=candidates(target=float("nan")))
    assert r["unfilled_reason"] == UNFILLED_NO_LEVELS
    # A signal on the era's last session has no fill session inside the era.
    r = one(cands=candidates(dates=(SESSIONS[40],)), era_last=SESSIONS[40])
    assert r["unfilled_reason"] == UNFILLED_NO_SESSION
    # Unfilled candidates are not carried: no entry, no exit, no legs charged.
    out, cm = run(drop=[FILL])
    assert out.iloc[0]["entry_date"] is None and cm.calls == []


# --- Exits ------------------------------------------------------------------------

def test_time_stop_after_tenth_session_at_next_open():
    r = one(edits={s(11): (101.0, 101.5, 100.5, 101.0)})
    assert r["exit_reason"] == "time" and r["exit_leg"] == "exit_time"
    assert r["exit_date"] == s(11) and r["exit_price"] == 101.0
    assert r["sessions_held"] == 10
    assert r["gross"] == pytest.approx(0.01)


def test_target_on_close_fills_next_open():
    r = one(edits={s(3): (100.0, 105.5, 99.5, 105.0), s(4): (106.0, 106.5, 105.5, 106.0)})
    assert r["exit_reason"] == "target" and r["exit_date"] == s(4)
    assert r["exit_price"] == 106.0 and r["exit_leg"] == "exit_target"


def test_hard_stop_at_level():
    r = one(edits={s(2): (100.0, 100.5, 96.0, 99.0)})
    assert r["exit_reason"] == "stop" and r["exit_date"] == s(2)
    assert r["exit_price"] == pytest.approx(STOP) and r["exit_leg"] == "exit_stop"


def test_stop_gap_through_fills_at_the_open():
    r = one(edits={s(2): (95.0, 95.5, 94.0, 95.0)})
    assert r["exit_reason"] == "stop" and r["exit_price"] == 95.0


@pytest.mark.parametrize("stress", STRESS_CASES, ids=lambda c: c.name)
def test_stress_stop_fills_at_the_low(stress):
    r = one(edits={s(2): (100.0, 100.5, 96.0, 99.0)}, stress=stress)
    assert r["exit_reason"] == "stop" and r["exit_price"] == 96.0


def test_stop_wins_a_tie_with_the_target():
    r = one(edits={s(2): (100.0, 106.0, 96.0, 106.0), s(3): (106.0, 106.5, 105.5, 106.0)})
    assert r["exit_reason"] == "stop" and r["exit_date"] == s(2)
    assert r["exit_price"] == pytest.approx(STOP)


def test_fill_session_is_never_an_exit_session():
    # The fill session trades through the stop and closes above the target.
    r = one(edits={FILL: (100.0, 110.0, 90.0, 110.0)})
    assert r["exit_date"] != FILL
    assert r["exit_reason"] == "time" and r["exit_date"] == s(11)


def test_no_bar_sessions_do_not_advance_the_time_stop():
    r = one(drop=[s(3), s(4)])
    assert r["exit_reason"] == "time" and r["sessions_held"] == 10
    assert r["exit_date"] == s(13)


def test_five_no_bar_sessions_close_at_last_close_flagged():
    r = one(edits={s(2): (100.0, 100.5, 99.5, 98.0)}, drop=[s(k) for k in range(3, 8)])
    assert r["exit_reason"] == "no_bar_delist" and r["exit_leg"] == "exit_delist"
    assert r["exit_date"] == s(7)
    assert r["exit_price"] == 98.0          # held at the last close
    assert "held_at_last_close" in r["flags"]


def test_four_no_bar_sessions_do_not_close():
    r = one(drop=[s(k) for k in range(3, 7)])
    assert r["exit_reason"] == "time" and r["sessions_held"] == 10


def test_bars_stopping_with_a_later_delisting_record_take_its_treatment():
    lst = [dict(market="us_equity", symbol=SYM, event="delisted", date=s(12),
                reason="bankruptcyliquidation", exchange="NASDAQ", source="actions")]
    r = one(drop=after(2), listing=lst)
    assert r["exit_reason"] == "no_bar_delist" and r["exit_date"] == s(7)
    assert r["exit_price"] == pytest.approx(0.45 * 100.0)
    assert r["haircut"] == 0.45 and r["delist_reason"] == "bankruptcyliquidation"


# --- Delisting (spec/01) ------------------------------------------------------------

@pytest.mark.parametrize("reason,exchange,mult", [
    ("acquisitionby", "NYSE", 1.0),
    ("mergerto", "NASDAQ", 1.0),
    ("voluntarydelisting", "NASDAQ", 1.0),
    ("bankruptcyliquidation", "NASDAQ", 0.45),
    ("bankruptcyliquidation", "NYSE", 0.70),
    ("regulatorydelisting", "NASDAQ", 0.45),
    ("regulatorydelisting", "NYSEMKT", 0.70),
])
def test_delisting_treatment(reason, exchange, mult):
    lst = [dict(market="us_equity", symbol=SYM, event="delisted", date=s(3), reason=reason,
                exchange=exchange, source="actions")]
    r = one(edits={s(3): (100.0, 100.5, 99.5, 98.0)}, drop=after(3),
            listing=lst)
    assert r["exit_reason"] == "delist" and r["exit_date"] == s(3)
    assert r["exit_leg"] == "exit_delist"
    assert r["exit_price"] == pytest.approx(mult * 98.0)
    assert r["delist_reason"] == reason
    assert r["haircut"] == (None if mult == 1.0 else mult)


def test_post_delisting_price_replaces_the_haircut():
    lst = [dict(market="us_equity", symbol=SYM, event="delisted", date=s(3),
                reason="bankruptcyliquidation", exchange="NASDAQ", source="actions")]
    bars = {d: v for d, v in flat(SESSIONS).items() if d <= s(3)}
    bars[s(6)] = (12.0, 12.0, 12.0, 12.0)
    r = one(bars=bars, listing=lst)
    assert r["exit_reason"] == "delist" and r["exit_price"] == 12.0
    assert r["haircut"] is None and "post_delisting_price" in r["flags"]


def test_a_post_delisting_bar_is_never_traded_on():
    # Delisted on a Saturday; the store holds a post-delisting bar the next
    # Monday whose low is through the stop. It prices the exit, it doesn't stop it.
    sat = (pd.Timestamp(s(3)) + pd.offsets.Week(weekday=5)).strftime("%Y-%m-%d")
    lst = [dict(market="us_equity", symbol=SYM, event="delisted", date=sat,
                reason="bankruptcyliquidation", exchange="NASDAQ", source="actions")]
    bars = {d: v for d, v in flat(SESSIONS).items() if d <= sat}
    monday = min(d for d in SESSIONS if d > sat)
    bars[monday] = (20.0, 20.0, 10.0, 15.0)
    r = one(bars=bars, listing=lst)
    assert r["exit_reason"] == "delist" and r["exit_date"] == monday
    assert r["exit_price"] == 15.0 and "post_delisting_price" in r["flags"]


def test_haircut_exchange_unmapped_takes_the_harsher_haircut_flagged():
    lst = [dict(market="us_equity", symbol=SYM, event="delisted", date=s(3),
                reason="regulatorydelisting", exchange="BATS", source="actions")]
    r = one(drop=after(3), listing=lst)
    assert r["exit_price"] == pytest.approx(0.45 * 100.0)
    assert "haircut_exchange_unmapped" in r["flags"]


def test_delisting_on_the_canonical_fixture_nasdaq_bankruptcy():
    conn = fx.build_store()
    oracle = OracleReader(conn, fx.SNAPSHOT, fx.END, HOLDOUT)
    r = label(oracle, candidates(fx.DELIST_SYM, ("2021-03-15",), target=50.0), "smallcap",
              fx.END, CostModel("smallcap")).iloc[0]
    last = fx.unadjusted_close(fx.DELIST_SYM, fx.DELIST_DATE)
    assert r["exit_reason"] == "delist" and r["exit_date"] == fx.DELIST_DATE
    assert r["exit_price"] == pytest.approx(0.45 * last)
    assert r["delist_exchange"] == "NASDAQ"


# --- Corporate actions (spec/05, PM spec PR) -------------------------------------------

def test_split_mid_position_neither_stops_nor_moves_the_target():
    conn = fx.build_store()
    oracle = OracleReader(conn, fx.SNAPSHOT, fx.END, HOLDOUT)
    D0 = "2021-03-15"                        # fill 03-16, split ex-date 03-17
    # Target 114: the D-basis close on 03-19 is 2 x 57 = 114 (unadjusted 57).
    r = label(oracle, candidates(fx.SPLIT_SYM, (D0,), target=114.0), "smallcap", fx.END,
              CostModel("smallcap")).iloc[0]
    fill_open = fx.unadjusted_close(fx.SPLIT_SYM, "2021-03-16") - 0.5
    assert r["entry_price"] == fill_open and r["shares"] == math.floor(10_000 / fill_open)
    # The unadjusted 03-17 open (55.5) is far below the stop; in D's basis it is 111.
    assert r["exit_reason"] == "target"
    assert r["exit_date"] == "2021-03-22"
    exit_unadj = fx.unadjusted_close(fx.SPLIT_SYM, "2021-03-22") - 0.5
    assert r["exit_price"] == pytest.approx(2 * exit_unadj)
    assert r["exit_price_unadj"] == pytest.approx(exit_unadj)
    assert r["exit_shares"] == pytest.approx(2 * r["shares"])
    assert r["target_level"] == 114.0
    assert r["dividend_credit"] == pytest.approx(0.0)
    assert r["exit_notional"] == pytest.approx(r["exit_shares"] * exit_unadj)


def test_dividend_is_credited_through_the_adjusted_basis():
    conn = fx.build_store()
    oracle = OracleReader(conn, fx.SNAPSHOT, fx.END, HOLDOUT)
    D0 = "2021-03-08"                        # fill 03-09, ex-date 03-10
    r = label(oracle, candidates(fx.DIV_SYM, (D0,), target=1e9), "smallcap", fx.END,
              CostModel("smallcap")).iloc[0]
    assert r["exit_reason"] == "time"
    prev = fx.unadjusted_close(fx.DIV_SYM, "2021-03-09")
    f = 1.0 - fx.DIV_AMOUNT / prev
    entry = prev - 0.5
    exit_unadj = fx.unadjusted_close(fx.DIV_SYM, r["exit_date"]) - 0.5
    assert r["entry_price"] == pytest.approx(entry)
    assert r["exit_price"] == pytest.approx(exit_unadj / f)
    assert r["gross"] == pytest.approx(exit_unadj / f / entry - 1)
    assert r["dividend_credit"] == pytest.approx(r["gross"] - (exit_unadj / entry - 1))
    assert r["dividend_credit"] > 0
    assert r["exit_shares"] == r["shares"]


# --- Era boundary (spec/03) -----------------------------------------------------------

def test_open_position_closes_at_the_era_close_truncated_and_charged():
    out, cm = run(era_last=s(5), edits={s(5): (100.0, 100.5, 99.5, 101.0)})
    r = out.iloc[0]
    assert r["exit_reason"] == "era_end" and r["exit_date"] == s(5)
    assert r["exit_price"] == 101.0 and r["era_truncated"]
    assert "era_truncated" in r["flags"] and r["exit_leg"] == "exit_era_end"
    assert [c[1] for c in cm.calls] == ["entry", "exit_era_end"]


def test_validation_candidate_near_era_end_gets_null_long_labels_not_holdout_prices():
    sessions = sessions_between("2023-09-01", "2024-06-28")
    bars = flat([d for d in sessions if d < HOLDOUT])
    bars.update(flat([d for d in sessions if d >= HOLDOUT], price=1000.0))  # holdout prices
    cands = candidates(dates=("2023-12-01", "2023-12-22"))
    # The validation era ends 2023-12-31 (a Sunday); its last session is 12-29.
    out, _ = run(bars=bars, sessions=sessions, cands=cands, era_last="2023-12-31")
    a, b = out.iloc[0], out.iloc[1]
    assert a["fwd_5"] == pytest.approx(0.0)
    for h in (21, 63, 252):
        assert pd.isna(a[f"fwd_{h}"]), h
    assert all(pd.isna(b[f"fwd_{h}"]) for h in (5, 21, 63, 252))
    # The second position is still open on the era's last session: closed there.
    assert b["exit_reason"] == "era_end" and b["exit_date"] == "2023-12-29"
    assert b["exit_price"] == 100.0
    assert out["exit_price"].max() < 1000.0
    counts = forward_null_counts(out).set_index("horizon")
    assert counts.loc[5, "null"] == 1 and counts.loc[63, "null"] == 2
    assert counts.loc[252, "null"] == 2 and (counts["filled"] == 2).all()


def test_the_oracle_refuses_the_holdout():
    sessions = sessions_between("2023-09-01", "2024-03-29")
    cands = candidates(dates=("2023-12-01",))
    with pytest.raises(HoldoutLockedError):
        run(sessions=sessions, cands=cands, era_last="2024-03-29")
    with pytest.raises(OracleBoundError):
        run(sessions=sessions, cands=cands, era_last="2024-03-29", oracle_last="2023-12-29")


def test_forward_returns_from_the_entry_fill():
    edits = {FILL: (100.0, 100.5, 99.5, 100.0), s(5): (100.0, 100.5, 99.5, 110.0),
             s(21): (100.0, 100.5, 99.5, 120.0)}
    r = one(edits=edits)
    assert r["fwd_5"] == pytest.approx(0.10) and r["fwd_21"] == pytest.approx(0.20)
    assert pd.isna(r["fwd_63"])  # 63 sessions past the fill is past the scenario's end


# --- Bucket (spec/04) -------------------------------------------------------------------

@pytest.mark.parametrize("signal,bucket", [
    ("2021-03-08", "news"),    # filing 03-12 is D+4
    ("2021-03-05", "noise"),   # filing 03-12 is D+5
    ("2021-03-16", "news"),    # filing 03-12 is D-2
    ("2021-03-17", "noise"),   # filing 03-12 is D-3
])
def test_bucket_window(signal, bucket):
    conn = fx.build_store()
    oracle = OracleReader(conn, fx.SNAPSHOT, fx.END, HOLDOUT)
    r = label(oracle, candidates(fx.DIV_SYM, (signal,), target=1e9), "smallcap", fx.END,
              CostModel("smallcap")).iloc[0]
    assert r["bucket"] == bucket
    assert r["eventcodes"] == ("13|81" if bucket == "news" else None)


def test_unfilled_candidates_are_still_bucketed():
    ev = [dict(market="us_equity", symbol=SYM, filing_date=D, eventcodes="22",
               available_at=SESSIONS[D_IDX + 1])]
    r = one(drop=[FILL], events=ev)
    assert r["status"] == "unfilled" and r["bucket"] == "news" and r["eventcodes"] == "22"


# --- Costs ------------------------------------------------------------------------------

def test_both_legs_charged_and_net_is_the_decision_quantity():
    out, cm = run(edits={s(11): (102.0, 102.5, 101.5, 102.0)})
    r = out.iloc[0]
    assert [c[1] for c in cm.calls] == ["entry", "exit_time"]
    assert cm.calls[0][2] == pytest.approx(r["entry_notional"])
    assert cm.calls[1][2] == pytest.approx(r["exit_notional"])
    assert r["entry_spread"] == pytest.approx(2 * 0.0025) and r["exit_spread"] == 0.0025
    assert r["entry_slippage"] == STUB_SLIPPAGE and r["entry_fee"] == 0.0
    assert bool(r["entry_floor_bound"]) is True
    c_in = r["entry_spread"] + r["entry_slippage"] + r["entry_fee"]
    c_out = r["exit_spread"] + r["exit_slippage"] + r["exit_fee"]
    assert r["net"] == pytest.approx(r["gross"] - c_in - c_out * r["exit_notional"] / r["entry_notional"])
    assert r["net"] < r["gross"]


# --- Crypto --------------------------------------------------------------------------

def test_crypto_fills_at_the_0100_utc_hourly_open():
    conn = fx.build_store()
    oracle = OracleReader(conn, fx.SNAPSHOT, fx.END, "2025-01-01")
    cands = candidates("BTCUSDT", ("2021-03-06", "2021-03-10"), target=1e9, lane="crypto")
    out = label(oracle, cands, "crypto", fx.END, CostModel("crypto"), lot_size=1e-4)
    a, b = out.iloc[0], out.iloc[1]
    k = pd.read_sql_query("SELECT open FROM bars_hourly WHERE symbol='BTCUSDT' "
                          "AND ts='2021-03-07T01:00:00.000Z'", conn)["open"].iloc[0]
    assert a["entry_date"] == "2021-03-07" and a["entry_price"] == pytest.approx(k)
    assert a["shares"] == pytest.approx(math.floor(10_000 / k / 1e-4) * 1e-4)
    assert a["bucket"] == "noise"
    # No 1h kline on 03-11 in the fixture: unfilled, not carried.
    assert b["status"] == "unfilled" and b["unfilled_reason"] == UNFILLED_NO_BAR

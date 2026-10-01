"""Hand-checked behaviour of the screening engine on tiny arrays."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from experiments.screen import data, engine, movers, v1rule
from experiments.screen.engine import EventSpec
from tests.screen._synth import crypto_klines, equity_bars


def _tiny(lane="equity", n_sess=40, n_tk=3):
    cal = pd.Index(pd.bdate_range("2020-01-01", periods=n_sess)) if lane == "equity" else pd.Index(pd.date_range("2020-01-01", periods=n_sess))
    O = np.ones((n_sess, n_tk)) * 100.0
    O[:, 0] = 100 * 1.01 ** np.arange(n_sess)          # +1% per session
    O[:, 1] = 100 * 0.99 ** np.arange(n_sess)          # -1% per session
    C = O * 1.001
    A = {"cal": cal, "tickers": pd.Index(["UP", "DN", "FLAT"]), "lane": lane, "a_open": O, "a_close": C, "a_high": C * 1.01,
         "a_low": O * 0.99, "close": C, "in_universe": np.ones((n_sess, n_tk), dtype=bool),
         "med_dv_20_prev": np.full((n_sess, n_tk), 5e6), "rvol_20": np.full((n_sess, n_tk), 0.5),
         "ar_spread_prev": np.full((n_sess, n_tk), 0.01), "shock": np.zeros((n_sess, n_tk)), "top20": np.zeros((n_sess, n_tk), dtype=bool)}
    return A


def test_schedule_cost_buckets():
    c = engine.schedule_cost("equity", np.array([2e7, 5e6, 7e5]))
    assert c["low"].tolist() == [0.001, 0.002, 0.004]
    assert c["base"].tolist() == [0.002, 0.004, 0.008]
    assert c["high"].tolist() == [0.004, 0.008, 0.016]
    cc = engine.schedule_cost("crypto", np.array([1.0, 2.0]))
    assert cc["base"].tolist() == [0.006, 0.006] and cc["alt80"].tolist() == [0.008, 0.008] and cc["high"].tolist() == [0.01, 0.01]


def test_event_trades_forward_returns_and_comparator():
    A = _tiny()
    raw = np.zeros(A["a_close"].shape, dtype=bool)
    raw[10, 0] = True   # candidate on session 10 in UP
    spec = EventSpec("t", "long", 5)
    tr = engine.event_trades(A, raw, spec, None, ("2020-01-01", "2020-12-31"))
    assert len(tr) == 1
    r = tr.iloc[0]
    assert r["traded"]
    # fill at open of session 11, exit at open of session 16: five +1% steps
    assert math.isclose(r["fwd_5"], 1.01 ** 5 - 1, rel_tol=1e-12)
    assert math.isclose(r["fwd_1"], 0.01, rel_tol=1e-12)
    # universe mean over UP, DN, FLAT of the same open-to-open return
    exp = np.mean([1.01 ** 5 - 1, 0.99 ** 5 - 1, 0.0])
    assert math.isclose(r["uni_fwd_5"], exp, rel_tol=1e-12)
    assert math.isclose(r["excess_5"], (1.01 ** 5 - 1) - exp, rel_tol=1e-12)
    assert r["bucket"] == "1-10M" and r["cost_base"] == 0.004
    # short direction flips the sign
    trs = engine.event_trades(A, raw, EventSpec("t", "short", 5), None, ("2020-01-01", "2020-12-31"))
    assert math.isclose(trs.iloc[0]["excess_5"], -r["excess_5"], rel_tol=1e-12)


def test_event_trades_held_rule_and_era_boundary():
    A = _tiny()
    raw = np.zeros(A["a_close"].shape, dtype=bool)
    raw[[10, 12, 16, 36], 0] = True
    spec = EventSpec("t", "long", 5)
    tr = engine.event_trades(A, raw, spec, None, ("2020-01-01", str(A["cal"][-1].date())))
    # 10 trades (exit session 16); 12 is held (12 < 16); 16 is tradeable (16 < 16 is false); 36 has no 5-session label
    assert tr["traded"].tolist() == [True, False, True, False]
    assert tr["held"].tolist() == [False, True, False, False]
    assert np.isnan(tr.iloc[3]["fwd_5"])
    # era ending earlier nulls the label of the last candidate inside the era
    tr2 = engine.event_trades(A, raw, spec, None, ("2020-01-01", str(A["cal"][18].date())))
    assert len(tr2) == 3 and not tr2.iloc[2]["traded"] and np.isnan(tr2.iloc[2]["fwd_5"]) and not np.isnan(tr2.iloc[2]["fwd_1"])


def test_event_summary_and_controls_shift_z():
    A = _tiny(n_sess=120)
    rng = np.random.default_rng(0)
    raw = rng.random(A["a_close"].shape) < 0.2
    spec = EventSpec("t", "long", 5)
    era = ("2020-01-01", "2020-12-31")
    tr = engine.event_trades(A, raw, spec, None, era)
    s0 = engine.event_summary(tr, 5, "0")
    sb = engine.event_summary(tr, 5, "base")
    assert sb["trades"] == s0["trades"] and sb["mean_net"] == pytest.approx(s0["mean_net"] - 0.004)
    ctl = engine.event_controls(A, raw, spec, None, era, tr)
    assert ctl["planted_shift"] == pytest.approx(0.005 / s0["se"], rel=1e-9)
    assert ctl["placebo_trades"] > 0


def test_zstats_and_top10():
    s = pd.Series([1.0, 2.0, 3.0, 4.0])
    z = engine.zstats(s)
    assert z["days"] == 4 and z["daymean"] == 2.5 and z["se"] == pytest.approx(s.std(ddof=1) / 2)
    t = engine.top10_stats(s, s)
    assert t["top10_share"] == 1.0 and np.isnan(t["z_wo_top10"])


def test_ts_mom_weekly_diff_is_minus_return_in_flat_weeks():
    d1, h1 = crypto_klines(n_symbols=3, n_days=200)
    A = data.build_arrays(data.crypto_features(d1, "2019-01-01", "2019-12-31"), "crypto", h1)
    pos = np.zeros(A["a_close"].shape, dtype=bool)
    pos[::2, :] = True
    wk = engine.ts_mom_weekly(A, pos, "C00USDT", ("2019-04-01", "2019-07-15"))
    assert wk["date"].dt.dayofweek.eq(6).all()
    v = wk[wk["valid"]]
    flat = v[v["pos"] == 0]
    assert np.allclose(flat["diff_0"], -flat["bh"])
    assert np.allclose(v[v["pos"] == 1]["diff_0"], 0.0)
    # base cost: half the 60 bps round trip per switch
    assert np.allclose(v["diff_base"], v["diff_0"] - 0.003 * v["switch"])
    # the week's return is Monday 01:00 open to the next Monday 01:00 open
    D = v["date"].iloc[0]
    j = A["tickers"].get_loc("C00USDT")
    i0, i1 = A["cal"].get_loc(D + pd.Timedelta(days=1)), A["cal"].get_loc(D + pd.Timedelta(days=8))
    assert v["bh"].iloc[0] == pytest.approx(A["o1"][i1, j] / A["o1"][i0, j] - 1)
    r = engine.rank_summary(wk, "base")
    assert r["weeks"] == len(v) and r["time_in_market"] == pytest.approx(v["pos"].mean())


def test_xs_mom_weekly_top_decile_and_tranches():
    d1, h1 = crypto_klines(n_symbols=10, n_days=200)
    A = data.build_arrays(data.crypto_features(d1, "2019-01-01", "2019-12-31"), "crypto", h1)
    A["in_universe"][:] = True
    sc = np.tile(np.arange(10, dtype=float), (A["a_close"].shape[0], 1))  # C09 always ranks first
    wk = engine.xs_mom_weekly(A, sc, ("2019-04-01", "2019-07-15"), 3)
    v = wk[wk["valid"]]
    assert (v["k"] == 1).all() and v["tranches"].iloc[0] == 1 and v["tranches"].iloc[2] == 3
    j = A["tickers"].get_loc("C09USDT")
    D = v["date"].iloc[0]
    i0, i1 = A["cal"].get_loc(D + pd.Timedelta(days=1)), A["cal"].get_loc(D + pd.Timedelta(days=8))
    exp = A["o1"][i1, j] / A["o1"][i0, j] - 1
    assert v["port"].iloc[0] == pytest.approx(exp)
    uni = np.nanmean(A["o1"][i1] / A["o1"][i0] - 1)
    assert v["uni"].iloc[0] == pytest.approx(uni)
    # cost: one round trip per new tranche, averaged over live tranches
    assert v["diff_base"].iloc[0] == pytest.approx(v["diff_0"].iloc[0] - 0.006)
    assert v["diff_base"].iloc[2] == pytest.approx(v["diff_0"].iloc[2] - 0.006 / 3)


def test_v1_rule_runs_through_the_new_arrays():
    bars = equity_bars(n_tickers=8, n_sessions=400, seed=3)
    A = data.build_arrays(data.equity_features(bars, "2019-01-01", "2021-12-31"), "equity")
    res, trades = v1rule.run_v1(A, "equity", "uncapped", None)
    assert set(trades) == {"close", "next_open", "next_close"}
    assert {"candidates", "filled", "fwd5_excess", "z_fwd5"} <= set(res.columns)


def test_movers_counts_and_lifts():
    A = _tiny(n_sess=300)
    A["a_close"][:, 0] = 100 * 1.03 ** np.arange(300)   # 5x in ~55 sessions, 10x in ~78
    for k in ("rvol_20", "med_dv_20_prev"):
        A[k] = np.full(A["a_close"].shape, 1.0)
    for k in ("close_to_high_250", "ret_20", "ret_60", "vol_pctl_250", "zscore_20"):
        A[k] = np.random.default_rng(0).random(A["a_close"].shape)
    A["cap"] = np.array([1e9, 2e9, 3e9])
    era = ("2020-01-01", str(A["cal"][-1].date()))
    c = movers.counts(A, None, era, "u")
    r = c[(c["kind"] == "up") & (c["horizon"] == 63)]
    assert r["names"].sum() >= 1 and (c["names"] <= c["names_eligible"]).all()
    l = movers.lifts(A, None, era, "u")
    up = l[l["group"] == "up5x63"]
    assert set(up["feature"]) >= {"close", "rvol_20", "cap"} and (up["events"] >= 1).all()
    assert set(l["group"]) == {"up5x63", "down80_63"}


def test_autopsy_selection_and_rule_matrix():
    from experiments.screen import autopsy
    lifts = pd.DataFrame([
        {"universe": "u", "group": "up5x63", "feature": "ret_60", "events": 50, "lift_top": 2.1, "lift_bottom": 0.4},
        {"universe": "u", "group": "up5x63", "feature": "close", "events": 50, "lift_top": 0.3, "lift_bottom": 1.9},
        {"universe": "u", "group": "up5x63", "feature": "cap", "events": 50, "lift_top": 0.1, "lift_bottom": 3.0},
        {"universe": "u", "group": "up5x63", "feature": "rvol_20", "events": 50, "lift_top": 1.4, "lift_bottom": 0.9},
        {"universe": "u", "group": "up5x63", "feature": "zscore_20", "events": 50, "lift_top": 1.6, "lift_bottom": 0.9},
        {"universe": "u", "group": "up5x63", "feature": "ret_20", "events": 60, "lift_top": 1.6, "lift_bottom": 0.9},
    ])
    sel = autopsy.select_features(lifts, "u", "up5x63")
    assert [(f["feature"], f["side"]) for f in sel] == [("ret_60", "top"), ("close", "bottom"), ("ret_20", "top")]
    assert autopsy.select_features(lifts, "u", "down80_63") == []
    A = _tiny(n_sess=10, n_tk=3)
    A["ret_60"] = np.tile(np.array([3.0, 1.0, 2.0]), (10, 1))
    M = autopsy.rule_matrix(A, "ret_60", "top", None)
    assert M[:, 0].all() and not M[:, 1].any() and not M[:, 2].any()   # rank 1.0 >= 0.8; 0.667 and 0.333 are not
    assert not autopsy.rule_matrix(A, "ret_60", "bottom", None).any()   # ranks 1/3, 2/3, 1 are all above 0.2
    B = {"in_universe": np.ones((4, 10), dtype=bool), "f": np.tile(np.arange(10, dtype=float), (4, 1))}
    Mb = autopsy.rule_matrix(B, "f", "bottom", None)
    assert Mb[:, :2].all() and not Mb[:, 2:].any()                        # ranks 0.1 and 0.2 qualify
    B["in_universe"][:, 0] = False                                         # ranks are among the universe only
    assert autopsy.rule_matrix(B, "f", "bottom", None)[:, 1].all()


def test_event_trades_intraday_horizons_for_crypto():
    A = _tiny(lane="crypto", n_sess=30)
    A["o1"] = A["a_open"].copy(); A["o4"] = A["a_open"] * 1.02; A["o12"] = A["a_open"] * 0.99
    raw = np.zeros(A["a_close"].shape, dtype=bool); raw[5, 2] = True
    tr = engine.event_trades(A, raw, EventSpec("t", "long", 5), None, ("2020-01-01", "2020-12-31"))
    assert tr.iloc[0]["fwd_i04"] == pytest.approx(0.02) and tr.iloc[0]["fwd_i12"] == pytest.approx(-0.01)
    assert tr.iloc[0]["excess_i04"] == pytest.approx(0.0)
    assert "126" in set(engine.event_report({"next_open": tr}, EventSpec("t", "long", 5), "crypto", "dev", "crypto")["horizon"])


def test_crypto_symbol_segmented_at_kline_gaps():
    d1, h1 = crypto_klines(n_symbols=3, n_days=120)
    sym = "C00USDT"
    m = (d1["symbol"] == sym) & (d1["open_time"] >= "2019-02-10") & (d1["open_time"] <= "2019-02-20")
    d1 = d1[~m].copy()
    d1.loc[(d1["symbol"] == sym) & (d1["open_time"] > "2019-02-20"), ["open", "high", "low", "close"]] *= 1000.0  # a redenomination
    px = data.crypto_features(d1, "2019-01-01", "2019-12-31")
    assert set(px.loc[px["symbol"] == sym, "ticker"]) == {sym, sym + "~2"}
    seg2 = px[px["ticker"] == sym + "~2"]
    assert seg2["date"].min() == pd.Timestamp("2019-02-21") and seg2["ret_1"].iloc[0] != seg2["ret_1"].iloc[0]  # NaN: no return across the gap
    assert not seg2["full_hist"].iloc[:29].any()                     # the new instrument re-earns its 30-day history
    A = data.build_arrays(px, "crypto", h1)
    j1, j2 = A["tickers"].get_loc(sym), A["tickers"].get_loc(sym + "~2")
    i = A["cal"].get_loc(pd.Timestamp("2019-03-01"))
    assert np.isnan(A["o1"][i, j1]) and not np.isnan(A["o1"][i, j2])  # the hourly open follows the instrument
    px0 = data.crypto_features(d1, "2019-01-01", "2019-12-31", segment_gaps=False)
    assert set(px0.loc[px0["symbol"] == sym, "ticker"]) == {sym}

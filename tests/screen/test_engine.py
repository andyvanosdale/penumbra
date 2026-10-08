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


# ================================================================ rank mode, equities (wave 2)
def _rank_arrays(n_tickers=120, n_sessions=600, seed=5):
    bars = equity_bars(n_tickers=n_tickers, n_sessions=n_sessions, seed=seed)
    A = data.build_arrays(data.equity_features(bars, "2019-01-01", "2021-12-31"), "equity")
    A["panel"] = data.equity_features(bars, "2019-01-01", "2021-12-31")
    return A


def test_rebalance_dates_on_a_holiday_calendar():
    cal = pd.Index(pd.bdate_range("2020-01-01", "2020-12-31"))
    cal = cal.drop([pd.Timestamp("2020-01-31"), pd.Timestamp("2020-07-03"), pd.Timestamp("2020-12-25"), pd.Timestamp("2020-11-27")])
    mi = engine.monthly_dates(cal)
    assert len(mi) == 12
    assert cal[mi[0]] == pd.Timestamp("2020-01-30")     # the holiday month-end falls back one session
    assert cal[mi[11]] == pd.Timestamp("2020-12-31")
    wi = engine.weekly_session_dates(cal)
    d = cal[wi]
    assert pd.Timestamp("2020-07-02") in d and pd.Timestamp("2020-07-03") not in d   # Good-Friday-style week ends Thursday
    assert pd.Timestamp("2020-11-26") in d and pd.Timestamp("2020-11-27") not in d   # a dropped Friday: Thursday is the week's last session
    assert len(wi) == 53 and (pd.DatetimeIndex(d).isocalendar()["week"].diff().dropna().abs() >= 1).all()
    f = engine.rank_fills(cal, 12, ("2020-03-01", "2020-09-30"))
    assert f["date"].iloc[0] == pd.Timestamp("2020-03-31") and f["valid"].sum() == 5   # the August and September rebalances exit after the era: null
    assert (f["fill_idx"] == cal.get_indexer(f["date"]) + 1).all()
    assert str(f["exit_date"].iloc[0].date()) == "2020-05-01"                           # the session after the April month-end


def test_rank_zstats_mde80_and_newey_west():
    rng = np.random.default_rng(0)
    d = rng.normal(0.0, 0.05, 131)
    z = engine.rank_zstats(d, 12)
    se = d.std(ddof=1) / math.sqrt(131)
    assert z["se"] == pytest.approx(se) and z["mde80_pp"] == pytest.approx(12 * 2.8416 * se * 100)
    assert z["z_gate"] == pytest.approx(min(z["z_plain"], z["z_nw"]))
    # a white-noise series gives z_nw close to z_plain; a constant shift leaves the NW SE unchanged
    assert abs(z["z_plain"] - z["z_nw"]) < 0.5
    assert engine.nw_se(d + 0.01, 3) == pytest.approx(engine.nw_se(d, 3))
    w = rng.normal(0.0, 0.025, 573)
    assert engine.rank_zstats(w, 52)["mde80_pp"] == pytest.approx(52 * 2.8416 * (w.std(ddof=1) / math.sqrt(573)) * 100)


def test_planted_shift_equals_x_over_se():
    rng = np.random.default_rng(1)
    for ppy, X in ((12, 42), (52, 10)):
        d = rng.normal(0.001, 0.05 if ppy == 12 else 0.025, 131 if ppy == 12 else 573)
        a = engine.rank_zstats(d, ppy); b = engine.rank_zstats(d + X / 1e4, ppy)
        assert b["z_plain"] - a["z_plain"] == pytest.approx(X / 1e4 / a["se"], abs=1e-9)
        assert abs(X / 1e4 / (engine.SIGMA_LOCKED[ppy] / math.sqrt(len(d))) - 0.96) < 0.02   # the bar-sized shift at the locked sigma


def test_rank_basket_ties_and_min_k():
    ranked = np.ones(40, dtype=bool)
    score = np.arange(40, dtype=float); score[30:] = 39.0   # ten names tie at the top
    b, k, n = engine.rank_basket(score, ranked, "top", 5)   # ceil(40/5) = 8 < 10: skipped
    assert k == 0 and not b.any() and n == 40
    ranked = np.ones(120, dtype=bool); score = np.arange(120, dtype=float); score[105:] = 119.0
    b, k, n = engine.rank_basket(score, ranked, "top", 10)   # ceil(120/10) = 12; the 15 tied names are all included
    assert k == 15 and b[105:].all() and not b[:105].any()
    b, k, _ = engine.rank_basket(score, ranked, "bottom", 10)
    assert k == 12 and b[:12].all()
    score[3] = np.nan
    b, k, n = engine.rank_basket(score, ranked, "bottom", 10)
    assert n == 119 and not b[3]


def test_random_draw_count_and_leaving_name_rule():
    P, N = 6, 60
    ranked = np.ones((P, N), dtype=bool)
    ranked[3, :20] = False                    # names 0..19 leave the ranked set on date 3
    k = np.array([12, 12, 12, 12, 15, 10]); tau = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    sets = {"ranked": ranked}
    B = engine.random_baskets(sets, k, tau, 1, engine.RANDOM_SEED)
    assert (B.sum(axis=1) == k).all()
    assert not (B & ~ranked).any()
    assert np.array_equal(B[1], B[2])                           # tau 0: every held name kept
    assert (B[3] & B[2] & ranked[3]).sum() == (B[2] & ranked[3]).sum()   # the leavers are replaced, the rest kept
    assert (B[4] & B[3]).sum() == 12 and B[4].sum() == 15             # k rises: 3 new slots
    assert (B[5] & B[4]).sum() == 10                                   # k falls: dropped uniformly to 10
    B2 = engine.random_baskets(sets, k, tau, 1, engine.RANDOM_SEED)
    assert np.array_equal(B, B2)                                       # one default_rng(seed) per draw: deterministic
    assert not np.array_equal(B, engine.random_baskets(sets, k, tau, 1, engine.RANDOM_SEED + 1))
    # hold 3: the kept names come from the tranche formed three dates earlier
    B3 = engine.random_baskets(sets, np.full(P, 12), np.zeros(P), 3, 7)
    assert (B3[3] & B3[0] & ranked[3]).sum() == (B3[0] & ranked[3]).sum()


def test_rank_equity_end_to_end_and_scale_by_10():
    A = _rank_arrays()
    era = ("2020-03-01", "2021-12-31")
    spec = engine.RankSpec("2a-v1", 12, "top", 10)
    score = np.array(A["ret_12_1"], dtype=float)
    res = engine.rank_equity(A, None, spec, score, era, "dev")
    wk = res["periods"]
    v = wk[wk["valid"]]
    assert len(v) >= 12 and (v["k"] >= 10).all() and (v["n"] >= v["k"]).all()
    # hand check of one period: basket mean of open-to-open returns minus the ranked-set mean
    i = v.index[2]
    F, E = res["fills"].loc[i, "fill_idx"], res["fills"].loc[i, "exit_idx"]
    b, c = res["sets"]["basket"][i], res["sets"]["comp"][i]
    r = A["a_open"][E] / A["a_open"][F] - 1
    assert v.loc[i, "port"] == pytest.approx(np.nanmean(r[b])) and v.loc[i, "uni"] == pytest.approx(np.nanmean(r[c]))
    assert v.loc[i, "diff_0"] == pytest.approx(v.loc[i, "port"] - v.loc[i, "uni"])
    # first period: the whole basket enters; cost = mean round trip of the basket
    i0 = v.index[0]
    assert v.loc[i0, "entering"] == v.loc[i0, "k"] and v.loc[i0, "tau"] == 1.0
    assert v.loc[i0, "cost_base"] == pytest.approx(np.mean(res["rt"]["base"][i0][res["sets"]["basket"][i0]]))
    assert np.allclose(v["diff_base"], v["diff_0"] - v["cost_base"], atol=1e-15)
    # scale by 10 leaves everything unchanged
    B = dict(A)
    for key in ("a_open", "a_high", "a_low", "a_close", "close"):
        B[key] = A[key] * 10.0
    res10 = engine.rank_equity(B, None, spec, score, era, "dev")
    for col in ("port", "uni", "match", "diff_0", "diff_base", "diff_high"):
        a1, a2 = res["periods"][col].to_numpy(), res10["periods"][col].to_numpy()
        assert np.array_equal(np.isnan(a1), np.isnan(a2)) and np.allclose(np.nan_to_num(a1), np.nan_to_num(a2), rtol=0, atol=1e-12)
    assert np.array_equal(res["sets"]["basket"], res10["sets"]["basket"])
    # 2b's score is scale-free; the USD 2 floor is not (checked separately through in_universe)
    s2 = B["close"] / data._rolling_max(B["close"], 250)
    m = ~np.isnan(A["close_to_max_close_250"])
    assert np.allclose(s2[m], A["close_to_max_close_250"][m], atol=1e-12)
    # controls run and the planted shift matches X / SE
    ctl, rnd = engine.rank_controls_equity(res, spec, A, None, score, era, "dev", draws=5)
    zs = engine.rank_zstats(v["diff_0"].to_numpy(), 12)
    assert ctl["planted_bar_shift"] == pytest.approx(0.0042 / zs["se"], abs=0.01) and ctl["planted_50_shift"] == pytest.approx(0.005 / zs["se"], abs=0.01)
    assert len(rnd) == 5 and (rnd["periods"] == len(v)).all() and 1 <= ctl["random_rank"] <= 6
    assert np.isfinite(ctl["mirror_z"]) and np.isfinite(ctl["price_matched_excess"]) and ctl["lag20_periods"] > 0
    rep = engine.rank_report_equity(res, ctl, spec, "uncapped", "dev")
    assert set(rep["period"]) >= {"all", "half2", "ex_top5pct", "ex_jan", "ex_2020"} and len(rep[rep["cost"] == "base"]) == len(rep) / 4
    assert {"z_gate", "mde80_pp", "random_rank", "lag250_z0", "verdict"} <= set(rep.columns)


def test_rank_equity_tranches_and_weekly_bottom():
    A = _rank_arrays()
    era = ("2020-03-01", "2021-12-31")
    spec3 = engine.RankSpec("2a-v3", 12, "top", 10, hold=3)
    score = np.array(A["ret_12_1"], dtype=float)
    res = engine.rank_equity(A, None, spec3, score, era, "dev")
    wk = res["periods"]
    v = wk[wk["valid"]]
    assert v["live"].iloc[0] == 1 and v["live"].iloc[2] == 3
    # the first three tranches enter whole; the fourth is measured against the first
    assert (v["tau"].iloc[:3] == 1.0).all() and v["tau"].iloc[3] <= 1.0
    assert v["cost_base"].iloc[2] == pytest.approx(np.mean(res["rt"]["base"][v.index[2]][res["sets"]["basket"][v.index[2]]]) / 3)
    specw = engine.RankSpec("2d-v1", 52, "bottom", 10, liq_floor=1e5)
    sw = np.array(A["ret_5"], dtype=float)
    rw = engine.rank_equity(A, None, specw, sw, era, "dev")
    vw = rw["periods"][rw["periods"]["valid"]]
    assert len(vw) > 50
    i = vw.index[5]
    b = rw["sets"]["basket"][i]; r = rw["sets"]["ranked"][i]
    assert np.nanmax(sw[rw["sets"]["D"][i]][b]) <= np.nanmin(sw[rw["sets"]["D"][i]][r & ~b])   # the lowest scores are held
    assert (A["med_dv_20_prev"][rw["sets"]["D"][i]][r] >= 1e5).all()
    ctl, _ = engine.rank_controls_equity(rw, specw, A, None, sw, era, "dev", draws=2)
    assert "bounce_gap_bps" in ctl


def test_verdict_rank_on_synthetic_rows():
    base = {"periods": 131, "z_gate": 2.4, "ann_excess": 0.08, "ann_excess_high": 0.02, "mde80_pp": 14.9, "random_rank": 199, "mirror_z": -0.5,
            "years_positive": 8, "half1_excess": 0.06, "half2_excess": 0.09, "z_wo_top5pct": 1.9, "z_ex_jan": 2.1, "z_ex2020": 1.8,
            "price_matched_excess": 0.05, "lag250_z0": 0.4}
    V = engine.verdict_rank
    assert V(base, "uncapped", 12) == "confirm" and V(base, "smallcap", 12) == "diagnostic-pass"
    assert V({**base, "periods": 100}, "uncapped", 12) == "insufficient"
    assert V({**base, "z_gate": 1.2}, "uncapped", 12) == "null (underpowered below 15 pp)"
    assert V({**base, "z_gate": 1.2, "mde80_pp": 9.0}, "uncapped", 12) == "null"
    assert V({**base, "ann_excess_high": -0.01}, "uncapped", 12).startswith("null")
    assert V({**base, "random_rank": 190}, "uncapped", 12) == "null"
    assert V({**base, "mirror_z": 2.5}, "uncapped", 12) == "artifact"
    assert V({**base, "z_ex2020": 1.2}, "uncapped", 12) == "artifact"
    assert V({**base, "price_matched_excess": 0.03}, "uncapped", 12) == "artifact"   # less than half the excess
    assert V({**base, "lag250_z0": 2.2}, "uncapped", 12) == "characteristic"
    dev = {"z_gate": 2.4, "periods": 131, "ann_excess": 0.08}
    assert engine.verdict_rank_confirm(dev, {"z_gate": 1.3, "periods": 35, "ann_excess": 0.05, "years_positive": 2}, 12) == "confirm (gate passed, C8 pending)"
    assert engine.verdict_rank_confirm(dev, {"z_gate": 0.8, "periods": 35, "ann_excess": 0.05, "years_positive": 2}, 12) == "fails confirm"
    assert engine.verdict_rank_confirm(dev, {"z_gate": 1.3, "periods": 20, "ann_excess": 0.05, "years_positive": 2}, 12) == "insufficient"
    assert engine.p_sidak(engine.p_one_sided(2.0)) == pytest.approx(1 - (1 - 0.02275) ** 9, abs=1e-4)


def test_ledger_migration_keeps_the_76_rows(tmp_path, monkeypatch):
    from experiments.screen import ledger
    src = ledger.LEDGER
    before = ledger.read()
    assert len(before) == 76
    tmp = tmp_path / "ledger.md"
    tmp.write_text(src.read_text())
    monkeypatch.setattr(ledger, "LEDGER", tmp)
    legacy_cells = [c.strip() for c in src.read_text().splitlines()[-1].strip().strip("|").split("|")]
    df = ledger.upsert([])                      # migrates the header once
    assert len(df) == 76 and list(df.columns) == ledger.COLUMNS
    assert (df[["family_n", "p_sidak", "random", "lag250", "mirror"]] == "n/a").all().all()
    again = ledger.read()
    assert again.equals(df)                      # re-read unchanged
    for c, val in zip(ledger.LEGACY_COLUMNS, legacy_cells):
        assert str(again.iloc[-1][c]) == val    # every legacy cell survives
    assert "| family_n | p_sidak | random | lag250 | mirror | entry |" in tmp.read_text()
    ledger.upsert([{"date": "2026-10-08", "signal": "2a", "variant": "v1", "universe": "uncapped", "verdict": "null", "family_n": "9", "entry": "x"}])
    assert len(ledger.read()) == 77

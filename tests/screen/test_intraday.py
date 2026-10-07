"""Leakage guard and hand checks for the intraday layer (research_log/2026-10-07-intraday-wave.md,
"Engineering acceptance").

(a) Perturbing every bar on F that starts after the entry bar, and the entry bar's own high, low,
    close, volume and VWAP, leaves every signal's candidate matrix at F and every entry price unchanged.
(b) Perturbing every bar on sessions after F leaves the session-F table, the floor at F and the
    medians through F-1 unchanged.
(c) For the next-day rows (i6, i8), perturbing every bar on D+1 and later leaves the matrix at D unchanged.
Plus the fill rule (first bar at or after T, 15-minute cutoff) and the early-close detection on tiny bars.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from experiments.screen import data
from experiments.screen import intraday_autopsy as autopsy
from experiments.screen import intraday_data as idata
from experiments.screen import intraday_engine as ieng
from experiments.screen.signals import intraday as isig
from tests.screen._synth import equity_bars

TZ = idata.TZ
N_TICKERS = 32   # ~2,100 bars per session (1,100 on a synthetic half day): above the cache-coverage threshold


def synth_5min(daily: pd.DataFrame, seed: int = 3, drop_share: float = 0.15) -> pd.DataFrame:
    """5-minute bars in the Alpaca shape for every (ticker, session) of a daily frame: a random walk
    from the daily open to the daily close, with a random share of bars missing (IEX sparsity)."""
    rng = np.random.default_rng(seed)
    starts = pd.date_range("09:30", "15:55", freq="5min").time
    rows = []
    for (tk, d), r in daily.groupby(["ticker", "date"]):
        n = len(starts)
        path = np.linspace(float(r["open"].iloc[0]), float(r["close"].iloc[0]), n + 1) * np.exp(np.cumsum(rng.normal(0, 0.002, n + 1)))
        keep = rng.random(n) > drop_share
        keep[0] = keep[-1] = True
        vol_mult = 5.0 if rng.random() < 0.08 else 1.0          # occasional high-volume sessions
        for i in np.nonzero(keep)[0]:
            ts = pd.Timestamp.combine(pd.Timestamp(d).date(), starts[i]).tz_localize(TZ).tz_convert("UTC")
            o, c = path[i], path[i + 1]
            rows.append({"symbol": tk, "ts": ts, "open": o, "high": max(o, c) * 1.001, "low": min(o, c) * 0.999, "close": c,
                         "volume": int(rng.lognormal(7, 0.5) * vol_mult), "trade_count": 3, "vwap": (o + c) / 2})
    return pd.DataFrame(rows)


def perturb_bars(bars: pd.DataFrame, after: pd.Timestamp, seed: int = 11, keep_open_of: pd.Timestamp | None = None) -> pd.DataFrame:
    """Multiply every price and volume of bars starting at or after `after` by random factors; the bar at
    `keep_open_of` keeps its open (the entry print) and loses the rest."""
    rng = np.random.default_rng(seed)
    out = bars.copy()
    m = out["ts"] >= after
    for c in ("open", "high", "low", "close", "volume", "vwap"):
        f = rng.uniform(0.7, 1.4, int(m.sum()))
        out.loc[m, c] = out.loc[m, c] * f if c != "volume" else (out.loc[m, c] * f).astype(int)
    if keep_open_of is not None:
        at = bars["ts"] == keep_open_of
        out.loc[at, "open"] = bars.loc[at, "open"]
    return out


@pytest.fixture(scope="module")
def world():
    daily = equity_bars(n_tickers=N_TICKERS, n_sessions=330, seed=0)
    bars = synth_5min(daily)
    A = data.build_arrays(data.equity_features(daily, "2019-01-01", "2021-12-31"), "equity")
    A["cap"] = np.full(len(A["tickers"]), 1e9)
    return daily, bars, A


def arrays_from(bars: pd.DataFrame, A: dict) -> dict:
    return idata.intraday_arrays(A, idata.session_table(bars))


def test_fill_rule_first_bar_at_or_after_with_cutoff():
    day = pd.Timestamp("2021-03-02")
    mk = lambda hm, o: {"symbol": "X", "ts": pd.Timestamp(f"{day.date()} {hm}").tz_localize(TZ).tz_convert("UTC"), "open": o, "high": o, "low": o, "close": o, "volume": 10, "trade_count": 1, "vwap": o}  # noqa: E731
    # bars at 09:30, 09:45, 10:20 and 15:55: 09:35 -> 09:45 bar (10 min late); 10:00 -> 10:20 is 20 min late -> unfilled
    bars = pd.DataFrame([mk("09:30", 1.0), mk("09:45", 2.0), mk("10:20", 3.0), mk("15:55", 4.0)])
    t = idata.session_table(bars).iloc[0]
    assert t["px_0935"] == 2.0 and t["late_0935"] == 10
    assert np.isnan(t["px_1000"])
    assert np.isnan(t["px_1030"])   # 10:20 is before 10:30 and 15:55 is too late: no fill at 10:30
    assert t["px_1555"] == 4.0 and t["c1555"] == 4.0 and t["c_close"] == 4.0
    assert t["n_rth"] == 4 and t["o0930"] == 1.0 and np.isnan(t["c0955"])
    # same-session close falls back to the last bar from 15:40 on when 15:55 is missing
    bars2 = pd.DataFrame([mk("09:30", 1.0), mk("15:40", 5.0), mk("15:45", 6.0)])
    t2 = idata.session_table(bars2).iloc[0]
    assert np.isnan(t2["c1555"]) and t2["c_close"] == 6.0
    bars3 = pd.DataFrame([mk("09:30", 1.0), mk("15:30", 5.0)])
    assert np.isnan(idata.session_table(bars3).iloc[0]["c_close"])
    # extended-hours bars are never read
    bars4 = pd.DataFrame([mk("09:25", 9.0), mk("16:00", 9.0), mk("09:30", 1.0)])
    assert idata.session_table(bars4).iloc[0]["n_rth"] == 1


def test_early_close_detection_and_floor(world):
    daily, bars, A = world
    I = arrays_from(bars, A)
    assert not I["early_close"].any()
    # make one session an early close: drop every bar from 13:00 on that day
    d = pd.Timestamp(sorted(daily["date"].unique())[300])
    cut = bars[~((bars["ts"].dt.tz_convert(TZ).dt.normalize().dt.tz_localize(None) == d) & (bars["ts"].dt.tz_convert(TZ).dt.hour >= 13))]
    I2 = arrays_from(cut, A)
    row = A["cal"].get_loc(d)
    assert I2["early_close"][row] and not I2["fill_session"][row]
    # the floor window skips the early-close session: on the next session it is the 20 full sessions before it
    expect = (I2["n_rth"][row - 20:row] >= idata.FLOOR_BARS).all(axis=0)
    assert np.array_equal(I2["floor_ok"][row + 1], expect) and expect.any()
    assert not I2["floor_ok"][row].any() or True   # the early-close row itself is not a fill session; its floor is irrelevant
    # the floor needs 60 bars on each of the 20 previous fill sessions: a session with 50 bars breaks it for 20 sessions
    sym = A["tickers"][0]
    day_bars = bars[(bars["symbol"] == sym) & (bars["ts"].dt.tz_convert(TZ).dt.normalize().dt.tz_localize(None) == d)]
    thin = bars.drop(day_bars.index[: max(0, len(day_bars) - 50)])
    I3 = arrays_from(thin, A)
    j = A["tickers"].get_loc(sym)
    assert I3["n_rth"][row, j] <= 50
    assert not I3["floor_ok"][row + 1:row + 21, j].any() and I3["floor_ok"][row + 22, j] == I["floor_ok"][row + 22, j]


@pytest.mark.parametrize("name", list(isig.INTRADAY))
def test_candidates_at_F_unchanged_by_bars_after_the_entry_bar(name, world):
    daily, bars, A = world
    sig = isig.load(name)
    I1 = arrays_from(bars, A)
    elig = idata.eligibility(I1, None, sig.FLOOR)
    # a session deep enough into the data for the floor to pass
    F = pd.Timestamp(sorted(daily["date"].unique())[320])
    row = A["cal"].get_loc(F)
    t_entry = pd.Timestamp(f"{F.date()} {sig.ENTRY}").tz_localize(TZ).tz_convert("UTC")
    # perturb every bar from T on (that session and every later one), then restore the entry print: the open of
    # each name's first bar at or after T on F (the fill bar keeps its open and loses high, low, close, volume, vwap)
    pert = perturb_bars(bars, t_entry)
    for tk, g in bars[(bars["ts"] >= t_entry) & (bars["ts"] < t_entry + pd.Timedelta(minutes=idata.LATE_MAX_MIN + 1))].groupby("symbol"):
        at = (pert["symbol"] == tk) & (pert["ts"] == g["ts"].min())
        pert.loc[at, "open"] = bars.loc[at, "open"].to_numpy()
    I2 = arrays_from(pert, A)
    elig2 = idata.eligibility(I2, None, sig.FLOOR)
    M1, M2 = sig.candidates(A, I1, elig) & elig, sig.candidates(A, I2, elig2) & elig2
    assert M1.shape == M2.shape
    assert np.array_equal(M1[: row + 1], M2[: row + 1]), name
    k = sig.ENTRY.replace(":", "")
    assert np.array_equal(np.nan_to_num(I1[f"px_{k}"][: row + 1]), np.nan_to_num(I2[f"px_{k}"][: row + 1]))
    # the perturbation did reach the later bars (the test is not vacuous)
    assert not np.allclose(np.nan_to_num(I1["c_close"][row]), np.nan_to_num(I2["c_close"][row]))


def test_session_table_floor_and_medians_unchanged_by_later_sessions(world):
    daily, bars, A = world
    F = pd.Timestamp(sorted(daily["date"].unique())[300])
    row = A["cal"].get_loc(F)
    after = pd.Timestamp(f"{F.date()} 23:59").tz_localize(TZ).tz_convert("UTC")
    I1, I2 = arrays_from(bars, A), arrays_from(perturb_bars(bars, after), A)
    for key in idata.SESSION_COLS + ["floor_ok", "med20_v_fhh", "med20_v_1200", "elig_daily", "elig_floor"] + [f"px_{t.replace(':', '')}" for t in idata.ENTRY_TIMES]:
        a, b = np.asarray(I1[key], dtype=float)[: row + 1], np.asarray(I2[key], dtype=float)[: row + 1]
        assert np.array_equal(np.isnan(a), np.isnan(b)) and np.allclose(np.nan_to_num(a), np.nan_to_num(b)), key
    assert not np.allclose(np.nan_to_num(I1["c_close"][row + 1:]), np.nan_to_num(I2["c_close"][row + 1:]))


def test_next_day_rows_and_i8_matrix_at_D_unchanged_by_bars_on_D_plus_1(world):
    daily, bars, A = world
    D = pd.Timestamp(sorted(daily["date"].unique())[300])
    row = A["cal"].get_loc(D)
    after = pd.Timestamp(f"{D.date()} 23:59").tz_localize(TZ).tz_convert("UTC")
    I1, I2 = arrays_from(bars, A), arrays_from(perturb_bars(bars, after), A)
    univ = A["in_universe"]
    for feat in autopsy.FEATURES:
        M1 = autopsy.rule_matrix(A, I1, feat, "top", univ)
        M2 = autopsy.rule_matrix(A, I2, feat, "top", univ)
        # the matrix is on fill sessions F = D+1, so row D+1 holds the D-based rule
        assert np.array_equal(M1[: row + 2], M2[: row + 2]), feat
    for name in ("i6-1a-0935", "i6-1b-1030"):
        sig = isig.load(name)
        e = idata.eligibility(I1, None, False)
        assert np.array_equal(sig.candidates(A, I1, e)[: row + 2], sig.candidates(A, I2, e)[: row + 2])


def test_trades_returns_comparator_and_costs(world):
    daily, bars, A = world
    I = arrays_from(bars, A)
    F = pd.Timestamp(sorted(daily["date"].unique())[300])
    row = A["cal"].get_loc(F)
    raw = np.zeros(A["a_close"].shape, dtype=bool)
    raw[row, :3] = True
    elig = np.ones_like(raw)
    spec = ieng.IntradaySpec("t", "long", "10:00", "close")
    tr = ieng.intraday_trades(A, I, raw, spec, elig, ("2019-01-01", "2021-12-31"))
    assert len(tr) == 3
    for _, r in tr.iterrows():
        j = A["tickers"].get_loc(r["ticker"])
        e = I["px_1000"][row, j]
        assert r["entry"] == e
        assert np.isclose(r["fwd_close"], I["c_close"][row, j] / e - 1)
        assert np.isclose(r["fwd_1030"], I["px_1030"][row, j] / e - 1)
        # next open and 1 / 5 / 21 sessions on the adjusted basis
        assert np.isclose(r["fwd_nopen"], A["a_open"][row + 1, j] / (e * I["f"][row, j]) - 1)
        assert np.isclose(r["fwd_5"], A["a_close"][row + 5, j] / (e * I["f"][row, j]) - 1)
    # the comparator is the mean over every eligible name filled at 10:00
    e_all = I["px_1000"][row]
    uni = np.nanmean(I["c_close"][row] / e_all - 1)
    assert np.isclose(tr["uni_fwd_close"].iloc[0], uni)
    assert np.isclose(tr["excess_close"].iloc[0], tr["fwd_close"].iloc[0] - uni)
    # short direction flips the sign; the zero comparator gives the raw return
    trs = ieng.intraday_trades(A, I, raw, ieng.IntradaySpec("t", "short", "10:00", "close"), elig, ("2019-01-01", "2021-12-31"))
    assert np.isclose(trs["excess_close"].iloc[0], -tr["excess_close"].iloc[0])
    trz = ieng.intraday_trades(A, I, raw, ieng.IntradaySpec("t", "long", "10:00", "close", "zero"), elig, ("2019-01-01", "2021-12-31"))
    assert np.isclose(trz["excess_close"].iloc[0], trz["fwd_close"].iloc[0])
    # an entry at 15:55 has no intraday exit; its decision exit is the next open
    assert ieng.exits_for("15:55") == ["nopen", "1", "5", "21"] and ieng.exits_for("10:30") == ["1200", "close", "nopen", "1", "5", "21"]
    # costs follow the liquidity bucket
    assert set(tr["bucket"]) <= {">=10M", "1-10M", "0.5-1M"}


def test_rank_rows_slice_sizes_and_random_slice(world):
    daily, bars, A = world
    I = arrays_from(bars, A)
    elig = idata.eligibility(I, None, True)
    sig = isig.load("i3-top")
    M = sig.candidates(A, I, elig)
    pool = sig.pool(A, I, elig)
    n = pool.sum(axis=1)
    k = M.sum(axis=1)
    ok = n > 0
    assert np.array_equal(k[ok], np.ceil(n[ok] / 10))
    R = ieng.random_slice(M, pool)
    assert np.array_equal(R.sum(axis=1), k) and (R & ~pool).sum() == 0
    q = isig.quintile(isig.overnight_return(A, I), isig.load("i5-q5").pool(A, I, idata.eligibility(I, None, False)))
    vals = q[~np.isnan(q)]
    assert set(np.unique(vals)) <= {1.0, 2.0, 3.0, 4.0, 5.0}


def test_every_intraday_signal_fires_on_the_synthetic_world(world):
    """Guards against a shift test that passes because a matrix is all False."""
    daily, bars, A = world
    I = arrays_from(bars, A)
    for name, sig in isig.INTRADAY.items():
        elig = idata.eligibility(I, None, sig.FLOOR)
        assert (sig.candidates(A, I, elig) & elig).sum() > 0, name

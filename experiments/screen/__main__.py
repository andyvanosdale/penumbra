"""CLI of the screening engine.

    python -m experiments.screen pull [--equity] [--caps] [--crypto] [--no-1h]
    python -m experiments.screen regress --v1-results <csv>   # v1 rule through the new engine vs the original script
    python -m experiments.screen run --signal 1a[,1b-5d,...|all] --universe smallcap[,uncapped,crypto|all] --era dev|confirm --out DIR
    python -m experiments.screen movers --universe all --era dev --out DIR
    python -m experiments.screen tables --out DIR

Set PENUMBRA_DATA_ROOT (docs/environment.md). Results go to --out (default
$PENUMBRA_DATA_ROOT/screen/processed/wave1); trade-level files stay under the raw root.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from experiments.screen import autopsy, data, engine, movers, signals, v1rule

log = logging.getLogger("screen")
EQ_UNIVERSES = ["smallcap", "uncapped"]
ALL_UNIVERSES = EQ_UNIVERSES + ["crypto"]
EVENT_SIGNALS = ["1a", "1b-5d", "1b-21d", "1c-short", "1c-long"]
RANK_SIGNALS = ["1d", "1e"]
RANK_EQ_SIGNALS = ["2a", "2b", "2d"]
WAVE2_VARIANTS = ["v1", "v2", "v3"]


def _out(args) -> Path:
    wave2 = getattr(args, "signal", None) and all(n in RANK_EQ_SIGNALS for n in str(args.signal).split(",")) or getattr(args, "proof", None)
    p = Path(args.out) if args.out else data.roots().processed / ("wave2" if wave2 else "wave1")
    p.mkdir(parents=True, exist_ok=True)
    return p


# ---------------------------------------------------------------- pull
def cmd_pull(args) -> None:
    if args.equity:
        data.stage_universe()
        data.stage_prices(data.EQ_PULL_START, data.EQ_PULL_END, workers=args.workers)
    if args.caps:
        data.stage_caps()
    if args.crypto:
        data.stage_crypto(data.CR_PULL_START, data.CR_PULL_END, workers=max(args.workers, 8), need_1h=not args.no_1h)
    if args.intraday:
        data.stage_crypto_intraday()
    if args.splits:
        data.stage_splits(budget_s=args.budget_hours * 3600 if args.budget_hours else None)


# ---------------------------------------------------------------- arrays per lane (built once)
class Lanes:
    def __init__(self, eq_window=None, cr_window=None, segment_gaps: bool = True):
        self._eq = None; self._cr = None; self.segment_gaps = segment_gaps
        self.eq_window = eq_window or (data.EQ_PULL_START, data.EQ_PULL_END)
        self.cr_window = cr_window or (data.CR_PULL_START, data.CR_PULL_END)

    def equity(self):
        if self._eq is None:
            t0 = time.time()
            self._eq = data.equity_arrays(*self.eq_window)
            log.info("equity arrays %s..%s: %d sessions x %d tickers, %.0fs", *self.eq_window, len(self._eq[0]["cal"]), len(self._eq[0]["tickers"]), time.time() - t0)
        return self._eq

    def crypto(self):
        if self._cr is None:
            t0 = time.time()
            self._cr = data.crypto_arrays(*self.cr_window, segment_gaps=self.segment_gaps)
            log.info("crypto arrays %s..%s: %d days x %d pairs, %.0fs (calendar gaps %d)", *self.cr_window, len(self._cr["cal"]), len(self._cr["tickers"]), time.time() - t0, data.calendar_gaps(self._cr))
        return self._cr

    def arrays(self, universe: str):
        if universe == "crypto":
            return self.crypto(), None, "crypto"
        A, masks = self.equity()
        return A, masks[universe], "equity"

    def meta(self) -> dict:
        m = {}
        if self._eq is not None:
            A, masks = self._eq
            m["equity"] = {"window": list(self.eq_window), "sessions": int(len(A["cal"])), "tickers": int(len(A["tickers"])),
                           "first_session": str(A["cal"][0].date()), "last_session": str(A["cal"][-1].date()),
                           "tickers_with_cap": int(np.sum(~np.isnan(A["cap"]))), "tickers_under_cap": int(masks["smallcap"].sum()),
                           "universe_smallcap": data.universe_size_stats(A, masks["smallcap"]),
                           "universe_uncapped": data.universe_size_stats(A, None)}
        if self._cr is not None:
            A = self._cr
            m["crypto"] = {"window": list(self.cr_window), "days": int(len(A["cal"])), "pairs": int(len(A["tickers"])),
                           "first_day": str(A["cal"][0].date()), "last_day": str(A["cal"][-1].date()), "calendar_gaps": data.calendar_gaps(A),
                           "o1_coverage_of_universe_cells": float(np.mean(~np.isnan(A["o1"][A["in_universe"]]))) if "o1" in A else None,
                           "universe": data.universe_size_stats(A, None)}
        return m


# ---------------------------------------------------------------- regress
def cmd_regress_wave1_rank(args) -> None:
    """Wave 2 engineering acceptance: 1d and 1e through the unchanged crypto rank path against the
    committed wave-1 result files (atol 5e-7). Skipped, and recorded, when klines_1d.parquet is absent."""
    out = _out(args)
    src = Path(args.wave1_rank)
    rep = {"source": str(src), "atol": args.atol}
    if not (data.roots().binance / "klines_1d.parquet").exists():
        rep["status"] = "skipped: klines_1d.parquet absent (Binance 1d klines were not pulled on this machine)"
        (out / "regress_wave1_rank.json").write_text(json.dumps(rep, indent=2))
        print(json.dumps(rep, indent=2))
        return
    lanes = Lanes()
    A = lanes.crypto()
    diffs = []
    for name, unis in (("1d", ["BTCUSDT", "ETHUSDT"]), ("1e", ["crypto"])):
        sig = signals.load(name)
        for uni in unis:
            s_new = _run_rank(sig, A, uni, "dev", out)
            old = pd.read_csv(src / f"results_{name}_{uni}_dev.csv", dtype={"cost": str, "period": str})
            new = pd.read_csv(out / f"results_{name}_{uni}_dev.csv", dtype={"cost": str, "period": str})
            m = old.merge(new, on=["cost", "period"], suffixes=("_old", "_new"))
            for c in ("weeks", "mean_weekly_diff", "se", "z", "ann_excess"):
                a, b = m[f"{c}_old"].to_numpy(dtype=float), m[f"{c}_new"].to_numpy(dtype=float)
                bad = ~np.isclose(a, b, rtol=0, atol=args.atol, equal_nan=True)
                if bad.any():
                    diffs.append({"row": f"{name}_{uni}", "column": c, "rows": int(bad.sum()), "max_abs_diff": float(np.nanmax(np.abs(a - b)))})
    rep["status"] = "ok" if not diffs else "differences"; rep["differences"] = diffs
    (out / "regress_wave1_rank.json").write_text(json.dumps(rep, indent=2))
    print(json.dumps(rep, indent=2))
    if diffs:
        sys.exit(1)


def cmd_regress(args) -> None:
    """Run the v1 rule through the new data layer on the v1 windows and compare with the original script's results CSV."""
    if args.wave1_rank:
        return cmd_regress_wave1_rank(args)
    lanes = Lanes(("2015-01-01", "2023-12-31"), ("2018-01-01", "2022-12-31"), segment_gaps=False)  # the v1 script did not segment
    out = _out(args)
    frames = []
    for uni in (args.universe.split(",") if args.universe != "all" else ALL_UNIVERSES):
        A, mask, lane = lanes.arrays(uni)
        res, trades = v1rule.run_v1(A, lane, "top100" if uni == "crypto" else uni, mask)
        frames.append(res)
        log.info("regress %s: %s", uni, {f: int(t["filled"].sum()) for f, t in trades.items()})
    new = pd.concat(frames, ignore_index=True)
    new.to_csv(out / "regress_v1_new_engine.csv", index=False)
    (out / "regress_v1_tables.md").write_text("# v1 rule through the new engine\n" + v1rule.headline_markdown(new))
    print(v1rule.headline_markdown(new))
    if args.v1_results:
        old = pd.read_csv(args.v1_results, dtype={"cost": str, "year": str})
        keys = ["market", "universe", "fill", "cost", "year"]
        cols = [c for c in new.columns if c not in keys]
        m = old.merge(new, on=keys, suffixes=("_old", "_new"))
        diffs = []
        for c in cols:
            a, b = m[f"{c}_old"].to_numpy(dtype=float), m[f"{c}_new"].to_numpy(dtype=float)
            both_nan = np.isnan(a) & np.isnan(b)
            d = np.where(both_nan, 0.0, np.abs(a - b))
            bad = np.nonzero(~np.isclose(a, b, rtol=0, atol=args.atol, equal_nan=True))[0]
            if len(bad):
                diffs.append((c, len(bad), float(np.nanmax(d))))
        cmp = {"rows_compared": int(len(m)), "rows_old": int(len(old)), "rows_new": int(len(new)),
               "columns_with_differences": [{"column": c, "rows": n, "max_abs_diff": x} for c, n, x in diffs]}
        (out / "regress_v1_comparison.json").write_text(json.dumps(cmp, indent=2))
        print(json.dumps(cmp, indent=2))
        if diffs:
            sys.exit(1)


# ---------------------------------------------------------------- run
def _run_event(sig, A, mask, lane, universe, era_name, out: Path, raw=None, extra: dict | None = None) -> dict:
    spec = engine.EventSpec(sig.NAME, sig.DIRECTION, sig.HORIZON)
    era = engine.ERAS[lane][era_name]
    raw = sig.candidates(A) if raw is None else raw
    trades = {fill: engine.event_trades(A, raw, spec, mask, era, fill) for fill in ("next_open", "close", "next_close")}
    res = engine.event_report(trades, spec, lane, era_name, universe)
    ctl = engine.event_controls(A, raw, spec, mask, era, trades["next_open"])
    tag = f"{sig.NAME}_{universe}_{era_name}"
    res.to_csv(out / f"results_{tag}.csv", index=False)
    (out / f"controls_{tag}.json").write_text(json.dumps(ctl, indent=2, default=float))
    pd.concat(trades.values()).to_parquet(data.roots().raw / f"trades_wave1_{tag}.parquet", index=False)
    head = res[(res["fill"] == "next_open") & (res["horizon"] == str(sig.HORIZON)) & (res["period"] == "all")].set_index("cost")
    hb = head.loc["base"]
    summary = {"signal": sig.NAME, "universe": universe, "era": era_name, "mode": "event", "direction": sig.DIRECTION,
               "horizon": sig.HORIZON, "trades": int(hb["trades"]), "entry_days": int(hb["entry_days"]),
               "mean_net_base_bps": float(hb["mean_net"] * 1e4), "z_base": float(hb["z"]),
               "mean_net_0_bps": float(head.loc["0", "mean_net"] * 1e4), "z_0": float(head.loc["0", "z"]),
               "mean_net_high_bps": float(head.loc["high", "mean_net"] * 1e4), **ctl}
    if extra:
        summary.update(extra(trades["next_open"]) if callable(extra) else extra)
    log.info("%s: %s", tag, {k: (round(v, 2) if isinstance(v, float) else v) for k, v in summary.items()})
    return summary


def _run_rank(sig, A, universe, era_name, out: Path) -> dict:
    era = engine.ERAS["crypto"][era_name]
    if sig.NAME == "1d":
        pos = sig.position(A)
        wk = engine.ts_mom_weekly(A, pos, universe, era)
        pl = engine.ts_mom_weekly(A, pos, universe, era, lag_days=engine.PLACEBO_LAG)
    else:
        sc = sig.scores(A)
        wk = engine.xs_mom_weekly(A, sc, era, sig.HOLD_WEEKS)
        pl = engine.xs_mom_weekly(A, sc, era, sig.HOLD_WEEKS, lag_days=engine.PLACEBO_LAG)
    res = engine.rank_report(wk, sig.NAME, universe, era_name)
    ctl = engine.rank_controls(wk, pl)
    tag = f"{sig.NAME}_{universe}_{era_name}"
    res.to_csv(out / f"results_{tag}.csv", index=False)
    wk.to_csv(out / f"weekly_{tag}.csv", index=False)
    (out / f"controls_{tag}.json").write_text(json.dumps(ctl, indent=2, default=float))
    head = res[res["period"] == "all"].set_index("cost")
    summary = {"signal": sig.NAME, "universe": universe, "era": era_name, "mode": "rank", "horizon": 7,
               "weeks": int(head.loc["base", "weeks"]), "ann_excess_base_pp": float(head.loc["base", "ann_excess"] * 100),
               "z_base": float(head.loc["base", "z"]), "ann_excess_0_pp": float(head.loc["0", "ann_excess"] * 100),
               "z_0": float(head.loc["0", "z"]), "ann_excess_high_pp": float(head.loc["high", "ann_excess"] * 100), **ctl}
    log.info("%s: %s", tag, {k: (round(v, 2) if isinstance(v, float) else v) for k, v in summary.items()})
    return summary


# ---------------------------------------------------------------- rank mode, equities (wave 2)
def _spec(sig, variant: str) -> engine.RankSpec:
    v = sig.VARIANTS[variant]
    return engine.RankSpec(name=f"{sig.NAME}-{variant}", ppy=sig.PPY, side=sig.SIDE, div=v["div"], hold=v.get("hold", 1),
                           liq_floor=getattr(sig, "LIQ_FLOOR", None), subset_top_half=v.get("subset_top_half", False),
                           comparator=v.get("comparator", "ranked"))


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    m = ~np.isnan(a) & ~np.isnan(b)
    if m.sum() < 10:
        return np.nan
    return float(pd.Series(a[m]).rank().corr(pd.Series(b[m]).rank()))


def _diag(A, mask, res, spec, era_name) -> dict:
    """Vintage table, Spearman(2a, 2b) and top-decile overlap per D, rank Spearman at D vs D-250,
    price-quintile shares per year, calendar-month table."""
    sets, wk = res["sets"], res["periods"]
    D = sets["D"]
    first_bar = pd.Series(A["panel"].groupby("ticker")["date"].min()).reindex(A["tickers"])
    late = (first_bar > A["cal"][0]).to_numpy()
    years = wk["year"].to_numpy()
    valid = wk["valid"].to_numpy()
    vint = []
    for y in sorted(set(years[valid].astype(int))):
        m = (years == y) & valid
        held = sets["basket"][m]
        vint.append({"year": int(y), "eligible_mean": float(sets["n"][m].mean()), "held_mean": float(held.sum(axis=1).mean()),
                     "held_first_seen_after_start": float((held & late[None, :]).sum() / max(held.sum(), 1))})
    sp, ov, stab = [], [], []
    score_full = res.get("score_full")
    for i, d in enumerate(D):
        r = sets["ranked"][i]
        a, b = A["ret_12_1"][d], A["close_to_max_close_250"][d]
        sp.append(_spearman(np.where(r, a, np.nan), np.where(r, b, np.nan)))
        ba, _, _ = engine.rank_basket(a, r, "top", 10); bb, kb, _ = engine.rank_basket(b, r, "top", 10)
        ov.append(float((ba & bb).sum() / kb) if kb else np.nan)
        if score_full is not None and d - engine.PLACEBO_LAG_LONG >= 0:
            stab.append(_spearman(np.where(r, score_full[d], np.nan), np.where(r, score_full[d - engine.PLACEBO_LAG_LONG], np.nan)))
    q_shares = {}
    for y in sorted(set(years[valid].astype(int))):
        m = (years == y) & valid
        qs = np.zeros(5); tot = 0
        for i in np.nonzero(m)[0]:
            q = engine._quintiles(A["close"][D[i]], sets["comp"][i])
            held = sets["basket"][i]
            for qq in range(1, 6):
                qs[qq - 1] += int((held & (q == qq)).sum())
            tot += int(held.sum())
        q_shares[str(int(y))] = (qs / max(tot, 1)).round(4).tolist()
    v = wk[wk["valid"]]
    cal_month = {int(mo): {"periods": int(len(g)), "mean_diff_base": float(g["diff_base"].mean())} for mo, g in v.groupby("month")}
    return {"vintage": vint, "spearman_2a_2b_median": float(np.nanmedian(sp)) if sp else np.nan,
            "top_decile_overlap_2a_2b_median": float(np.nanmedian(ov)) if ov else np.nan,
            "score_rank_spearman_D_vs_D250_median": float(np.nanmedian(stab)) if stab else np.nan,
            "price_quintile_shares_by_year": q_shares, "calendar_month": cal_month}


def _run_rank_equity(sig, variant: str, A, mask, universe: str, era_name: str, out: Path, cache: dict, draws: int = engine.RANDOM_DRAWS,
                     floor: str | None = None) -> dict:
    spec = _spec(sig, variant)
    era = engine.ERAS["equity"][era_name]
    key = (spec.ppy, era_name, floor)
    if key not in cache:
        fills = engine.rank_fills(A["cal"], spec.ppy, era)
        R, liq = engine.holding_returns(A, fills)
        cache[key] = (fills, R, liq)
    fills, R, liq = cache[key]
    score = sig.scores(A, variant)
    score2 = sig.subset_scores(A) if spec.subset_top_half else None
    t0 = time.time()
    res = engine.rank_equity(A, mask, spec, score, era, era_name, score2, fills, R, liq)
    res["score_full"] = score
    ctl, rnd = engine.rank_controls_equity(res, spec, A, mask, score, era, era_name, score2, draws=draws)
    rep = engine.rank_report_equity(res, ctl, spec, universe, era_name)
    head = rep[rep["period"] == "all"].set_index("cost")
    hb = head.loc["base"].to_dict()
    hb["ann_excess_high"] = float(head.loc["high", "ann_excess"])
    p_dev = engine.p_one_sided(hb["z_gate"])
    rep["p_sidak"] = engine.p_sidak(p_dev)
    verdict = engine.verdict_rank(hb, universe, spec.ppy) if era_name == "dev" else ""
    rep["verdict"] = verdict
    tag = f"{spec.name}_{universe}_{era_name}" + (f"_floor-{floor}" if floor else "")
    rep.to_csv(out / f"results_{tag}.csv", index=False)
    res["periods"].to_csv(out / f"periods_{tag}.csv", index=False)
    engine.rank_ladder(res["sets"], R, fills, spec.ppy).to_csv(out / f"ladder_{tag}.csv", index=False)
    ctl["p_dev"] = p_dev; ctl["p_sidak"] = float(rep["p_sidak"].iloc[0]); ctl["verdict"] = verdict
    ctl["flags"] = {"autocorr": bool(abs(hb["z_plain"] - hb["z_nw"]) > engine.AUTOCORR_FLAG) if not np.isnan(hb["z_nw"]) else False,
                    "size_concentrated": bool(abs(hb["trade_weighted_mean"] - hb["mean_diff_period"]) > hb["se"]) if not np.isnan(hb["se"]) else False}
    (out / f"controls_{tag}.json").write_text(json.dumps(ctl, indent=2, default=float))
    rnd.to_csv(out / f"random_{tag}.csv", index=False)
    (out / f"diag_{tag}.json").write_text(json.dumps(_diag(A, mask, res, spec, era_name), indent=2, default=float))
    summary = {"signal": sig.NAME, "variant": variant, "universe": universe, "era": era_name, "mode": "rank-equity", "ppy": spec.ppy,
               "floor": floor or "close", "periods": int(hb["periods"]), "k_median": hb["k_median"], "n_eligible_median": hb["n_eligible_median"],
               "ann_excess_base_pp": hb["ann_excess"] * 100, "ann_excess_0_pp": float(head.loc["0", "ann_excess"]) * 100,
               "ann_excess_high_pp": hb["ann_excess_high"] * 100, "z_gate_base": hb["z_gate"], "z_plain_base": hb["z_plain"], "z_nw_base": hb["z_nw"],
               "z_gate_0": float(head.loc["0", "z_gate"]), "se_bps": hb["se"] * 1e4, "mde80_pp": hb["mde80_pp"], "hit_rate": hb["hit_rate"],
               "turnover_oneway_ann": hb["turnover_oneway_ann"], "cost_drag_ann_pp": hb["cost_drag_ann"] * 100, "years_positive": int(hb["years_positive"]),
               "half1_excess_pp": hb["half1_excess"] * 100, "half2_excess_pp": hb["half2_excess"] * 100, "z_ex2020": hb["z_ex2020"], "z_contrib_2020": hb["z_contrib_2020"],
               "z_ex_jan": hb["z_ex_jan"], "z_wo_top5pct": hb["z_wo_top5pct"], "top5pct_share": hb["top5pct_share"],
               "mirror_z": ctl["mirror_z"], "mirror_ann_excess_pp": ctl["mirror_ann_excess"] * 100, "random_rank": ctl.get("random_rank"),
               "random_pctile_excess": ctl.get("random_pctile_excess"), "random_engine_check": ctl.get("random_engine_check"),
               "lag250_z0": ctl["lag250_z0"], "lag250_ann_excess_pp": ctl["lag250_ann_excess"] * 100, "lag250_periods": ctl["lag250_periods"],
               "actual_on_lag250_dates_z": ctl["actual_on_lag250_dates_z"], "lag20_z0": ctl["lag20_z0"],
               "price_matched_excess_pp": ctl["price_matched_excess"] * 100, "price_ratio_top_uni": ctl["price_ratio_top_uni"],
               "planted_bar_shift": ctl["planted_bar_shift"], "planted_50_shift": ctl["planted_50_shift"], "p_dev": p_dev, "p_sidak": ctl["p_sidak"],
               "verdict": verdict, "runtime_s": round(time.time() - t0)}
    if "bounce_gap_bps" in ctl:
        summary["bounce_gap_bps"] = ctl["bounce_gap_bps"]; summary["bounce_flag"] = ctl["bounce_flag"]
    log.info("%s: %s", tag, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in summary.items()})
    return summary


def cmd_proof(args, out: Path) -> None:
    """Rebalance dates and fills in a window: counts only, no score is read."""
    lanes = Lanes()
    A, _ = lanes.equity()
    start, end = args.proof
    rep = {"window": [start, end]}
    for name, ppy in (("month_ends", 12), ("week_ends", 52)):
        f = engine.rank_fills(A["cal"], ppy, (start, end))
        idx = A["cal"].get_indexer(f["date"])
        fill_ok = bool((f["fill_idx"].to_numpy() == idx + 1).all())
        rep[name] = {"count": int(len(f)), "first": str(f["date"].iloc[0].date()), "last": str(f["date"].iloc[-1].date()),
                     "valid_in_window": int(f["valid"].sum()), "every_fill_one_session_after_D": fill_ok,
                     "dates": [str(d.date()) for d in f["date"]]}
    (out / f"proof_{start}_{end}.json").write_text(json.dumps(rep, indent=2))
    print(json.dumps({k: ({kk: vv for kk, vv in v.items() if kk != "dates"} if isinstance(v, dict) else v) for k, v in rep.items()}, indent=2))


def _floor_arrays(A: dict) -> tuple[dict, dict]:
    """A copy of the arrays whose universe uses the USD 2 floor on raw_close (close x the product
    of the ratios of the splits after D) instead of the split-adjusted close; and the flip stats."""
    splits = data.load_splits()
    if splits is None:
        raise SystemExit("floor diagnostic needs raw/universe/splits.parquet (pull --splits)")
    px = A["panel"]
    base_ok = (px["full_hist"] & (px["med_dv_20_prev"] >= data.EQ_DV_FLOOR) & (px["rvol_20"] > data.EQ_VOL_FLOOR) & px["rvol_20_prev"].notna())
    nofloor = data._wide(px.assign(_nf=base_ok), "_nf", A["cal"], A["tickers"]) == 1.0
    raw_close = data.raw_close_array(A, splits)
    with np.errstate(invalid="ignore"):
        uni_raw = nofloor & (raw_close >= data.EQ_PRICE_FLOOR)
    B = dict(A)
    B["in_universe"] = uni_raw
    B["raw_close"] = raw_close
    stats = {}
    for era_name, era in engine.ERAS["equity"].items():
        m, _ = engine.era_rows(A["cal"], era)
        locked, raw = A["in_universe"][m], uni_raw[m]
        either = locked | raw
        stats[era_name] = {"locked_universe_days": int(locked.sum()), "raw_universe_days": int(raw.sum()),
                           "flip_share_of_locked": float((locked != raw).sum() / max(locked.sum(), 1)),
                           "admitted_by_raw_only": int((raw & ~locked).sum()), "ejected_by_raw": int((locked & ~raw).sum())}
    return B, {"splits_rows": int(len(splits)), "tickers_with_splits": int(splits["ticker"].nunique()), "eras": stats}


def cmd_run(args) -> None:
    out = _out(args)
    if args.proof:
        return cmd_proof(args, out)
    names = EVENT_SIGNALS + RANK_SIGNALS if args.signal == "all" else args.signal.split(",")
    lanes = Lanes()
    summaries = []
    t0 = time.time()
    cache: dict = {}
    floor_meta = None
    for name in names:
        sig = signals.load(name)
        unis = sig.UNIVERSES if args.universe == "all" else [u for u in args.universe.split(",") if u in sig.UNIVERSES]
        for uni in unis:
            if sig.MODE == "event":
                A, mask, lane = lanes.arrays(uni)
                summaries.append(_run_event(sig, A, mask, lane, uni, args.era, out))
            elif getattr(sig, "LANE", "crypto") == "equity":
                A, mask, lane = lanes.arrays(uni)
                if args.floor:
                    if "floor" not in cache:
                        cache["floor"] = _floor_arrays(A)
                    A, floor_meta = cache["floor"]
                for variant in (args.variant.split(",") if args.variant else WAVE2_VARIANTS):
                    summaries.append(_run_rank_equity(sig, variant, A, mask, uni, args.era, out, cache, draws=args.draws, floor=args.floor))
            else:
                A = lanes.crypto()
                summaries.append(_run_rank(sig, A, uni, args.era, out))
    if args.floor:
        _write_floor_diag(out, summaries, floor_meta, args.era)
    mp = out / f"meta_{args.era}.json"
    meta = json.loads(mp.read_text()) if mp.exists() else {}
    meta.setdefault("lanes", {}).update(lanes.meta())
    meta.setdefault("runs", {})[pd.Timestamp.utcnow().isoformat()] = {"signals": names, "universe": args.universe, "variant": args.variant, "floor": args.floor,
                                                                      "draws": args.draws, "runtime_s": round(time.time() - t0)}
    key = (lambda s: f"{s['signal']}-{s['variant']}_{s['universe']}" if "variant" in s else f"{s['signal']}_{s['universe']}")
    if args.floor:
        meta.setdefault("floor_summaries", {}).update({key(s): s for s in summaries})
    else:
        meta.setdefault("summaries", {}).update({key(s): s for s in summaries})
    mp.write_text(json.dumps(meta, indent=2, default=float))
    print(pd.DataFrame(summaries).to_string())


def _write_floor_diag(out: Path, summaries: list, floor_meta: dict, era: str) -> None:
    """floor_diag_<tag>.csv per row: net excess under the locked (split-adjusted) and the raw floor."""
    for s in summaries:
        tag = f"{s['signal']}-{s['variant']}_{s['universe']}_{era}"
        locked = pd.read_csv(out / f"results_{tag}.csv", dtype={"cost": str, "period": str})
        lb = locked[(locked["period"] == "all") & (locked["cost"] == "base")].iloc[0]
        delta = (s["ann_excess_base_pp"] - lb["ann_excess"] * 100) / abs(lb["ann_excess"] * 100) if lb["ann_excess"] != 0 else np.nan
        row = {"signal": s["signal"], "variant": s["variant"], "universe": s["universe"], "era": era,
               "flip_share_of_locked": floor_meta["eras"][era]["flip_share_of_locked"],
               "admitted_by_raw_only": floor_meta["eras"][era]["admitted_by_raw_only"], "ejected_by_raw": floor_meta["eras"][era]["ejected_by_raw"],
               "ann_excess_base_locked_pp": lb["ann_excess"] * 100, "z_gate_locked": lb["z_gate"],
               "ann_excess_base_raw_pp": s["ann_excess_base_pp"], "z_gate_raw": s["z_gate_base"],
               "relative_change": delta, "flag_moved_over_25pct": bool(abs(delta) > 0.25) if not np.isnan(delta) else False}
        pd.DataFrame([row]).to_csv(out / f"floor_diag_{tag}.csv", index=False)
    (out / f"floor_meta_{era}.json").write_text(json.dumps(floor_meta, indent=2))


# ---------------------------------------------------------------- autopsy to rule (amendment A2)
class _Rule:
    MODE = "event"

    def __init__(self, name, direction):
        self.NAME, self.DIRECTION, self.HORIZON = name, direction, autopsy.DECISION_H


def cmd_autopsy(args) -> None:
    """Select the top-lift features from the committed lift table and run them as prospective rules."""
    out = _out(args)
    lifts = pd.read_csv(args.lifts)
    lanes = Lanes()
    selected, summaries = [], []
    t0 = time.time()
    for market, sel_uni, run_unis in (("equity", "uncapped", EQ_UNIVERSES), ("crypto", "crypto", ["crypto"])):
        for group, direction in autopsy.GROUP_DIRECTION.items():
            feats = autopsy.select_features(lifts, sel_uni, group)
            for fdef in feats:
                selected.append({"market": market, "selected_on": sel_uni, "group": group, "direction": direction, **fdef,
                                 "rule": autopsy.rule_name(group, fdef["feature"])})
            if not feats:
                log.info("autopsy %s %s: no feature with lift >= %.1f", market, group, autopsy.LIFT_MIN)
            only = set(args.only.split(",")) if args.only else None
            feats = [f for f in feats if only is None or autopsy.rule_name(group, f["feature"]) in only]
            if only is not None:
                run_unis = [u for u in run_unis if not args.universe or u in args.universe.split(",")]
            for uni in run_unis:
                if not feats:
                    continue
                A, mask, lane = lanes.arrays(uni)
                era = engine.ERAS[lane][args.era]
                for fdef in feats:
                    rule = _Rule(autopsy.rule_name(group, fdef["feature"]), direction)
                    raw = autopsy.rule_matrix(A, fdef["feature"], fdef["side"], mask)
                    extra = lambda tr, A=A, mask=mask, era=era, group=group: autopsy.extra_metrics(A, tr, mask, era, group)  # noqa: E731
                    s = _run_event(rule, A, mask, lane, uni, args.era, out, raw=raw, extra=extra)
                    s.update({"feature": fdef["feature"], "side": fdef["side"], "selection_lift": fdef["lift"], "group": group})
                    summaries.append(s)
    if not args.only:
        pd.DataFrame(selected).to_csv(out / "a2r_selected_features.csv", index=False)
    mp = out / f"meta_{args.era}.json"
    meta = json.loads(mp.read_text()) if mp.exists() else {}
    meta.setdefault("lanes", {}).update(lanes.meta())
    meta.setdefault("runs", {})[pd.Timestamp.utcnow().isoformat()] = {"signals": "autopsy", "runtime_s": round(time.time() - t0)}
    meta.setdefault("summaries", {}).update({f"{s['signal']}_{s['universe']}": s for s in summaries})
    mp.write_text(json.dumps(meta, indent=2, default=float))
    pd.DataFrame(summaries).to_csv(out / f"a2r_summary_{args.era}.csv", index=False)
    print(pd.DataFrame(selected).to_string())
    print(pd.DataFrame(summaries).to_string())


# ---------------------------------------------------------------- movers
def cmd_movers(args) -> None:
    out = _out(args)
    lanes = Lanes()
    cs, ls = [], []
    for uni in (ALL_UNIVERSES if args.universe == "all" else args.universe.split(",")):
        A, mask, lane = lanes.arrays(uni)
        era = engine.ERAS[lane][args.era]
        cs.append(movers.counts(A, mask, era, uni))
        ls.append(movers.lifts(A, mask, era, uni))
        log.info("movers %s done", uni)
    c, l = pd.concat(cs, ignore_index=True), pd.concat(ls, ignore_index=True)
    c.to_csv(out / f"movers_counts_{args.era}.csv", index=False)
    l.to_csv(out / f"movers_lifts_{args.era}.csv", index=False)
    md = "# Extreme movers (hypothesis material, not a result)\n" + movers.counts_markdown(c) + "\n" + movers.lifts_markdown(l)
    (out / f"movers_{args.era}.md").write_text(md)
    print(md)


# ---------------------------------------------------------------- tables
def _fmt_bps(x) -> str:
    return "n/a" if pd.isna(x) else f"{x * 1e4:+.0f}"


def _fmt_z(x) -> str:
    return "n/a" if pd.isna(x) else f"{x:+.2f}"


def event_tables(out: Path, era: str) -> str:
    lines = []
    files = sorted(out.glob(f"results_*_{era}.csv"))
    for f in files:
        res = pd.read_csv(f, dtype={"cost": str, "period": str, "horizon": str})
        if "fill" not in res.columns:
            continue
        sig, uni = res["signal"].iloc[0], res["universe"].iloc[0]
        lane = res["lane"].iloc[0]
        H = str(res.loc[res["decision"], "horizon"].iloc[0])
        ctl = json.loads((out / f"controls_{sig}_{uni}_{era}.json").read_text())
        no = res[(res["fill"] == "next_open")]
        d = no[(no["horizon"] == H) & (no["period"] == "all")].set_index("cost")
        levels = engine.COST_LEVELS[lane]
        lines.append(f"\n**{sig} / {uni} / {era} — direction {res['direction'].iloc[0] if 'direction' in res else ''}, decision horizon {H} sessions, next-open fill**\n")
        meta = json.loads((out / f"meta_{era}.json").read_text())["summaries"].get(f"{sig}_{uni}", {})
        if "match_rate_per_day" in meta:
            lines.append(f"Autopsy rule on `{meta['feature']}` ({meta['side']} quintile, selection lift {meta['selection_lift']:.2f}): match rate {meta['match_rate_per_day']:.1%} of the universe per day; "
                         f"{meta['hits']} of {meta['trades']} trades made the original 63-session move ({meta['hit_original_move']:.2%}) against a universe base rate of {meta['universe_base_rate']:.2%} (realized lift {meta['lift_realized']:.2f}).\n")
        lines.append("| candidates | held | trades | days | " + " | ".join(f"net @{c}" for c in levels) + " | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |")
        lines.append("|" + "---|" * (10 + len(levels)))
        b = d.loc["base"]
        lines.append(f"| {int(b['candidates'])} | {int(b['held'])} | {int(b['trades'])} | {int(b['entry_days'])} | "
                     + " | ".join(_fmt_bps(d.loc[c, "mean_net"]) for c in levels)
                     + f" | {b['hit_rate']:.3f} | {_fmt_bps(b['daymean'])} | {_fmt_bps(b['se'])} | {_fmt_z(b['z'])} | {b['top10_share']:.1%} | {_fmt_z(b['z_wo_top10'])} |")
        # horizon curve at zero cost and base
        lines.append("\nHorizon curve (next-open fill; mean excess per trade, bps; z): ")
        lines.append("| horizon | trades | gross excess | z @0 | net @base | z @base |")
        lines.append("|---|---|---|---|---|---|")
        for h in [str(x) for x in engine.HORIZONS] + list(engine.INTRADAY):
            sel0 = no[(no["horizon"] == h) & (no["period"] == "all") & (no["cost"] == "0")]
            if sel0.empty:
                continue
            r0 = sel0.iloc[0]
            rb = no[(no["horizon"] == h) & (no["period"] == "all") & (no["cost"] == "base")].iloc[0]
            lines.append(f"| {h}{' *' if h == H else ''} | {int(r0['trades'])} | {_fmt_bps(r0['mean_net'])} | {_fmt_z(r0['z'])} | {_fmt_bps(rb['mean_net'])} | {_fmt_z(rb['z'])} |")
        # halves and per year at base
        lines.append("\nPer period (decision horizon, base cost): ")
        lines.append("| period | trades | days | net | z |")
        lines.append("|---|---|---|---|---|")
        for _, r in no[(no["horizon"] == H) & (no["cost"] == "base") & (no["period"] != "all")].iterrows():
            lines.append(f"| {r['period']} | {int(r['trades'])} | {int(r['entry_days'])} | {_fmt_bps(r['mean_net'])} | {_fmt_z(r['z'])} |")
        # fills
        lines.append("\nFill comparison (decision horizon, zero cost / base): ")
        lines.append("| fill | trades | gross excess | z @0 | net @base |")
        lines.append("|---|---|---|---|---|")
        for fill in ("close", "next_open", "next_close"):
            r0 = res[(res["fill"] == fill) & (res["horizon"] == H) & (res["period"] == "all") & (res["cost"] == "0")].iloc[0]
            rb = res[(res["fill"] == fill) & (res["horizon"] == H) & (res["period"] == "all") & (res["cost"] == "base")].iloc[0]
            lines.append(f"| {fill} | {int(r0['trades'])} | {_fmt_bps(r0['mean_net'])} | {_fmt_z(r0['z'])} | {_fmt_bps(rb['mean_net'])} |")
        lines.append(f"\nControls: placebo (lag 20) z @0 {_fmt_z(ctl['placebo_z_0'])}, @base {_fmt_z(ctl['placebo_z_base'])} on {ctl['placebo_trades']} trades; "
                     f"planted +50 bps z {_fmt_z(ctl['planted_z_0'])} vs actual {_fmt_z(ctl['actual_z_0'])} (shift {_fmt_z(ctl['planted_shift'])}).")
    return "\n".join(lines)


def rank_tables(out: Path, era: str) -> str:
    lines = []
    for f in sorted(out.glob(f"results_1[de]_*_{era}.csv")):
        res = pd.read_csv(f, dtype={"cost": str, "period": str, "horizon": str})
        sig, uni = res["signal"].iloc[0], res["universe"].iloc[0]
        ctl = json.loads((out / f"controls_{sig}_{uni}_{era}.json").read_text())
        d = res[res["period"] == "all"].set_index("cost")
        lines.append(f"\n**{sig} / {uni} / {era} — weekly, Sunday close → Monday 01:00 UTC fill**\n")
        lines.append("| cost | weeks | ann. excess (pp) | mean weekly diff (bps) | SE | z | hit | ann. ret strat | ann. ret comp | vol strat | vol comp | max DD strat | max DD comp | top-10 share | z w/o top 10 |")
        lines.append("|" + "---|" * 15)
        for c in engine.COST_LEVELS["crypto"]:
            if c not in d.index:
                continue
            r = d.loc[c]
            lines.append(f"| {c} | {int(r['weeks'])} | {r['ann_excess'] * 100:+.1f} | {_fmt_bps(r['mean_weekly_diff'])} | {_fmt_bps(r['se'])} | {_fmt_z(r['z'])} | {r['hit_rate']:.3f} | "
                         f"{r['ann_ret_strat']:+.1%} | {r['ann_ret_comp']:+.1%} | {r['ann_vol_strat']:.0%} | {r['ann_vol_comp']:.0%} | {r['max_dd_strat']:.0%} | {r['max_dd_comp']:.0%} | {r['top10_share']:.1%} | {_fmt_z(r['z_wo_top10'])} |")
        extra = f"time in market {d.loc['base', 'time_in_market']:.2f}, round trips per year {d.loc['base', 'round_trips_per_year']:.1f}" if "time_in_market" in d else f"round trips per year {d.loc['base', 'round_trips_per_year']:.1f}"
        lines.append(f"\n{extra}. Per period at base cost:")
        lines.append("| period | weeks | ann. excess (pp) | z |")
        lines.append("|---|---|---|---|")
        for _, r in res[(res["cost"] == "base") & (res["period"] != "all")].iterrows():
            lines.append(f"| {r['period']} | {int(r['weeks'])} | {r['ann_excess'] * 100:+.1f} | {_fmt_z(r['z'])} |")
        lines.append(f"\nControls: placebo (lag 20 days) z @0 {_fmt_z(ctl['placebo_z_0'])}, @base {_fmt_z(ctl['placebo_z_base'])}; "
                     f"planted +50 bps/week z {_fmt_z(ctl['planted_z_0'])} vs actual {_fmt_z(ctl['actual_z_0'])} (shift {_fmt_z(ctl['planted_shift'])}).")
    return "\n".join(lines)


def _fmt_pp(x) -> str:
    return "n/a" if pd.isna(x) else f"{x * 100:+.1f}"


def rank_equity_tables(out: Path, era: str) -> str:
    lines = []
    files = sorted(out.glob(f"results_2*_{era}.csv"))
    if not files:
        return ""
    lines.append(f"\n## Rank mode on equities (wave 2), {era} era\n")
    lines.append("Annualized net excess over the equal-weight ranked set in pp; z is z_gate = min(z_plain, z_nw) at the cost level; SE in bps per period; "
                 "`rnd` is the actual net excess's rank among itself and the 200 random slices (pass ≥ 191 of 201); `lag250` and `mirror` are zero-cost z_gate; "
                 "`pm` is the price-matched net excess at base; `plant` is the planted bar-sized shift (expected X/SE).\n")
    lines.append("| row | universe | periods | k | n | gross | @low | @base | @high | SE | z @0 | z_plain | z_nw | z @base | MDE80 | hit | turnover | drag | top-5% share | z w/o top 5% | half1 / half2 | yrs+ | z ex-2020 (contrib) | z ex-Jan | mirror z (pp) | rnd | lag250 z (pp) | actual on lag dates | lag20 z | pm (pp) | price ratio | plant | p_sidak | verdict |")
    lines.append("|" + "---|" * 34)
    for f in files:
        res = pd.read_csv(f, dtype={"cost": str, "period": str})
        sig, var, uni = res["signal"].iloc[0], res["variant"].iloc[0], res["universe"].iloc[0]
        d = res[res["period"] == "all"].set_index("cost")
        b = d.loc["base"]
        lines.append(f"| {sig}-{var} | {uni} | {int(b['periods'])} | {b['k_median']:.0f} | {b['n_eligible_median']:.0f} | {_fmt_pp(d.loc['0', 'ann_excess'])} | {_fmt_pp(d.loc['low', 'ann_excess'])} | **{_fmt_pp(b['ann_excess'])}** | {_fmt_pp(d.loc['high', 'ann_excess'])} | "
                     f"{b['se'] * 1e4:.0f} | {_fmt_z(d.loc['0', 'z_gate'])} | {_fmt_z(b['z_plain'])} | {_fmt_z(b['z_nw'])} | **{_fmt_z(b['z_gate'])}** | {b['mde80_pp']:.1f} | {b['hit_rate']:.3f} | {b['turnover_oneway_ann']:.2f} | {_fmt_pp(b['cost_drag_ann'])} | "
                     f"{b['top5pct_share']:.1%} | {_fmt_z(b['z_wo_top5pct'])} | {_fmt_pp(b['half1_excess'])} / {_fmt_pp(b['half2_excess'])} | {int(b['years_positive'])} | {_fmt_z(b['z_ex2020'])} ({_fmt_z(b['z_contrib_2020'])}) | {_fmt_z(b['z_ex_jan'])} | "
                     f"{_fmt_z(b['mirror_z'])} ({_fmt_pp(b['mirror_ann_excess'])}) | {int(b['random_rank']) if not pd.isna(b['random_rank']) else 'n/a'} | {_fmt_z(b['lag250_z0'])} ({_fmt_pp(b['lag250_ann_excess'])}; {int(b['lag250_periods'])}) | {_fmt_z(b['actual_on_lag250_dates_z'])} | {_fmt_z(b['lag20_z0'])} | "
                     f"{_fmt_pp(b['price_matched_excess'])} | {b['price_ratio_top_uni']:.2f} | {_fmt_z(b['planted_bar_shift'])} | {b['p_sidak']:.3f} | {b['verdict']} |")
    lines.append("\nPer fill year at base cost, annualized net excess (pp) and z_gate:\n")
    lines.append("| row | universe | " + " | ".join(str(y) for y in range(2010, 2024)) + " |")
    lines.append("|" + "---|" * 16)
    for f in files:
        res = pd.read_csv(f, dtype={"cost": str, "period": str})
        sig, var, uni = res["signal"].iloc[0], res["variant"].iloc[0], res["universe"].iloc[0]
        yr = res[(res["cost"] == "base") & res["period"].str.match(r"^20\d\d$")].set_index("period")
        cells = [f"{_fmt_pp(yr.loc[str(y), 'ann_excess'])} ({_fmt_z(yr.loc[str(y), 'z_gate'])})" if str(y) in yr.index else "—" for y in range(2010, 2024)]
        lines.append(f"| {sig}-{var} | {uni} | " + " | ".join(cells) + " |")
    lines.append("\nDecile ladder (1 = highest score), annualized excess over the comparator at zero cost (pp), z_gate:\n")
    lines.append("| row | universe | " + " | ".join(f"D{i}" for i in range(1, 11)) + " |")
    lines.append("|" + "---|" * 12)
    for f in files:
        res = pd.read_csv(f, dtype={"cost": str, "period": str})
        sig, var, uni = res["signal"].iloc[0], res["variant"].iloc[0], res["universe"].iloc[0]
        lad = pd.read_csv(out / f"ladder_{sig}-{var}_{uni}_{era}.csv").set_index("decile")
        lines.append(f"| {sig}-{var} | {uni} | " + " | ".join(f"{_fmt_pp(lad.loc[i, 'ann_excess'])} ({_fmt_z(lad.loc[i, 'z_gate'])})" for i in range(1, 11)) + " |")
    lines.append("\nControls and diagnostics per row:\n")
    for f in files:
        res = pd.read_csv(f, dtype={"cost": str, "period": str})
        sig, var, uni = res["signal"].iloc[0], res["variant"].iloc[0], res["universe"].iloc[0]
        tag = f"{sig}-{var}_{uni}_{era}"
        c = json.loads((out / f"controls_{tag}.json").read_text()); g = json.loads((out / f"diag_{tag}.json").read_text())
        extra = f"; bounce gap {c['bounce_gap_bps']:+.1f} bps/week (flag {c['bounce_flag']})" if "bounce_gap_bps" in c else ""
        lines.append(f"- **{sig}-{var} / {uni}**: random draws median z @0 {_fmt_z(c.get('random_median_z0', np.nan))}, median excess {_fmt_pp(c.get('random_median_ann_excess_0', np.nan))} "
                     f"(engine check {c.get('random_engine_check')}); planted +{c['planted_bar_bps']} bps shift {_fmt_z(c['planted_bar_shift'])} vs expected {_fmt_z(c['planted_bar_expected'])}, +50 bps shift {_fmt_z(c['planted_50_shift'])}; "
                     f"1a overlay @base {_fmt_pp(c['overlay_1a_ann_excess_base'])} (z {_fmt_z(c['overlay_1a_z_base'])}, {c['overlay_1a_dropped_mean']:.1f} names dropped per period); "
                     f"skipped periods {c['skipped_periods']}, unfilled {c['unfilled_total']}, liquidated {c['liquidated_total']}; flags {c['flags']}{extra}; "
                     f"Spearman(2a, 2b) {g['spearman_2a_2b_median']:.2f}, top-decile overlap {g['top_decile_overlap_2a_2b_median']:.2f}, score rank Spearman D vs D−250 {g['score_rank_spearman_D_vs_D250_median']:.2f}; "
                     f"price-quintile shares (last year) {g['price_quintile_shares_by_year'][max(g['price_quintile_shares_by_year'])]}.")
    for f in sorted(out.glob(f"floor_diag_*_{era}.csv")):
        r = pd.read_csv(f).iloc[0]
        lines.append(f"- floor diagnostic {r['signal']}-{r['variant']} / {r['universe']}: flip share {r['flip_share_of_locked']:.2%}; net @base locked {r['ann_excess_base_locked_pp']:+.2f} pp (z {r['z_gate_locked']:+.2f}) vs raw floor {r['ann_excess_base_raw_pp']:+.2f} pp (z {r['z_gate_raw']:+.2f}); relative change {r['relative_change']:+.1%}; flag {r['flag_moved_over_25pct']}.")
    return "\n".join(lines)


# ---------------------------------------------------------------- ledger
def interesting(s: dict) -> bool:
    """The pre-registered 'interesting' threshold (graduation rules 1 and 2) on a run summary."""
    if s["mode"] == "event":
        return (s["z_base"] >= 3.0 and s["entry_days"] >= 100 and s["trades"] >= 500
                and s["mean_net_base_bps"] >= 50 and s["mean_net_high_bps"] > 0)
    return (s["z_base"] >= 3.0 and s["weeks"] >= 36 and s["ann_excess_base_pp"] >= 5 and s["ann_excess_high_pp"] > 0)


def artifact_free(s: dict, res: pd.DataFrame) -> bool:
    """Graduation rule 4: sign holds without the top 10 days, placebo flat, sign holds in both halves."""
    if s["mode"] == "event":
        d = res[(res["fill"] == "next_open") & (res["horizon"] == str(s["horizon"])) & (res["cost"] == "base")].set_index("period")
        key = "mean_net"
    else:
        d = res[res["cost"] == "base"].set_index("period")
        key = "ann_excess"
    sign = np.sign(d.loc["all", key])
    return (np.sign(d.loc["all", "z_wo_top10"]) == sign and abs(s["placebo_z_0"]) < 2.0
            and np.sign(d.loc["half1", key]) == sign and np.sign(d.loc["half2", key]) == sign)


def cmd_ledger_wave2(args, dev: dict, conf: dict) -> None:
    from experiments.screen import ledger
    rows = []
    for key, s in dev.items():
        if s.get("mode") != "rank-equity":
            continue
        ppy = s["ppy"]
        unit = "mo" if ppy == 12 else "wk"
        verdict = s["verdict"]
        cz, cnet = "—", "—"
        if verdict == "confirm" and key in conf:
            c = conf[key]
            cz, cnet = f"{c['z_gate_base']:+.2f}", f"{c['ann_excess_base_pp']:+.1f} pp"
            d = {"z_gate": s["z_gate_base"], "periods": s["periods"], "ann_excess": s["ann_excess_base_pp"]}
            cc = {"z_gate": c["z_gate_base"], "periods": c["periods"], "ann_excess": c["ann_excess_base_pp"], "years_positive": c["years_positive"]}
            verdict = engine.verdict_rank_confirm(d, cc, ppy)
        rows.append({"date": args.date, "signal": s["signal"], "variant": s["variant"], "universe": s["universe"], "pre_reg_commit": args.prereg,
                     "mode": "rank long (v2 bar)" + (" smallcap non-graduating" if s["universe"] == "smallcap" else ""),
                     "decision_horizon": "1" + unit, "dev_z": f"{s['z_gate_base']:+.2f}", "dev_mean_net": f"{s['ann_excess_base_pp']:+.1f} pp",
                     "dev_n": f"{s['periods']} {unit} (MDE80 {s['mde80_pp']:.1f} pp)", "confirm_z": cz, "confirm_mean_net": cnet, "verdict": verdict,
                     "family_n": str(engine.FAMILY_N), "p_sidak": f"{s['p_sidak']:.3f}", "random": f"{s['random_rank']} / {engine.RANDOM_RANK_OF}",
                     "lag250": f"{s['lag250_z0']:+.2f}", "mirror": f"{s['mirror_z']:+.2f}", "entry": args.entry})
    df = ledger.upsert(rows)
    print(df.to_string())


def cmd_ledger(args) -> None:
    from experiments.screen import ledger
    out = _out(args)
    dev = json.loads((out / "meta_dev.json").read_text())["summaries"]
    cp = out / "meta_confirm.json"
    conf = json.loads(cp.read_text())["summaries"] if cp.exists() else {}
    if any(s.get("mode") == "rank-equity" for s in dev.values()):
        return cmd_ledger_wave2(args, dev, conf)
    rows = []
    for key, s in dev.items():
        sig = s["signal"]
        base, variant = (sig.split("-", 1) + ["—"])[:2]
        res = pd.read_csv(out / f"results_{sig}_{s['universe']}_dev.csv", dtype={"cost": str, "period": str, "horizon": str})
        if s["mode"] == "event":
            net, n = f"{s['mean_net_base_bps']:+.0f} bps", f"{s['trades']} / {s['entry_days']}"
        else:
            net, n = f"{s['ann_excess_base_pp']:+.1f} pp", f"{s['weeks']} wk"
        hot = interesting(s)
        verdict = "confirm" if hot else "null"
        cz, cnet = "—", "—"
        if hot and key in conf:
            c = conf[key]
            cz = f"{c['z_base']:+.2f}"
            cnet = f"{c['ann_excess_base_pp']:+.1f} pp" if c["mode"] == "rank" else f"{c['mean_net_base_bps']:+.0f} bps"
            same_sign = np.sign(c["z_base"]) == np.sign(s["z_base"])
            if not artifact_free(s, res):
                verdict = "artifact"
            elif same_sign and c["z_base"] >= 1.5:
                verdict = "graduate"
            else:
                verdict = "fails confirm"
        rows.append({"date": args.date, "signal": base, "variant": variant, "universe": s["universe"], "pre_reg_commit": args.prereg,
                     "mode": s["mode"] + (f" {s['direction']}" if s["mode"] == "event" else ""), "decision_horizon": f"{s['horizon']}{'d' if s['mode'] == 'rank' else 's'}",
                     "dev_z": f"{s['z_base']:+.2f}", "dev_mean_net": net, "dev_n": n, "confirm_z": cz, "confirm_mean_net": cnet,
                     "verdict": verdict, "entry": args.entry})
    df = ledger.upsert(rows)
    print(df.to_string())


def cmd_tables(args) -> None:
    out = _out(args)
    for era in ("dev", "confirm"):
        if not list(out.glob(f"results_*_{era}.csv")):
            continue
        md = (f"# Wave 2 tables — {era} era\n" + rank_equity_tables(out, era)) if list(out.glob(f"results_2*_{era}.csv")) else (f"# Wave 1 tables — {era} era\n" + event_tables(out, era) + "\n" + rank_tables(out, era))
        (out / f"tables_{era}.md").write_text(md)
        print(md)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)
    ap = argparse.ArgumentParser(prog="python -m experiments.screen")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pull"); p.add_argument("--equity", action="store_true"); p.add_argument("--caps", action="store_true")
    p.add_argument("--crypto", action="store_true"); p.add_argument("--no-1h", action="store_true"); p.add_argument("--workers", type=int, default=4)
    p.add_argument("--intraday", action="store_true")
    p.add_argument("--splits", action="store_true"); p.add_argument("--budget-hours", type=float, default=None)
    p.set_defaults(fn=cmd_pull)
    p = sub.add_parser("regress"); p.add_argument("--v1-results", default=None); p.add_argument("--universe", default="all")
    p.add_argument("--wave1-rank", default=None, help="wave-1 result dir: reproduce 1d / 1e through the unchanged crypto rank path")
    p.add_argument("--atol", type=float, default=5e-7); p.add_argument("--out", default=None); p.set_defaults(fn=cmd_regress)
    p = sub.add_parser("run"); p.add_argument("--signal", default=None); p.add_argument("--universe", default="all")
    p.add_argument("--era", default="dev", choices=["dev", "confirm"]); p.add_argument("--out", default=None)
    p.add_argument("--variant", default=None, help="wave 2: comma list of v1,v2,v3 (default all three)")
    p.add_argument("--floor", default=None, choices=["raw_close"], help="wave 2: USD 2 floor diagnostic on raw_close")
    p.add_argument("--proof", nargs=2, metavar=("START", "END"), default=None, help="wave 2: rebalance dates and fills in the window, no scores")
    p.add_argument("--draws", type=int, default=engine.RANDOM_DRAWS)
    p.set_defaults(fn=cmd_run)
    p = sub.add_parser("movers"); p.add_argument("--universe", default="all"); p.add_argument("--era", default="dev", choices=["dev"])
    p.add_argument("--out", default=None); p.set_defaults(fn=cmd_movers)
    p = sub.add_parser("autopsy"); p.add_argument("--lifts", required=True); p.add_argument("--era", default="dev", choices=["dev", "confirm"])
    p.add_argument("--only", default=None, help="comma list of rule names (confirm era: only the rules that cleared dev)")
    p.add_argument("--universe", default=None); p.add_argument("--out", default=None); p.set_defaults(fn=cmd_autopsy)
    p = sub.add_parser("tables"); p.add_argument("--out", default=None); p.set_defaults(fn=cmd_tables)
    p = sub.add_parser("ledger"); p.add_argument("--out", default=None); p.add_argument("--prereg", required=True)
    p.add_argument("--date", default=str(pd.Timestamp.utcnow().date())); p.add_argument("--entry", default="2026-10-01-wave-1-screen.md")
    p.set_defaults(fn=cmd_ledger)
    a = ap.parse_args()
    if a.cmd == "run" and not a.signal and not a.proof:
        ap.error("run needs --signal or --proof")
    a.fn(a)

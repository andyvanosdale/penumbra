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


def _out(args) -> Path:
    p = Path(args.out) if args.out else data.roots().processed / "wave1"
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
def cmd_regress(args) -> None:
    """Run the v1 rule through the new data layer on the v1 windows and compare with the original script's results CSV."""
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


def cmd_run(args) -> None:
    out = _out(args)
    names = EVENT_SIGNALS + RANK_SIGNALS if args.signal == "all" else args.signal.split(",")
    lanes = Lanes()
    summaries = []
    t0 = time.time()
    for name in names:
        sig = signals.load(name)
        unis = sig.UNIVERSES if args.universe == "all" else [u for u in args.universe.split(",") if u in sig.UNIVERSES]
        for uni in unis:
            if sig.MODE == "event":
                A, mask, lane = lanes.arrays(uni)
                summaries.append(_run_event(sig, A, mask, lane, uni, args.era, out))
            else:
                A = lanes.crypto()
                summaries.append(_run_rank(sig, A, uni, args.era, out))
    mp = out / f"meta_{args.era}.json"
    meta = json.loads(mp.read_text()) if mp.exists() else {}
    meta.setdefault("lanes", {}).update(lanes.meta())
    meta.setdefault("runs", {})[pd.Timestamp.utcnow().isoformat()] = {"signals": names, "universe": args.universe, "runtime_s": round(time.time() - t0)}
    meta.setdefault("summaries", {}).update({f"{s['signal']}_{s['universe']}": s for s in summaries})
    mp.write_text(json.dumps(meta, indent=2, default=float))
    print(pd.DataFrame(summaries).to_string())


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


def cmd_ledger(args) -> None:
    from experiments.screen import ledger
    out = _out(args)
    dev = json.loads((out / "meta_dev.json").read_text())["summaries"]
    cp = out / "meta_confirm.json"
    conf = json.loads(cp.read_text())["summaries"] if cp.exists() else {}
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
        md = f"# Wave 1 tables — {era} era\n" + event_tables(out, era) + "\n" + rank_tables(out, era)
        (out / f"tables_{era}.md").write_text(md)
        print(md)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)
    ap = argparse.ArgumentParser(prog="python -m experiments.screen")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pull"); p.add_argument("--equity", action="store_true"); p.add_argument("--caps", action="store_true")
    p.add_argument("--crypto", action="store_true"); p.add_argument("--no-1h", action="store_true"); p.add_argument("--workers", type=int, default=4)
    p.add_argument("--intraday", action="store_true")
    p.set_defaults(fn=cmd_pull)
    p = sub.add_parser("regress"); p.add_argument("--v1-results", default=None); p.add_argument("--universe", default="all")
    p.add_argument("--atol", type=float, default=5e-7); p.add_argument("--out", default=None); p.set_defaults(fn=cmd_regress)
    p = sub.add_parser("run"); p.add_argument("--signal", required=True); p.add_argument("--universe", default="all")
    p.add_argument("--era", default="dev", choices=["dev", "confirm"]); p.add_argument("--out", default=None); p.set_defaults(fn=cmd_run)
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
    a.fn(a)

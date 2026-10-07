"""CLI of the intraday wave (research_log/2026-10-07-intraday-wave.md).

    python -m experiments.screen.intraday_cli build [--months 2021-03] [--workers 8]   # session tables from the 5-minute cache
    python -m experiments.screen.intraday_cli proof --month 2021-03                    # small-month summary (no signal scored)
    python -m experiments.screen.intraday_cli run --signal all|i1,i2-up,... --universe all|smallcap,uncapped --era dev|confirm --out DIR
    python -m experiments.screen.intraday_cli autopsy --era dev --out DIR [--lifts CSV --only i8-up-...]   # i8 pass 1, then pass 2
    python -m experiments.screen.intraday_cli baselines --era dev --out DIR
    python -m experiments.screen.intraday_cli tables --out DIR
    python -m experiments.screen.intraday_cli ledger --out DIR --prereg COMMIT

Set PENUMBRA_DATA_ROOT (the daily panel and caches live under it) and, if the Alpaca cache is
not at ~/penumbra-data/alpaca, PENUMBRA_ALPACA_ROOT. Results go to --out (default
$PENUMBRA_DATA_ROOT/screen/processed/intraday); trade-level files stay under the raw root.
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

from experiments.screen import data, engine
from experiments.screen import intraday_autopsy as autopsy
from experiments.screen import intraday_data as idata
from experiments.screen import intraday_engine as ieng
from experiments.screen.signals import intraday as isig

log = logging.getLogger("screen.intraday")
EQ_UNIVERSES = ["smallcap", "uncapped"]
DAILY_WINDOW = ("2019-01-01", "2023-12-31")     # 250 sessions of warm-up before the first fill session (2020-08-03)


def _out(args) -> Path:
    p = Path(args.out) if args.out else data.roots().processed / "intraday"
    p.mkdir(parents=True, exist_ok=True)
    return p


def sessions_dir() -> Path:
    p = data.roots().cache / f"intraday_sessions_{idata.PANEL_VERSION}"
    p.mkdir(parents=True, exist_ok=True)
    return p


# ---------------------------------------------------------------- build / proof
def cmd_build(args) -> None:
    months = args.months.split(",") if args.months else None
    t0 = time.time()
    logp = idata.build_session_panel(sessions_dir(), months, workers=args.workers)
    print(logp.to_string() if len(logp) else "nothing to build (all months cached)")
    log.info("build done in %.0fs", time.time() - t0)


def cmd_proof(args) -> None:
    """Small-month proof: the session table of one month, summarized; no signal is scored."""
    out = _out(args)
    idata.build_session_panel(sessions_dir(), [args.month], workers=1)
    df = idata.load_session_panel(sessions_dir(), [args.month])
    by_date = df.groupby("date")
    last_m = by_date["last_m"].max()
    early = last_m[last_m < idata.EARLY_CLOSE_MIN].index
    bars = df["n_rth"]
    summary = {
        "month": args.month, "sessions": int(df["date"].nunique()), "names_with_bars": int(df["symbol"].nunique()),
        "name_sessions": int(len(df)), "early_close_sessions": [str(d.date()) for d in early],
        "bars_per_name_session": {"p10": float(bars.quantile(0.1)), "median": float(bars.median()), "p90": float(bars.quantile(0.9)),
                                   "share_ge_60": float((bars >= idata.FLOOR_BARS).mean()), "share_full_78": float((bars == 78).mean())},
        "names_with_ge_60_bars_every_session": int((df.groupby("symbol")["n_rth"].min() >= idata.FLOOR_BARS).sum()),
        "fill_at_entry_times": {},
    }
    for t in idata.ENTRY_TIMES:
        key = t.replace(":", "")
        late = df[f"late_{key}"]
        summary["fill_at_entry_times"][t] = {"filled_share": float(late.notna().mean()), "mean_late_min": float(late.mean()),
                                             "late_share": float((late.dropna() > 0).mean())}
    summary["c1555_present_share"] = float(df["c1555"].notna().mean())
    summary["c_close_present_share"] = float(df["c_close"].notna().mean())
    summary["o0930_present_share"] = float(df["o0930"].notna().mean())
    (out / f"proof_{args.month}.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


# ---------------------------------------------------------------- arrays
class Arrays:
    def __init__(self):
        self._A = None; self._I = None; self.masks = None

    def load(self):
        if self._A is None:
            t0 = time.time()
            self._A, self.masks = data.equity_arrays(*DAILY_WINDOW)
            log.info("daily arrays %s..%s: %d sessions x %d tickers, %.0fs", *DAILY_WINDOW, len(self._A["cal"]), len(self._A["tickers"]), time.time() - t0)
            panel = idata.load_session_panel(sessions_dir())
            self._I = idata.intraday_arrays(self._A, panel)
            log.info("intraday arrays: %d fill sessions, %d early closes, %.0fs", int(self._I["fill_session"].sum()), int(self._I["early_close"].sum()), time.time() - t0)
        return self._A, self._I

    def meta(self, era_name: str) -> dict:
        A, I = self.load()
        in_era, _ = engine.era_rows(A["cal"], ieng.ERAS[era_name])
        m = {"daily_window": list(DAILY_WINDOW), "sessions": int(len(A["cal"])), "tickers": int(len(A["tickers"])),
             "tickers_with_cap": int(np.sum(~np.isnan(A["cap"]))), "tickers_under_cap": int(self.masks["smallcap"].sum()),
             "era": list(ieng.ERAS[era_name]), "universes": {}, "fill_gaps": {}}
        for uni in EQ_UNIVERSES:
            m["universes"][uni] = idata.universe_stats(I, self.masks[uni], in_era)
            m["fill_gaps"][uni] = idata.fill_gap_stats(I, idata.eligibility(I, self.masks[uni], False), in_era)
        return m


# ---------------------------------------------------------------- run
def _run_one(sig, A, I, mask, universe, era_name, out: Path, raw=None, extra=None) -> dict:
    spec = ieng.IntradaySpec(sig.NAME, sig.DIRECTION, sig.ENTRY, sig.HORIZON, sig.COMPARATOR)
    era = ieng.ERAS[era_name]
    elig = idata.eligibility(I, mask, sig.FLOOR)
    raw = sig.candidates(A, I, elig) if raw is None else raw
    tr = ieng.intraday_trades(A, I, raw, spec, elig, era)
    res = ieng.intraday_report(tr, spec, universe, era_name)
    pool = sig.pool(A, I, elig) if sig.RANK else None
    ctl = ieng.controls(A, I, raw, spec, elig, era, tr, pool)
    tag = f"{sig.NAME}_{universe}_{era_name}"
    res.to_csv(out / f"results_{tag}.csv", index=False)
    (out / f"controls_{tag}.json").write_text(json.dumps(ctl, indent=2, default=float))
    tr.to_parquet(data.roots().raw / f"trades_intraday_{tag}.parquet", index=False)
    head = res[(res["horizon"] == sig.HORIZON) & (res["period"] == "all")].set_index("cost")
    hb = head.loc["base"]
    summary = {"signal": sig.NAME, "universe": universe, "era": era_name, "mode": "intraday", "direction": sig.DIRECTION,
               "entry": sig.ENTRY, "horizon": sig.HORIZON, "floor": sig.FLOOR, "rank": sig.RANK,
               "candidates": int(hb["candidates"]), "trades": int(hb["trades"]), "entry_days": int(hb["entry_days"]),
               "mean_net_base_bps": float(hb["mean_net"] * 1e4), "z_base": float(hb["z"]),
               "mean_net_0_bps": float(head.loc["0", "mean_net"] * 1e4), "z_0": float(head.loc["0", "z"]),
               "mean_net_high_bps": float(head.loc["high", "mean_net"] * 1e4), **ctl}
    if extra:
        summary.update(extra(tr))
    log.info("%s: %s", tag, {k: (round(v, 2) if isinstance(v, float) else v) for k, v in summary.items()})
    return summary


def _save_meta(out: Path, era_name: str, arrays: Arrays, summaries: list[dict], t0: float, what: str) -> None:
    mp = out / f"meta_{era_name}.json"
    meta = json.loads(mp.read_text()) if mp.exists() else {}
    meta["lanes"] = arrays.meta(era_name)
    meta.setdefault("runs", {})[pd.Timestamp.utcnow().isoformat()] = {"what": what, "runtime_s": round(time.time() - t0)}
    meta.setdefault("summaries", {}).update({f"{s['signal']}_{s['universe']}": s for s in summaries})
    mp.write_text(json.dumps(meta, indent=2, default=float))


def cmd_run(args) -> None:
    out = _out(args)
    names = list(isig.INTRADAY) if args.signal == "all" else args.signal.split(",")
    arrays = Arrays()
    A, I = arrays.load()
    summaries, t0 = [], time.time()
    for name in names:
        sig = isig.load(name)
        for uni in (EQ_UNIVERSES if args.universe == "all" else args.universe.split(",")):
            summaries.append(_run_one(sig, A, I, arrays.masks[uni], uni, args.era, out))
    _save_meta(out, args.era, arrays, summaries, t0, f"run {args.signal} {args.universe}")
    print(pd.DataFrame(summaries)[["signal", "universe", "trades", "entry_days", "mean_net_0_bps", "mean_net_base_bps", "z_0", "z_base", "placebo_z_0", "planted_shift"]].to_string())


# ---------------------------------------------------------------- i8
def cmd_autopsy(args) -> None:
    out = _out(args)
    arrays = Arrays()
    A, I = arrays.load()
    era = ieng.ERAS[args.era]
    t0 = time.time()
    if not args.lifts:
        # pass 1: counts and lifts (dev era only), written and committed before pass 2
        assert args.era == "dev", "the lift table is a dev-era object"
        cs, ls = [], []
        for uni in EQ_UNIVERSES:
            univ = A["in_universe"] if arrays.masks[uni] is None else (A["in_universe"] & arrays.masks[uni][None, :])
            cs.append(autopsy.counts(A, univ, era, uni)); ls.append(autopsy.lifts(A, I, univ, era, uni))
        c, l = pd.concat(cs, ignore_index=True), pd.concat(ls, ignore_index=True)
        c.to_csv(out / "i8_counts_dev.csv", index=False); l.to_csv(out / "i8_lifts_dev.csv", index=False)
        md = "# i8 pass 1: one-session movers and intraday lifts (hypothesis material, not a result)\n" + autopsy.counts_markdown(c) + "\n" + autopsy.lifts_markdown(l)
        (out / "i8_movers_dev.md").write_text(md)
        print(md)
        return
    lifts = pd.read_csv(args.lifts)
    selected, summaries = [], []
    only = set(args.only.split(",")) if args.only else None
    for group, direction in autopsy.GROUP_DIRECTION.items():
        feats = autopsy.select_features(lifts, "uncapped", group)
        for fdef in feats:
            selected.append({"selected_on": "uncapped", "group": group, "direction": direction, **fdef, "rule": autopsy.rule_name(group, fdef["feature"])})
        if not feats:
            log.info("i8 %s: no feature with lift >= %.1f", group, autopsy.LIFT_MIN)
        feats = [f for f in feats if only is None or autopsy.rule_name(group, f["feature"]) in only]
        for uni in (EQ_UNIVERSES if not args.universe else args.universe.split(",")):
            mask = arrays.masks[uni]
            univ = A["in_universe"] if mask is None else (A["in_universe"] & mask[None, :])
            elig = idata.eligibility(I, mask, False)
            for fdef in feats:
                name = autopsy.rule_name(group, fdef["feature"])
                sig = isig.IntradaySignal(name, direction, autopsy.ENTRY, autopsy.HORIZON, False, False, lambda A_, I_, e_: None)
                raw = autopsy.rule_matrix(A, I, fdef["feature"], fdef["side"], univ)
                extra = lambda tr, group=group, elig=elig: autopsy.extra_metrics(A, I, tr, elig, era, group)  # noqa: E731
                s = _run_one(sig, A, I, mask, uni, args.era, out, raw=raw, extra=extra)
                s.update({"feature": fdef["feature"], "side": fdef["side"], "selection_lift": fdef["lift"], "group": group})
                summaries.append(s)
    if not args.only:
        pd.DataFrame(selected).to_csv(out / "i8_selected_features.csv", index=False)
    _save_meta(out, args.era, arrays, summaries, t0, "i8 pass 2")
    pd.DataFrame(summaries).to_csv(out / f"i8_summary_{args.era}.csv", index=False)
    print(pd.DataFrame(selected).to_string())
    if summaries:
        print(pd.DataFrame(summaries)[["signal", "universe", "trades", "entry_days", "mean_net_0_bps", "mean_net_base_bps", "z_0", "z_base", "placebo_z_0", "match_rate_per_day", "hit_original_move", "universe_base_rate"]].to_string())


# ---------------------------------------------------------------- daily baselines
def cmd_baselines(args) -> None:
    """Wave 1's 1a / 1b through the wave-1 engine on this era (next-open fill, 1-session horizon) and the daily-bar
    open-to-close / open-to-next-open excess for the i2 and i6 candidate sets."""
    from experiments.screen import signals as wsig
    out = _out(args)
    arrays = Arrays()
    A, I = arrays.load()
    era = ieng.ERAS[args.era]
    rows = []
    for uni in EQ_UNIVERSES:
        mask = arrays.masks[uni]
        for name in ("1a", "1b-5d"):
            sig = wsig.load(name)
            spec = engine.EventSpec(sig.NAME, sig.DIRECTION, 1)
            tr = engine.event_trades(A, sig.candidates(A), spec, mask, era, "next_open")
            for cost in ("0", "base"):
                s = engine.event_summary(tr, 1, cost, spec.sign)
                rows.append({"baseline": f"wave-1 {name} next-open, 1 session (open F to open F+1)", "universe": uni, "cost": cost,
                             "trades": s["trades"], "days": s["entry_days"], "mean_net_bps": s["mean_net"] * 1e4, "z": s["z"]})
        elig = idata.eligibility(I, mask, False)
        for label, raw, direction in (("i2-up candidates, daily open fill", isig.load("i2-up").candidates(A, I, elig), "long"),
                                      ("i2-down candidates, daily open fill", isig.load("i2-down").candidates(A, I, elig), "short"),
                                      ("i6-1a candidates (shock <= -2 on F-1), daily open fill", isig.load("i6-1a-0935").candidates(A, I, elig), "short"),
                                      ("i6-1b candidates (1b on F-1), daily open fill", isig.load("i6-1b-0935").candidates(A, I, elig), "long")):
            b = ieng.daily_baseline(A, raw & I["fill_session"][:, None], direction, elig, era)
            for path, s in b.items():
                rows.append({"baseline": f"{label}, {path.replace('_', ' ')}", "universe": uni, "cost": "0 / base", "trades": s["trades"], "days": s["days"],
                             "mean_net_bps": f"{s['mean_gross_bps']:+.0f} / {s['mean_net_base_bps']:+.0f}", "z": f"{s['z_0']:+.2f} / {s['z_base']:+.2f}"})
    df = pd.DataFrame(rows)
    df.to_csv(out / f"baselines_{args.era}.csv", index=False)
    print(df.to_string())


# ---------------------------------------------------------------- tables
def _fmt_bps(x) -> str:
    return "n/a" if pd.isna(x) else f"{x * 1e4:+.0f}"


def _fmt_z(x) -> str:
    return "n/a" if pd.isna(x) else f"{x:+.2f}"


def tables(out: Path, era: str) -> str:
    lines = []
    meta = json.loads((out / f"meta_{era}.json").read_text())
    for f in sorted(out.glob(f"results_*_{era}.csv")):
        res = pd.read_csv(f, dtype={"cost": str, "period": str, "horizon": str})
        sig, uni = res["signal"].iloc[0], res["universe"].iloc[0]
        H = str(res.loc[res["decision"], "horizon"].iloc[0])
        ctl = json.loads((out / f"controls_{sig}_{uni}_{era}.json").read_text())
        s = meta["summaries"].get(f"{sig}_{uni}", {})
        d = res[(res["horizon"] == H) & (res["period"] == "all")].set_index("cost")
        b = d.loc["base"]
        lines.append(f"\n**{sig} / {uni} / {era} — {res['direction'].iloc[0]}, entry {res['fill'].iloc[0]}, decision exit `{H}`"
                     f"{', floored universe' if s.get('floor') else ''}**\n")
        if "match_rate_per_day" in s:
            lines.append(f"i8 rule on `{s['feature']}` ({s['side']} quintile, selection lift {s['selection_lift']:.2f}): match rate {s['match_rate_per_day']:.1%} per day; "
                         f"{s['hits']} of {s['trades']} trades made the original one-session move ({s['hit_original_move']:.2%}) against a universe base rate of {s['universe_base_rate']:.2%}.\n")
        lines.append("| candidates | unfilled | held | trades | days | " + " | ".join(f"net @{c}" for c in ieng.COST_LEVELS) + " | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |")
        lines.append("|" + "---|" * (11 + len(ieng.COST_LEVELS)))
        lines.append(f"| {int(b['candidates'])} | {ctl['fill_unfilled_share']:.1%} | {int(b['held'])} | {int(b['trades'])} | {int(b['entry_days'])} | "
                     + " | ".join(_fmt_bps(d.loc[c, "mean_net"]) for c in ieng.COST_LEVELS)
                     + f" | {b['hit_rate']:.3f} | {_fmt_bps(b['daymean'])} | {_fmt_bps(b['se'])} | {_fmt_z(b['z'])} | {b['top10_share']:.1%} | {_fmt_z(b['z_wo_top10'])} |")
        lines.append("\nHorizon curve (mean excess per trade, bps; z):")
        lines.append("| exit | trades | gross excess | z @0 | net @base | z @base |")
        lines.append("|---|---|---|---|---|---|")
        for h in ieng.EXITS:
            sel0 = res[(res["horizon"] == h) & (res["period"] == "all") & (res["cost"] == "0")]
            if sel0.empty:
                continue
            r0 = sel0.iloc[0]
            rb = res[(res["horizon"] == h) & (res["period"] == "all") & (res["cost"] == "base")].iloc[0]
            lines.append(f"| {h}{' *' if h == H else ''} | {int(r0['trades'])} | {_fmt_bps(r0['mean_net'])} | {_fmt_z(r0['z'])} | {_fmt_bps(rb['mean_net'])} | {_fmt_z(rb['z'])} |")
        lines.append("\nPer period (decision exit, base cost):")
        lines.append("| period | trades | days | net | z |")
        lines.append("|---|---|---|---|---|")
        for _, r in res[(res["horizon"] == H) & (res["cost"] == "base") & (res["period"] != "all")].iterrows():
            lines.append(f"| {r['period']} | {int(r['trades'])} | {int(r['entry_days'])} | {_fmt_bps(r['mean_net'])} | {_fmt_z(r['z'])} |")
        extra = ""
        if "random_placebo_z_0" in ctl:
            extra = f" Random-slice placebo z @0 {_fmt_z(ctl['random_placebo_z_0'])} on {ctl['random_placebo_trades']} trades."
        lines.append(f"\nControls: placebo (lag 20) z @0 {_fmt_z(ctl['placebo_z_0'])}, @base {_fmt_z(ctl['placebo_z_base'])} on {ctl['placebo_trades']} trades; "
                     f"planted +50 bps z {_fmt_z(ctl['planted_z_0'])} vs actual {_fmt_z(ctl['actual_z_0'])} (shift {_fmt_z(ctl['planted_shift'])}).{extra} "
                     f"Power: {ctl['power_days']} days, day-mean SE {ctl['power_se_bps']:.0f} bps, z = 3 needs {ctl['power_required_net_bps_for_z3']:.0f} bps net per trade. "
                     f"Fills: mean lateness {ctl['fill_mean_late_min']:.1f} min, {ctl['fill_late_share']:.1%} of fills late, {ctl['fill_unfilled_share']:.1%} unfilled.")
    return "\n".join(lines)


def cmd_tables(args) -> None:
    out = _out(args)
    for era in ("dev", "confirm"):
        if not list(out.glob(f"results_*_{era}.csv")):
            continue
        md = f"# Intraday wave tables — {era} era\n" + tables(out, era)
        (out / f"tables_{era}.md").write_text(md)
        print(md)


# ---------------------------------------------------------------- ledger
def interesting(s: dict) -> bool:
    return (s["z_base"] >= 3.0 and s["entry_days"] >= 100 and s["trades"] >= 500
            and s["mean_net_base_bps"] >= 50 and s["mean_net_high_bps"] > 0)


def artifact_free(s: dict, res: pd.DataFrame) -> bool:
    d = res[(res["horizon"] == str(s["horizon"])) & (res["cost"] == "base")].set_index("period")
    sign = np.sign(d.loc["all", "mean_net"])
    ok = (np.sign(d.loc["all", "z_wo_top10"]) == sign and abs(s["placebo_z_0"]) < 2.0
          and np.sign(d.loc["half1", "mean_net"]) == sign and np.sign(d.loc["half2", "mean_net"]) == sign)
    if s.get("rank") and "random_placebo_z_0" in s:
        ok = ok and abs(s["random_placebo_z_0"]) < 2.0
    return bool(ok)


def cmd_ledger(args) -> None:
    from experiments.screen import ledger
    out = _out(args)
    dev = json.loads((out / "meta_dev.json").read_text())["summaries"]
    cp = out / "meta_confirm.json"
    conf = json.loads(cp.read_text())["summaries"] if cp.exists() else {}
    rows = []
    for key, s in dev.items():
        sig = s["signal"]
        if sig not in isig.LEDGERED and not sig.startswith("i8-"):
            continue
        if sig.startswith("i8-"):
            base, variant = "i8", sig[3:]
        elif sig.startswith("i6-"):
            base, variant = sig.rsplit("-", 1)
        else:
            base, variant = (sig.split("-", 1) + ["—"])[:2]
        res = pd.read_csv(out / f"results_{sig}_{s['universe']}_dev.csv", dtype={"cost": str, "period": str, "horizon": str})
        hot = interesting(s)
        verdict = "confirm" if hot else "null"
        cz, cnet = "—", "—"
        if hot and key in conf:
            c = conf[key]
            cz, cnet = f"{c['z_base']:+.2f}", f"{c['mean_net_base_bps']:+.0f} bps"
            if not artifact_free(s, res):
                verdict = "artifact"
            elif np.sign(c["z_base"]) == np.sign(s["z_base"]) and c["z_base"] >= 1.5:
                verdict = "graduate"
            else:
                verdict = "fails confirm"
        rows.append({"date": args.date, "signal": base, "variant": variant, "universe": s["universe"], "pre_reg_commit": args.prereg,
                     "mode": f"intraday {s['direction']} {s['entry']}", "decision_horizon": s["horizon"],
                     "dev_z": f"{s['z_base']:+.2f}", "dev_mean_net": f"{s['mean_net_base_bps']:+.0f} bps", "dev_n": f"{s['trades']} / {s['entry_days']}",
                     "confirm_z": cz, "confirm_mean_net": cnet, "verdict": verdict, "entry": args.entry})
    df = ledger.upsert(rows)
    print(df.to_string())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)
    ap = argparse.ArgumentParser(prog="python -m experiments.screen.intraday_cli")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("build"); p.add_argument("--months", default=None); p.add_argument("--workers", type=int, default=8); p.set_defaults(fn=cmd_build)
    p = sub.add_parser("proof"); p.add_argument("--month", default="2021-03"); p.add_argument("--out", default=None); p.set_defaults(fn=cmd_proof)
    p = sub.add_parser("run"); p.add_argument("--signal", required=True); p.add_argument("--universe", default="all")
    p.add_argument("--era", default="dev", choices=["dev", "confirm"]); p.add_argument("--out", default=None); p.set_defaults(fn=cmd_run)
    p = sub.add_parser("autopsy"); p.add_argument("--lifts", default=None); p.add_argument("--era", default="dev", choices=["dev", "confirm"])
    p.add_argument("--only", default=None); p.add_argument("--universe", default=None); p.add_argument("--out", default=None); p.set_defaults(fn=cmd_autopsy)
    p = sub.add_parser("baselines"); p.add_argument("--era", default="dev", choices=["dev", "confirm"]); p.add_argument("--out", default=None); p.set_defaults(fn=cmd_baselines)
    p = sub.add_parser("tables"); p.add_argument("--out", default=None); p.set_defaults(fn=cmd_tables)
    p = sub.add_parser("ledger"); p.add_argument("--out", default=None); p.add_argument("--prereg", required=True)
    p.add_argument("--date", default=str(pd.Timestamp.utcnow().date())); p.add_argument("--entry", default="2026-10-07-intraday-wave.md")
    p.set_defaults(fn=cmd_ledger)
    a = ap.parse_args()
    a.fn(a)

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

from experiments.screen import data, engine, movers, signals, v1rule

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


# ---------------------------------------------------------------- arrays per lane (built once)
class Lanes:
    def __init__(self, eq_window=None, cr_window=None):
        self._eq = None; self._cr = None
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
            self._cr = data.crypto_arrays(*self.cr_window)
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
    lanes = Lanes(("2015-01-01", "2023-12-31"), ("2018-01-01", "2022-12-31"))
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
def _run_event(sig, A, mask, lane, universe, era_name, out: Path) -> dict:
    spec = engine.EventSpec(sig.NAME, sig.DIRECTION, sig.HORIZON)
    era = engine.ERAS[lane][era_name]
    raw = sig.candidates(A)
    trades = {fill: engine.event_trades(A, raw, spec, mask, era, fill) for fill in ("next_open", "close", "next_close")}
    res = engine.event_report(trades, spec, lane, era_name, universe)
    ctl = engine.event_controls(A, raw, spec, mask, era, trades["next_open"])
    tag = f"{sig.NAME}_{universe}_{era_name}"
    res.to_csv(out / f"results_{tag}.csv", index=False)
    (out / f"controls_{tag}.json").write_text(json.dumps(ctl, indent=2, default=float))
    pd.concat(trades.values()).to_parquet(data.roots().raw / f"trades_wave1_{tag}.parquet", index=False)
    head = res[(res["fill"] == "next_open") & (res["horizon"] == sig.HORIZON) & (res["period"] == "all")].set_index("cost")
    hb = head.loc["base"]
    summary = {"signal": sig.NAME, "universe": universe, "era": era_name, "mode": "event", "direction": sig.DIRECTION,
               "horizon": sig.HORIZON, "trades": int(hb["trades"]), "entry_days": int(hb["entry_days"]),
               "mean_net_base_bps": float(hb["mean_net"] * 1e4), "z_base": float(hb["z"]),
               "mean_net_0_bps": float(head.loc["0", "mean_net"] * 1e4), "z_0": float(head.loc["0", "z"]),
               "mean_net_high_bps": float(head.loc["high", "mean_net"] * 1e4), **ctl}
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
        res = pd.read_csv(f, dtype={"cost": str, "period": str})
        if "fill" not in res.columns:
            continue
        sig, uni = res["signal"].iloc[0], res["universe"].iloc[0]
        lane = res["lane"].iloc[0]
        H = int(res.loc[res["decision"], "horizon"].iloc[0])
        ctl = json.loads((out / f"controls_{sig}_{uni}_{era}.json").read_text())
        no = res[(res["fill"] == "next_open")]
        d = no[(no["horizon"] == H) & (no["period"] == "all")].set_index("cost")
        levels = engine.COST_LEVELS[lane]
        lines.append(f"\n**{sig} / {uni} / {era} — direction {res['direction'].iloc[0] if 'direction' in res else ''}, decision horizon {H} sessions, next-open fill**\n")
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
        for h in engine.HORIZONS:
            r0 = no[(no["horizon"] == h) & (no["period"] == "all") & (no["cost"] == "0")].iloc[0]
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
        res = pd.read_csv(f, dtype={"cost": str, "period": str})
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
    p.set_defaults(fn=cmd_pull)
    p = sub.add_parser("regress"); p.add_argument("--v1-results", default=None); p.add_argument("--universe", default="all")
    p.add_argument("--atol", type=float, default=5e-7); p.add_argument("--out", default=None); p.set_defaults(fn=cmd_regress)
    p = sub.add_parser("run"); p.add_argument("--signal", required=True); p.add_argument("--universe", default="all")
    p.add_argument("--era", default="dev", choices=["dev", "confirm"]); p.add_argument("--out", default=None); p.set_defaults(fn=cmd_run)
    p = sub.add_parser("movers"); p.add_argument("--universe", default="all"); p.add_argument("--era", default="dev", choices=["dev"])
    p.add_argument("--out", default=None); p.set_defaults(fn=cmd_movers)
    p = sub.add_parser("tables"); p.add_argument("--out", default=None); p.set_defaults(fn=cmd_tables)
    a = ap.parse_args()
    a.fn(a)

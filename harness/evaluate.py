"""Evaluator (plan §3.5 / §6.6).

Produces the standard report and the two baselines every run must be compared
against:

  * Random entry with the SAME number of trades (the key baseline).
  * Buy-and-hold the sector (excess vs sector is ~0 by construction; reported
    for completeness and as a sanity check that excess returns are centered).

Required metrics (plan §3.5):
  hit rate, average excess return per signal AFTER costs, signal count,
  max drawdown, and the baseline comparison.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import Optional

import numpy as np
import pandas as pd

from harness.backtest import BacktestResult
from harness.costs import CostModel, DEFAULT_COSTS


@dataclass
class Metrics:
    signal_count: int
    hit_rate: float                  # fraction of signals with positive net excess
    label_hit_rate: float            # fraction of signals whose binary label == 1
    avg_excess_gross: float          # mean gross excess return per signal
    avg_excess_net: float            # mean excess return per signal AFTER costs
    median_excess_net: float
    max_drawdown: float              # on the cumulative net-excess equity curve
    round_trip_cost: float

    def as_dict(self) -> dict:
        return asdict(self)


def _max_drawdown(returns: np.ndarray) -> float:
    """Max drawdown of the cumulative (additive) equity curve of per-trade returns."""
    if len(returns) == 0:
        return 0.0
    equity = np.cumsum(returns)
    running_max = np.maximum.accumulate(equity)
    drawdown = equity - running_max
    return float(drawdown.min())  # <= 0


def _metrics_from_excess(excess_gross: np.ndarray,
                         labels: Optional[np.ndarray],
                         costs: CostModel) -> Metrics:
    rt = costs.round_trip()
    if len(excess_gross) == 0:
        return Metrics(0, float("nan"), float("nan"), float("nan"),
                       float("nan"), float("nan"), 0.0, rt)
    net = excess_gross - rt
    hit_rate = float((net > 0).mean())
    label_hr = float(labels.mean()) if labels is not None and len(labels) else float("nan")
    return Metrics(
        signal_count=int(len(net)),
        hit_rate=hit_rate,
        label_hit_rate=label_hr,
        avg_excess_gross=float(excess_gross.mean()),
        avg_excess_net=float(net.mean()),
        median_excess_net=float(np.median(net)),
        max_drawdown=_max_drawdown(net),
        round_trip_cost=rt,
    )


def evaluate(result: BacktestResult,
             costs: CostModel = DEFAULT_COSTS,
             seed: int = 999) -> dict:
    """Return strategy metrics, baselines, and a comparison summary."""
    scored = result.all_scored
    if scored is None or scored.empty:
        raise ValueError("no scored rows to evaluate — backtest produced nothing.")

    sig = scored[scored["signal"] == 1]
    strat = _metrics_from_excess(
        sig["excess_return"].to_numpy(float),
        sig["label"].to_numpy(int),
        costs,
    )

    # Baseline 1: random entry, same trade count, drawn from the same scored pool.
    rng = np.random.default_rng(seed)
    n_sig = len(sig)
    pool = scored["excess_return"].to_numpy(float)
    pool_lbl = scored["label"].to_numpy(int)
    n_boot = 500
    rand_net_means, rand_hit_rates = [], []
    rt = costs.round_trip()
    for _ in range(n_boot):
        pick = rng.choice(len(pool), size=min(n_sig, len(pool)), replace=False)
        net = pool[pick] - rt
        rand_net_means.append(net.mean())
        rand_hit_rates.append((net > 0).mean())
    rand_net_means = np.array(rand_net_means)
    random_baseline = {
        "trade_count": int(min(n_sig, len(pool))),
        "avg_excess_net_mean": float(rand_net_means.mean()),
        "avg_excess_net_std": float(rand_net_means.std()),
        "hit_rate_mean": float(np.mean(rand_hit_rates)),
        "bootstrap_iters": n_boot,
    }

    # Baseline 2: buy-and-hold sector => excess vs sector, averaged over all rows.
    buy_hold_sector = {
        "avg_excess_gross_all": float(pool.mean()),
        "note": "excess vs sector is ~0 by construction; sanity check only.",
    }

    # Comparison: how many standard deviations is the strategy from random?
    z = float("nan")
    if random_baseline["avg_excess_net_std"] > 0 and not math.isnan(strat.avg_excess_net):
        z = (strat.avg_excess_net - random_baseline["avg_excess_net_mean"]) / \
            random_baseline["avg_excess_net_std"]

    return {
        "strategy": strat.as_dict(),
        "baseline_random_entry": random_baseline,
        "baseline_buy_hold_sector": buy_hold_sector,
        "comparison": {
            "z_vs_random": z,
            "beats_random_after_costs": bool(
                not math.isnan(strat.avg_excess_net)
                and strat.avg_excess_net > random_baseline["avg_excess_net_mean"]
            ),
        },
        "run": {
            "folds": result.folds,
            "model_backend": result.model_backend,
            "scored_rows": int(len(scored)),
        },
    }


def format_report(report: dict) -> str:
    s = report["strategy"]
    rb = report["baseline_random_entry"]
    c = report["comparison"]
    run = report["run"]
    lines = [
        "=" * 64,
        " PENUMBRA BACKTEST REPORT",
        "=" * 64,
        f" model backend     : {run['model_backend']}",
        f" walk-forward folds: {run['folds']}",
        f" scored (tkr,date) : {run['scored_rows']}",
        "-" * 64,
        " STRATEGY (signal-following, after costs)",
        f"   signal count          : {s['signal_count']}",
        f"   hit rate (net > 0)    : {s['hit_rate']:.4f}",
        f"   label hit rate (y=1)  : {s['label_hit_rate']:.4f}",
        f"   avg excess (gross)    : {s['avg_excess_gross']*100:.4f}%",
        f"   avg excess (net)      : {s['avg_excess_net']*100:.4f}%",
        f"   median excess (net)   : {s['median_excess_net']*100:.4f}%",
        f"   max drawdown          : {s['max_drawdown']*100:.4f}%",
        f"   round-trip cost       : {s['round_trip_cost']*100:.4f}%",
        "-" * 64,
        " BASELINE: random entry, same trade count",
        f"   avg excess (net) mean : {rb['avg_excess_net_mean']*100:.4f}%"
        f"  (sd {rb['avg_excess_net_std']*100:.4f}%, {rb['bootstrap_iters']} iters)",
        f"   hit rate mean         : {rb['hit_rate_mean']:.4f}",
        "-" * 64,
        " COMPARISON",
        f"   z vs random           : {c['z_vs_random']:.3f}",
        f"   beats random (net)    : {c['beats_random_after_costs']}",
        "=" * 64,
    ]
    return "\n".join(lines)

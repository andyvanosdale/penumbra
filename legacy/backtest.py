"""Walk-forward backtest runner (plan §3.5 / §6.2).

Train on a rolling window, predict the next slice, roll forward. This mimics real
deployment and catches strategies that only worked in one regime.

Wiring (the strict interfaces meet here, and ONLY here):
  features.build_features  -> X            (never sees the future)
  labels.Labeler.label     -> y            (the only future-aware call)
  model.LogisticRegression -> predictions
  costs.CostModel          -> applied by the evaluator

Signal rule: cross-sectional top-quantile ranking. On each decision date we rank
the universe by predicted P(outperform) and fire "start to buy" on the top
`signal_quantile` fraction. Ties (e.g. a degenerate constant-probability model,
which is exactly what a useless feature produces) are broken with a *seeded* RNG,
so a meaningless feature degenerates gracefully into random entry — which is
precisely the null we want to observe from an uninformative feature.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from typing import Optional, Sequence

import numpy as np
import pandas as pd

from legacy.features import build_features, features_to_vector, FEATURE_NAMES
from legacy.labels import Labeler
from legacy.model import LogisticRegressionModel
from legacy.store import PITStore


@dataclass
class BacktestConfig:
    tickers: Sequence[str]
    start: str                       # first decision date (inclusive)
    end: str                         # last decision date (inclusive)
    train_days: int = 252            # ~1 trading year
    test_days: int = 63              # ~1 trading quarter
    horizon: int = 5
    threshold: float = 0.02
    signal_quantile: float = 0.20    # fire on the top 20% each day
    seed: int = 12345


@dataclass
class BacktestResult:
    signals: pd.DataFrame            # one row per fired signal
    all_scored: pd.DataFrame         # every (ticker, date) we scored & labeled
    config: BacktestConfig
    model_backend: str = ""
    folds: int = 0
    meta: dict = field(default_factory=dict)


def build_panel(store: PITStore, labeler: Labeler,
                tickers: Sequence[str], dates: Sequence[str]) -> pd.DataFrame:
    """Precompute the (feature, label) panel ONCE over all decision dates.

    Each cell is produced by the same chokepoints used everywhere else —
    build_features (as-of only) and labeler.label (the sole future-aware call) —
    so the point-in-time contract is identical to scoring day-by-day; we simply
    avoid recomputing the same cell on every walk-forward fold.
    """
    records = []
    for d in dates:
        for t in tickers:
            feat = build_features(store, t, d)
            if feat is None:
                continue
            lab = labeler.label(t, d)
            if lab.label is None:        # incomplete forward window -> skip
                continue
            row = {"date": d, "ticker": t,
                   "label": int(lab.label), "excess_return": lab.excess_return}
            for name, val in zip(FEATURE_NAMES, features_to_vector(feat)):
                row[name] = val
            records.append(row)
    cols = ["date", "ticker", "label", "excess_return", *FEATURE_NAMES]
    return pd.DataFrame(records, columns=cols)


def run_backtest(store: PITStore, cfg: BacktestConfig) -> BacktestResult:
    rng = np.random.default_rng(cfg.seed)
    labeler = Labeler(store, horizon=cfg.horizon, threshold=cfg.threshold)

    calendar = store.trading_days(start=cfg.start, end=cfg.end)
    if len(calendar) < cfg.train_days + cfg.test_days:
        raise ValueError(
            f"calendar has {len(calendar)} days; need at least "
            f"{cfg.train_days + cfg.test_days} for one walk-forward fold."
        )

    panel = build_panel(store, labeler, cfg.tickers, calendar)
    by_date = {d: g for d, g in panel.groupby("date")}

    scored_records: list[dict] = []
    backend = ""
    fold = 0
    cursor = cfg.train_days
    while cursor < len(calendar):
        train_dates = calendar[cursor - cfg.train_days: cursor]
        test_dates = calendar[cursor: cursor + cfg.test_days]
        if not test_dates:
            break
        fold += 1

        train = panel[panel["date"].isin(train_dates)]
        if train.empty:
            cursor += cfg.test_days
            continue
        Xtr = train[FEATURE_NAMES].to_numpy(float)
        ytr = train["label"].to_numpy(int)

        model = LogisticRegressionModel()
        model.fit(Xtr, ytr)
        backend = model.backend

        # Score the test slice day by day; rank cross-sectionally.
        for d in test_dates:
            day = by_date.get(d)
            if day is None or day.empty:
                continue
            Xte = day[FEATURE_NAMES].to_numpy(float)
            probs = np.asarray(model.predict_proba(Xte), dtype=float)
            n = len(probs)
            k = max(1, int(round(cfg.signal_quantile * n)))
            # Seeded random tiebreak so constant-prob models -> random selection.
            jitter = rng.random(n) * 1e-9
            order = np.argsort(-(probs + jitter))
            chosen = set(order[:k].tolist())

            for i, (_, r) in enumerate(day.reset_index(drop=True).iterrows()):
                scored_records.append({
                    "date": d, "ticker": r["ticker"], "prob": float(probs[i]),
                    "label": int(r["label"]), "excess_return": r["excess_return"],
                    "signal": 1 if i in chosen else 0, "fold": fold,
                })
        cursor += cfg.test_days

    all_scored = pd.DataFrame(scored_records)
    signals = (all_scored[all_scored["signal"] == 1].reset_index(drop=True)
               if not all_scored.empty else all_scored)
    return BacktestResult(
        signals=signals, all_scored=all_scored, config=cfg,
        model_backend=(backend if fold else ""), folds=fold,
        meta={"calendar_days": len(calendar)},
    )

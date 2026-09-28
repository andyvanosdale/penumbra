"""Penumbra backtest harness.

Five components with strict interfaces (plan §3). Data leakage between
components is the primary failure mode; clean interfaces are the main defense.

  store.py    point-in-time data store          (knowledge_date discipline)
  features.py build_features(ticker, ts)         (NEVER sees the future)
  labels.py   label(ticker, ts)         [QUARANTINED — the only future-aware code]
  model.py    train / predict wrapper
  costs.py    transaction-cost & slippage model
  backtest.py walk-forward runner
  evaluate.py metrics, baselines, reports
"""

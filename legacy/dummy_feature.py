"""Negative-control backtest: a deliberately uninformative "is it Monday" feature.

Runs the harness end-to-end and confirms it reports NO edge — hit rate and average
net excess return indistinguishable from the random-entry baseline. If the harness
finds an "edge" in this useless feature, STOP and find the bug (plan §4).

    python -m legacy.dummy_feature

SUCCESS CRITERION: the strategy sits within a small tolerance of the random-entry
baseline (|z| < Z_TOLERANCE).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from config.env import legacy_data_root
from legacy.eras import DEVELOPMENT
from legacy.universe import TICKERS
from legacy.backtest import BacktestConfig, run_backtest
from legacy.costs import DEFAULT_COSTS
from legacy.evaluate import evaluate, format_report
from legacy.store import PITStore

# Acceptance tolerance: how far the strategy may sit from random and still count
# as "no edge". |z| < 2 ~ within noise; a larger gap is a red flag to audit.
Z_TOLERANCE = 2.0


def main(db_path: str | None = None) -> dict:
    db_path = str(db_path) if db_path else str(legacy_data_root() / "processed" / "pit.sqlite")
    if not Path(db_path).exists():
        sys.exit(f"No store at {db_path}. Run:\n"
                 "  python -m legacy.make_synthetic   # or ingest.pull_prices\n"
                 "  python -m legacy.load_to_store")

    store = PITStore(db_path)
    # Clamp the run to the development era (plan §6.1). Use what the data covers.
    cal = store.trading_days()
    start = max(cal[0], DEVELOPMENT.start.strftime("%Y-%m-%d"))
    end = min(cal[-1], DEVELOPMENT.end.strftime("%Y-%m-%d"))

    cfg = BacktestConfig(
        tickers=TICKERS, start=start, end=end,
        train_days=252, test_days=63,
        horizon=5, threshold=0.02, signal_quantile=0.20, seed=12345,
    )
    print(f"negative control | dev era {start} -> {end} | {len(TICKERS)} tickers")
    result = run_backtest(store, cfg)
    report = evaluate(result, costs=DEFAULT_COSTS)
    store.close()

    print(format_report(report))

    z = report["comparison"]["z_vs_random"]
    passed = (z == z) and abs(z) < Z_TOLERANCE   # z==z guards against NaN
    verdict = "PASS — no edge detected (as required)" if passed else \
        "FAIL — apparent edge in a useless feature; AUDIT FOR LEAKAGE"
    print(f"\nVERDICT: {verdict}  (|z|={abs(z):.3f} vs tol {Z_TOLERANCE})")

    report["passed"] = bool(passed)
    out = legacy_data_root() / "processed" / "dummy_feature_report.json"
    out.write_text(json.dumps(report, indent=2))
    print(f"Report written: {out}")
    return report


if __name__ == "__main__":
    # Optional positional arg overrides the store path (default: $PENUMBRA_DATA_ROOT/legacy/processed/pit.sqlite).
    db = sys.argv[1] if len(sys.argv) > 1 else None
    r = main(db)
    sys.exit(0 if r.get("passed") else 1)

"""Load a raw snapshot into the point-in-time store (plan §10.3).

Builds the as-of-aware price table: every row gets a knowledge_date. For a daily
OHLCV bar, knowledge_date = the bar's own date (a bar is knowable at its close).

    python -m ingest.load_to_store                      # newest snapshot -> default db
    python -m ingest.load_to_store --raw <path> --db <path>

Reads .parquet (real pulls) or .csv (synthetic) — whichever snapshot is newest
unless --raw is given.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from harness.store import PITStore

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
DEFAULT_DB = ROOT / "data" / "processed" / "pit.sqlite"


def newest_snapshot() -> Path:
    candidates = sorted(
        list(RAW_DIR.glob("*prices_*.parquet")) + list(RAW_DIR.glob("*prices_*.csv")),
        key=lambda p: p.stat().st_mtime,
    )
    if not candidates:
        sys.exit("No snapshot found in data/raw/. Run ingest/make_synthetic.py "
                 "or ingest/pull_prices.py first.")
    return candidates[-1]


def load_raw(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", default=None, help="path to a snapshot file")
    ap.add_argument("--db", default=str(DEFAULT_DB))
    args = ap.parse_args()

    raw_path = Path(args.raw) if args.raw else newest_snapshot()
    df = load_raw(raw_path)
    print(f"Loading {raw_path.name}  ({len(df)} rows)")

    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    # Fresh build: remove an existing db so loads are reproducible.
    if Path(args.db).exists():
        Path(args.db).unlink()

    store = PITStore(args.db)
    n = store.write_prices(df)
    print(f"Wrote {n} rows into {args.db}")
    print(f"  store row count: {store.count()}")
    print(f"  trading days   : {len(store.trading_days())}")
    store.close()


if __name__ == "__main__":
    main()

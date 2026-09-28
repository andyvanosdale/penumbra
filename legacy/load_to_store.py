"""Load a raw snapshot into the point-in-time store (plan §10.3).

Builds the as-of-aware price table: every row gets a knowledge_date. For a daily
OHLCV bar, knowledge_date = the bar's own date (a bar is knowable at its close).

    python -m legacy.load_to_store                      # newest snapshot -> default db
    python -m legacy.load_to_store --raw <path> --db <path>

Reads .parquet (real pulls) or .csv (synthetic) — whichever snapshot is newest
unless --raw is given.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from config.env import legacy_data_root
from legacy.store import PITStore


def newest_snapshot(raw_dir: Path) -> Path:
    candidates = sorted(
        list(raw_dir.glob("*prices_*.parquet")) + list(raw_dir.glob("*prices_*.csv")),
        key=lambda p: p.stat().st_mtime,
    )
    if not candidates:
        sys.exit(f"No snapshot found in {raw_dir}. Run legacy.make_synthetic "
                 "or legacy.pull_prices first.")
    return candidates[-1]


def load_raw(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", default=None, help="path to a snapshot file")
    ap.add_argument("--db", default=None, help="path to the SQLite db")
    args = ap.parse_args()

    raw_path = Path(args.raw) if args.raw else newest_snapshot(legacy_data_root() / "raw")
    df = load_raw(raw_path)
    print(f"Loading {raw_path.name}  ({len(df)} rows)")

    db_path = Path(args.db) if args.db else legacy_data_root() / "processed" / "pit.sqlite"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # Fresh build: remove an existing db so loads are reproducible.
    if db_path.exists():
        db_path.unlink()

    store = PITStore(str(db_path))
    n = store.write_prices(df)
    print(f"Wrote {n} rows into {db_path}")
    print(f"  store row count: {store.count()}")
    print(f"  trading days   : {len(store.trading_days())}")
    store.close()


if __name__ == "__main__":
    main()

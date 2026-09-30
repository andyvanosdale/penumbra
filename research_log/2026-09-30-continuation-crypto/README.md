Result files of screen 2 (issue 39), written by `experiments/screen_continuation_crypto.py run`
to `$PENUMBRA_DATA_ROOT/screen/processed/continuation/` and copied here unchanged. The
research-log entry `../2026-09-30-continuation-crypto.md` reads from them.

- `tables.md`: headline, per-year, regime and decision-rule tables.
- `results.csv`: one row per run × cost variant (the headline table's source, with the
  candidate, fill, skip and cost diagnostics).
- `per_year.csv`, `regime.csv`: the per-year and regime tables.
- `meta.json`: data coverage, the spot pairs without a perpetual, the rule verdicts, the
  extreme trades and the top-10 entry days.
- `spot_to_perp_map.csv`: the spot → USD-M perpetual map (leading numeric multiplier stripped).

Raw klines, funding and the per-trade parquet stay out of git (`$PENUMBRA_DATA_ROOT/screen/raw/`).

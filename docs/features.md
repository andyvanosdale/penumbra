# Features

The feature builder: `harness/features.py`. Spec: `spec/04-features-and-labels.md`
(Conventions, Features, Flags). Also `spec/02` (Trading calendars, Store
adjustment) and `spec/01` (Eligibility, for `sector_rel_ret_1`'s "eligible
equities"). Contract: `docs/architecture.md`, "Adjustment". Issue 8.

`build_features(reader, lane, dates, symbols=None, eligible=None)` returns a
DataFrame keyed by `(lane, market, symbol, date)`, one column per feature and
flag, for every date in `dates` (which must be lane trading days) and every
symbol in `symbols` (`None` = every symbol the store carries for the lane's
market in the window). It reads only through `harness.store.reader.AsOfReader`;
it never imports `harness.store.oracle` or `harness.labels`
(`tests/test_architecture.py`).

## Conventions, as implemented

- A window of *n* days ends at and includes D unless stated otherwise. "Days" are
  the lane's trading sessions (`harness.store.calendar_for_lane`: `nyse` for
  `smallcap`/`discovered`, `utc` for `crypto`), not calendar days.
- **Missing bar, no forward-fill.** A symbol's bars are reindexed onto the lane's
  session calendar before any window is computed, so a session with no bar is a
  `NaN` row, never carried forward. Every rolling feature requires every session
  in its window to have a value (`harness.features._roll`,
  `_midrank_pctl`); one missing session makes the feature `NaN` at every D whose
  window contains it, not just at the missing session itself.
- **Standard deviations are sample (n - 1)**: `pandas.Series.std(ddof=1)`
  (the pandas default) everywhere a feature definition calls for one.
- **Adjustment: one panel, read once.** Price features use the
  split-and-dividend-adjusted series (`AsOfReader.panel(..., adjust="split_div")`).
  Per `docs/architecture.md` ("Adjustment", consequence 1), the builder reads that
  panel exactly once per call, adjusted as of the panel's last date (`max(dates)`),
  rather than once per D. This is valid because every feature below is a ratio, a
  log return, or a rank: for any D inside the panel, the panel-end-adjusted series
  equals the as-of-D-adjusted series times one constant on every bar dated on or
  before D, and every feature here is invariant to that constant.
  `tests/features/test_scale_invariance.py` is the proof: it multiplies every
  price (and its dollar volume) by an arbitrary constant and asserts every
  feature is unchanged. In-memory, only bars dated on or before each D are ever
  used to compute that D's features (matching an as-of-D bars read exactly,
  since a daily bar's `available_at` equals its date), and events are re-filtered
  to `available_at <= D` from the single windowed events read before use, so no
  feature ever reads a row with `available_at` after D
  (`tests/features/test_asof_future_rows.py`,
  `tests/features/test_feature_invariance.py`).
- **Annualization**: sqrt(252) for the `nyse` calendar, sqrt(365) for `utc`
  (`harness.features.ANNUALIZATION`).
- **Two kinds of "return".** The Conventions section defines both: "today's
  return" is the simple return, close_D / close_{D-1} - 1; the 1-day *log*
  return is `ret_1`. `sector_rel_ret_1` and `ret_per_vol` use today's (simple)
  return, per the features table; every other return-shaped feature uses the log
  return.

## Features

| Feature | Formula as implemented | Window | Notes |
| --- | --- | --- | --- |
| `ret_1` | `ln(close_D / close_{D-1})` | 2 sessions (D-1, D) | |
| `rvol_20` | sample std of the 20 log returns ending D, × sqrt(annualization) | 21 bars (D-20..D) | |
| `rvol_20_prev` | `rvol_20` evaluated at D-1 | 21 bars (D-21..D-1) | Implemented as `rvol_20.shift(1)` on the session-indexed series — the same rolling values, one session later |
| `shock` | `ret_1 / (rvol_20_prev / sqrt(annualization))` | as above | The denominator is the *daily* (de-annualized) sample std over the 20 days ending D-1; D's own return never enters it |
| `zscore_20` | `(close_D - mean_20) / std_20` of close | 20 bars (D-19..D) | |
| `vol_pctl_250` | midrank of D's dollar volume among the 250 values ending D, ÷ 250 | 250 bars (D-249..D) | Dollar volume is unadjusted close × unadjusted volume (equities) or kline quote volume (crypto) — the store's `dollar_volume` column, untouched by adjustment. **Ties**: the midrank convention, `rank(x) = count(v < x) + (count(v == x) + 1) / 2`, same as `pandas.Series.rank(method="average")`. A value tied for the top of its window does not score a full 1.0 alone; all-tied gives every session `(n+1)/(2n)` |
| `sector_rel_ret_1` | today's (simple) return − equal-weight average today's return of eligible equities in the same sector, excluding the name | today's return, plus one cross-section per D | Equities only. "Eligible" is the `eligible` parameter (a DataFrame with `date`, `symbol` columns, the shape `AsOfReader.lane_membership` returns); the sector is `AsOfReader.symbols(...)["sector"]`, the store's allowlisted non-point-in-time input. `NaN` when the name's sector has no other eligible member with a valid return that day. See "The `eligible` parameter" below |
| `dist_52w_low` | `close_D / min(low over 250 days ending D) - 1` | 250 bars | |
| `dd_from_20d_high` | `close_D / max(high over 20 days ending D) - 1` | 20 bars | |
| `close_loc` | `(close_D - low_D) / (high_D - low_D)`, `0.5` when `high_D == low_D` | 1 bar | `NaN` if the bar itself is missing |
| `gap` | `open_D / close_{D-1} - 1` | 2 sessions | |
| `range_rel_20` | `(high_D - low_D) / mean(high - low over 20 days ending D)` | 20 bars | |
| `ret_per_vol` | today's (simple) return `/ (vol_pctl_250 + 0.01)` | as `vol_pctl_250` | |
| `close_loc_chg_2` | `close_loc_D - close_loc_{D-2}` | 3 sessions (D-2, D-1, D) | D-1's bar is not otherwise used, but a missing D-1 does not itself null the feature — only a missing D or D-2 bar does |

## Flags

| Flag | Lane | Formula as implemented |
| --- | --- | --- |
| `filing_2d` | equities | `True` iff an EVENTS row for the symbol has `available_at` equal to the lane trading session at D-1 or D-2, for any `eventcodes` value. `available_at` is used exactly as the store holds it (the loader already sets it to the next NYSE session after the filing, or the filing date itself for known-pre-16:00 filings); it is never recomputed from the filing date here |

For the `crypto` lane, `filing_2d` and `sector_rel_ret_1` are `NaN` (nullable
`boolean` for `filing_2d`) rather than omitted, so `build_features`'s output has
the same columns for every lane.

## The `eligible` parameter

`sector_rel_ret_1` needs the point-in-time universe of "eligible equities"
(spec/01 Eligibility), which is issue 6's universe builder, being built in
parallel. `build_features` takes it as `eligible`: a DataFrame with `date` and
`symbol` columns naming every eligible name on each date (the shape
`AsOfReader.lane_membership(...)` already returns, so the universe builder's
output can be passed through directly once it exists).

When `eligible` is omitted (`None`), the builder falls back to "every symbol
with a valid (non-`NaN`) simple return on D" as the eligible set — a local
stand-in, **not** the spec/01 screen, since issue 6 is not merged yet. This is
flagged in the PR description; switch callers to the real universe as soon as
issue 6 lands. The fallback only affects `sector_rel_ret_1`; every other
feature is unaffected by `eligible`.

"Eligible" gates who is *averaged* into the sector peer group, not whether a
name gets a `sector_rel_ret_1` value at all: a name outside the eligible set
(e.g. `discovered`-only names, or any name when `eligible` is omitted for a
symbol the fallback excludes) still gets a value, computed against its
eligible peers; it is excluded from the average only when it is itself one of
them. This reads the spec's "excluding the name itself" as describing which
name to drop from an otherwise eligible-only average, not as a precondition
that the name itself must be eligible — flagged for the PA alongside the
`eligible` stand-in above, since neither is a locked parameter.

## Lookback and history requirements

The builder fetches one calendar read and one `panel` bars read per call,
spanning from `LOOKBACK_SESSIONS` (250) sessions before the earliest requested
date through the latest requested date. A name without 250 sessions of prior
history in the store is not an error: `vol_pctl_250` and `dist_52w_low` are
simply `NaN` at every D where the window isn't full, consistent with the
missing-bar rule above.

`VOL_PCTL_WINDOW` and `DIST_52W_WINDOW` are both `config.params.SPEC01.equities_full_history_days`
(250) rather than a second `250` literal: it is the same number spec/01 fixes
as the equity full-history requirement, chosen precisely so that an eligible
equity's feature windows are always full (spec/01 Eligibility, "so every
feature window is full"). `config/params.py` has no locked constant for the
20-day feature windows or for the sqrt(252)/sqrt(365) annualization — those
20s in spec/01/06/07 govern unrelated things (the liquidity/vol floors, the
cost spread window, the regime-split window), not this table — so
`RVOL_WINDOW`, `ZSCORE_WINDOW`, `DD_20D_WINDOW`, `RANGE_REL_WINDOW` and
`ANNUALIZATION` stay as `harness/features.py`'s own constants, read directly
off spec/04's table.

## Testing

`tests/features/`:

- One hand-checked fixture per feature (`test_returns_and_vol.py`,
  `test_zscore_and_vol_pctl.py`, `test_price_levels.py`,
  `test_sector_rel_ret_1.py`, `test_filing_2d.py`), each computing its expected
  value independently of `harness/features.py` (plain arithmetic, `math.log`,
  `statistics.stdev`, or hand-worked fractions), never by re-deriving it with the
  same rolling code under test.
  - `test_shock_uses_the_window_ending_D_minus_1_not_D` is the fixture the issue
    requires: a real, non-zero baseline volatility over the 20 days before D,
    then a large one-day move on D. It asserts the correct value (using the
    prior-window denominator) and that this differs meaningfully from what
    `shock` would be if the window wrongly included D itself.
- `test_scale_invariance.py`: multiplies every price and its dollar volume by a
  constant and asserts every feature at D is unchanged (`docs/architecture.md`
  "Adjustment", consequence 1).
- `test_asof_future_rows.py` (marked `leakage`): builds one store with future
  bars and a future EVENTS row alongside the historical data, and one without
  them, and asserts `build_features` at D is identical between the two — the
  as-of read check (spec/02 Leakage tests, first bullet): no feature reads a
  row with `available_at` after D.
- `test_feature_invariance.py` (marked `leakage`): calls issue 18's
  `harness.testing.assert_feature_invariance` directly against
  `build_features`, over a synthetic store built per-sample from
  `tests/invariance/_synth.py`'s panel generator (the same generator issue
  18's own reference-feature tests use). Every value `build_features` gives at
  D must be unchanged when the data dated after D is deleted, scaled,
  shock-scaled or shuffled (spec/02 Leakage tests, second bullet).
- `test_crypto_lane.py`: the same `ret_1`/`rvol_20_prev` check on the `crypto`
  lane, to exercise the `utc` calendar (every day is a session) and the
  sqrt(365) annualization independently of the equity-lane tests.

`tests/fixtures/features.py` is a new fixture module (`build_equity_store`,
`build_crypto_store`) rather than an extension of `tests/fixtures/store.py`, per
the issue 8 brief; it builds small, purpose-built panels so each test's expected
value is easy to check by hand.

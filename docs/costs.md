# Costs

The per-lane cost model: `harness/costs.py`. Spec: `spec/06-costs.md` (the cost
model), `spec/01-lanes-and-universe.md` (the participation denominator), `spec/04`
(Conventions: adjusted series, trading-day/annualization conventions). Contract:
`docs/architecture.md`, "Packages and ownership" (issue 7). Locked parameters:
`config/params.py` (`SPEC06_EQUITY`, `SPEC06_CRYPTO`, `STRESS_CASES`).

Costs are applied inside the backtester, on both legs of every fill, before any
result is written (spec/06). This module computes the modeled cost of one leg; it
has no opinion about when a leg happens or which price it fills at (the strategy
rule and the labeler decide that).

## Calibration status: unverified

The Abdi-Ranaldo estimator here is implemented exactly as spec/06 states it (two-day
products of close-to-midrange log distances, negatives zeroed, 20-session mean ending
D-1, square root, half per side) and matches the reference implementation the
free-data screen used independently (issue #15;
`research_log/2026-09-28-free-data-screen.md`). That screen found the estimate runs
large on real names: a median of 2.35% on the equity screen universe (60% median
annualized vol) and a mean of 3.4% round trip on candidates after the 2x entry
multiplier, an order of magnitude above plausible quoted spreads for that vol level;
crypto runs larger still (mean 6.0% round trip). The 0.25% equity floor rarely binds
at that vol level (0.02% of candidates in the screen), so it does not mask the effect.

This is consistent with this module's own estimator test
(`tests/costs/test_estimator.py`): spec/06's negatives-zeroed-before-averaging rule
biases the mean upward (Jensen's inequality on `max(0, X)`) once daily volatility
swamps the spread signal, and 60%-vol small-cap names are exactly that regime.

**No rule may be costed with this model until a sample of actually-quoted spreads
validates it against real quotes.** This is a calibration question, not an
implementation bug, and is out of this issue's scope to resolve; the estimator is
not tuned here. Flagged for the PM/PA to decide how to proceed (a different
estimator, a vol-conditional adjustment, or an empirically-fit floor) before any
lane's results are read as evidence rather than as a harness smoke test.

## Interface

- `CostInputs`: everything one leg's cost depends on, all read as of the signal day
  D: `half_spread_est`, `close_unadj_d`, `rvol_20_d`, `median_dollar_volume` and,
  for `crypto` only, `top20_by_quote_volume`.
- `CostModel(lane, stress=None, multiplier=1.0).leg(inputs, leg_type, order_notional)`
  returns a `LegCost` (`spread`, `slippage`, `fee`, `floor_bound`, and a `total`
  property that sums the three components).
- `cost_inputs(reader, lane, symbols, dates)` builds `CostInputs` rows from the
  point-in-time store, one row per (symbol, D), reading nothing after D.
- `CostModel.breakeven_multiple(net_fn)` root-finds the cost multiplier at which
  `net_fn(multiplier)` is zero (the evaluator supplies `net_fn`, issue 11).
- `cost_report(trades)` computes the per-lane, per-year reporting the evaluator
  reads (below).

## The estimator

`abdi_ranaldo_spread(high, low, close)` implements Abdi, B. F. and Ranaldo, A.
(2017), "A Simple Estimation of Bid-Ask Spreads from Daily Close, High, and Low
Prices", *Review of Financial Studies* 30(12), 4437-4480. With the log mid-range
eta_t = (ln H_t + ln L_t) / 2 and the log close c_t = ln(Close_t):

    S_t^2 = 4 (c_t - eta_t)(c_t - eta_{t+1})

for each pair of consecutive sessions (t, t+1), averaged after zeroing any
negative S_t^2 (spec/06), and the round-trip spread estimate is
s = sqrt(mean(S_t^2)). Every consecutive pair in the input window is used: N
sessions give N-1 two-day estimates.

`cost_inputs` builds the window as the 20 lane sessions immediately before D
(sessions D-20 .. D-1 by session offset, sorted ascending as s_1 .. s_20), pairing
(s_1,s_2), (s_2,s_3), ..., (s_19,s_20) -- 19 estimates from 20 sessions. It reads
the split-and-dividend-adjusted series (`adjust="split_div"`), since a raw split
discontinuity would otherwise look like a spurious two-day spread. `half_spread_est`
is half of `abdi_ranaldo_spread(...)`, unfloored (the floor is applied in
`CostModel.leg`, not here).

## Spread, participation and the entry-leg multipliers

- The entry leg charges the (floored) half-spread at 2x and measures
  participation against 10% of `median_dollar_volume`; exit legs charge 1x and the
  full median (spec/06, `SPEC06_EQUITY`/`SPEC06_CRYPTO`
  `entry_spread_multiplier`/`entry_participation_base`).
- Slippage per side: `0.5 * sigma_d * sqrt(participation)`, `sigma_d = rvol_20_d /
  sqrt(252)` for equities or `/ sqrt(365)` for crypto (spec/02 "Annualization"),
  `participation = order_notional / (median_dollar_volume * participation_base)`.
- Fees: 0 for equities; 0.10% taker per side for crypto (`SPEC06_CRYPTO.
  taker_fee_per_side`), charged on every leg regardless of entry/exit.

## Floors

Equities: `max(0.25%, one tick / close_unadj_d)`, tick = USD 0.01
(`SPEC06_EQUITY.tick_size_usd`). Crypto: 0.05% when `top20_by_quote_volume`, else
0.15% (`SPEC06_CRYPTO.spread_floor_top_tier_pct` / `spread_floor_other_pct`).
`top20_by_quote_volume` ranks every `binance_spot` symbol by trailing 30-day quote
volume as of D (spec/06; the 30-day window is `SPEC01.
crypto_volume_ranking_window_days`, the same window spec/01 uses for the crypto
universe rank) and is `None` for equity lanes.

**Flagged spec ambiguity (see the PR description for the full reasoning, and the
docstring at the top of `harness/costs.py`):** spec/06 says "the estimate is
floored at max(...)" without saying whether "the estimate" is the half-spread (the
per-side number the table's "Spread (per side)" column is about) or the full
round-trip AR estimate before it is halved. This module floors the half-spread
directly -- the more conservative reading (it can only raise modeled costs) and the
one matching the column's own "per side" framing. The floor is applied before the
entry leg's 2x multiplier, so the entry leg's minimum charge is `2 * floor`, not
`floor`.

## Stress and the breakeven multiple

`STRESS_CASES` (`config/params.py`): `spread_x2` (spread component x2),
`slippage_x2` (slippage x2), `fixed_10bps_per_leg` (10 bps added to every leg's fee
component). `stress.stop_fills_at_low` is exposed on the `StressCase` dataclass but
never read here -- it is the labeler's concern (issue 9), not the cost model's.

`multiplier` (default 1.0) scales every component of every leg uniformly, after
stress is applied. `CostModel.breakeven_multiple(net_fn)` bisects on the multiplier
for the value at which `net_fn(multiplier) == 0`, expanding its search bracket
outward if needed; `net_fn` is the caller's (the evaluator's) business entirely --
this module has no notion of what "net return" means.

## Reading the store: `cost_inputs`

`cost_inputs(reader, lane, symbols, dates)` is the only place this module reads
`harness.store.reader.AsOfReader` (spec/02 Store; `docs/architecture.md`, "Import
rules": the cost model, the universe builder and the feature builder are the three
callers of the as-of reader). For each requested D, it reads the lane's calendar
(`harness.store.calendar_for_lane`) once, up to and including D, and slices three
windows from it:

- the spread/median window (20 sessions ending D-1, for `half_spread_est` and
  `median_dollar_volume`, spec/01: dollar volume is unadjusted, "so that the
  signal day's own volume spike does not qualify a name" -- the same reasoning
  applies to costs);
- the RVOL window (21 sessions ending D inclusive, giving the 20 one-day log
  returns spec/04's `rvol_20` averages);
- for `crypto`, the 30-session ranking window ending D inclusive.

Every store read passes `as_of=D` and an end date of D, so nothing dated after D
is ever fetched -- this is the leakage invariant `tests/costs/
test_cost_inputs_invariance.py` checks via `harness.testing.invariance.
perturbations`. Bars are read with `adjust="split_div"`: within an as-of-D panel, a
bar dated exactly D is unaffected by adjustment (no action can be dated in the
empty interval (D, D]), so `close_unadj_d` is read from the same call rather than a
second `adjust="none"` read.

`cost_inputs` raises rather than guesses when a symbol is missing a bar inside one
of its windows on D (spec/02: a name with a gap in a window is not forward-filled,
it is ineligible on D, so `cost_inputs` should not be called for it), or when fewer
lane sessions are known before D than the windows need.

## Reporting: `cost_report`

`cost_report(trades)` is written against a per-leg trades frame, columns:

| Column | Meaning |
| --- | --- |
| `lane` | The lane the leg belongs to |
| `symbol` | The traded symbol |
| `entry_date` | The trade's signal date D (buckets the leg into a report year) |
| `leg` | A `LegType`: `entry`, `exit_target`, `exit_stop`, `exit_time`, `exit_delist` or `exit_era_end` |
| `notional` | The leg's order notional |
| `spread`, `slippage`, `fee` | The `LegCost` components, as fractions of notional |
| `floor_bound` | Whether the spread floor bound on this leg |

This is spec/06's "each trade records its modeled spread, slippage and fee
separately, per leg" as a long (one-row-per-leg) frame. It returns four frames:

- `cost_distribution`: `describe()` of the per-leg total cost in basis points, by
  (lane, year);
- `floor_bound_share`: the share of legs on which the floor bound, by (lane, year);
- `mean_cost_bps_by_leg`: the mean cost per side in basis points, by (lane, year,
  leg), with `leg` relabeled to `entry`/`target`/`stop`/`time_stop`/`delist`/
  `era_end` (`LEG_REPORT_LABELS`) -- spec/06 names the first four explicitly, the
  last two are reported too for completeness;
- `component_sums`: each component's summed cost in notional currency
  (`spread_cost`, `slippage_cost`, `fee_cost`), by (lane, year). The evaluator
  divides these by its own gross-return sum to get each component's share of gross
  (spec/06); `cost_report` sums, the evaluator divides.

## What is out of scope here

The labeler (issue 9) decides when each leg happens and at what price, including
the stress case's stop-at-the-low rule. The evaluator (issue 11) consumes
`cost_report` and `breakeven_multiple`'s `net_fn` callable. No crypto ingest exists
yet (issue 4 is gated on the pre-build free-data screen), so the crypto branch of
this module -- the tier floor, the taker fee, the sqrt(365) annualization -- is
implemented and tested against synthetic inputs only; `cost_inputs`'s crypto
ranking path is implemented against the same store contract equities use, but is
not exercised against real crypto data.

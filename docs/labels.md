# Labels

The quarantined labeler: `harness/labels.py`, with the as-of entry levels in
`harness/levels.py`. Spec: `spec/04` (Labels), `spec/05` (steps 5–7, Parameters,
Corporate actions during an open position), `spec/03` (Era boundaries), `spec/01`
(Delisting while a position is open), `spec/06` (marketable fills, stress stop at
the low). Contract: `docs/architecture.md` ("Adjustment", consequence 2; "Store";
the import rules). Issue 9; the exit rules are shared with issue 10.

## Quarantine

- `harness/labels.py` is the only module that reads prices after the signal
  date, and it reads them only through `harness.store.oracle.OracleReader`. Every
  read is bounded by the era's last trading day, and none reaches the holdout
  unless the oracle was built with the logged unlock.
- Only `harness/backtest.py` imports the labeler. Labels meet features only there.
- `harness/levels.py` computes the target and the signal day's range from the
  as-of-D store (`AsOfReader`) only. It may not import the oracle or the labeler
  (`tests/test_architecture.py`). The exit-invariance test targets it through a
  real store (`tests/labels/test_levels.py`, marked `leakage`).

## Interface

```python
from harness.levels import entry_levels, hard_stop_level
levels = entry_levels(reader, lane, symbols, D)   # symbol, signal_date, target_level, stop_range

from harness.labels import label, forward_null_counts
labels = label(oracle, candidates, lane, era_last_date, cost_model, stress=None, lot_size=1e-8)
```

`candidates` has one row per candidate: `symbol`, `signal_date` (D),
`target_level` and `stop_range` (D's high − low), both in D's
split-and-dividend-adjusted basis, and `cost_inputs`, the cost model's inputs
object for that candidate (issue 7's `CostInputs`). The backtester builds these
from as-of data. Candidate selection and the no-re-entry rule are issue 10's.

`cost_model` is anything with `leg(inputs, leg_type, order_notional) -> LegCost`
(`CostModelLike` in `labels.py`). The labeler never imports `harness.costs`; the
backtester builds the model, with its stress case and multiplier, and passes it
in. `stress` is a `config.params.StressCase`. The labeler reads only its
`stop_fills_at_low`.

`era_last_date` may be a non-session (the validation era ends on a Sunday). The
boundary the rule uses is the last lane session on or before it.

## Entry (spec/05 step 5)

- Equities fill at the open of the next lane session after D. Crypto fills at
  the open of the 01:00 UTC 1h kline on D+1.
- A candidate is `unfilled`, with a reason, and never carried to a later day,
  when it has:
  - no bar on the fill day: `no_bar_on_fill_day`;
  - D's high equal to its low: `zero_range`;
  - no fill session inside the era: `no_fill_session_in_era`;
  - NaN levels (an incomplete window): `levels_missing`.
- Shares are floor(USD 10,000 / the unadjusted fill price), since sizing uses
  the unadjusted series (spec/02 Store). For crypto, shares are rounded down to
  `lot_size`. `entry_notional` = shares × the unadjusted fill price.
- The hard stop is fill − 1.5 × `stop_range`, in D's basis.

## Exits (spec/05 step 6)

The labeler starts at the first session after the fill session. The fill session
is never an exit session. On each later session with a bar, it checks in this
order:

1. **Hard stop.** If the open ≤ the stop, exit at the open. Otherwise, if the
   low < the stop, exit at the stop, or at the low when `stop_fills_at_low`.
2. **Target.** If the close ≥ the target, exit at the next session's open.
3. **Time stop.** On the 10th session after the fill session that has a bar,
   exit at the next session's open.

The stop wins ties, because it is checked first. A session with no bar
evaluates nothing and doesn't advance the time stop. A pending next-open exit
fills at the next session that has a bar. The fifth consecutive session with no
bar closes the position with the delisting treatment (`no_bar_delist`), dated
that session.

`exit_reason` is one of `stop`, `target`, `time`, `delist`, `no_bar_delist` or
`era_end`. Each maps to a cost leg: `exit_stop`, `exit_target`, `exit_time`,
`exit_delist` (used by both delisting reasons) and `exit_era_end`.

## Delisting (spec/01)

The labeler reads `delisted` events through `OracleReader.listing`. The position
closes on the first session on or after the delisting date. That session's stop
is checked first when it has a bar, and a pending next-open exit fills first.

| Case | Exit price |
| --- | --- |
| `acquisitionby`, `mergerto`, `voluntarydelisting` | the last close |
| `bankruptcyliquidation`, `regulatorydelisting` | 0.45 × the last close on NASDAQ; 0.70 × on NYSE or NYSE American (`NYSEMKT`) |
| any of the above, crypto | the last close |
| a post-delisting price in the store | replaces the haircut (flag `post_delisting_price`) |
| bars stop with no delisting record | held at the last close (flag `held_at_last_close`) |

- The last close is the close of the last bar on or before the delisting date.
- The exchange is the listing row's `exchange`, the exchange at delisting.
- A "post-delisting price" is the close of the first bar dated after the
  delisting date. The store has no dedicated column for it yet (see "Open
  points").
- Conservative readings, flagged on the row:
  - a haircut-class delisting on an exchange the spec doesn't name (NYSEARCA,
    BATS, missing) takes the harsher haircut, 0.45, and is flagged
    `haircut_exchange_unmapped`;
  - a delisting whose reason is none of the five spec/01 names takes the
    haircut treatment and is flagged `delist_reason_unknown`.
- A position whose bars stop takes the recorded treatment when the delisting is
  recorded later in the era. Otherwise it is held at its last close and closed
  on the fifth no-bar session.

## Corporate actions (spec/05, "Corporate actions during an open position")

- The target and the stop are fixed in D's basis. The labeler reads every later
  bar with `OracleReader.bars(..., adjust="split_div", basis=D)`, which divides
  it by the factors of actions dated in (D, t]. A split therefore neither
  triggers the stop nor moves the target.
- The share count scales with the split: `exit_shares` = shares × the product
  of split ratios in (fill, exit].
- **Dividend credit.** A cash dividend paid while the position is open is
  credited through the dividend-adjusted basis. The exit price in D's basis is
  the unadjusted price ÷ (1 − div / close<sub>ex−1</sub>). That is the
  unadjusted price with the dividend reinvested at the ex-date's prior close,
  the store's CRSP-style factor (`docs/store.md`). `gross` includes the credit.
  `dividend_credit` reports it separately: `gross` minus the same trade's return
  in the split-only basis.
- A dividend whose ex-date is the fill session isn't credited. The buyer at
  that open isn't entitled to it, and the entry and exit are divided by the same
  factor.
- `exit_price_unadj` converts the exit back to the unadjusted series using the
  exit bar's own adjustment. The cost model uses it for the exit notional.

## Era boundary (spec/03)

- A position still open on the era's last session is closed at that close,
  with reason `era_end`. It is charged the `exit_era_end` leg and flagged
  `era_truncated`. When there is no bar that day, it closes at the last close,
  flagged `no_bar_at_era_end`.
- All reads end at `era_last_date`. A later date raises `OracleBoundError`
  (past the oracle's era bound) or `HoldoutLockedError` (into a locked
  holdout). The labeler raises before it labels anything.

## Returns and costs

- **Gross:** `exit_price / entry_price − 1`, from entry fill to exit fill, in
  D's basis, before costs, with the dividend credit.
- **Per leg:** `{entry,exit}_leg`, `_spread`, `_slippage`, `_fee` and
  `_floor_bound`, as the cost model returned them (fractions of that leg's
  order notional).
- **Net:** the decision quantity (spec/04). Each leg is charged on its own
  notional, expressed per unit of entry notional:

  ```
  net = gross − (entry spread + slippage + fee)
              − (exit spread + slippage + fee) × exit_notional / entry_notional
  ```

## Forward returns (spec/04, spec/03)

- `fwd_5`, `fwd_21`, `fwd_63` and `fwd_252` run from the entry fill to the
  close h lane sessions after the fill session, in D's basis, before costs.
  They are the horizon curve's input and are never a decision input.
- They are null when that session is past the era's last session, i.e.
  censored. Holdout prices never reach them.
- A name delisted by the horizon is valued by its delisting treatment. A name
  with no bar on the horizon session is held at its last close.
- `forward_null_counts(labels)` gives, per horizon, the filled candidates, the
  null (censored) count and the non-null count, for the report.

## Bucket (spec/04)

- `news` when any EVENTS row for the name has a filing date in [D − 2, D + 4]
  lane sessions. Otherwise `noise`.
- `eventcodes` holds the union of the matching rows' codes, `|`-joined.
- Unfilled candidates are bucketed too. Crypto has no EVENTS and is always
  `noise`.
- A window cut short by the era's end is flagged `bucket_window_truncated`.

## Output

`label` returns one row per candidate, with the columns in
`harness.labels.OUTPUT_COLUMNS`:

- **Status:** `status` (`filled` or `unfilled`) and `unfilled_reason`.
- **Levels:** `target_level`, `stop_range` and `stop_level`.
- **Entry:** date, price in D's basis, unadjusted price, shares and notional.
- **Exit:** date, price, unadjusted price, shares, notional, reason and
  `sessions_held` (sessions with a bar after the fill).
- **Delisting:** `delist_reason`, `delist_exchange` and `haircut`.
- **Flags:** `era_truncated` and `flags` (`|`-joined).
- **Costs:** the per-leg components.
- **Returns:** `gross`, `dividend_credit`, `net` and the forward returns.
- **Bucket:** `bucket` and `eventcodes`.

## Tests

- `tests/labels/test_labels.py` covers:
  - every exit path;
  - the tie rule;
  - the fill session;
  - the gap-through fill and the stress fill at the low;
  - no-bar sessions and the five-session close;
  - each delisting class and the post-delisting price;
  - the split and the dividend;
  - the era-truncated close;
  - the null 63- and 252-day labels near the validation era's end;
  - the holdout refusal;
  - the bucket window at D−2, D−3, D+4 and D+5;
  - the unfilled cases, crypto and the cost legs.
- `tests/labels/test_levels.py` covers the levels and exit invariance, marked
  `leakage`.
- The fixtures are `tests/fixtures/store.py` (the canonical store) and
  `tests/fixtures/label_store.py` (scenario stores).
- `tests/labels/_cost_stub.py` stands in for `harness.costs` until issue 7
  merges.

## Open points

- **The post-delisting price has no store column.** The labeler reads the first
  bar after the delisting date as that price. Issue 5 (listing and adjustment)
  should say where the loader puts it.
- **Unmapped exchange or reason.** These take the harsher treatment and are
  flagged (see "Delisting"). spec/01 names neither case.
- **A pending next-open exit on a no-bar session** waits for the next session
  with a bar, with the five-session rule still running. spec/05 says "the open
  of the next session" and doesn't cover a halt on that session.
- **Performance.** Each filled candidate makes a few small oracle reads. That is
  enough for a dev run. Batching per symbol is possible if profiling shows the
  need.

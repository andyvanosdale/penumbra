# Universe builders

Per-lane universe construction: `harness/universe.py`. Spec: `spec/01` (Lanes
and universe, all of it), `spec/02` (Store, Trading calendars), `spec/04`
(Conventions: dollar volume, annualization). Contract: `docs/architecture.md`,
"Packages and ownership". Issue 6.

**Scope of this document and this module.** The `UniverseBuilder` interface and
the two equity lane builders, `smallcap` and `discovered`. The `crypto` builder
and its dated exclusion list are not built here: issue 15 (the pre-build
screen, running on `screen/free-data`) may remove the crypto lane by spec
change before its universe rule is built (`docs/architecture.md`, "Build
order"). `BUILDERS`, the lane-name registry, is where a future `CryptoBuilder`
slots in without changing this interface or its callers.

## Interface

```python
class UniverseBuilder(Protocol):
    def build(self, reader: AsOfReader, lane: str, dates: Sequence[str]) -> pd.DataFrame:
        ...
```

`dates` are lane trading sessions (`harness.store.calendar_for_lane`); a date
the lane's calendar doesn't carry as a session raises. The returned frame has
one row per (lane, market, symbol, date) admitted on that date, with columns
`lane`, `market`, `symbol`, `date`, `screen_values` (a dict of the values that
admitted the name — not yet JSON-encoded, so a caller can inspect it as data
before it's written).

`BUILDERS` maps a lane name to its builder (`BUILDERS["smallcap"]`,
`BUILDERS["discovered"]`). Each builder checks the `lane` argument it's called
with against the one it owns and raises on a mismatch, since the interface
takes `lane` explicitly (for a uniform, lane-agnostic caller) even though each
concrete builder is fixed to one lane.

`write_lane_membership(conn, snapshot_id, frame)` JSON-encodes `screen_values`
and writes the frame into `lane_membership` through `harness.store.writer`,
with `available_at` set to the row's own date (`docs/store.md`).

## Read path: one windowed read per call

Every read goes through `harness.store.reader.AsOfReader`. A `build()` call
issues one `panel` read (unadjusted, for price and dollar volume), one more
`panel` read (`adjust="split_div"`, for the vol screen), one `marketcap` read,
one `listing` read and one `symbols` read (for the allowlisted `category`) —
regardless of how many dates it's asked for — spanning from `HISTORY_SESSIONS`
(250) lane trading sessions before the earliest requested date to the latest
one, with `as_of` set to the latest requested date. The one exception is
`exchange`, which is point-in-time (see below) and fetched once per requested
date rather than folded into the windowed reads.

This is correct by construction, not by assumption about vendor behavior:
`harness.store.schema.AVAILABLE_ON_DATE` lists `bars_daily`, `marketcap` and
`listing` (with `calendar`, `actions` and `lane_membership`) as tables whose
writer refuses any row whose `available_at` differs from its own date
(`docs/store.md`, "Availability invariant"). A row dated t <= D is therefore
always known by D regardless of which `as_of` a read used to fetch it, so a
single read with `as_of = max(dates)` returns exactly the rows a per-date
`as_of = D` read would return for each requested D — the SQL
`available_at <= as_of` filter adds no visibility beyond what the date-range
filter already gives. `symbols` is the one exception (`available_at` is a
symbol's first listing date, not "this row's own date"), and only its
allowlisted `category` is read this way; `exchange` is point-in-time and
fetched once per requested date instead (see below).

The per-D screen values are then computed from that one panel without looking
past D: every rolling computation (bar-completeness count, dollar-volume
median, log-return vol) is a pandas `rolling` over a chronologically sorted
per-symbol series, which by construction only reads the current and earlier
rows. `tests/universe/test_invariance.py` pins both halves of this: that a row
violating the availability invariant can't be written at all, and that a call
asked for extra, later dates leaves an earlier date's result unchanged even
when every table (bars, market cap, listing) carries ordinary, compliant rows
dated after it. It also checks the invariance directly — perturbing every bar
(via `harness.testing.invariance.perturbations`) and, separately, every
market-cap row and listing event dated after D leaves D's membership
unchanged.

Missing bars are never forward-filled (spec/02 Trading calendars): a
(symbol, session) slot with no bar is absent from every rolling window that
touches it, including the 250-day completeness count.

## Equity eligibility (spec/01 Eligibility)

On lane trading day D, a name is eligible when all of:

- TICKERS `category` is one of `Domestic Common Stock`, `Domestic Common Stock
  Primary Class`, `Domestic Common Stock Secondary Class`, and `exchange` (on
  D, point-in-time; see below) is one of NYSE, NASDAQ, NYSEMKT, NYSEARCA, BATS.
- Listed on D per `AsOfReader.listed`'s rule (a `listed` event on or before D
  and no `delisted` event on or before D, so a name is excluded on and after
  its delisting date) — replicated here as a vectorized
  `min(listed date) <= D < min(delisted date)` per symbol rather than calling
  `listed()` once per date, since both are the same "exists a date <= D" test
  and the vectorized form is what makes the one-windowed-read design possible.
- A bar on each of the 250 lane trading days ending at D.

**Relisting.** `min(listed date) <= D < min(delisted date)` takes the earliest
event of each kind, so a name that delists and is later relisted under the
same permaticker stays excluded from every date on and after its *first*
delisting, even past the relisting date — it never satisfies
`D < min(delisted date)` again. This matches `AsOfReader.listed`'s own SQL (an
"exists a `delisted` event on or before D" check, not "the most recent event
is `listed`"), so this module is consistent with the store, not introducing a
new gap. `docs/store.md`'s "Open points" doesn't currently call this out; spec/02
doesn't say whether a relisting should ever re-admit a name, so this is a store
behavior to confirm with the PM, not something this module should diverge from
unilaterally.

**`category` and `exchange` (PM ruling on issue 6's Q3/Q4, penumbra-specs
PR 10):**

- `category` is allowlisted like `sector` (spec/04): a TICKERS current value,
  read as-is with no point-in-time reconstruction.
- `exchange` on D is point-in-time: the most recent ACTIONS listing or
  exchange-change event on or before D, falling back to the TICKERS current
  `exchange`. The real implementation, `AsOfReader.exchange_on(market,
  symbols, date, as_of)`, is being added to `harness/store/reader.py` by the
  Sharadar-loader worker (issues 3+5, branch `ingest/sharadar`) and hasn't
  merged yet. `harness.universe._exchange_on` is a local stand-in with that
  exact call signature and return shape (`symbol`, `exchange`, `source`): it
  calls `reader.exchange_on(...)` when the method exists, and otherwise falls
  back to the current TICKERS `exchange` (today's non-point-in-time behavior),
  marked `# TODO(PA): switch to exchange_on after ingest/sharadar merges`.
  Since the real method takes one date, not a window, `_exchange_frame` calls
  it once per requested date rather than folding it into the one windowed
  panel read described above.

## Screens (spec/01 Parameters)

Every threshold and window length below (`SMALLCAP_CEILING`, `LIQUIDITY_FLOOR`,
`LIQUIDITY_WINDOW`, `VOL_FLOOR`, `VOL_WINDOW`, `PRICE_FLOOR`,
`HISTORY_SESSIONS`) comes from `config.params.SPEC01` (issue 17, PR 24) —
`config/params.py` is the single input to the run's configuration hash
(spec/03 Run record), so it's read from there rather than duplicated as local
constants.

- **`smallcap`**: DAILY `marketcap` dated exactly D (`available_at` = D) below
  USD 2,000,000,000. A name with no DAILY row as of D is ineligible for
  `smallcap` (and, per spec/01, eligible for `discovered`).
- **`discovered`**: no market-cap condition at all — present or absent,
  above or below the ceiling, none of it matters here.
- **Both lanes**: median dollar volume over the 20 lane trading days ending
  **D−1** (not D, so the signal day's own volume never qualifies a name) above
  USD 500,000; 20-day annualized realized vol (sample std, ddof=1, of the
  1-day log returns on the split-and-dividend-adjusted series over the 20 days
  ending D, ×√252) above 40%; the **unadjusted** close on D at or above
  USD 2.00.

**`smallcap` and `discovered` membership is not deduplicated (confirmed by the
PA, PR 32 review).** spec/01's lane table gives `discovered` no cap limit and
no rule excluding a name that also qualifies for `smallcap`; the size targets
fit `discovered` being a superset. A name can be a member of both lanes on the
same date; the two lanes are never *pooled into one model* (spec/01,
`DECISIONS.md` "Three lanes, never pooled"), which is a different thing from
disjoint membership. Lanes are reported separately, never pooled — this module
implements the literal reading.

## Sanity report

`sanity_report(membership, ranges=TARGET_SIZE_RANGES, persistent_sessions=20)`
returns a frame of `lane`, `date`, `n`, `low`, `high`, `out_of_range` and
`persistent_excursion`; it never drops a row (spec/01: "Persistent sizes
outside the range are flagged, not silently accepted"). `TARGET_SIZE_RANGES`
is `{"smallcap": (500, 1500), "discovered": (600, 2000)}` (spec/01 Parameters);
a lane missing from `ranges` (crypto, for now) is reported with no target and
never flagged.

**"Persistent" is this module's own definition, not the spec's**: at least
`PERSISTENT_SESSIONS` (20) consecutive rows, in the order `membership` is
given, with `out_of_range` set for the same lane. The spec's estimate ranges
are exactly that — estimates to be replaced from the first dev build
(spec/01, `DECISIONS.md` "Universe eligibility and delisting treatment") — and
say nothing about how long an excursion must run before it's "persistent"
rather than one noisy day; 20 sessions (one calendar month of NYSE trading) is
an operational choice made for issue 6, flagged here for the PM to confirm or
replace. `sanity_report` takes no calendar of its own, so it treats
`membership`'s date sequence as already gap-free per lane (a full era's dates,
with no missing trading sessions) — the run that calls it owns supplying that.

## Testing

`tests/universe/`, on a synthetic store built by
`tests/fixtures/universe_store.py` (a new fixture module — the shared
`tests/fixtures/store.py` is unmodified; that fixture's one month of March
2021 data can't hold a 250-session lookback). The new fixture spans four and a
half years of NYSE weekdays and gives each test full control over a symbol's
category, exchange, listing, splits, price path (an alternating log-return
walk that hits a target annualized vol exactly) and volume, so every screen
can be pushed just above or below its floor deterministically.

Covered: the listing boundary (a name is excluded on and after its delisting
date, checked both on the delisting date and the session after, and
re-included once a stray gap ages out of the 250-day window); the point-in-time
`exchange` rule (a name that moves from OTC to NASDAQ mid-range is ineligible
before the move and eligible on and after it, exercised through a fake
`exchange_on` that stands in for ingest/sharadar's not-yet-merged one, so the
integration seam is checked independent of the real loader); the market-cap
as-of rule, including a future DAILY row within a call's fetched panel that
must not be used for an earlier date; the missing-marketcap discovered-only
rule (and the symmetric case, marketcap present but at or above the ceiling);
every eligibility filter (ADR, OTC, fund, preferred, wrong exchange), against
every eligible category; the 250-day completeness rule with one missing bar,
both inside and aged out of the window; the D−1 median-volume window, with a
constructed volume distribution where a day-D spike would flip the median
above the floor if the window were off by one session but not when the window
correctly ends at D−1; the price floor on the unadjusted close across a
3-for-1 split, with the split-and-dividend-adjusted series (the vol screen's
input) checked to stay smooth across the same split; the writer round trip
through the store; and, on the single-windowed-read design (see above), that
a row violating the store's availability invariant can't be written at all,
and that a call given extra, later dates matches one asked only for D even
when bars, market cap and listing all carry ordinary rows dated after it.
Two invariance checks cover the rest: that a call asked for more dates
doesn't change an earlier date's computed values, and that perturbing every
bar after D (via `harness.testing.invariance.perturbations`'s delete /
multiply / shock / shuffle battery) and, separately, every market-cap row and
listing event dated after D, leaves D's membership unchanged.

`tests/universe/test_boundaries.py` pins exact values, not just pass/fail
outcomes, against seven mutants a PR 32 review found that the rest of the
suite let through — each one flipped a boundary and still passed all 33
tests at the time: the liquidity window ending D−2 instead of D−1 (a
monotonic dollar-volume ramp gives the three candidate 20-session windows
three different medians, one `STEP` apart, so any one-session shift is
caught exactly); `HISTORY_SESSIONS` off by one (a symbol with exactly 250
complete sessions vs. one missing exactly the 250th session back); vol
computed on the unadjusted series instead of the split-and-dividend-adjusted
one (a split inside the vol window, where the true adjusted vol is a small
fraction of what the unadjusted series's spurious jump would give); the vol
window ending D−1 instead of D (a flat price through D−1 then one large jump
on D, so a window that misses D reads zero vol); `ddof=0` instead of `1`
(constructed so the two straddle the 40% floor); the price floor as `>`
instead of `>=` (exactly USD 2.00, eligible); and the liquidity floor as `>=`
instead of `>` (a median of exactly USD 500,000, ineligible). Each mutant was
applied by hand and confirmed to fail at least one of these tests before this
revision was sent for review again.

### 2026-10-01 — Wave 1 of the signal-screening program (1a–1e and the extreme-movers counts)

**Phase:** 0 (screening program, wave 1; no build)
**Commit:** `af23489` (pre-registration) · `cbc3c67` (amendment) · `6343335`, `59c8d43`,
`f912434` (engine) · `07dd1de` (data and regression) · `40eac00` (dev tables) · the
commit that closes this entry (autopsy, confirm, ledger, interpretation) is named in
`research_log.md`
**Status:** complete
**Branch:** `screen/wave-1`
**Proposal:** `andyvanosdale/penumbra-specs` branch `claude/zen-clarke-ocjx6t` at
`5417b070` — `proposals/2026-09-30-signal-screening-pivot.md` (sections 4, 6, 7, 8) and
`proposals/2026-09-30-path-to-a-living.md`. Feature definitions from `spec/04`; eras from
`spec/03`. The proposal is under owner review; its program frame, crypto-in-universe,
shorting-reported-only and no-signal-cap decisions are accepted (section 11).
**Predecessors:** `2026-09-28-free-data-screen.md` (the v1 screen; its engine is
`experiments/screen_free_data.py`), `2026-09-30-continuation-crypto.md` (screen 2).

**Owner's question.** Do historical signals predict drops and rises in equities (and
crypto) over the next days to weeks? This wave screens the five catalog signals whose
data is already cached and whose features already exist, plus the extreme-movers counts
study, under one protocol.

#### Pre-registration (written BEFORE any data for this wave was downloaded or read)

Nothing below is fitted. Every number is transcribed from the proposal's catalog
(section 7), its protocol (section 6) or the owner's wave-1 instruction. A parameter
change after a result is read is a new ledger row, never an edit; at most three
variants per signal.

##### Hypotheses (one per signal)

- **1a Post-shock continuation (short side / long-avoid).** A one-day drop of at least
  2.0 trailing daily vols in a universe name is followed by 5 sessions of continued
  *under*performance against the same-day universe, large enough that a short entered
  at the next open earns ≥ +50 bps per trade over the universe net of the base cost
  schedule. Read alongside as a long-avoidance signal (the same number at zero cost).
- **1b Up-shock continuation (long).** A one-day rise of at least 2.0 trailing daily
  vols on volume at least 2× the trailing 20-session median is followed by continued
  *out*performance against the same-day universe over the next 5 sessions (variant
  1b/5d) and the next 21 sessions (variant 1b/21d), each ≥ +50 bps per trade net of the
  base schedule.
- **1c Slide-cohort momentum (two legs).** A name that has slid to `zscore_20` ≤ −2
  without a one-day shock (|`shock`| < 1) and with top-half 250-session volume
  percentile continues to underperform the same-day universe over the next 21 sessions
  (short / long-avoid leg, ≥ +50 bps net); the mirror winners cohort (`zscore_20` ≥ +2,
  |`shock`| < 1) continues to outperform over 21 sessions (long leg, ≥ +50 bps net).
- **1d Crypto time-series momentum (BTC, ETH).** Holding BTCUSDT (separately ETHUSDT)
  only in weeks when both its trailing 30-day and 90-day returns are positive, and being
  flat otherwise, beats buy-and-hold of the same pair by ≥ 5 percentage points a year
  net of the base schedule.
- **1e Crypto cross-sectional momentum.** Among the top-100 USDT pairs, the top decile
  by trailing 3-week return, bought weekly and held 3 weeks, beats the equal-weight
  universe by ≥ 5 percentage points a year net of the base schedule.
- **Extreme-movers counts (a study, not a signal).** No hypothesis is tested. It records
  the base rates of extreme moves per year and universe and the lift ratios of as-of
  features the day before a 5× move over 63 sessions. Its output is a list of
  candidate hypotheses for wave 3 (at most three pre-registrations may come from it)
  and is explicitly not evidence.

##### Common protocol (locked; identical for every signal)

- **Data.** Equities: yfinance daily bars (`auto_adjust=False`), 2009-01-01 → 2023-12-31,
  for the Nasdaq Trader common-stock list (`nasdaqlisted.txt`, `otherlisted.txt`,
  filtered exactly as the v1 screen: common stock / ordinary shares / class shares on
  NYSE, Nasdaq, NYSE American, Arca, BATS; ETFs, test issues, preferreds, warrants,
  rights, units, notes, ADRs/ADSs, funds, SPACs and partnerships excluded). Market caps:
  the Nasdaq screener export (`api.nasdaq.com`), then yfinance `fast_info` for the
  remainder, both *current*. Crypto: Binance public bucket (`data.binance.vision`)
  monthly 1d klines for every USDT spot pair, 2018-01-01 → 2024-12-31, and 1h klines
  (for the 01:00 UTC open) for every pair that ever enters the top-100 universe. The
  equity holdout (2024-01-01 onward) and the crypto holdout (2025-01-01 onward) are
  never downloaded; the download end dates above are the hard bound. The 2009 start is
  warm-up only, so the 250-session history rule no longer empties the first dev year.
  Fallback if a host is blocked by the egress proxy: record it under "Run details" and
  use the v1 fallback (owner-supplied file dropped into the data root).
- **Survivorship bias (equities).** The list is the *current* listing: every name
  delisted before 2026-10-01 is missing and every cap is today's. Direction per signal:
  1a and 1c-short understate the true effect (the worst continuers were delisted);
  1b, 1c-long and the extreme-movers winner counts overstate it (winners survive to be
  listed); the extreme-movers drop counts are understated. Crypto has no survivorship
  bias (the bucket keeps delisted pairs).
- **Universes**, evaluated per session D exactly as the v1 screen built them, with the
  2009 warm-up as the only change. `smallcap`: current cap < USD 2B, bar on each of the
  250 sessions ending D, median unadjusted dollar volume over D−20..D−1 ≥ USD 500k,
  `rvol_20` > 40% annualized, close on D ≥ USD 2.00. `uncapped`: the same without the
  cap limit. `crypto`: top 100 USDT pairs by trailing 30-day quote volume as of D,
  1d kline on each of the 30 days ending D, base not a stablecoin / leveraged / wrapped
  token (the v1 exclusion sets), 30-day annualized vol > 20%.
- **Eras** (`spec/03`). Equities: dev 2010-01-01 → 2020-12-31, confirm 2021-01-01 →
  2023-12-31. Crypto: dev 2018-01-01 → 2022-12-31, confirm 2023-01-01 → 2024-12-31.
  Signal days D lie inside the era. Era boundary: a forward return whose exit session
  falls after the era's last session is null and is not counted (the count per horizon
  is reported), so no dev-era statistic reads a confirm-era bar. Dev tables are written
  and committed before any confirm-era run; the confirm era is run only for a signal
  that meets the "interesting" threshold in dev. Both halves of the dev era are
  reported: equities 2010-01-01 → 2015-06-30 and 2015-07-01 → 2020-12-31; crypto
  2018-01-01 → 2020-06-30 and 2020-07-01 → 2022-12-31.
- **Features** (`spec/04`, on the as-of-adjusted series: yfinance `Adj Close` /
  `Close` ratio applied to O/H/L/C; crypto unadjusted). `ret_1` = ln(close_D /
  close_{D−1}); `rvol_20` = annualized sample std (√252 equities, √365 crypto) of the 20
  1-day log returns ending D; `rvol_20_prev` = `rvol_20` at D−1; `shock` = `ret_1` /
  (`rvol_20_prev` / √annualization); `zscore_20` = (close − mean of the 20 closes ending
  D) / sample std of those 20 closes; `vol_pctl_250` = rank of D's dollar volume among
  the 250 values ending at D, divided by 250 (NaN with fewer than 250 bars);
  `vol_ratio_20` = D's volume / median of the 20 volumes ending D−1 (share volume for
  equities, quote volume for crypto); `ret_30`, `ret_90` = close_D / close_{D−30 days}
  − 1 and over 90 UTC days (crypto 1d klines); `ret_21` = close_D / close_{D−21} − 1.
- **Fills.** Event mode: entry at the next session's open (equities, O_{D+1}); crypto
  at the open of the 01:00 UTC 1h kline on D+1 (a missing 1h bar makes the candidate
  unfilled, recorded as such). Exit at the same price type on session F+H, where F =
  D+1 is the fill session and H the horizon: open-to-open over H sessions. No hard stop
  and no target in this wave (the catalog specifies time stops only). Signal-close and
  next-close fills are reported as the bounce diagnostic at the decision horizon and do
  not decide. Fixed USD 10,000 notional per trade.
- **Horizons.** Forward returns at 1, 5, 21 and 63 sessions from the fill are stored for
  every candidate event, each with the same-day universe mean of the same quantity, so
  the horizon curve is read from one run. The decision horizon is named per signal
  below and cannot change after the run.
- **No re-entry while held.** A candidate in a name the signal already holds at D's
  close (an earlier event in that name whose exit session is after D) is recorded as
  `held` and not traded. Applied per signal, per leg, per horizon variant.
- **Comparator.** The same-day universe: the equal-weight mean, over every name eligible
  on D, of the same forward quantity from the same fill session and price type. No
  cost is charged to the universe. Short-side quantities are sign-adjusted so that a
  positive number means the short (or the avoidance) beat the universe: short excess =
  universe mean − candidate return − cost.
- **Rank mode** (1d, 1e). Rebalance date D = every Sunday (UTC day) in the era; the
  signal uses 1d klines through D's close; the position is entered at the 01:00 UTC
  open on Monday D+1 and held to the 01:00 UTC open on the following Monday D+8 (one
  weekly observation). A missing 01:00 UTC bar at either end makes that name's week
  null for that name (reported). Comparator per week: 1d, buy-and-hold of the same pair
  over the same week; 1e, the equal-weight mean of the universe eligible on the
  tranche's formation date over the same week. Annual turnover is reported.
- **Cost schedule** (flat round trip, by the name's median dollar volume over
  D−20..D−1, three levels; subtracted from each candidate's excess, never from the
  universe):

  | bucket | low | base | high |
  |---|---|---|---|
  | equities, median dollar volume ≥ USD 10M | 10 | 20 | 40 |
  | equities, USD 1M–10M | 20 | 40 | 80 |
  | equities, USD 0.5M–1M | 40 | 80 | 160 |
  | crypto, top-100 (all) | 40 | 60 | 100 |

  Crypto is also re-costed at a flat 80 bps round trip (`alt80`), as instructed; the
  proposal's 30/40/60 top-20 tier is not used (the owner's wave-1 instruction sets
  40/60/100 for the whole top-100). The `spec/06` Abdi–Ranaldo estimate (`spec`) is
  computed and reported alongside for the later calibration comparison; it decides
  nothing. Rank mode charges the round trip on each unit of turnover: 1d, half the
  round trip per switch (flat→long, long→flat); 1e, one round trip per tranche at
  formation (a third of a round trip per weekly observation, since three tranches are
  live). Zero cost is reported everywhere as the gross.
- **Statistic.** Event mode: the day-clustered z = mean over entry days of the daily
  mean (over that day's traded candidates) of the net excess, divided by its standard
  error over entry days. Rank mode: the same over weekly rebalance dates of the weekly
  strategy-minus-comparator difference. Reported with it: trades, entry days (or weeks),
  trade-weighted mean net excess per trade, day-weighted mean and SE, median, hit rate,
  mean gross and 1–99% winsorized mean gross, share of absolute P&L from the top 10
  entry days, z with those days removed, the sign and z in each half of the dev era,
  and per-year rows.
- **Controls** (every run, every universe). Stale-signal placebo: the signal lagged 20
  sessions (the candidate on D is the name that qualified on D−20; rank mode ranks on
  the features as of D−20). Planted positive control: +50 bps added to every traded
  candidate's excess (rank mode: to every weekly difference) at zero cost; it is
  deterministic and is never re-run. Expected: placebo |z| < 2; planted z − actual z
  ≈ 50 bps / SE.
- **Model.** None. Fixed rules. No LLM call, no fitting, no purchase.

##### Signals (locked rules, universes, decision horizon, direction)

| # | variant | candidate rule on D (universe-eligible names only) | direction | universes | decision horizon H |
|---|---|---|---|---|---|
| 1a | — | `shock` ≤ −2.0 | short / long-avoid | `smallcap`, `uncapped`, `crypto` | 5 sessions |
| 1b | 5d | `shock` ≥ +2.0 and `vol_ratio_20` ≥ 2.0 | long | `smallcap`, `uncapped`, `crypto` | 5 |
| 1b | 21d | same candidates as 1b/5d | long | same | 21 |
| 1c | short | `zscore_20` ≤ −2.0 and |`shock`| < 1.0 and `vol_pctl_250` ≥ 0.5 | short / long-avoid | `smallcap`, `uncapped`, `crypto` | 21 |
| 1c | long | `zscore_20` ≥ +2.0 and |`shock`| < 1.0 | long | same | 21 |
| 1d | — | long the pair for the week when `ret_30` > 0 and `ret_90` > 0 at D; flat otherwise | long / flat | BTCUSDT, ETHUSDT (each its own row) | 7 days (weekly) |
| 1e | — | top decile (top ⌈n/10⌉ names) of the eligible top-100 by `ret_21` at D, equal weight, held 3 weeks; a new tranche every week, three live tranches averaged | long | `crypto` | 7 days (weekly obs; 21-day hold) |

Notes transcribed from the catalog: 1c's volume condition applies to the short leg
only (the proposal's long leg carries no volume condition); 1b uses the volume
confirmation on both horizon variants; 1d's comparator is buy-and-hold of the same
pair (owner's instruction), not the equal-weight universe; in crypto `vol_pctl_250`
needs 250 days of history, which the 30-day universe rule does not, so 1c-short in
crypto fires only in names with a 250-day record. For 1d the first rebalance with a
90-day return is in April 2018 (no pre-2018 bar is downloaded). Short legs are
reported, not primary (owner, 2026-09-30): a graduating short leg would be implemented
as long-avoidance, and the zero-cost figure is the one that reading uses.

##### Extreme-movers counts study (locked definitions)

- **Events.** For horizon h ∈ {1, 21, 63, 252} sessions, the move starting on session
  D has ratio_h = close_{D+h−1} / close_{D−1} on the adjusted series. Up thresholds:
  2× (h = 1), 3× (21), 5× (63), 10× (252). Mirror drops: ratio ≤ 0.50 (1), ≤ 0.333
  (21), ≤ 0.20 (63), ≤ 0.10 (252). A name must be universe-eligible on D−1 (the
  last as-of date before the move). A name counts once per calendar year (year of D)
  per threshold; event-days are also reported. Denominator: names eligible on at
  least one session of that year. Universes: `smallcap`, `uncapped`, `crypto`. Era:
  dev only (equities 2010–2020, crypto 2018–2022); the confirm era is not read by this
  study, so any wave-3 signal it suggests still has an untouched confirm era.
- **Lift ratios** for the 63-session 5× group only (as instructed). For each as-of
  feature at D−1 — close (price), median dollar volume (D−21..D−2 relative to D−1),
  `rvol_20`, close / 250-session high, `ret_20`, `ret_60`, `vol_pctl_250`, `zscore_20`,
  `shock`, and current market cap (equities only; static, biased) — the within-day
  percentile rank among the universe at D−1 is computed; lift_top = share of events
  with rank ≥ 0.8 divided by 0.2, lift_bottom = share with rank ≤ 0.2 divided by 0.2,
  pooled over the dev era, with the event count. Filing / headline cause and sector are
  not in the free data and are not computed. Nothing in this table is a result; a lift
  ≥ 1.5 with a plausible mechanism is a candidate for a wave-3 pre-registration (cap
  three, per the catalog).

##### What is interesting and what is not (per ledger row; from the graduation rule)

- **Event mode (1a, 1b/5d, 1b/21d, 1c-short, 1c-long), per universe.** *Interesting*
  in dev: day-clustered z ≥ 3.0 on the decision horizon at base cost, over ≥ 100 entry
  days and ≥ 500 trades, trade-weighted mean net excess per trade ≥ 50 bps at base cost
  and > 0 at high cost. *Not interesting*: anything else. An interesting dev result is
  the only thing that triggers a confirm-era run.
- **Rank mode (1d per pair, 1e).** *Interesting* in dev: z ≥ 3.0 over ≥ 36 weekly
  rebalance dates, annualized net excess over the comparator (52 × mean weekly
  difference) ≥ 5 percentage points at base cost and > 0 at high cost. *Not
  interesting*: anything else.
- **Graduation** (earns a spec, the Sharadar purchase and the harness build) requires,
  in addition: confirm era same sign with z ≥ 1.5 and no parameter change; the sign
  holds with the top 10 days removed; placebo |z| < 2; the sign holds in both halves
  of the dev era; at most three variants in the ledger (a fourth raises the dev z bar
  to 3.5).
- **Decision quantity**, named once: event mode, the trade-weighted mean net excess
  per trade at the decision horizon at base cost (with its day-clustered z); rank mode,
  the annualized net excess over the comparator at base cost (with its weekly z).
- **Ledger verdicts.** `null` (dev not interesting), `confirm` (dev interesting, confirm
  pending), `graduate` (all rules met), `fails confirm` (dev interesting, confirm rule
  not met), `artifact` (dev interesting but rule 4 fails).

##### Decision rules (applied literally after the tables are written)

1. A row that is not interesting in dev gets verdict `null`; no confirm run; no further
   variant of that signal in this wave.
2. A row that is interesting in dev is run once on the confirm era with the identical
   rule; verdict `graduate` if confirm z ≥ 1.5 with the same sign and rule 4 holds,
   `fails confirm` if confirm fails, `artifact` if rule 4 fails.
3. If 1a or 1c graduate, epic 7 (slide-cohort momentum) is promoted and the momentum
   lane is the build target (proposal, week-1 decision). If nothing graduates, wave 2
   (rank mode on equities: 2a, 2b, 2d) is the next step per the schedule, and this
   entry says what the wave-1 nulls rule out.
4. The extreme-movers tables are filed as hypothesis material only; any signal drawn
   from them is pre-registered separately, at most three.

##### Engineering acceptance (the refactor, proven before any new number is read)

- `experiments/screen_free_data.py` is split into `experiments/screen/` (`data.py`,
  `engine.py`, `signals/<name>.py`, `ledger.py`, CLI `python -m experiments.screen run
  --signal <name> --universe <u>`). The original script is kept unchanged for the
  regression.
- **Regression:** the v1 rule (`shock` ≤ −2, close / next-open / next-close fills,
  target, stop, 10-session time stop, spec cost) is re-run through the refactored
  engine on the v1 windows (equities 2015-01-01 → 2023-12-31, crypto 2018-01-01 →
  2022-12-31) and must match the original script, run on the same freshly pulled data,
  to the basis point on every headline cell (candidates, trades, 5d excess and net at
  every cost level, hit rate, z, days) for `smallcap`, `uncapped` and `crypto`. The
  original script's output on the fresh pull is also compared against the committed v1
  tables; any difference there is data drift (a list re-pulled three days later,
  current caps, vendor restatements) and is reported as such, not hidden.
- **Shift test per signal:** perturb every bar after D; the candidate (or rank) matrix
  at D must not change. Runs in `pytest -q` for every signal file.
- `tests/test_architecture.py` import rules hold (nothing under `experiments/` imports
  `legacy`, the oracle or the labeler).

##### What this screen cannot show

Point-in-time caps, delistings on the equity side, intraday fills, borrow cost or
availability for the short legs, the spec's 1,000-draw benchmark, and the true spread
(the schedule is a placeholder until the owner's quote sample). The equity biases favour
the long signals and work against the short ones; a null on a long signal here is
conclusive, a null on a short signal is conservative, and a positive on either is only
a reason to run the confirm era.

##### Amendment 2026-10-01 (before any data was read; the locked text above is unchanged)

Two additions from the owner's brief extension, received after the pre-registration
commit `af23489` and before any bar of this wave's data was read (the pulls were still
running). Appended, not edited in.

**A1. Horizon grid widened.** Forward returns are stored and reported at 1, 5, 21, 63,
126 and 252 sessions from the fill for every candidate event in every event-mode signal
(1a, 1b, 1c and the autopsy-to-rule runs below), each with its same-day universe mean.
The decision horizons stay as pre-registered; the added horizons are horizon curve
only. The era-boundary rule applies per horizon (a 252-session label is null for every
signal in the era's last year, and the trade count per horizon is reported with it).
Crypto adds two intraday horizons from the cached 1h klines, no new download: the return
from the 01:00 UTC fill on D+1 to the 04:00 UTC hourly open (`i04`) and to the 12:00 UTC
hourly open (`i12`) on D+1, with the same-day universe comparator on the same prices.
Equities: intraday horizons need minute bars and are deferred to a separate pre-registered
intraday wave; none are pulled in this run.

**A2. Autopsy to rule (step D2).** Closes the loop from the extreme-movers lift table to
prospective rules, under the proposal's wall between hypothesis generation and test.

- *Groups.* The 63-session 5× group (up) and the 63-session −80% group (ratio ≤ 0.20,
  down). The lift table is produced for both (the down group's lifts are added to the
  movers study, same definition: within-day percentile of each as-of feature at D−1
  among the universe on D−1, first qualifying D per name-year).
- *Feature selection (locked procedure, applied after the lift table is written and
  committed).* From the `uncapped` lift table for equities and the `crypto` lift table
  for crypto, the three features with the highest max(lift_top, lift_bottom), each
  ≥ 1.5; fewer if fewer qualify; none if none does. Current market cap is excluded from
  selection: it is today's cap, not an as-of feature. Ties broken by event count, then
  alphabetically.
- *Rule.* On session D, a universe-eligible name is a candidate when the feature's
  within-day percentile rank among the universe on D (data through D's close, the same
  rank the lift used) is ≥ 0.8 if the lift came from the top quintile, or ≤ 0.2 if from
  the bottom quintile. The cut is the one that produced the lift and is locked before
  the run. Direction: long for the up group, short / long-avoid for the down group.
  Decision horizon 63 sessions (the move horizon); 5 and 21 sessions and the rest of the
  grid are reported. Equity rules run on `smallcap` and `uncapped`; crypto rules on
  `crypto`. Fill, comparator, cost schedule, no re-entry while held, placebo (lag 20),
  planted +50 bps and the statistic are the common protocol. One ledger row per rule and
  universe, named `a2r-up-<feature>` / `a2r-down-<feature>`; at most three per direction
  per market (the catalog's cap, applied per direction).
- *Reported per rule.* The match rate per day (mean over era sessions of candidates
  divided by universe size); the forward excess at every horizon; the hit rate for the
  original move (share of traded candidates whose 63-session forward return is ≥ +400%
  for the up rules, ≤ −80% for the down rules) against the universe base rate (mean over
  days of the share of the universe with the same outcome); whether the basket beats the
  universe net of the base schedule (mean net excess per trade and the day-clustered z at
  63 sessions).
- *Interesting threshold and confirm.* The event-mode threshold above (z ≥ 3.0 at base
  cost over ≥ 100 entry days and ≥ 500 trades, mean net ≥ 50 bps at base, > 0 at high).
  The confirm era is run only for rules that clear it.
- *Stated up front.* The features are selected on the dev era and the rules are first
  run on the same dev era, so a dev result for an autopsy-derived rule is in-sample by
  construction and is not evidence; only the confirm era is. The subsection "Autopsy to
  rule" says which features describe past movers but do not predict.

#### Run details

- **Commits.** Pre-registration `af23489`; amendment `cbc3c67`; refactor `6343335` (ledger
  subcommand on top), amendment code `59c8d43`; the data pull, regression and every result
  below: the commits named in `research_log.md` and `ledger.md`.
- **Dataset snapshot date:** 2026-10-01 (all pulls; no host was blocked this time).
  Equities: Nasdaq Trader `nasdaqlisted.txt` 5,640 rows + `otherlisted.txt`
  7,659 → 7,127 after exchange / ETF / test filters →
  5,547 common stock → 4,888 after exclusions (v1: 4,887). yfinance daily
  bars, `auto_adjust=False`, 2009-01-01 → 2023-12-31, 82 batches of 60, 4 threads, 33 min;
  724 symbols returned no bar in the window (post-2023 listings and renames), 4,164 did.
  Market caps: 4,763 from the Nasdaq screener export (`api.nasdaq.com`, reachable
  today, pulled directly rather than owner-supplied), 125 from yfinance `fast_info`;
  all current. Crypto: Binance public bucket, monthly 1d klines for every USDT pair with
  data in 2018-01-01 → 2024-12-31 (539 pairs; 354 after the stablecoin / leveraged /
  wrapped exclusions in the 2018–2022 window), 1h klines for the 434 pairs that ever
  enter the top-100 over 2018–2024, 79 min at 12 threads; the 04:00 and 12:00 UTC opens
  were extracted from the same cached zips (no further download). No bar dated
  2024-01-01 or later (equities) or 2025-01-01 or later (crypto) was downloaded; the pull
  functions refuse such an end date.
- **Survivorship bias.** As pre-registered: the equity list is the 2026-10-01 listing, so
  every name delisted before today is absent and every cap is today's. The crypto bucket
  keeps delisted pairs.
- **Regression (engineering acceptance).** The original script
  (`experiments/screen_free_data.py`, unchanged) was run on the fresh pull, then the v1
  rule was run through the new package (`python -m experiments.screen regress`) on the
  same files and the v1 windows. Result: every cell identical — 240 of 240 rows for
  `smallcap` + `uncapped` and 90 of 90 for `crypto`, no column differing at 5 × 10⁻⁷
  (`regress_v1_comparison_{equity,crypto}.json`; tables from both engines in
  `regress_v1_tables_*.md`). Against the *committed* v1 tables of 2026-09-28: crypto
  reproduces to the basis point in every cell (5d excess −43.81 / −41.54 / −52.06 bps at
  the three fills, z −3.67 / −3.73 / −4.40; the bucket is unchanged); equities differ by
  data drift only (20 columns, `regress_v1_drift_vs_committed.json`): 4,164 tickers with
  bars instead of 4,166, 2,475 names under USD 2B instead of 2,465 (today's caps),
  `smallcap` candidates 32,219 vs 31,927, next-open 5d excess −10.8 vs −10.9 bps
  (`smallcap`) and +6.0 vs +5.9 (`uncapped`), z −2.49 vs −2.49 and −1.56 vs −1.56. The
  refactor is proven; the wave-1 runs below are the first new numbers read.
- **Shift tests.** `tests/screen/test_shift.py`: eight signal modules, equities and
  crypto, through the real panels; `pytest -q` 428 passed.
- **Compute.** 4 cores / 15 GB. Equity panel 2009–2023: 10.7M rows, 3,774 sessions,
  4,164 tickers, 58 s to build, cached as parquet (1.4 GB); arrays about 2 min per
  process. Crypto panel 2018–2024: 3 s. Runtimes per stage below.
- **Anomalies during run.** The v1 anomalies carry over (split-adjusted price floor,
  zero-open placeholder bars treated as missing, yfinance ticker `NA`). New: none at the
  pull. Added here as the runs complete.

#### Results

Dev era only in this section (equities 2010-01-01 → 2020-12-31, crypto 2018-01-01 →
2022-12-31). Result files, one per signal and universe, are in
`research_log/2026-10-01-wave-1-screen/`: `results_<signal>_<universe>_dev.csv` (every
fill × horizon × cost level × period), `controls_*.json`, `weekly_*.csv` (rank mode),
`meta_dev.json` (universe sizes and run summaries), `tables_dev.md` (the per-signal
blocks with per-year rows and the full horizon and fill tables), `movers_*` and the
regression files. Trade-level files stay under the data root. **Universe sizes with the
2009 warm-up:** `smallcap` median 230 names per session (p10 99, p90 754; 2,065 ever),
`uncapped` median 409 (p10 174, p90 1,314; 3,698 ever); crypto median 100 (p10 17; 445
instruments ever, after the segmentation below). The v1 numbers were median 332 / 642 on
2015–2023; 2010–2014 has fewer liquid 40%-vol names in a current listing.

**Anomaly found and corrected during the run (crypto symbol identity).** The first
crypto tables carried impossible universe means in the close-fill diagnostic and the
long horizons (1c-short crypto close fill +146,920 bps; 1b-21d crypto close fill
−32,711 bps). Cause: Binance keeps a pair's symbol across token swaps, redenominations
and relists, so the 1d series of LUNAUSDT jumps 177,400× across the 18-day gap between
the Terra collapse (last bar 2022-05-13 at 0.00005) and the LUNA 2.0 listing
(2022-05-31 at 8.87); COCOSUSDT (1,295× across a 4-day gap, 2021-01), DREPUSDT (108×),
VENUSDT (÷18,000, the VET swap), SUNUSDT, BNXUSDT, QUICKUSDT, VIDTUSDT, BTCSTUSDT and
STRAXUSDT are the same kind. No one could earn those paths. The correction, applied at
the data layer and committed (`f912434`) before any table was written into this entry: a
gap of more than three days in a pair's daily klines ends the instrument, and the bars
after it form a new instrument (`LUNAUSDT~2`) that must re-earn its 30-day history
before entering the universe; the hourly opens follow the instrument. Equities are not
segmented (a halt that resumes at a new price is a real outcome for a holder). The
decision cells moved by at most 3 bps: 1a crypto −6 bps / z +2.61 before and after;
1b-5d +20 / −0.41 both; 1b-21d −97 / −1.55 → −100 / −1.57; 1c-short +229 / +2.40 → +231 /
+2.41; 1c-long +187 / +0.94 → +187 / +0.99; 1d unchanged; 1e −13.5 pp / −0.58 → −12.4 /
−0.53. The pre-fix tables are kept as `tables_dev_before_gap_fix.md`. The v1
regression was proven on the unsegmented panel (the v1 script did not segment) and the
`regress` command keeps that path.

**Placebo at base cost.** The placebo's z at base cost is mechanically negative (a flat
cost charged to a null signal: −4.5 in 1a `smallcap`); the control is the zero-cost
placebo, as in v1, and that is what the tables and the artifact check use. Both are in
the control files.

##### Dev era: event-mode signals, decision horizon, next-open fill

Mean net excess per trade in bps at each cost level (short legs sign-adjusted so positive means the short, or the avoidance, beat the universe); z is day-clustered at base cost; `interesting` is the pre-registered threshold (z ≥ 3.0 at base, ≥ 100 days, ≥ 500 trades, net ≥ 50 bps at base and > 0 at high).

| signal | universe | dir | H | candidates | held | trades | days | net @0 | @low | @base | @high | @alt80 | z @0 | z @base | hit @base | top-10 share | z w/o top 10 | half1 / half2 net | placebo z @0 | planted shift | interesting |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1a | smallcap | short | 5 | 23,023 | 4,216 | 18,722 | 2,507 | +25 | +4 | **-18** | -61 | — | +3.04 | **-0.71** | 0.491 | 6.4% | -0.53 | -26 / -14 | -1.08 | +4.21 | no |
| 1a | uncapped | short | 5 | 47,073 | 9,108 | 37,854 | 2,666 | +1 | -16 | **-34** | -69 | — | +2.82 | **-1.29** | 0.485 | 11.7% | -1.14 | -19 / -41 | -0.30 | +5.38 | no |
| 1a | crypto | short | 5 | 4,351 | 872 | 3,462 | 369 | +54 | +14 | **-6** | -46 | -26 | +3.58 | **+2.61** | 0.569 | 18.7% | +3.33 | +28 / -21 | +0.13 | +0.81 | no |
| 1b-5d | smallcap | long | 5 | 13,039 | 1,541 | 11,409 | 2,504 | -45 | -68 | **-91** | -136 | — | -3.39 | **-6.35** | 0.418 | 6.2% | -6.67 | -74 / -99 | -0.39 | +3.19 | no |
| 1b-5d | uncapped | long | 5 | 24,012 | 2,322 | 21,587 | 2,689 | -28 | -48 | **-67** | -105 | — | -3.15 | **-6.45** | 0.433 | 6.6% | -6.47 | -50 / -77 | -0.39 | +4.15 | no |
| 1b-5d | crypto | long | 5 | 3,326 | 750 | 2,570 | 913 | +80 | +40 | **+20** | -20 | -0 | +0.49 | **-0.41** | 0.356 | 11.8% | -3.04 | -21 / +37 | +0.65 | +0.75 | no |
| 1b-21d | smallcap | long | 21 | 13,039 | 2,814 | 9,799 | 2,426 | -79 | -102 | **-125** | -171 | — | -4.07 | **-5.92** | 0.429 | 5.0% | -6.20 | -67 / -158 | -0.67 | +1.99 | no |
| 1b-21d | uncapped | long | 21 | 24,012 | 4,410 | 19,043 | 2,639 | -53 | -72 | **-91** | -129 | — | -3.06 | **-5.11** | 0.438 | 6.7% | -5.29 | -38 / -124 | +0.12 | +2.57 | no |
| 1b-21d | crypto | long | 21 | 3,326 | 1,348 | 1,957 | 813 | -40 | -80 | **-100** | -140 | -120 | -1.04 | **-1.57** | 0.343 | 11.4% | -3.66 | -30 / -128 | -0.43 | +0.45 | no |
| 1c-short | smallcap | short | 21 | 8,812 | 3,007 | 5,711 | 1,860 | +18 | -3 | **-24** | -65 | — | -0.17 | **-1.56** | 0.512 | 7.1% | -1.29 | -27 / -22 | +0.03 | +1.65 | no |
| 1c-short | uncapped | short | 21 | 17,580 | 5,880 | 11,578 | 2,245 | -9 | -26 | **-43** | -77 | — | -0.76 | **-2.32** | 0.502 | 7.9% | -2.22 | -25 / -53 | +0.64 | +2.17 | no |
| 1c-short | crypto | short | 21 | 488 | 111 | 361 | 122 | +291 | +251 | **+231** | +191 | +211 | +2.82 | **+2.41** | 0.593 | 37.7% | +2.19 | +211 / +236 | +0.93 | +0.34 | no |
| 1c-long | smallcap | long | 21 | 16,379 | 6,910 | 8,969 | 2,210 | -12 | -34 | **-56** | -101 | — | +0.21 | **-1.46** | 0.445 | 7.0% | -1.67 | -13 / -78 | -0.83 | +1.82 | no |
| 1c-long | uncapped | long | 21 | 33,254 | 14,012 | 18,460 | 2,510 | -19 | -37 | **-56** | -92 | — | -0.39 | **-2.30** | 0.443 | 8.3% | -2.38 | -10 / -80 | -0.15 | +2.46 | no |
| 1c-long | crypto | long | 21 | 3,174 | 1,517 | 1,634 | 671 | +247 | +207 | **+187** | +147 | +167 | +1.35 | **+0.99** | 0.373 | 15.0% | -0.43 | +141 / +205 | +0.32 | +0.30 | no |

##### Dev era: rank-mode signals (weekly; Sunday close → Monday 01:00 UTC fill)

Annualized net excess over the comparator (52 × mean weekly difference) in percentage points; z over weeks at base cost. 1d's comparator is buy-and-hold of the pair; 1e's is the equal-weight top-100 at each tranche's formation date.

| signal | universe | weeks | ann. excess @0 | @low | @base | @high | @alt80 | z @0 | z @base | hit | ann. ret strat / comp @base | vol strat / comp | max DD strat / comp | time in mkt | RT / yr | half1 / half2 @base | placebo z @0 | planted shift | interesting |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1d | BTCUSDT | 259 | +9.9 | +8.5 | **+7.8** | +6.3 | +7.0 | +0.37 | **+0.29** | 0.336 | +32.0% / +1.1% | 40% / 73% | -40% / -76% | 0.29 | 3.6 | +8.2 / +7.3 | +0.49 | +0.96 | no |
| 1d | ETHUSDT | 259 | +18.2 | +17.0 | **+16.4** | +15.2 | +15.8 | +0.52 | **+0.47** | 0.336 | +62.5% / +0.5% | 59% / 98% | -49% / -94% | 0.33 | 3.0 | +35.9 / -3.2 | -0.15 | +0.74 | no |
| 1e | crypto | 255 | -1.9 | -8.9 | **-12.4** | -19.4 | -15.9 | -0.08 | **-0.53** | 0.416 | -25.8% / -10.6% | 104% / 95% | -95% / -89% | 1.00 | 17.3 | +1.6 / -26.1 | -1.84 | +1.11 | no |

##### Horizon curve, next-open fill, gross excess per trade (bps) with the day-clustered z at zero cost; the decision horizon is starred

The 126- and 252-session columns lose the era's last half-year and last year to the era boundary (trade counts in the result files). Crypto `i04` / `i12` are the 01:00 → 04:00 and 01:00 → 12:00 UTC opens on D+1.

| signal | universe | 1 | 5 | 21 | 63 | 126 | 252 | i04 | i12 |
|---|---|---|---|---|---|---|---|---|---|
| 1a | smallcap | +18 (+2.83) | +25 (+3.04) * | +29 (+1.07) | +28 (+1.01) | +41 (+1.40) | -0 (+0.16) | — | — |
| 1a | uncapped | +9 (+2.22) | +1 (+2.82) * | +2 (+1.16) | -13 (+1.68) | +12 (+2.26) | -11 (+1.28) | — | — |
| 1a | crypto | -8 (-0.30) | +54 (+3.58) * | +102 (+1.91) | +148 (+1.28) | -405 (-0.72) | -1192 (-0.36) | +1 (+0.01) | +3 (+1.10) |
| 1b-5d | smallcap | -29 (-4.27) | -45 (-3.39) * | -95 (-4.26) | -116 (-3.32) | -43 (-0.74) | -82 (-0.51) | — | — |
| 1b-5d | uncapped | -20 (-3.93) | -28 (-3.15) * | -60 (-3.39) | -79 (-2.51) | +11 (+0.36) | +63 (+1.36) | — | — |
| 1b-5d | crypto | -24 (-1.66) | +80 (+0.49) * | +75 (-0.67) | -288 (-1.87) | +287 (+0.21) | -1027 (-1.98) | +13 (+0.07) | +17 (+0.34) |
| 1b-21d | smallcap | -25 (-4.21) | -49 (-3.47) | -79 (-4.07) * | -102 (-3.07) | -59 (-0.96) | -50 (-1.96) | — | — |
| 1b-21d | uncapped | -19 (-4.09) | -33 (-3.50) | -53 (-3.06) * | -69 (-2.21) | +3 (+0.44) | +78 (+0.96) | — | — |
| 1b-21d | crypto | -41 (-1.56) | +29 (+0.26) | -40 (-1.04) * | -301 (-1.01) | -460 (+0.00) | -1760 (-1.05) | +16 (+0.11) | +11 (+0.50) |
| 1c-short | smallcap | -6 (-0.72) | -6 (-1.82) | +18 (-0.17) * | -6 (-1.05) | +99 (+0.34) | +52 (-0.23) | — | — |
| 1c-short | uncapped | -0 (-0.92) | -6 (-1.91) | -9 (-0.76) * | +0 (-0.92) | +53 (-0.02) | +62 (-0.02) | — | — |
| 1c-short | crypto | +23 (+2.97) | +36 (+2.93) | +291 (+2.82) * | +873 (+3.60) | +1353 (+2.75) | -3566 (+0.01) | +1 (+1.53) | +4 (+0.20) |
| 1c-long | smallcap | +1 (+0.81) | -8 (+0.39) | -12 (+0.21) * | +24 (+0.51) | +52 (+1.00) | +97 (+0.77) | — | — |
| 1c-long | uncapped | -8 (+1.16) | -11 (+0.22) | -19 (-0.39) * | +11 (-0.47) | +74 (+1.33) | +127 (+0.89) | — | — |
| 1c-long | crypto | +26 (-0.08) | +75 (+0.40) | +247 (+1.35) * | +121 (+0.82) | +1152 (+1.90) | +587 (+0.16) | -12 (-2.34) | -17 (-1.56) |

##### Fill comparison at the decision horizon, zero cost (gross excess, bps; z)

| signal | universe | signal close | next open | next close |
|---|---|---|---|---|
| 1a | smallcap | +15 (+1.85) | +25 (+3.04) | +1 (+1.24) |
| 1a | uncapped | +8 (+2.14) | +1 (+2.82) | -13 (+1.16) |
| 1a | crypto | +44 (+3.25) | +54 (+3.58) | +60 (+5.10) |
| 1b-5d | smallcap | -23 (-1.97) | -45 (-3.39) | -25 (-2.22) |
| 1b-5d | uncapped | -13 (-1.94) | -28 (-3.15) | -17 (-1.96) |
| 1b-5d | crypto | +72 (+0.38) | +80 (+0.49) | +81 (+1.20) |
| 1b-21d | smallcap | -62 (-3.10) | -79 (-4.07) | -60 (-3.07) |
| 1b-21d | uncapped | -40 (-2.16) | -53 (-3.06) | -39 (-1.98) |
| 1b-21d | crypto | -24 (-1.35) | -40 (-1.04) | +19 (+0.08) |
| 1c-short | smallcap | +14 (-0.29) | +18 (-0.17) | +14 (-0.15) |
| 1c-short | uncapped | -11 (-1.04) | -9 (-0.76) | -14 (-0.72) |
| 1c-short | crypto | +307 (+2.95) | +291 (+2.82) | +252 (+2.40) |
| 1c-long | smallcap | -11 (+0.25) | -12 (+0.21) | -3 (+0.65) |
| 1c-long | uncapped | -19 (-0.18) | -19 (-0.39) | -10 (-0.25) |
| 1c-long | crypto | +241 (+1.01) | +247 (+1.35) | +219 (+1.30) |


##### Extreme-movers counts and lifts (hypothesis material, not a result)

Names per year that made each move, counted once per name-year, universe-eligible on
the session before the move began; the last column is the number of names eligible on
at least one session that year. Equity counts are survivorship-biased in the direction
stated in the pre-registration (winners over-represented, the −90% set
under-represented: the free listing has no name that went to zero). Lifts: the
within-day percentile of each feature at D−1 among the universe on D−1, at the first
qualifying D per name-year; lift = share of events in the quintile ÷ 0.2. `cap` is
today's cap (static) and is excluded from the autopsy-to-rule selection. In crypto,
`close_to_high_250` and `vol_pctl_250` exist only for names with 250 days of history
(the smaller n).

**smallcap: names per year (eligible on D−1) at each threshold; names eligible that year in the last column**

| year | x2/1d | x3/21d | x5/63d | x10/252d | -0.5/1d | -0.333/21d | -0.2/63d | -0.1/252d | eligible |
|---|---|---|---|---|---|---|---|---|---|
| 2010 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 3 | 480 |
| 2011 | 0 | 2 | 0 | 0 | 3 | 2 | 3 | 4 | 533 |
| 2012 | 1 | 1 | 0 | 1 | 4 | 4 | 3 | 2 | 433 |
| 2013 | 0 | 1 | 1 | 1 | 4 | 4 | 2 | 2 | 469 |
| 2014 | 2 | 2 | 0 | 0 | 7 | 10 | 2 | 6 | 567 |
| 2015 | 1 | 0 | 0 | 0 | 7 | 8 | 7 | 9 | 597 |
| 2016 | 1 | 2 | 0 | 0 | 10 | 9 | 6 | 10 | 671 |
| 2017 | 2 | 5 | 2 | 1 | 10 | 14 | 9 | 18 | 697 |
| 2018 | 1 | 5 | 3 | 1 | 14 | 19 | 14 | 36 | 836 |
| 2019 | 4 | 2 | 3 | 9 | 22 | 24 | 44 | 45 | 846 |
| 2020 | 35 | 43 | 19 | 3 | 24 | 105 | 27 | 0 | 1307 |
| total | 47 | 63 | 28 | 16 | 106 | 200 | 118 | 135 | |

**uncapped: names per year (eligible on D−1) at each threshold; names eligible that year in the last column**

| year | x2/1d | x3/21d | x5/63d | x10/252d | -0.5/1d | -0.333/21d | -0.2/63d | -0.1/252d | eligible |
|---|---|---|---|---|---|---|---|---|---|
| 2010 | 0 | 0 | 0 | 0 | 1 | 2 | 2 | 5 | 1305 |
| 2011 | 0 | 2 | 0 | 0 | 4 | 4 | 3 | 5 | 1550 |
| 2012 | 2 | 1 | 0 | 2 | 5 | 6 | 3 | 2 | 1041 |
| 2013 | 0 | 1 | 1 | 1 | 5 | 4 | 2 | 3 | 974 |
| 2014 | 3 | 4 | 0 | 0 | 9 | 11 | 3 | 9 | 1124 |
| 2015 | 1 | 1 | 0 | 0 | 8 | 9 | 11 | 14 | 1312 |
| 2016 | 1 | 2 | 0 | 0 | 17 | 15 | 9 | 12 | 1553 |
| 2017 | 4 | 8 | 2 | 1 | 11 | 14 | 10 | 21 | 1286 |
| 2018 | 3 | 6 | 4 | 2 | 16 | 23 | 15 | 39 | 1771 |
| 2019 | 5 | 5 | 5 | 13 | 24 | 24 | 53 | 56 | 1772 |
| 2020 | 39 | 53 | 27 | 5 | 32 | 165 | 34 | 0 | 2745 |
| total | 58 | 83 | 39 | 24 | 132 | 277 | 145 | 166 | |

**crypto: names per year (eligible on D−1) at each threshold; names eligible that year in the last column**

| year | x2/1d | x3/21d | x5/63d | x10/252d | -0.5/1d | -0.333/21d | -0.2/63d | -0.1/252d | eligible |
|---|---|---|---|---|---|---|---|---|---|
| 2018 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 21 |
| 2019 | 0 | 3 | 1 | 3 | 0 | 0 | 0 | 3 | 81 |
| 2020 | 2 | 29 | 51 | 64 | 31 | 14 | 0 | 0 | 171 |
| 2021 | 9 | 63 | 59 | 23 | 0 | 20 | 9 | 42 | 227 |
| 2022 | 5 | 7 | 1 | 0 | 6 | 31 | 22 | 21 | 256 |
| total | 16 | 102 | 112 | 90 | 37 | 65 | 31 | 68 | |

**smallcap: 5× over 63 sessions, 28 name-years; within-day percentile of the feature at D−1 among the universe on D−1**

| feature | lift top quintile | lift bottom quintile | median percentile | n |
|---|---|---|---|---|
| close | 1.61 | 1.96 | 0.36 | 28 |
| med_dv_20_prev | 0.71 | 1.96 | 0.34 | 28 |
| rvol_20 | 3.39 | 0.36 | 0.90 | 28 |
| close_to_high_250 | 0.36 | 3.21 | 0.10 | 28 |
| ret_20 | 1.79 | 1.25 | 0.43 | 28 |
| ret_60 | 1.43 | 1.61 | 0.50 | 28 |
| vol_pctl_250 | 1.43 | 0.89 | 0.69 | 28 |
| zscore_20 | 1.07 | 0.36 | 0.53 | 28 |
| shock | 0.89 | 1.25 | 0.41 | 28 |
| cap | 0.71 | 2.14 | 0.22 | 28 |

**smallcap: −80% over 63 sessions, 118 name-years; within-day percentile of the feature at D−1 among the universe on D−1**

| feature | lift top quintile | lift bottom quintile | median percentile | n |
|---|---|---|---|---|
| close | 2.54 | 0.76 | 0.81 | 118 |
| med_dv_20_prev | 0.68 | 1.61 | 0.36 | 118 |
| rvol_20 | 2.08 | 0.51 | 0.73 | 118 |
| close_to_high_250 | 0.68 | 1.78 | 0.31 | 118 |
| ret_20 | 1.99 | 0.55 | 0.69 | 118 |
| ret_60 | 1.48 | 1.19 | 0.54 | 118 |
| vol_pctl_250 | 1.91 | 0.47 | 0.71 | 118 |
| zscore_20 | 2.16 | 0.55 | 0.72 | 118 |
| shock | 2.08 | 0.51 | 0.65 | 118 |
| cap | 0.72 | 1.91 | 0.30 | 118 |

**uncapped: 5× over 63 sessions, 39 name-years; within-day percentile of the feature at D−1 among the universe on D−1**

| feature | lift top quintile | lift bottom quintile | median percentile | n |
|---|---|---|---|---|
| close | 1.28 | 2.82 | 0.17 | 39 |
| med_dv_20_prev | 0.26 | 2.31 | 0.24 | 39 |
| rvol_20 | 3.59 | 0.13 | 0.93 | 39 |
| close_to_high_250 | 0.26 | 3.46 | 0.07 | 39 |
| ret_20 | 1.28 | 2.44 | 0.25 | 39 |
| ret_60 | 1.28 | 2.18 | 0.37 | 39 |
| vol_pctl_250 | 1.67 | 0.77 | 0.69 | 39 |
| zscore_20 | 0.77 | 0.90 | 0.51 | 39 |
| shock | 0.64 | 1.79 | 0.29 | 39 |
| cap | 0.00 | 2.69 | 0.19 | 39 |

**uncapped: −80% over 63 sessions, 145 name-years; within-day percentile of the feature at D−1 among the universe on D−1**

| feature | lift top quintile | lift bottom quintile | median percentile | n |
|---|---|---|---|---|
| close | 2.24 | 0.83 | 0.75 | 145 |
| med_dv_20_prev | 0.59 | 1.79 | 0.29 | 145 |
| rvol_20 | 2.21 | 0.41 | 0.75 | 145 |
| close_to_high_250 | 0.52 | 2.00 | 0.26 | 145 |
| ret_20 | 2.14 | 0.59 | 0.73 | 145 |
| ret_60 | 1.45 | 1.14 | 0.51 | 145 |
| vol_pctl_250 | 1.76 | 0.76 | 0.65 | 145 |
| zscore_20 | 2.10 | 0.48 | 0.72 | 145 |
| shock | 1.86 | 0.52 | 0.65 | 145 |
| cap | 0.52 | 2.28 | 0.26 | 145 |

**crypto: 5× over 63 sessions, 112 name-years; within-day percentile of the feature at D−1 among the universe on D−1**

| feature | lift top quintile | lift bottom quintile | median percentile | n |
|---|---|---|---|---|
| close | 0.40 | 1.74 | 0.34 | 112 |
| med_dv_20_prev | 0.49 | 1.56 | 0.37 | 112 |
| rvol_20 | 1.56 | 0.80 | 0.58 | 112 |
| close_to_high_250 | 0.45 | 1.27 | 0.38 | 55 |
| ret_20 | 0.71 | 1.07 | 0.46 | 112 |
| ret_60 | 0.73 | 1.15 | 0.47 | 96 |
| vol_pctl_250 | 1.00 | 1.55 | 0.35 | 55 |
| zscore_20 | 0.89 | 1.12 | 0.49 | 112 |
| shock | 0.62 | 1.47 | 0.40 | 112 |

**crypto: −80% over 63 sessions, 31 name-years; within-day percentile of the feature at D−1 among the universe on D−1**

| feature | lift top quintile | lift bottom quintile | median percentile | n |
|---|---|---|---|---|
| close | 1.13 | 0.97 | 0.56 | 31 |
| med_dv_20_prev | 1.29 | 0.97 | 0.56 | 31 |
| rvol_20 | 3.23 | 0.32 | 0.90 | 31 |
| close_to_high_250 | 2.33 | 0.33 | 0.78 | 15 |
| ret_20 | 3.06 | 0.97 | 0.88 | 31 |
| ret_60 | 3.20 | 0.80 | 0.92 | 25 |
| vol_pctl_250 | 3.33 | 0.33 | 0.88 | 15 |
| zscore_20 | 3.06 | 0.81 | 0.87 | 31 |
| shock | 2.42 | 0.81 | 0.77 | 31 |

##### Confirm era

No catalog signal (1a–1e) met the interesting threshold in dev, so **no catalog signal
was run on the confirm era**; the equity confirm era (2021–2023) and the crypto confirm
era (2023–2024) are unread for all 18 catalog rows. Four autopsy-derived rules did clear
the dev threshold (next subsection) and were run once on the equity confirm era, with
no parameter change; the crypto confirm era was not read by anything in this wave.

##### Autopsy to rule (step D2, amendment A2)

**Selection**, applied by the locked procedure to the committed lift table (`40eac00`):
the three features with the highest lift ≥ 1.5 per group, from the `uncapped` table for
equities and the `crypto` table for crypto, `cap` excluded, ties by event count then
name. Twelve rules, eighteen ledger rows.

| market (selected on) | group | rule | feature | quintile | selection lift | events |
|---|---|---|---|---|---|---|
| equity (uncapped) | 5× / 63 | `a2r-up-rvol_20` | rvol_20 | top | 3.59 | 39 |
| equity (uncapped) | 5× / 63 | `a2r-up-close_to_high_250` | close_to_high_250 | bottom | 3.46 | 39 |
| equity (uncapped) | 5× / 63 | `a2r-up-close` | close | bottom | 2.82 | 39 |
| equity (uncapped) | −80% / 63 | `a2r-down-close` | close | top | 2.24 | 145 |
| equity (uncapped) | −80% / 63 | `a2r-down-rvol_20` | rvol_20 | top | 2.21 | 145 |
| equity (uncapped) | −80% / 63 | `a2r-down-ret_20` | ret_20 | top | 2.14 | 145 |
| crypto (crypto) | 5× / 63 | `a2r-up-close` | close | bottom | 1.74 | 112 |
| crypto (crypto) | 5× / 63 | `a2r-up-med_dv_20_prev` | med_dv_20_prev | bottom | 1.56 | 112 |
| crypto (crypto) | 5× / 63 | `a2r-up-rvol_20` | rvol_20 | top | 1.56 | 112 |
| crypto (crypto) | −80% / 63 | `a2r-down-vol_pctl_250` | vol_pctl_250 | top | 3.33 | 15 |
| crypto (crypto) | −80% / 63 | `a2r-down-rvol_20` | rvol_20 | top | 3.23 | 31 |
| crypto (crypto) | −80% / 63 | `a2r-down-ret_60` | ret_60 | top | 3.20 | 25 |

Each rule fires on D when the feature's within-day percentile among the universe on D is
≥ 0.8 (top) or ≤ 0.2 (bottom): by construction it matches about a fifth of the universe
every session, so these are baskets, not picks. Long for the 5× group, short /
long-avoid for the −80% group, 63-session decision horizon, next-open fill, no
re-entry while held, the common cost schedule and controls. "Made the move" is the
number (share) of traded candidates whose 63-session forward return was ≥ +400% (up
rules) or ≤ −80% (down rules); "universe base rate" is the mean over sessions of the
share of the universe that made the same move from the same fill.

**Dev era** (equities 2010–2020, crypto 2018–2022; in-sample by construction, since the
features were chosen on these years):

| rule | universe | dir | match / day | trades | days | net @0 | @base | @high | z @0 | z @base | top-10 share | z w/o top 10 | half1 / half2 @base | made the move | universe base rate | realized lift | placebo z @0 | planted shift | interesting | 
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `a2r-up-rvol_20` | smallcap | long | 20.3% | 6,021 | 2,261 | -18 | **-70** | -121 | -1.44 | **-2.23** | 7.0% | -4.25 | -165 / -17 | 7 (0.12%) | 0.03% | 4.39 | -0.28 | +0.75 | no |
| `a2r-up-close_to_high_250` | smallcap | long | 19.8% | 4,287 | 1,919 | +22 | **-29** | -80 | -0.75 | **-1.39** | 7.9% | -3.17 | -86 / +5 | 6 (0.14%) | 0.03% | 5.29 | -0.80 | +0.61 | no |
| `a2r-up-close` | smallcap | long | 19.8% | 4,000 | 1,915 | +494 | **+440** | +385 | +6.08 | **+5.28** | 7.5% | +4.75 | +253 / +554 | 4 (0.10%) | 0.03% | 3.78 | +6.10 | +0.72 | yes |
| `a2r-up-rvol_20` | uncapped | long | 20.2% | 11,430 | 2,543 | +28 | **-16** | -60 | -1.20 | **-2.21** | 6.6% | -3.11 | -111 / +43 | 9 (0.08%) | 0.01% | 5.35 | -0.47 | +1.10 | no |
| `a2r-up-close_to_high_250` | uncapped | long | 19.9% | 8,517 | 2,308 | +7 | **-36** | -80 | -2.02 | **-2.74** | 7.8% | -4.60 | -116 / +16 | 7 (0.08%) | 0.01% | 5.58 | -0.97 | +0.77 | no |
| `a2r-up-close` | uncapped | long | 19.9% | 7,776 | 2,273 | +392 | **+346** | +299 | +5.86 | **+5.10** | 7.2% | +5.11 | +218 / +430 | 4 (0.05%) | 0.01% | 3.50 | +6.51 | +0.78 | yes |
| `a2r-down-close` | smallcap | short | 20.3% | 3,834 | 1,878 | +577 | **+530** | +483 | +7.67 | **+7.00** | 6.2% | +9.83 | +431 / +589 | 28 (0.73%) | 0.24% | 2.99 | +7.95 | +0.70 | yes |
| `a2r-down-rvol_20` | smallcap | short | 20.3% | 6,021 | 2,261 | +18 | **-33** | -85 | +1.44 | **+0.65** | 7.2% | +2.29 | +60 / -85 | 29 (0.48%) | 0.24% | 1.97 | +0.28 | +0.75 | no |
| `a2r-down-ret_20` | smallcap | short | 20.3% | 9,495 | 2,535 | +69 | **+20** | -30 | -0.05 | **-1.25** | 5.9% | -0.98 | -89 / +82 | 34 (0.36%) | 0.24% | 1.46 | +0.49 | +1.19 | no |
| `a2r-down-close` | uncapped | short | 20.2% | 8,908 | 2,389 | +366 | **+333** | +299 | +8.70 | **+7.88** | 4.7% | +9.36 | +288 / +361 | 31 (0.35%) | 0.18% | 1.95 | +9.12 | +1.12 | yes |
| `a2r-down-rvol_20` | uncapped | short | 20.2% | 11,430 | 2,543 | -28 | **-72** | -116 | +1.20 | **+0.18** | 6.8% | +0.75 | +21 / -130 | 32 (0.28%) | 0.18% | 1.57 | +0.47 | +1.10 | no |
| `a2r-down-ret_20` | uncapped | short | 20.2% | 19,391 | 2,676 | +73 | **+33** | -6 | +0.98 | **-0.45** | 6.5% | -0.43 | -23 / +70 | 42 (0.22%) | 0.18% | 1.21 | +1.01 | +1.70 | no |
| `a2r-up-close` | crypto | long | 19.0% | 547 | 454 | +1901 | **+1841** | +1801 | +1.54 | **+1.47** | 41.8% | -2.45 | +341 / +2314 | 18 (3.29%) | 1.21% | 2.73 | +1.03 | +0.06 | no |
| `a2r-up-med_dv_20_prev` | crypto | long | 19.0% | 1,013 | 698 | +479 | **+419** | +379 | +1.04 | **+0.91** | 23.8% | -2.24 | +193 / +467 | 28 (2.76%) | 1.21% | 2.29 | +0.52 | +0.11 | no |
| `a2r-up-rvol_20` | crypto | long | 22.0% | 1,149 | 821 | -142 | **-202** | -242 | +0.33 | **+0.18** | 18.1% | -2.35 | -56 / -264 | 26 (2.26%) | 1.21% | 1.87 | +0.97 | +0.13 | no |
| `a2r-down-vol_pctl_250` | crypto | short | 12.0% | 1,102 | 722 | +18 | **-42** | -82 | -0.31 | **-0.47** | 17.3% | +2.29 | +10 / -56 | 0 (0.00%) | 0.15% | 0.00 | +0.28 | +0.14 | no |
| `a2r-down-rvol_20` | crypto | short | 22.0% | 1,149 | 821 | +142 | **+82** | +42 | -0.33 | **-0.49** | 18.3% | +1.82 | -64 / +144 | 4 (0.35%) | 0.15% | 2.33 | -0.97 | +0.13 | no |
| `a2r-down-ret_60` | crypto | short | 20.0% | 929 | 677 | +382 | **+322** | +282 | +0.68 | **+0.54** | 17.7% | +4.04 | -79 / +480 | 5 (0.54%) | 0.15% | 3.60 | -0.83 | +0.12 | no |

Horizon curve, dev, gross excess per trade in bps (z at zero cost):

| rule | universe | 1 | 5 | 21 | 63 * | 126 | 252 |
|---|---|---|---|---|---|---|---|
| `a2r-up-rvol_20` | smallcap | -28 (-2.64) | -43 (-2.98) | -63 (-2.06) | -18 (-1.44) | -37 (-1.16) | -279 (-0.55) |
| `a2r-up-close_to_high_250` | smallcap | +1 (-0.52) | -5 (+0.44) | -65 (-1.23) | +22 (-0.75) | -30 (-1.14) | -243 (-0.73) |
| `a2r-up-close` | smallcap | +12 (+0.81) | +69 (+2.21) | +176 (+3.93) | +494 (+6.08) | +941 (+6.75) | +1414 (+7.45) |
| `a2r-up-rvol_20` | uncapped | -19 (-2.25) | -38 (-2.15) | -46 (-2.02) | +28 (-1.20) | +85 (-0.69) | -67 (-0.88) |
| `a2r-up-close_to_high_250` | uncapped | -10 (-1.07) | -17 (-2.07) | -59 (-2.48) | +7 (-2.02) | -22 (-3.06) | -306 (-3.07) |
| `a2r-up-close` | uncapped | +6 (+0.72) | +41 (+2.08) | +127 (+4.52) | +392 (+5.86) | +797 (+8.38) | +1299 (+9.33) |
| `a2r-down-close` | smallcap | +19 (+1.85) | +87 (+4.13) | +204 (+5.05) | +577 (+7.67) | +1002 (+10.14) | +1679 (+12.16) |
| `a2r-down-rvol_20` | smallcap | +28 (+2.64) | +43 (+2.98) | +63 (+2.06) | +18 (+1.44) | +37 (+1.16) | +279 (+0.55) |
| `a2r-down-ret_20` | smallcap | +3 (-0.40) | +21 (+0.73) | +27 (+0.79) | +69 (-0.05) | +44 (-1.24) | -21 (-0.74) |
| `a2r-down-close` | uncapped | +13 (+2.21) | +43 (+4.41) | +122 (+6.41) | +366 (+8.70) | +617 (+10.44) | +1109 (+15.63) |
| `a2r-down-rvol_20` | uncapped | +19 (+2.25) | +38 (+2.15) | +46 (+2.02) | -28 (+1.20) | -85 (+0.69) | +67 (+0.88) |
| `a2r-down-ret_20` | uncapped | +3 (+0.27) | +15 (+0.38) | +23 (+0.68) | +73 (+0.98) | +56 (-0.62) | -41 (-1.49) |
| `a2r-up-close` | crypto | +19 (+0.45) | +41 (+0.05) | +220 (+0.56) | +1901 (+1.54) | +5671 (+2.46) | +13601 (+2.92) |
| `a2r-up-med_dv_20_prev` | crypto | +30 (+1.17) | -60 (+0.32) | +4 (+0.34) | +479 (+1.04) | +516 (+0.81) | +681 (-0.34) |
| `a2r-up-rvol_20` | crypto | +17 (+0.64) | +4 (+0.78) | -131 (-0.08) | -142 (+0.33) | +364 (+1.24) | -2136 (-0.78) |
| `a2r-down-vol_pctl_250` | crypto | +11 (-0.09) | -122 (-1.60) | -216 (-1.49) | +18 (-0.31) | -504 (-0.76) | +422 (+0.45) |
| `a2r-down-rvol_20` | crypto | -17 (-0.64) | -4 (-0.78) | +131 (+0.08) | +142 (-0.33) | -364 (-1.24) | +2136 (+0.78) |
| `a2r-down-ret_60` | crypto | +7 (-0.35) | +8 (-0.69) | +173 (+0.89) | +382 (+0.68) | +855 (+0.90) | +876 (+1.25) |

**Confirm era** (equities 2021-01-01 → 2023-12-31; the four rules that cleared the dev
threshold, run once, same rule):

| rule | universe | dir | match / day | trades | days | net @0 | @base | @high | z @0 | z @base | top-10 share | z w/o top 10 | half1 / half2 @base | made the move | universe base rate | realized lift | placebo z @0 | planted shift | interesting | 
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `a2r-up-close` | smallcap | long | 19.9% | 2,666 | 640 | +762 | **+709** | +656 | +6.41 | **+5.91** | 19.7% | +5.86 | +836 / +528 | 3 (0.11%) | 0.03% | 3.56 | +5.48 | +0.46 | yes |
| `a2r-up-close` | uncapped | long | 20.0% | 4,416 | 664 | +492 | **+445** | +397 | +5.58 | **+4.80** | 19.9% | +4.19 | +617 / +215 | 5 (0.11%) | 0.03% | 4.23 | +4.03 | +0.77 | yes |
| `a2r-down-close` | smallcap | short | 20.1% | 2,600 | 618 | +959 | **+915** | +871 | +7.37 | **+6.96** | 20.2% | +8.88 | +864 / +975 | 39 (1.50%) | 0.43% | 3.48 | +7.78 | +0.45 | yes |
| `a2r-down-close` | uncapped | short | 20.1% | 5,139 | 664 | +446 | **+415** | +383 | +5.87 | **+5.37** | 22.8% | +5.37 | +464 / +362 | 43 (0.84%) | 0.29% | 2.90 | +8.06 | +0.80 | yes |

Horizon curve and per year, confirm, gross (z) and per-year net at base (z):

| rule | universe | 1 | 5 | 21 | 63 * | 126 | 252 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|---|---|---|---|---|
| `a2r-up-close` | smallcap | +34 (+1.02) | +81 (+1.97) | +333 (+5.00) | +762 (+6.41) | +1179 (+9.23) | +1986 (+10.64) | +923 (+4.93) | +732 (+4.47) | +330 (+1.61) |
| `a2r-up-close` | uncapped | +24 (+1.12) | +32 (+1.80) | +190 (+3.22) | +492 (+5.58) | +769 (+6.69) | +1280 (+8.10) | +703 (+4.18) | +381 (+3.28) | +171 (+0.76) |
| `a2r-down-close` | smallcap | +48 (+2.67) | +104 (+2.81) | +316 (+3.86) | +959 (+7.37) | +1557 (+11.37) | +2393 (+18.57) | +937 (+2.99) | +843 (+5.85) | +983 (+3.46) |
| `a2r-down-close` | uncapped | +23 (+2.72) | +61 (+3.67) | +191 (+6.85) | +446 (+5.87) | +719 (+9.11) | +1225 (+10.41) | +621 (+1.96) | +292 (+5.22) | +364 (+4.17) |

**Reading, rule by rule.**

- *Volatility (`rvol_20`, top quintile) describes both tails and predicts neither.* It
  was selected for the 5× group (lift 3.6) and for the −80% group (2.2), so the long
  and the short rule hold the same basket with opposite signs: −70 / −16 bps net
  (long) and −33 / −72 (short) in equities, −202 / +82 in crypto. The feature says
  "this name will move", not which way. Verdict `null` on all six rows.
- *Distance below the 250-day high (bottom quintile, long)* describes the equity 5×
  names (lift 3.5) and loses money prospectively: −29 / −36 bps net, z −1.4 / −2.7, and
  negative at 126 and 252 sessions. The fallen names that later multiplied were a few
  among many that kept falling. `null`.
- *Recent gain (`ret_20`, top quintile, short)* for the −80% group: +20 / +33 bps net,
  z −1.3 / −0.5: a blow-off top precedes some collapses and nothing on average. `null`.
- *Crypto*: cheap (bottom price, +1,841 bps gross at 63 sessions but z 1.47, 42% of the
  P&L from ten days, sign flips with those days removed), illiquid (+419, z 0.9), and
  the three down-group features (−42 to +322, |z| < 0.6): all `null`. The crypto 5× hit
  rate among matches is 2–3% against a 1.2% base rate: a real lift and still a
  1-in-30 pick.
- *Price level, equities (`close`): the one pair that cleared the bar, and it is an
  artifact under the pre-registered rules.* Long the cheapest quintile: +440 / +346 bps
  net at base over 63 sessions (z +5.3 / +5.1) in dev and +709 / +445 (z +5.9 / +4.8)
  in confirm. Short the most expensive quintile: +530 / +333 (z +7.0 / +7.9) in dev
  and +915 / +415 (z +7.0 / +5.4) in confirm. Both legs beat the equal-weight universe
  in every year of both eras, the curves rise monotonically to 252 sessions, and the
  stale-signal placebo is as significant as the signal (z +6.1, +6.5, +8.0, +9.1).
  Rule 4 fails on the placebo, so the verdict is `artifact` on all four rows, and the
  reason the placebo fails is the reason the result should not be believed: a name's
  price quintile is a persistent characteristic, so the "lagged" rule is the same
  basket. What the four rows measure is a monotonic price-level premium in *this
  sample*: cheap names outrun the universe, the universe outruns expensive names,
  by about 18 percentage points a year net. That is an order of magnitude above the
  small-cap or low-price premia in delisting-complete data, and it is exactly what a
  current listing manufactures: delistings concentrate in the cheapest quintile of a
  40%-vol universe, every name in this sample survived to 2026, so the cheap names here
  are the ones that recovered. The confirm era (2021–2023, a small-cap drawdown with
  many delistings whose survivors rebounded) is the worst possible place to test it.
  The hit rate for the original move says the same: 4 of 4,000 cheap-quintile trades
  went on to 5× (0.10%, a 3.8× lift on a 0.03% base rate). The feature finds past
  winners at four times the base rate and still names one in a thousand.
- *Which features describe past movers but do not predict:* volatility, distance
  below the 52-week high, recent gain, and (in crypto) illiquidity and price. *Price
  level in equities* predicts in this sample and cannot be separated from survivorship
  on free data; it is not evidence either way until it is run on a delisting-complete
  universe with delisting returns.

#### Interpretation

- **Was the pre-registered "interesting" criterion met?** No, for every catalog
  signal: 18 of 18 rows are `null` in dev, so none went to the confirm era. Of the
  autopsy-derived rules, 14 of 18 are `null` and 4 are `artifact` (dev and confirm
  both clear rules 1–3; rule 4 fails on the placebo). Zero graduates. The ledger has
  36 rows for this wave.
- **What does this tell us about the hypothesis** (do historical signals predict
  drops and rises over the next days to weeks)?
  - *Post-shock continuation (1a) exists before costs and not after.* The universe
    beats the −2σ names over the next five sessions by +25 bps (`smallcap`, z +3.0),
    +1 bps (`uncapped`, z +2.8) and +54 bps (crypto, z +3.6) gross; at the base
    schedule that is −18, −34 and −6 bps. In crypto the gross continuation grows to
    +102 bps at 21 sessions and +148 at 63 (z 1.9, 1.3) and the day-weighted edge is
    +161 ± 62 bps at base; the trade-weighted mean, which is the pre-registered
    quantity, is −6. As a long-avoidance rule (zero cost) it is worth +25 / +54 bps
    per avoided name over a week: real, small, and not a strategy.
  - *Up-shock continuation (1b) is reversal in equities.* A +2σ day on 2× volume is
    followed by −45 / −28 bps gross over five sessions and −79 / −53 over 21 (z −3 to
    −4), in both halves of the era and in nine of eleven years; the survivorship bias
    favours this long and it still loses. The high-volume-return premium does not show
    up at this resolution. Crypto: +80 gross at five sessions (z +0.5), −40 at 21.
  - *Slide-cohort momentum (1c) is flat in equities* (−24 to −56 bps net, |z| ≤ 2.3,
    gross within ±20 bps) in both legs. In crypto the short leg is the only
    positive-and-costed cell of the wave (+231 bps net, z +2.4) on 361 trades over
    122 days with 38% of the P&L from ten days: below the counts floor and the z
    floor. The long leg is +187 bps net at z +1.0.
  - *Crypto time-series momentum (1d) cannot be decided at this sample size.* Long
    BTC only when its 30- and 90-day returns are positive earned +32% a year against
    +1% for buy-and-hold over 2018–2022 (ETH +63% vs +1%), with half the drawdown and
    a third of the time in the market, and the weekly z is +0.29 / +0.47. The weekly
    SE is 52–67 bps, so the rank-mode bar (z ≥ 3 over ≥ 36 weeks) requires a mean
    weekly edge of 150–200 bps, which is 80–100 percentage points a year. The planted
    +50 bps a week (26 pp a year) moves z by only 0.7–1.0. The pre-registered test has
    no power for this signal; the point estimates are large and their sign flips by
    year (+76, −1, −70, −45, +80 pp). This is a null against the rule, not evidence
    against trend-following.
  - *Crypto cross-sectional momentum (1e) is negative*: −12 pp a year net (z −0.5),
    −37 and −59 pp in 2021 and 2022. The 1–4 week premium of the literature does not
    appear in the top-100 at a weekly 01:00 UTC fill with three-week holds.
  - *Extreme movers.* The base rates decide the premise: in the free equity sample a
    5× quarter happens to 0.1–0.2% of eligible names a year (27 of the 39 uncapped
    name-years are 2020) and a 10× year to 24 names in eleven years; −80% quarters are
    four times as common even with the delisted names missing. In crypto a 5× quarter
    happened to 20–25% of the top-100 in 2020 and 2021 and to 1 name in 2022. The
    autopsy says what the owner's premise predicts, that the movers looked alike the
    day before (volatile, far below their highs, cheap, illiquid, or, for the
    collapses, recently up), and the prospective runs say that those descriptions do
    not pick direction. The one feature that does, price level, is confounded with
    survival.
  - *Horizon grid.* No catalog signal's curve improves toward a horizon that would
    rescue it; where the long horizons are positive (1a and 1c-long in equities at
    126–252 sessions, +41 to +127 bps gross) the z is under 1.5. The crypto intraday
    horizons (01:00 → 04:00 and → 12:00 UTC) are within ±17 bps of zero for every
    signal: nothing is left on the table in the first hours after the fill.
- **What does it tell us about the harness?** The refactor reproduces the v1 script
  cell for cell on both markets and the committed v1 crypto tables to the basis point.
  The zero-cost placebo is flat for every event signal (|z| ≤ 1.1) and for the rank
  signals (|z| ≤ 1.8), and the planted +50 bps moves z by 2–5 units in equities and
  0.3–1.1 in crypto, as in v1: equity samples would have seen a real +50 bps, crypto
  event samples would not have resolved one against zero (1c-short crypto SE 148 bps).
  Two things the wave taught: (1) Binance reuses symbols across token swaps and relists,
  which the v1 screen had not caught because its horizon was short; the segmentation
  rule is now in the data layer and the pre-fix tables are kept. (2) The lag-20
  stale-signal placebo tests event-ness: for a persistent characteristic it reproduces
  the signal, so it cannot clear a rank-type rule and should not be the only
  artifact check for one; a random-quintile or long-lag placebo belongs in the
  protocol for rank mode. The placebo-at-base-cost figure is mechanically negative
  and is reported, not used. The cost schedule remains a placeholder (the owner's
  quote sample is still the fix); the `spec` column shows what the uncalibrated
  Abdi–Ranaldo model would charge (−350 to −690 bps per trade), which is why no
  decision here rests on it.
- **Confidence.** High for the equity catalog nulls: every bias in the sample favours
  the long signals, the samples are 5,700–37,900 trades over 1,860–2,690 entry days,
  and the estimates are 1.5–6.5 standard errors below the threshold. High for 1e and
  for the equity autopsy nulls. Medium-high for the crypto event nulls (hundreds of
  entry days, heavy day clustering, one borderline cell on 361 trades). Low for 1d in
  either direction: the test is underpowered by a factor of ten. The four `artifact`
  rows are confidently *not* evidence of an edge and confidently *not* evidence
  against one; they are the survivorship bias made visible, which is what the
  pre-registration said a long-only positive on this data would be.

#### Next action (per the pre-registered decision rules)

1. **Rule 1 (every catalog row `null`): no confirm run, no further variant, no build.**
   Epic 7 (slide-cohort momentum) is not promoted; the continuation effect does not
   survive the cost schedule (proposal, week-1 decision: no).
2. **Rule 2 (autopsy rules): four `artifact`, fourteen `null`.** No autopsy-derived
   signal graduates. The price-level pair is recorded as the wave's one open question
   (below); it earns nothing until it is run on a delisting-complete universe.
3. **Rule 3: wave 2 is next** (rank mode on equities: 2a 12–1 momentum, 2b 52-week-high
   proximity, 2d weekly reversal in liquid names), with two protocol changes to propose
   to the PM before it runs, as new pre-registrations rather than edits: a rank-mode
   placebo that is not defeated by persistence (random quintile, or a 250-session
   lag), and a rank-mode power statement (weeks × SE) next to the z bar, since the
   current bar cannot be met by any plausible monthly or weekly premium in 11 years
   of data.
4. **Rule 4:** the extreme-movers tables are filed as hypothesis material; the three
   autopsy pre-registrations per direction have been spent in this wave, so wave 3's
   signal 3c draws nothing further from this table without a new proposal.
5. **Record in `penumbra-specs`:** this entry, the ledger, and the survivorship finding
   as a DECISIONS note ("Free data cannot test a price-sorted, quarter-horizon
   equity rule"). Separate PR on that repo, not made from this branch.
6. **No purchase.** Nothing here meets the graduation rule, so no Sharadar data is
   bought on this wave's account. The price-level question is the one result a
   delisting-complete sample would decide in an afternoon; whether that justifies the
   purchase on its own is the owner's call, and the proposal's own words are that free
   counts and lifts are provisional until then.

#### Open questions / followups

- **Survivorship, made concrete.** A free, bounded test of the price-level pair
  exists before any purchase: rebuild the universe from archived Nasdaq Trader
  directories (one per year, via the Wayback Machine if the egress policy allows it)
  so that names delisted since appear in their years, and re-run `a2r-up-close` and
  `a2r-down-close` with the delisted names' last available bars. If the premium halves
  or reverses, the four `artifact` rows are explained; if it survives, buy the data.
- **1d is undecided, not dead.** Trend-following on BTC and ETH shows the shape the
  literature reports (half the drawdown, a third of the exposure, higher return) and a
  z near zero on 259 weeks. A longer history (BTC from 2014 on another venue) or a
  daily evaluation would quadruple the observations; the bar itself needs the power
  statement above.
- **1a as a filter, not a trade.** The gross five-session continuation after a −2σ
  day (+25 bps `smallcap`, +54 bps crypto, z 3.0 / 3.6, placebo flat) is a usable
  avoidance rule for any long signal in this program: do not buy a −2σ name for a
  week. It costs nothing and it is the one robust directional read of the wave.
- **1b's reversal** (−45 / −79 bps over 5 / 21 sessions after a +2σ day on 2× volume,
  z −3 to −4, nine of eleven years) is a short-side candidate for a later wave if
  shorting is ever primary; as a long-avoid it says the same as 1a from the other
  side: do not chase a volume spike.
- The crypto intraday horizons are flat, so the 01:00 UTC fill convention is not
  leaving anything on the table; a 00:00 → 01:00 read (the hour between the signal
  close and the fill) was not pre-registered and was not computed.
- Equities' 2010–2014 universes are half the size of 2015–2020 in a current listing
  (median 230 vs 332 names in `smallcap`), another face of the same bias.

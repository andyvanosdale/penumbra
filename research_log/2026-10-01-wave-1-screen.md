### 2026-10-01 — Wave 1 of the signal-screening program (1a–1e and the extreme-movers counts)

**Phase:** 0 (screening program, wave 1; no build)
**Commit:** pre-registration = the commit that adds this file (hash recorded in
`research_log.md` and `ledger.md` once it exists) · code and results: filled in under
"Run details" when they are committed
**Status:** pre-registered
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

*(dev era first; confirm era, if any, in its own subsection after the dev tables are committed)*

#### Interpretation

*(written last)*

#### Next action (per the pre-registered decision rules)

*(written last)*

#### Open questions / followups

*(written last)*

### 2026-10-07 — Intraday wave of the signal-screening program (i1–i8 on 5-minute IEX bars)

**Phase:** 0 (screening program, intraday wave; no build)
**Commit:** the pre-registration commit is the first commit on `screen/intraday` after the
merge of `screen/wave-1` and the Alpaca puller branch; the data layer, dev tables, confirm
tables, ledger and interpretation commits are named in `research_log.md` as they land
**Status:** pre-registered
**Branch:** `screen/intraday`
**Brief:** `andyvanosdale/penumbra-specs` branch `claude/zen-clarke-ocjx6t`,
`proposals/2026-10-07-intraday-wave-brief.md` (steps A to D; the signal catalog i1–i8; eras,
universe, fills, horizons, costs, statistic and controls transcribed below). Program frame:
`proposals/2026-09-30-signal-screening-pivot.md` (protocol, graduation rule, ledger).
Conventions: `research_log/2026-10-01-wave-1-screen.md` and `experiments/screen/`.
**Predecessors:** wave 1 (`2026-10-01-wave-1-screen.md`: 36 ledger rows, zero graduates; the
open question "1a as a filter, not a trade" and the amendment A1 note that equity intraday
horizons need minute bars and a separate pre-registered wave; this is that wave).

**Owner's question.** Do the effects the daily screens saw (post-shock continuation that is
gross-positive and cost-negative; up-shock reversal) and the documented intraday regularities
(first-half-hour and last-hour momentum, gap fades, VWAP reversion, the overnight premium) exist
at intraday entries on a liquid equity universe, at a size that survives the cost schedule?

#### Pre-registration (written BEFORE any 5-minute bar of this wave was read)

Nothing below is fitted. Every rule is transcribed from the brief's catalog or fixed here, in
writing, before the first bar is read. A parameter change after a result is read is a new
ledger row, never an edit; at most three variants per signal (a fourth raises the dev z bar to
3.5 and is flagged in the ledger). Where the brief leaves a mechanical detail open (what "the
10:00 bar" is, what happens when the 15:55 bar is missing, which universe is the comparator),
the choice is made here, once, and is part of the locked text.

**Disclosure.** Before this text was written, one batch file of the cache
(`bars/5Min/2021-03/batch_010.parquet`) was opened to confirm the column schema, the UTC
timestamp convention and that the timestamp is the bar's start; and the manifest's row count
per month was listed. No return, no feature and no statistic was computed from any bar.

##### Hypotheses (one per signal)

- **i1 Opening-range breakout (long).** A name whose first half hour closes above the opening
  range on at least twice its usual first-half-hour volume continues to outperform the same-day
  universe from 10:00 to the close by ≥ +50 bps net of the base schedule. Prior: retail
  folklore; weak academic support; here to be tested.
- **i2 Gap continuation versus fade.** An opening gap of at least 2 trailing daily vols
  continues: the up gap outperforms the universe from 09:35 to the close (long leg, i2-up),
  the down gap underperforms it (short / long-avoid leg, i2-down), each ≥ +50 bps net. The
  fade reading is the same two rows with the sign reversed and is read from the same tables.
  Prior: fades are documented in large caps; continuation in small caps on news.
- **i3 First-half-hour momentum.** The top decile of the universe by 09:30 → 10:00 return
  outperforms the universe from 10:00 to the close (i3-top, long); the bottom decile
  underperforms it (i3-bottom, short / long-avoid); each ≥ +50 bps net. Prior: Gao, Han, Li
  and Zhou (2018), the first half hour predicts the last.
- **i4 Last-hour momentum (long).** The top decile by 09:30 → 15:00 return outperforms the
  universe from 15:30 to the close by ≥ +50 bps net. Same prior; the intraday momentum of that
  paper is concentrated in the last half hour.
- **i5 Overnight versus intraday.** Returns accrue overnight (Lou, Polk and Skouras 2019):
  the universe bought at 15:55 and sold at the next open earns a positive mean net of the full
  round trip (i5-all, a cost question above all), and names in the top quintile of the prior
  overnight return earn more overnight than the universe (i5-q5, long; the bottom quintile
  i5-q1 is the mirror row), ≥ +50 bps net per trade.
- **i6 Post-shock next-day path.** Wave 1's events (1a: `shock` ≤ −2.0; 1b: `shock` ≥ +2.0 and
  `vol_ratio_20` ≥ 2.0 on D) carry their daily effect into the first hours of D+1: the −2σ
  names underperform the universe from 09:35 (and from 10:30) to the close (i6-1a, short /
  long-avoid), and the +2σ-on-volume names, which reversed in wave 1 over 5 and 21 sessions,
  are tested long as the brief specifies (i6-1b, long), each ≥ +50 bps net. The daily
  next-open fill of wave 1, run on this era, is the baseline.
- **i7 VWAP give-back (short / long-avoid).** A name at least 2% above its session VWAP at
  12:00 on a day with at least twice its usual volume through 12:00 gives it back:
  underperforms the universe from 12:00 to the close by ≥ +50 bps net. Prior: VWAP is the
  institutional execution benchmark; mean reversion to it is the folklore and the mechanism
  (sell programs lean on it).
- **i8 Autopsy, intraday (hypothesis material, then up to three fixed rules per direction).**
  No hypothesis is tested by pass 1. It records, for the one-session 2× movers and −50% movers
  of the dev era, the lift ratios of four intraday features at D−1. Pass 2 runs the selected
  features as fixed prospective rules (long for the up group, short / long-avoid for the down
  group) at 09:35 on D+1 to the close; a dev result for them is in-sample by construction and
  is not evidence; only the confirm era is.

##### Common protocol (locked; identical for every signal)

- **Data.** Alpaca Market Data, IEX feed, 5-minute bars, `adjustment=raw`, pulled by
  `experiments/pull_alpaca_bars.py` on 2026-10-01 → 2026-10-07 into `~/penumbra-data/alpaca`
  (`bars/5Min/<YYYY-MM>/batch_*.parquet`, `universe/common_stock_list.csv`, `manifest.jsonl`;
  columns symbol, ts (UTC, bar start), open, high, low, close, volume, trade_count, vwap).
  Coverage 2020-07-27 → 2023-12-31 for 4,884 current-listing common stocks (months 2016-01 to
  2019-05 in the manifest hold the puller's probes and are empty or near-empty; they are not
  read). The feed prints a bar only where a trade printed on IEX in that window: coverage is
  full for liquid names and sparse for thin ones; IEX volume and VWAP are IEX's share of the
  tape, not the consolidated figures; the IEX "open" is the first IEX trade in the window, not
  the primary-listing opening print. Daily bars: yfinance (`auto_adjust=False`) 2009-01-01 →
  2023-12-31 for the same symbol list, pulled by the wave-1 stage (`experiments/screen/data.py`)
  on this machine, and the wave-1 feature panel built from them: these supply the session
  calendar, the universes, `shock`, `vol_ratio_20`, `rvol_20`, `med_dv_20_prev`, the adjusted
  opens and closes for the next-open and multi-session horizons, and the adjustment factor.
  Market caps: the Nasdaq screener export, then yfinance `fast_info`, both current. The
  holdout (2024-01-01 onward) was never downloaded for either source; the pull functions refuse
  such an end date.
- **Timestamps and sessions.** Bars are converted to America/New_York. Regular hours are the
  bars whose start lies in 09:30 → 15:55 inclusive (78 bars on a full session; the 15:55 bar
  ends at 16:00). A session is an early close when, across all names, no regular-hours bar
  starts at or after 13:00; early-close sessions are not fill sessions for any signal and do
  not count toward the 20-session coverage window (they are skipped, not failed). Extended-hours
  bars are never read.
- **Adjusted basis across sessions.** Intraday prices are raw. Whenever an intraday price on
  session F is compared with a daily price on another session, it is multiplied by that
  session's factor f_F = `adj_close_F / close_F` from the yfinance panel (the wave-1 as-of
  adjustment). Within-session returns are raw / raw and need no factor.
- **Survivorship bias.** The list is the current listing (2026-10-01): every name delisted
  before then is missing and every cap is today's. Long rows are overstated and short /
  long-avoid rows understated, as in wave 1; the same-session horizons are less exposed than
  wave 1's 21- and 63-session horizons, but a name that collapsed intraday and was later
  delisted is still absent.
- **Universes.** `smallcap` (current cap < USD 2B) and `uncapped`, with the wave-1 daily
  eligibility (bar on each of the 250 sessions ending D, median unadjusted dollar volume over
  D−20..D−1 ≥ USD 500k, `rvol_20` > 40%, close ≥ USD 2.00) evaluated with data through the
  close of the session before the fill: a name is eligible on fill session F when
  `in_universe` is true at F−1. **Coverage floor:** at least 60 regular-hours bars on each of
  the 20 (non-early-close) sessions ending F−1. Signals that need the session shape (i1, i3,
  i4, i7) are scored only on the floored universe and their comparator is the floored universe;
  i2, i5, i6 and i8 run on the daily universe without the floor and their comparator is the
  daily universe. The daily universe size is reported with and without the floor. A name
  without a fill bar at the entry time (below) is excluded from the comparator that day.
- **Eras** (locked for this wave). Dev 2020-08-01 → 2022-06-30 (23 months; the 2020–2021
  small-cap mania). Confirm 2022-07-01 → 2023-12-31 (18 months; the 2022 bear). The fill
  session F lies inside the era. Era boundary: a label whose exit session falls after the era's
  last session is null and is not counted (counts per horizon reported). Dev tables are
  written and committed before any confirm-era run; the confirm era is run only for a row that
  is interesting in dev. Halves: dev 2020-08-01 → 2021-07-15 and 2021-07-16 → 2022-06-30;
  confirm 2022-07-01 → 2023-03-31 and 2023-04-01 → 2023-12-31.
- **Fills.** Entry at a fixed clock time T: the open of the first regular-hours bar on F whose
  start is at or after T. The gap between T and that bar's start is logged per trade; a gap
  of more than 15 minutes (or no such bar) is recorded as unfilled. Candidate entry times
  09:35, 10:00, 10:30, 12:00, 15:30, 15:55, locked per signal below. Exit prices follow the
  same rule at the exit time: **10:30** and **12:00** are the opens of the first bars at or
  after those times (within 15 minutes); **same-session close** is the close of the 15:55 bar,
  or, when it is missing, the close of the last regular-hours bar starting at or after 15:40
  (none: null label); **next open** is the daily adjusted open of F+1; **1, 5, 21 sessions**
  are the daily adjusted closes of F+1, F+5, F+21. A horizon whose exit time is not after the
  entry time is not defined for that signal. The same fill and exit rules apply to every
  universe name in the comparator. Fixed USD 10,000 notional per trade.
- **Horizons stored for every event:** to 10:30, 12:00 and the close on F; next open; 1, 5, 21
  sessions; each with the same-day universe mean of the same quantity. The decision horizon is
  named per signal and cannot change after the run.
- **No re-entry while held.** As wave 1, at the decision horizon: a name the signal already
  holds (an earlier event whose exit session is after F) is recorded as `held` and not traded.
  Same-session decision horizons never hold across sessions; the rule binds i5.
- **Comparator.** The same-day universe (floored or daily, per the table): the equal-weight
  mean, over every eligible name filled at the same entry time, of the same forward quantity
  to the same exit. No cost is charged to the universe. Short-side quantities are
  sign-adjusted so a positive number means the short (or the avoidance) beat the universe.
  For i5-all the comparator is zero (the row's question is absolute); the equal-weight
  intraday return (09:30 open → same-session close) of the same names and the overnight-minus-
  intraday difference are reported next to it.
- **Cost schedule** (flat round trip in bps by the name's `med_dv_20_prev` at F; low / base /
  high; subtracted from each candidate's excess, never from the universe; every horizon,
  same-session included, pays the full round trip):

  | bucket | low | base | high |
  |---|---|---|---|
  | median dollar volume ≥ USD 10M | 10 | 20 | 40 |
  | USD 1M–10M | 20 | 40 | 80 |
  | USD 0.5M–1M | 40 | 80 | 160 |

  Zero cost is reported everywhere as the gross. The `spec/06` Abdi–Ranaldo figure is
  reported where the daily panel supplies it (`spec` column) and decides nothing.
- **Statistic.** The day-clustered z: mean over fill sessions of that session's mean (over
  its traded candidates) net excess, divided by its standard error over sessions. Reported
  with it, as wave 1: trades, entry days, trade-weighted mean net per trade at each cost
  level, day-weighted mean and SE, median, hit rate, mean gross and 1–99% winsorized gross,
  top-10-day share of absolute P&L, z without those days, sign and z in each half of the era,
  per-year rows, the fill-gap distribution and the unfilled share.
- **Controls** (every row, every universe). Stale-signal placebo: the same rule lagged 20
  sessions at the same clock time (the candidate on F is the name that qualified for a fill on
  F−20; for i6 and i8 the name whose signal day was D−20). Planted positive control: +50 bps
  added to every traded candidate's excess at zero cost; deterministic, never re-run. Expected:
  placebo |z| < 2 at zero cost; planted z − actual z ≈ 50 bps / SE. **Rank-type rows** (i3,
  i4, i5-q1, i5-q5: a cross-sectional slice of the universe each day) additionally carry a
  random-slice placebo (each day, a uniformly random subset of the same eligible set of the
  same size, numpy seed 20261007, same fills; expected |z| < 2) and a power statement: the
  number of fill sessions, the SE of the day-mean net excess, and the mean net per trade that
  z = 3.0 would require (3 × SE), so the reader can see whether the bar was reachable.
- **Model.** None. Fixed rules. No LLM call, no fitting, no purchase.

##### Signals (locked rules, entry, exit, decision horizon, direction, universe)

Notation: bar(hh:mm) is the regular-hours bar starting at hh:mm ET on fill session F;
o(·), h(·), c(·), v(·) its open, high, low-high, close, volume; px(T) the entry-rule price at
T (open of the first bar at or after T, within 15 minutes). Daily quantities carry the
session subscript and are the wave-1 panel's. "Decile" and "quintile" are computed each day
among the names of the signal's universe that have the feature on F (k = ⌈n/10⌉ names for a
decile, stable sort; quintile q = ⌈5 × percentile rank⌉). `median20(x)` is the median of x
over the 20 non-early-close sessions ending F−1 (NaN when fewer than 20 have x).

| # | variant | candidate rule on fill session F (universe-eligible names only) | dir | entry | exit (decision) | universe | floor |
|---|---|---|---|---|---|---|---|
| i1 | — | all six bars 09:30 … 09:55 present; c(09:55) > max h(09:30 … 09:50); v(09:30 … 09:55) summed ≥ 2.0 × median20 of the same sum | long | 10:00 | close | smallcap, uncapped | yes |
| i2 | up | gap σ = ln(o(09:30) × f_F / a_close_{F−1}) / (rvol_20_{F−1} / √252) ≥ +2.0; the 09:30 bar must exist | long | 09:35 | close (next open reported) | smallcap, uncapped | no |
| i2 | down | gap σ ≤ −2.0 | short / long-avoid | 09:35 | close (next open reported) | same | no |
| i3 | top | r_fhh = c(09:55) / o(09:30) − 1 in the top decile (both bars present) | long | 10:00 | close | smallcap, uncapped | yes |
| i3 | bottom | r_fhh in the bottom decile | short / long-avoid | 10:00 | close | same | yes |
| i4 | — | r_1500 = c(14:55) / o(09:30) − 1 in the top decile (both bars present) | long | 15:30 | close | smallcap, uncapped | yes |
| i5 | all | every eligible name with a 15:55 bar | long | 15:55 | next open | smallcap, uncapped | no |
| i5 | q5 | prior overnight return g = ln(o(09:30) × f_F / a_close_{F−1}) in the top quintile (09:30 and 15:55 bars present) | long | 15:55 | next open | same | no |
| i5 | q1 | g in the bottom quintile | long | 15:55 | next open | same | no |
| i6-1a | 0935 | `shock`_{F−1} ≤ −2.0 (wave 1's 1a candidate on D = F−1) | short / long-avoid | 09:35 | close | smallcap, uncapped | no |
| i6-1a | 1030 | same candidates | short / long-avoid | 10:30 | close | same | no |
| i6-1b | 0935 | `shock`_{F−1} ≥ +2.0 and `vol_ratio_20`_{F−1} ≥ 2.0 (wave 1's 1b) | long | 09:35 | close | same | no |
| i6-1b | 1030 | same candidates | long | 10:30 | close | same | no |
| i7 | — | px(12:00) ≥ 1.02 × VWAP_{12:00}, where VWAP_{12:00} = Σ vwap × v over bars 09:30 … 11:55 ÷ Σ v; and Σ v over 09:30 … 11:55 ≥ 2.0 × median20 of the same sum | short / long-avoid | 12:00 | close | smallcap, uncapped | yes |
| i8 | per rule | see "Autopsy, intraday" below; fill on D+1 | per group | 09:35 | close | smallcap, uncapped | no |

Notes. The brief's "10:00 bar" is read as the bar that ends at 10:00 (start 09:55), so that no
signal reads a bar that has not closed by its entry time; i7 compares the entry price itself
(the open of the fill bar) with the VWAP of the bars closed before it, which is what a
12:00 order could see. i2's two legs and i3's two legs are two variants each; i6 bundles two
wave-1 event types and is ledgered as two signals (i6-1a, i6-1b) of two variants each, so the
variant count per signal stays visible. The i5 quintile rows q2–q4 are reported from the
same run and are not ledgered. i5-all is universe-wide, so its "excess" is the absolute
overnight return; its intraday leg is reported beside it. Every row is reported on both
universes; `smallcap` ⊂ `uncapped`.

**Daily baselines** (reported in the entry, not ledgered): wave 1's 1a and 1b through the
wave-1 engine on this dev era (next-open fill, 1-session horizon, the daily analogue of
i6), and the daily-bar open-to-close and open-to-next-open excess for the i2 and i6 candidate
sets (fill at the daily open a_open_F). These say what the intraday entry adds to or removes
from the daily fill where one exists.

##### Autopsy, intraday (i8; locked definitions)

- **Movers.** On the adjusted daily closes, ratio_1 = a_close_D / a_close_{D−1}; up movers
  ratio_1 ≥ 2.0, down movers ratio_1 ≤ 0.50; the name must be universe-eligible on D−1; one
  event per name per calendar year per group (the first qualifying D); dev era only
  (D in 2020-08-01 → 2022-06-30; D−1 must have intraday bars, so D ≥ 2020-07-28). Per
  universe. Counts per year with the number of names eligible that year.
- **Features at D−1** (intraday, from the regular-hours bars of D−1): `fhh_ret` = c(09:55) /
  o(09:30) − 1; `fhh_vol_share` = Σ v(09:30 … 09:55) / Σ v(regular hours); `close_loc` =
  (c(last bar) − min low) / (max high − min low) over the regular-hours bars (NaN when the
  range is zero); `late_vol_share` = Σ v(15:00 … 15:55) / Σ v(regular hours). Exactly these
  four. Lift = share of events whose within-day percentile rank of the feature among the
  universe-eligible names with the feature on D−1 is ≥ 0.8 (top) or ≤ 0.2 (bottom), divided
  by 0.2; with the event count per feature (events whose D−1 feature is NaN drop from that
  feature's row). Nothing in the lift table is a result; it is hypothesis material.
- **Selection** (applied after the lift table is written and committed). From the `uncapped`
  lift table, per group, the three features with the highest max(lift_top, lift_bottom), each
  ≥ 1.5; fewer if fewer qualify; none if none does. Ties by event count, then alphabetically.
- **Rules.** On session D a universe-eligible name is a candidate when the feature's
  within-day percentile among the universe-eligible names with the feature on D is ≥ 0.8
  (lift from the top quintile) or ≤ 0.2 (bottom). Fill at 09:35 on D+1, decision horizon the
  same-session close, every horizon stored. Long for the up group, short / long-avoid for the
  down group. Both universes. Names `i8-up-<feature>` / `i8-down-<feature>`; at most three per
  direction. Reported per rule: match rate per day, the hit rate for the original move (share
  of traded candidates with a_close_F / a_close_{F−1} ≥ 2.0 or ≤ 0.50) against the universe
  base rate, the forward excess at every horizon, the controls. Threshold and confirm as for
  every event row. **Stated up front:** the features are selected on the dev era and the rules
  first run on it, so a dev result here is in-sample and not evidence; only the confirm era is.

##### What is interesting and what is not (per ledger row; from the graduation rule)

- **Interesting in dev** (every row, event and rank-type alike, since every row is a daily
  basket paying a per-trade round trip): day-clustered z ≥ 3.0 on the decision horizon at base
  cost, over ≥ 100 fill sessions and ≥ 500 trades, trade-weighted mean net excess per trade
  ≥ 50 bps at base cost and > 0 at high cost. **Not interesting:** anything else. An
  interesting dev result is the only thing that triggers a confirm-era run.
- **Graduation** requires, in addition: confirm era same sign with z ≥ 1.5 and no parameter
  change; the sign holds with the top 10 days removed; the stale-signal placebo |z| < 2 at zero
  cost, and for the rank-type rows the random-slice placebo |z| < 2 as well; the sign holds in
  both halves of the dev era; at most three variants of the signal in the ledger.
- **Decision quantity**, named once: the trade-weighted mean net excess per trade at the
  decision horizon at base cost, with its day-clustered z.
- **Ledger verdicts:** `null`, `confirm`, `graduate`, `fails confirm`, `artifact`, as wave 1.
- **i8 pass 1:** a lift ≥ 1.5 is a candidate for pass 2 and nothing more.

##### Decision rules (applied literally after the tables are written)

1. A row that is not interesting in dev gets verdict `null`; no confirm run; no further
   variant of that signal in this wave.
2. A row that is interesting in dev is run once on the confirm era with the identical rule;
   `graduate` if confirm z ≥ 1.5 with the same sign and the artifact rules hold, `fails
   confirm` if the confirm rule fails, `artifact` if an artifact rule fails.
3. If any row graduates, its first purchase is longer history, not more signals (brief): the
   next action is a proposal to extend the intraday cache backward (Alpaca's SIP history, or
   another vendor) and to re-run the identical rule on it, before any build. If nothing
   graduates, this entry says what the nulls rule out and the program's next step is the
   owner's review per the proposal's section 9 (the intraday question was that review's
   stated alternative to stopping).
4. The i8 lift table is filed as hypothesis material; its three pre-registrations per
   direction are spent in this wave.
5. The holdout (2024 onward) is not downloaded and not read. No purchase.

##### Engineering acceptance (proven before any new number is read)

- An intraday data layer in `experiments/screen/` that reads the parquet cache month by
  month, converts to America/New_York, keeps regular hours, detects early closes, builds a
  per-session, per-name table (the entry-rule price and lateness at each candidate time; the
  09:30 open; the 09:55, 14:55 and 15:55 bars; the opening-range high; first-half-hour, through-
  12:00, late-day and session volume; VWAP through 12:00; regular-hours bar count, high and low),
  aligns it to the wave-1 calendar and tickers (Alpaca's dot-form class symbols mapped to the
  list's dash form), computes the coverage floor and the 20-session medians with data through
  F−1, and caches the result under the data root.
- **Shift test** (`tests/screen/test_intraday.py`, in `pytest -q`): on synthetic 5-minute bars,
  (a) perturbing every bar on F that starts after the entry bar, and the entry bar's own high,
  low, close, volume and VWAP, leaves every signal's candidate matrix at F and every entry price
  unchanged; (b) perturbing every bar on sessions after F leaves the session-F table, the
  coverage floor at F and the medians through F−1 unchanged; (c) for i6 and i8 (signal on D,
  fill on D+1), perturbing every bar on D+1 and later leaves the candidate matrix at D
  unchanged. Plus the hand-checked fill rule (first bar at or after T, 15-minute cutoff, early
  close) on tiny arrays.
- **Small-month proof.** The layer is run on one month (2021-03) first and its summary
  (sessions, names with bars, bars per name per session, early closes found, share of the
  daily universe above the floor, fill-gap distribution at each entry time) is written to the
  entry before the full build. No signal is scored on the small month.
- `tests/test_architecture.py` import rules hold (nothing under `experiments/` imports
  `legacy`, the oracle or the labeler); the wave-1 tests keep passing.

##### What this screen cannot show

IEX is 2–3% of consolidated volume: a 5-minute bar is the IEX trades in that window, so
prices are last-trade prints that can be minutes stale for thin names, the IEX open is not
the opening auction, and every volume feature is IEX's share. Entry at a bar's open is a
trade at the last IEX print with no spread crossed; the cost schedule stands in for that and
remains a placeholder until the owner's quote sample. Point-in-time caps and delistings are
missing, as in wave 1. Twenty-three dev months and eighteen confirm months, both inside
unusual regimes, so a sign that holds in both eras has held in two regimes and no more. A
null on a long row here is conclusive for the free-data universe; a null on a short row is
conservative; a positive on either is only a reason to run the confirm era.

#### Run details

(Appended as the stages complete; the locked text above is unchanged.)

#### Results

(Dev era first, committed before any confirm-era run.)

#### Interpretation

(After the tables.)

#### Next action (per the pre-registered decision rules)

(After the tables.)

#### Open questions / followups

(After the tables.)

### 2026-10-07 — Intraday wave of the signal-screening program (i1–i8 on 5-minute IEX bars)

**Phase:** 0 (screening program, intraday wave; no build)
**Commit:** the pre-registration commit is the first commit on `screen/intraday` after the
merge of `screen/wave-1` and the Alpaca puller branch; the data layer, dev tables, confirm
tables, ledger and interpretation commits are named in `research_log.md` as they land
**Status:** running (dev tables written; i8 pass 2 and the confirm era pending)
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

- **Commits.** Pre-registration `d979e2a`; data layer, engine, signals, tests and the small-month
  proof `685f776`; the basis correction, dev tables and this section: the commit that adds them;
  i8 pass 2, the confirm era, the ledger and the interpretation: the commits named in
  `research_log.md`.
- **Dataset snapshot dates.** Alpaca 5-minute IEX cache: pulled 2026-10-01 → 2026-10-07 by
  `experiments/pull_alpaca_bars.py` (5,341 batch files in the manifest; the months 2016-01 →
  2019-05 are the puller's probes and hold 0 to 48 rows each; coverage 2020-07-27 → 2023-12-31,
  plus a one-bar stray on 2020-07-13). Regular-hours session tables: 2,914,997 name-sessions over
  865 sessions, 4,163 of the 4,884 list names with at least one bar. **Daily bars: the wave-1
  yfinance cache lived in the cloud session and was not on this machine, so the wave-1 stage was
  re-run here on 2026-10-07** with the Alpaca cache's symbol list (4,884 names, the 2026-10-01
  Nasdaq Trader listing) and the pre-registered window 2009-01-01 → 2023-12-31, `auto_adjust=False`:
  4,156 names returned bars (wave 1: 4,164), 728 returned none in the window. Yahoo throttled the
  pull to one 60-name batch every 2 to 11 minutes (9 hours in all; the threaded stage stalled twice
  in its backoff and the remaining batches were pulled one fresh process at a time by the same code
  path, writing the same files). Market caps 2026-10-07: 4,756 from the Nasdaq screener export,
  128 from yfinance `fast_info`, all current; 4,154 of the 4,155 panel tickers have one, 2,463 are
  under USD 2B. No bar dated 2024-01-01 or later was downloaded from either source.
- **Daily panel window.** Arrays are built on 2019-01-01 → 2023-12-31 (1,258 sessions × 4,155
  tickers, 21 s), which gives the 250-session history rule a full year before the first fill
  session; the features are the wave-1 panel's and do not depend on the window start.
- **Compute.** 12 cores / 64 GB. Session tables for 42 months: 11 s in 8 processes. Intraday
  arrays: 26 s. One row (trades, placebo, planted, random slice where applicable): 5 to 20 s; the
  34 dev rows, i8 pass 1 and the baselines: about 3 minutes.
- **Two engineering corrections before any signal was scored** (the small-month proof surfaced
  them; the locked text's mechanical rule is replaced, the intent is unchanged). (1) *Early
  closes.* The pre-registered test "no regular-hours bar starts at or after 13:00" does not fire on
  the real half days: a sliver of after-hours prints exists from 13:00 on (2021-11-26: 37 bars after
  13:00 against 81,480 before). The layer now marks a session an early close when the bars from
  13:00 on are fewer than 30% of the bars before 13:00 across all names, and drops those bars as
  extended hours. Found: exactly the six NYSE 13:00 closes in the window (2020-11-27, 2020-12-24,
  2021-11-26, 2022-11-25, 2023-07-03, 2023-11-24); three fall in the dev era. (2) *Coverage.* A
  session with fewer than 1,000 bars across all names is treated as not covered by the cache
  (2020-07-13, one bar) rather than as a session on which every name failed the floor.
- **Small-month proof (2021-03, `proof_2021-03.json`, no signal scored).** 23 sessions, 3,398
  names with bars, 74,308 name-sessions; bars per name-session p10 5, median 46, p90 78; 37.5% of
  name-sessions at or above the 60-bar floor, 10% with all 78 bars; 596 names with ≥ 60 bars on
  every session of the month; the 09:30 bar present in 60% of name-sessions, the 15:55 bar in 82%,
  a same-session close (15:55 or the 15:40+ fallback) in 90%; fills at 09:35 / 10:00 / 12:00 /
  15:30 for 77% / 78% / 74% / 85% of name-sessions, mean lateness 1.8 to 2.5 minutes, 22 to 30% of
  fills late.
- **Anomaly found and corrected after the first dev tables were read (price basis across
  sessions).** The first dev tables carried impossible next-open returns for i5 (mean +66,597,000
  bps; KUST at +637,000,000%) and 45,632 i2-down candidates against 2,522 i2-up. Cause: yfinance's
  `Close` with `auto_adjust=False` is already **split-adjusted** (only dividends are left out), so
  the pre-registered factor f_F = adj_close / close undoes dividends and not splits, and the ratio
  of a raw IEX price to a yfinance daily price is off by every split that came after F (KUST's
  later reverse splits: a factor of millions; every later reverse split in a penny name: a fake
  −2σ gap). The correction, applied at the engine (commit of this section) and re-run for every
  row: (a) the cross-session exits chain two legs at the session close, the IEX leg from the entry
  to the same-session close and the daily adjusted leg from a_close_F to the exit, so no return
  ever divides an IEX price by a daily one; (b) the gap and the prior overnight return (i2, i5
  quintiles) are the daily adjusted open against the prior adjusted close, ln(a_open_F /
  a_close_{F−1}), the official opening print known at 09:30, and the 09:30-bar requirement is
  dropped. Rows whose decision horizon is the same-session close and that do not use the gap
  (i1, i3, i4, i6, i7) are unchanged to the basis point. Cells before → after: i5-all `smallcap`
  gross +66,597,440 → +14 bps, `uncapped` +37,018,910 → +13; i5-q5 `smallcap` −68,769,510 → +9;
  i2-up `smallcap` 2,522 → 1,677 trades, gross +12 → −53 bps, z @base −2.15 → −2.14; i2-up
  `uncapped` 13,771 → 2,646 trades, +2 → −19, z −4.18 → −2.30; i2-down `smallcap` 45,632 → 1,060
  trades, +10 → +34, z @base −6.13 → +0.39; i2-down `uncapped` 48,483 → 1,699 trades, +10 → +33,
  z −5.01 → +1.38. The pre-fix tables, meta and baselines are kept as
  `tables_dev_before_basis_fix.md`, `meta_dev_before_basis_fix.json`,
  `baselines_dev_before_basis_fix.csv`. A test now scales the daily series by 10 and asserts
  every return is unchanged. No parameter was changed; the pre-registered thresholds, entry
  times, exits and universes are as written.
- **Universe sizes, dev era (479 fill sessions, 3 early closes, 0 sessions without coverage).**
  `smallcap` daily (eligibility at F−1): median 732 names per session (p10 611, p90 897; 1,704
  ever); **with the coverage floor: median 29 (p10 5, p90 52; 192 ever)**. `uncapped` daily:
  median 1,181 (p10 897, p90 1,681; 3,175 ever); floored: median 125 (p10 45, p90 308; 893 ever).
  The daily universes are two to three times wave 1's (median 230 / 409 over 2010–2020): the
  40%-vol floor admits most of the list in 2020–2022. The floor is strict: a name needs an IEX
  print in 60 of 78 five-minute windows on each of 20 consecutive sessions, and in a 2–3%-share
  venue only the most active names manage it; the session-shape rows (i1, i3, i4, i7) are
  therefore tests on a few dozen to a few hundred liquid names a day.
- **Fills, dev era, eligible name-sessions.** `smallcap`: filled at 09:35 / 10:00 / 10:30 /
  12:00 / 15:30 / 15:55 for 71% / 72% / 71% / 66% / 82% / 81%; mean lateness 2.6 to 3.4 minutes;
  32 to 41% of fills late. `uncapped`: 79% / 80% / 79% / 75% / 88% / 87%; 1.9 to 2.7 minutes;
  23 to 32% late. Per row the unfilled share is in the table (i6 loses 11 to 22% of its
  candidates to the 15-minute cutoff: the −2σ names are the thin ones).
- **Anomalies during run.** The two corrections and the basis bug above. The yfinance pull
  logged "some characters could not be decoded" for a few names (symbol-name encoding; no bar
  affected). `KUST` and the other names whose yfinance series sits on a different price level
  than the IEX prints are handled by the chain and are not excluded.

#### Results

Dev era only in this section (fill sessions 2020-08-03 → 2022-06-30). Result files, one per row
and universe, are in `research_log/2026-10-07-intraday-wave/`: `results_<row>_<universe>_dev.csv`
(every defined exit × cost level × period), `controls_*.json` (placebos, planted control, power
statement, fill statistics), `meta_dev.json` (universe sizes, fill shares, run summaries),
`tables_dev.md` (the per-row blocks), `baselines_dev.csv`, `i8_counts_dev.csv`,
`i8_lifts_dev.csv`, `i8_movers_dev.md`, and the pre-fix files named above. Trade-level files stay
under the data root.

##### Dev era: every row, decision exit, pre-registered entry time

Mean net excess per trade in bps at each cost level (short rows sign-adjusted so positive means
the short, or the avoidance, beat the universe; i5-all is the absolute overnight return); z is
day-clustered at base cost; `rnd` is the random-slice placebo z at zero cost (rank-type rows);
`SE` is the day-mean SE at base cost in bps (z = 3 needs 3 × SE net per trade); `interesting` is
the pre-registered threshold (z ≥ 3.0 at base, ≥ 100 days, ≥ 500 trades, net ≥ 50 bps at base and
> 0 at high).

| row | universe | dir | entry | exit | candidates | unfilled | trades | days | net @0 | @low | @base | @high | z @0 | z @base | hit @base | top-10 share | z w/o top 10 | half1 / half2 net | placebo z @0 | rnd | planted shift | SE | interesting |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| i1 | smallcap | long | 10:00 | close | 251 | 0% | 251 | 156 | +20 | +10 | **+0** | -20 | +0.49 | **-0.41** | 0.482 | 30.0% | -0.52 | +45 / -35 | -0.96 | — | +2.24 | 22 | no |
| i1 | uncapped | long | 10:00 | close | 1,368 | 0% | 1,367 | 339 | +21 | +11 | **+1** | -19 | +1.38 | **-0.37** | 0.475 | 19.0% | -0.65 | +4 / -1 | -1.07 | — | +4.36 | 11 | no |
| i2-up | smallcap | long | 09:35 | close | 1,845 | 8% | 1,677 | 426 | -53 | -73 | **-94** | -135 | -1.32 | **-2.14** | 0.390 | 18.3% | -4.94 | -103 / -78 | +0.33 | — | +0.96 | 52 | no |
| i2-up | uncapped | long | 09:35 | close | 2,856 | 6% | 2,646 | 456 | -19 | -36 | **-54** | -90 | -1.33 | **-2.30** | 0.429 | 18.5% | -4.29 | -59 / -45 | +0.16 | — | +1.26 | 40 | no |
| i2-down | smallcap | short | 09:35 | close | 1,195 | 9% | 1,060 | 368 | +34 | +15 | **-3** | -40 | +1.27 | **+0.39** | 0.504 | 16.4% | +1.84 | -3 / -3 | +0.48 | — | +1.14 | 44 | no |
| i2-down | uncapped | short | 09:35 | close | 1,860 | 7% | 1,699 | 414 | +33 | +17 | **+1** | -31 | +2.61 | **+1.38** | 0.513 | 15.5% | +1.80 | +13 / -9 | +0.39 | — | +1.81 | 28 | no |
| i3-top | smallcap | long | 10:00 | close | 1,493 | 0% | 1,492 | 464 | -3 | -13 | **-23** | -44 | -0.41 | **-2.40** | 0.460 | 10.3% | -2.77 | -13 / -34 | -0.48 | -0.07 | +4.96 | 10 | no |
| i3-top | uncapped | long | 10:00 | close | 7,094 | 0% | 7,089 | 464 | +10 | -0 | **-10** | -30 | +0.97 | **-2.03** | 0.463 | 13.5% | -2.13 | -8 / -12 | -1.91 | +0.64 | +7.48 | 7 | no |
| i3-bottom | smallcap | short | 10:00 | close | 1,493 | 0% | 1,493 | 464 | +12 | +2 | **-8** | -28 | +0.97 | **-0.88** | 0.470 | 13.4% | -1.82 | -5 / -10 | -0.13 | +0.07 | +4.63 | 11 | no |
| i3-bottom | uncapped | short | 10:00 | close | 7,094 | 0% | 7,094 | 464 | +11 | +1 | **-9** | -29 | +0.84 | **-2.38** | 0.480 | 11.8% | -3.05 | -6 / -12 | +0.25 | -0.64 | +8.05 | 6 | no |
| i4 | smallcap | long | 15:30 | close | 1,481 | 0% | 1,481 | 464 | +1 | -9 | **-19** | -39 | +1.44 | **-6.42** | 0.380 | 10.9% | -6.22 | -17 / -20 | +0.21 | -2.66 | +19.63 | 3 | no |
| i4 | uncapped | long | 15:30 | close | 7,041 | 0% | 7,041 | 464 | +1 | -9 | **-19** | -39 | +1.70 | **-12.59** | 0.358 | 12.1% | -13.00 | -17 / -20 | +1.63 | -0.41 | +35.72 | 1 | no |
| i5-all | smallcap | long | 15:55 | nopen | 285,831 | 0% | 284,996 | 478 | +14 | -4 | **-23** | -60 | +3.03 | **-4.77** | 0.416 | 11.1% | -4.11 | -4 / -39 | +2.70 | — | +10.47 | 5 | no |
| i5-all | uncapped | long | 15:55 | nopen | 514,425 | 0% | 512,725 | 478 | +13 | -2 | **-18** | -49 | +2.79 | **-3.95** | 0.436 | 11.5% | -3.58 | -1 / -33 | +2.52 | — | +10.63 | 5 | no |
| i5-q5 | smallcap | long | 15:55 | nopen | 57,385 | 0% | 57,218 | 478 | +9 | -10 | **-29** | -68 | +3.97 | **-13.30** | 0.358 | 8.8% | -15.98 | -21 / -37 | +2.78 | +0.70 | +22.43 | 2 | no |
| i5-q5 | uncapped | long | 15:55 | nopen | 103,069 | 0% | 102,729 | 478 | +7 | -10 | **-26** | -59 | +3.51 | **-13.63** | 0.368 | 9.1% | -14.64 | -18 / -33 | +3.00 | +0.03 | +25.96 | 2 | no |
| i5-q4 | smallcap | long | 15:55 | nopen | 57,174 | 0% | 57,007 | 478 | +1 | -18 | **-36** | -72 | +0.63 | **-28.81** | 0.324 | 6.4% | -30.62 | -35 / -36 | -0.07 | +1.31 | +40.38 | 1 | no |
| i5-q4 | uncapped | long | 15:55 | nopen | 102,833 | 0% | 102,493 | 478 | -0 | -15 | **-31** | -61 | +0.19 | **-28.83** | 0.338 | 6.7% | -33.35 | -32 / -30 | -0.18 | +0.61 | +46.94 | 1 | no |
| i5-q3 | smallcap | long | 15:55 | nopen | 57,179 | 0% | 57,012 | 478 | -1 | -19 | **-37** | -73 | -1.09 | **-29.96** | 0.316 | 7.3% | -35.92 | -40 / -35 | -0.05 | -0.57 | +40.08 | 1 | no |
| i5-q3 | uncapped | long | 15:55 | nopen | 102,884 | 0% | 102,544 | 478 | -1 | -16 | **-31** | -61 | -0.95 | **-34.21** | 0.335 | 7.0% | -37.00 | -33 / -30 | +0.53 | -0.57 | +54.89 | 1 | no |
| i5-q2 | smallcap | long | 15:55 | nopen | 57,159 | 0% | 56,992 | 478 | -3 | -21 | **-40** | -76 | -2.00 | **-27.86** | 0.315 | 7.2% | -31.44 | -43 / -36 | -4.05 | -0.69 | +35.19 | 1 | no |
| i5-q2 | uncapped | long | 15:55 | nopen | 103,052 | 0% | 102,712 | 478 | -3 | -18 | **-34** | -64 | -2.59 | **-32.55** | 0.335 | 6.8% | -33.65 | -37 / -30 | -2.96 | +0.06 | +48.02 | 1 | no |
| i5-q1 | smallcap | long | 15:55 | nopen | 56,934 | 0% | 56,767 | 478 | -6 | -25 | **-44** | -82 | -2.79 | **-21.40** | 0.336 | 9.0% | -25.18 | -44 / -44 | -1.74 | +1.51 | +24.60 | 2 | no |
| i5-q1 | uncapped | long | 15:55 | nopen | 102,587 | 0% | 102,247 | 478 | -3 | -19 | **-36** | -68 | -1.93 | **-19.44** | 0.358 | 10.0% | -22.39 | -36 / -35 | -1.62 | +2.00 | +26.86 | 2 | no |
| i6-1a-0935 | smallcap | short | 09:35 | close | 11,221 | 22% | 8,490 | 471 | +3 | -15 | **-33** | -69 | +2.12 | **-1.75** | 0.466 | 18.5% | -1.51 | -23 / -39 | -1.67 | — | +5.27 | 10 | no |
| i6-1a-0935 | uncapped | short | 09:35 | close | 19,256 | 16% | 15,794 | 476 | +3 | -12 | **-27** | -57 | +2.12 | **-1.87** | 0.473 | 21.6% | -1.63 | -19 / -32 | -1.61 | — | +6.23 | 8 | no |
| i6-1a-1030 | smallcap | short | 10:30 | close | 11,221 | 22% | 8,518 | 470 | +7 | -10 | **-28** | -64 | +2.86 | **-2.19** | 0.469 | 20.1% | -1.85 | -17 / -35 | -0.68 | — | +6.95 | 7 | no |
| i6-1a-1030 | uncapped | short | 10:30 | close | 19,256 | 16% | 15,889 | 477 | +7 | -8 | **-23** | -53 | +2.39 | **-2.99** | 0.470 | 22.3% | -2.64 | -21 / -25 | -1.43 | — | +8.50 | 6 | no |
| i6-1b-0935 | smallcap | long | 09:35 | close | 6,666 | 14% | 5,592 | 474 | -28 | -49 | **-69** | -111 | -1.10 | **-3.81** | 0.414 | 19.3% | -3.91 | -84 / -47 | +2.10 | — | +3.21 | 16 | no |
| i6-1b-0935 | uncapped | long | 09:35 | close | 10,234 | 11% | 8,962 | 475 | -19 | -37 | **-54** | -90 | -0.47 | **-3.25** | 0.431 | 19.3% | -3.19 | -66 / -37 | +1.38 | — | +3.77 | 13 | no |
| i6-1b-1030 | smallcap | long | 10:30 | close | 6,666 | 18% | 5,359 | 471 | +1 | -20 | **-40** | -81 | +1.65 | **-2.20** | 0.426 | 19.3% | -2.21 | -52 / -22 | +0.18 | — | +4.63 | 11 | no |
| i6-1b-1030 | uncapped | long | 10:30 | close | 10,234 | 13% | 8,717 | 475 | -3 | -20 | **-38** | -73 | +1.92 | **-2.20** | 0.424 | 21.0% | -2.34 | -44 / -28 | -0.53 | — | +5.67 | 9 | no |
| i7 | smallcap | short | 12:00 | close | 282 | 0% | 282 | 180 | +16 | +6 | **-4** | -24 | +0.14 | **-0.75** | 0.507 | 26.2% | -1.44 | +41 / -47 | +0.75 | — | +2.21 | 23 | no |
| i7 | uncapped | short | 12:00 | close | 957 | 0% | 957 | 292 | +0 | -10 | **-20** | -40 | +0.73 | **-0.46** | 0.478 | 21.5% | +0.24 | -5 / -33 | +0.70 | — | +2.97 | 17 | no |

##### Horizon curve, gross excess per trade (bps) with the day-clustered z at zero cost; the decision exit is starred

Exits in order: 10:30, 12:00, same-session close, next open, 1, 5, 21 sessions (an exit not after
the entry is "—"). The cross-session exits chain the IEX leg to the daily adjusted leg at the
session close.

| row | universe | 10:30 | 12:00 | close | next open | 1 | 5 | 21 |
|---|---|---|---|---|---|---|---|---|
| i1 | smallcap | +18 (+1.29) | +18 (+0.89) | +20 (+0.49) * | +76 (+1.28) | +82 (+1.21) | +29 (+0.26) | -129 (-0.91) |
| i1 | uncapped | +10 (+0.41) | +3 (+0.13) | +21 (+1.38) * | +38 (+2.11) | +29 (+1.13) | +33 (+1.54) | +51 (+1.20) |
| i2-up | smallcap | -72 (-2.56) | -57 (-1.19) | -53 (-1.32) * | -128 (-3.05) | -199 (-3.67) | -227 (-2.34) | -226 (-1.10) |
| i2-up | uncapped | -59 (-2.32) | -47 (-1.41) | -19 (-1.33) * | -65 (-2.92) | -112 (-3.88) | -140 (-3.26) | -196 (-2.04) |
| i2-down | smallcap | +36 (+1.85) | +51 (+1.81) | +34 (+1.27) * | +25 (+0.77) | +74 (+2.12) | +112 (+2.34) | +144 (+2.24) |
| i2-down | uncapped | +24 (+2.42) | +40 (+2.56) | +33 (+2.61) * | +24 (+1.58) | +60 (+2.21) | +79 (+2.20) | +99 (+2.18) |
| i3-top | smallcap | +2 (+0.70) | -1 (-0.32) | -3 (-0.41) * | +30 (+2.15) | +38 (+1.53) | -24 (-0.21) | -94 (-1.45) |
| i3-top | uncapped | +3 (+0.74) | +4 (+0.63) | +10 (+0.97) * | +32 (+3.24) | +45 (+3.00) | +48 (+2.15) | -0 (+0.48) |
| i3-bottom | smallcap | -2 (+0.03) | +1 (+0.06) | +12 (+0.97) * | +32 (+2.72) | +32 (+1.90) | +40 (+0.83) | +59 (+0.26) |
| i3-bottom | uncapped | +4 (+1.12) | +2 (-0.02) | +11 (+0.84) * | +28 (+2.37) | +32 (+1.50) | +22 (+1.13) | -41 (-0.50) |
| i4 | smallcap | — | — | +1 (+1.44) * | +26 (+3.46) | +32 (+2.53) | -6 (+0.06) | -27 (-0.19) |
| i4 | uncapped | — | — | +1 (+1.70) * | +21 (+3.92) | +22 (+2.16) | +37 (+2.09) | +21 (+0.98) |
| i5-all | smallcap | — | — | — | +14 (+3.03) * | -1 (-0.05) | -6 (-0.15) | -64 (-0.11) |
| i5-all | uncapped | — | — | — | +13 (+2.79) * | +5 (+0.30) | +21 (+0.57) | +36 (+1.45) |
| i5-q5 | smallcap | — | — | — | +9 (+3.97) * | -4 (-1.23) | +10 (+0.92) | +23 (+1.41) |
| i5-q5 | uncapped | — | — | — | +7 (+3.51) * | -3 (-0.80) | +9 (+0.96) | +28 (+1.80) |
| i5-q4 | smallcap | — | — | — | +1 (+0.63) * | +1 (+0.40) | +0 (+0.08) | -7 (-0.89) |
| i5-q4 | uncapped | — | — | — | -0 (+0.19) * | -1 (-0.47) | -6 (-0.69) | -7 (-0.92) |
| i5-q3 | smallcap | — | — | — | -1 (-1.09) * | +1 (+0.30) | +1 (+0.16) | +20 (+1.23) |
| i5-q3 | uncapped | — | — | — | -1 (-0.95) * | +3 (+1.56) | +3 (+1.08) | +6 (+0.53) |
| i5-q2 | smallcap | — | — | — | -3 (-2.00) * | +1 (+0.89) | -5 (-0.53) | -3 (-0.39) |
| i5-q2 | uncapped | — | — | — | -3 (-2.59) * | -0 (+0.10) | -6 (-1.33) | -7 (-0.85) |
| i5-q1 | smallcap | — | — | — | -6 (-2.79) * | +1 (+0.28) | -6 (-0.83) | -34 (-1.74) |
| i5-q1 | uncapped | — | — | — | -3 (-1.93) * | +2 (+0.23) | -1 (-0.41) | -21 (-1.42) |
| i6-1a-0935 | smallcap | -2 (+0.71) | -1 (+0.45) | +3 (+2.12) * | +2 (+2.05) | +5 (+1.74) | -9 (+1.28) | +22 (+0.37) |
| i6-1a-0935 | uncapped | -1 (+1.14) | +1 (+0.61) | +3 (+2.12) * | +4 (+2.48) | +7 (+1.94) | -7 (+1.41) | +13 (+0.75) |
| i6-1a-1030 | smallcap | — | +3 (+0.89) | +7 (+2.86) * | +8 (+2.80) | +11 (+1.89) | -9 (+0.71) | +17 (-0.10) |
| i6-1a-1030 | uncapped | — | +3 (+1.00) | +7 (+2.39) * | +8 (+3.09) | +11 (+1.59) | -6 (+0.85) | +11 (-0.04) |
| i6-1b-0935 | smallcap | -24 (-1.63) | -32 (-1.08) | -28 (-1.10) * | -27 (-1.43) | -73 (-2.36) | -85 (-1.45) | -169 (-2.31) |
| i6-1b-0935 | uncapped | -12 (-1.57) | -19 (-0.94) | -19 (-0.47) * | -13 (-0.85) | -53 (-1.98) | -57 (-1.14) | -152 (-2.37) |
| i6-1b-1030 | smallcap | — | -9 (-0.10) | +1 (+1.65) * | +5 (+0.96) | -41 (-0.54) | -57 (-0.38) | -123 (-1.18) |
| i6-1b-1030 | uncapped | — | -8 (+0.50) | -3 (+1.92) * | +5 (+1.30) | -35 (-0.37) | -38 (-0.32) | -126 (-1.43) |
| i7 | smallcap | — | — | +16 (+0.14) * | -54 (-1.56) | -34 (-0.70) | +21 (+0.28) | -7 (-0.43) |
| i7 | uncapped | — | — | +0 (+0.73) * | -45 (-1.67) | -35 (-0.84) | -188 (-1.40) | -128 (-1.03) |

##### Per year, decision exit, net at base (z)

| row | universe | 2020 / 2021 / 2022 |
|---|---|---|
| i1 | smallcap | +81 (+0.70) / +43 (+0.11) / -81 (-1.40) |
| i1 | uncapped | -4 (+0.76) / +10 (+0.23) / -6 (-1.96) |
| i2-up | smallcap | -23 (-1.17) / -165 (-3.44) / +27 (+0.80) |
| i2-up | uncapped | +32 (-0.73) / -151 (-3.22) / +24 (+0.77) |
| i2-down | smallcap | +0 (+0.36) / +79 (+2.58) / -147 (-1.52) |
| i2-down | uncapped | -1 (-0.57) / +86 (+3.34) / -119 (-1.08) |
| i3-top | smallcap | -7 (-0.31) / -24 (-1.70) / -31 (-2.14) |
| i3-top | uncapped | -11 (-2.16) / -12 (-0.93) / -8 (-1.42) |
| i3-bottom | smallcap | -11 (-0.79) / -1 (-0.04) / -18 (-1.11) |
| i3-bottom | uncapped | -24 (-2.52) / -4 (-1.17) / -6 (-1.25) |
| i4 | smallcap | -13 (-2.54) / -17 (-3.43) / -25 (-6.39) |
| i4 | uncapped | -17 (-6.41) / -17 (-7.38) / -21 (-10.86) |
| i5-all | smallcap | -4 (-0.70) / -17 (-2.98) / -44 (-4.27) |
| i5-all | uncapped | +2 (-0.19) / -14 (-2.70) / -37 (-3.65) |
| i5-q5 | smallcap | -24 (-5.22) / -28 (-9.07) / -34 (-8.88) |
| i5-q5 | uncapped | -21 (-5.71) / -25 (-9.14) / -32 (-8.87) |
| i5-q4 | smallcap | -39 (-12.33) / -34 (-20.55) / -37 (-16.68) |
| i5-q4 | uncapped | -33 (-14.26) / -30 (-19.75) / -30 (-15.85) |
| i5-q3 | smallcap | -41 (-17.42) / -37 (-18.30) / -37 (-21.16) |
| i5-q3 | uncapped | -31 (-16.72) / -32 (-23.37) / -29 (-20.28) |
| i5-q2 | smallcap | -43 (-11.41) / -41 (-20.34) / -36 (-17.11) |
| i5-q2 | uncapped | -36 (-16.36) / -35 (-22.87) / -30 (-16.92) |
| i5-q1 | smallcap | -44 (-11.31) / -43 (-13.92) / -46 (-12.54) |
| i5-q1 | uncapped | -35 (-11.00) / -36 (-13.89) / -35 (-8.86) |
| i6-1a-0935 | smallcap | +23 (+1.81) / -50 (-1.38) / -33 (-2.82) |
| i6-1a-0935 | uncapped | +18 (+1.71) / -47 (-1.83) / -24 (-2.23) |
| i6-1a-1030 | smallcap | +4 (+0.97) / -35 (-1.03) / -33 (-3.39) |
| i6-1a-1030 | uncapped | -3 (+0.49) / -35 (-2.50) / -20 (-2.30) |
| i6-1b-0935 | smallcap | -58 (-2.09) / -89 (-3.14) / -24 (-1.17) |
| i6-1b-0935 | uncapped | -38 (-1.66) / -79 (-2.89) / -13 (-0.83) |
| i6-1b-1030 | smallcap | -38 (-1.77) / -55 (-2.68) / +2 (+0.51) |
| i6-1b-1030 | uncapped | -36 (-1.02) / -48 (-2.44) / -14 (-0.02) |
| i7 | smallcap | -18 (+0.47) / +15 (-0.49) / -30 (-1.15) |
| i7 | uncapped | +14 (+1.42) / -35 (-1.31) / -20 (+0.24) |

##### Daily baselines (reported, not ledgered)

Wave 1's 1a and 1b through the wave-1 engine on this dev era (next-open fill, 1-session
horizon), and the daily-bar open-to-close and open-to-next-open excess of the i2 and i6 candidate
sets filled at the daily open. Where two numbers are given they are zero cost / base cost.

| baseline | universe | cost | trades | days | mean net (bps) | z |
|---|---|---|---|---|---|---|
| wave-1 1a next-open, 1 session (open F to open F+1) | smallcap | 0 | 10,700 | 478 | 8.207085327800712 | 3.2016711296946085 |
| wave-1 1a next-open, 1 session (open F to open F+1) | smallcap | base | 10,700 | 478 | -32.40226046659182 | -0.8091139577301607 |
| wave-1 1b-5d next-open, 1 session (open F to open F+1) | smallcap | 0 | 6,296 | 478 | -26.41372157238503 | -2.2353129319458187 |
| wave-1 1b-5d next-open, 1 session (open F to open F+1) | smallcap | base | 6,296 | 478 | -71.14370886590473 | -4.602019873422603 |
| i2-up candidates, daily open fill, open to close | smallcap | 0 / base | 1,845 | 434 | -95 / -138 | -2.56 / -3.39 |
| i2-up candidates, daily open fill, open to next open | smallcap | 0 / base | 1,843 | 433 | -159 / -202 | -3.84 / -4.60 |
| i2-down candidates, daily open fill, open to close | smallcap | 0 / base | 1,195 | 381 | -62 / -101 | -0.70 / -1.62 |
| i2-down candidates, daily open fill, open to next open | smallcap | 0 / base | 1,192 | 380 | -63 / -102 | -0.97 / -1.76 |
| i6-1a candidates (shock <= -2 on F-1), daily open fill, open to close | smallcap | 0 / base | 11,221 | 478 | +8 / -32 | +2.97 / -1.51 |
| i6-1a candidates (shock <= -2 on F-1), daily open fill, open to next open | smallcap | 0 / base | 11,198 | 477 | +8 / -32 | +3.08 / -0.84 |
| i6-1b candidates (1b on F-1), daily open fill, open to close | smallcap | 0 / base | 6,666 | 477 | -42 / -86 | -2.63 / -5.47 |
| i6-1b candidates (1b on F-1), daily open fill, open to next open | smallcap | 0 / base | 6,664 | 476 | -36 / -80 | -2.49 / -4.84 |
| wave-1 1a next-open, 1 session (open F to open F+1) | uncapped | 0 | 18,370 | 480 | 9.500234339195599 | 3.3197700880409142 |
| wave-1 1a next-open, 1 session (open F to open F+1) | uncapped | base | 18,370 | 480 | -24.46057132220887 | -0.7220835760453651 |
| wave-1 1b-5d next-open, 1 session (open F to open F+1) | uncapped | 0 | 9,735 | 478 | -21.372856964182823 | -2.2988970913127793 |
| wave-1 1b-5d next-open, 1 session (open F to open F+1) | uncapped | base | 9,735 | 478 | -59.7827182892984 | -4.880651401183854 |
| i2-up candidates, daily open fill, open to close | uncapped | 0 / base | 2,856 | 459 | -34 / -72 | -2.58 / -3.55 |
| i2-up candidates, daily open fill, open to next open | uncapped | 0 / base | 2,854 | 458 | -73 / -110 | -3.59 / -4.43 |
| i2-down candidates, daily open fill, open to close | uncapped | 0 / base | 1,860 | 427 | -43 / -77 | -0.07 / -1.23 |
| i2-down candidates, daily open fill, open to next open | uncapped | 0 / base | 1,853 | 426 | -49 / -83 | -0.66 / -1.54 |
| i6-1a candidates (shock <= -2 on F-1), daily open fill, open to close | uncapped | 0 / base | 19,256 | 479 | +10 / -24 | +2.97 / -1.64 |
| i6-1a candidates (shock <= -2 on F-1), daily open fill, open to next open | uncapped | 0 / base | 19,223 | 478 | +10 / -24 | +3.42 / -0.57 |
| i6-1b candidates (1b on F-1), daily open fill, open to close | uncapped | 0 / base | 10,234 | 477 | -34 / -72 | -2.58 / -5.45 |
| i6-1b candidates (1b on F-1), daily open fill, open to next open | uncapped | 0 / base | 10,229 | 476 | -26 / -64 | -2.39 / -4.92 |

##### i8 pass 1: one-session movers and intraday lifts (hypothesis material, not a result)

Movers on the adjusted daily closes, universe-eligible on D−1, one per name-year; lifts are the
within-day percentile of the intraday feature at D−1 among the universe-eligible names with the
feature on D−1 (n is the number of events with the feature; `fhh_ret` needs both the 09:30 and
the 09:55 bar, which the thin names that make these moves rarely have).

**smallcap: one-session movers per year (eligible on D−1); names eligible that year in the last column**

| year | ×2 / 1 session | −50% / 1 session | eligible |
|---|---|---|---|
| 2020 | 11 | 11 | 1132 |
| 2021 | 31 | 15 | 1488 |
| 2022 | 8 | 15 | 1366 |
| total | 50 | 41 | |

**uncapped: one-session movers per year (eligible on D−1); names eligible that year in the last column**

| year | ×2 / 1 session | −50% / 1 session | eligible |
|---|---|---|---|
| 2020 | 14 | 12 | 2298 |
| 2021 | 36 | 18 | 2598 |
| 2022 | 8 | 19 | 2650 |
| total | 58 | 49 | |

**smallcap: ×2 in one session, 50 name-years; within-day percentile of the intraday feature at D−1 among the universe on D−1**

| feature | lift top quintile | lift bottom quintile | median percentile | n |
|---|---|---|---|---|
| fhh_ret | 1.25 | 1.56 | 0.45 | 16 |
| fhh_vol_share | 1.28 | 1.70 | 0.37 | 47 |
| close_loc | 0.98 | 1.30 | 0.49 | 46 |
| late_vol_share | 0.96 | 1.81 | 0.33 | 47 |

**smallcap: −50% in one session, 41 name-years; within-day percentile of the intraday feature at D−1 among the universe on D−1**

| feature | lift top quintile | lift bottom quintile | median percentile | n |
|---|---|---|---|---|
| fhh_ret | 1.47 | 1.18 | 0.54 | 17 |
| fhh_vol_share | 0.98 | 1.10 | 0.54 | 41 |
| close_loc | 1.22 | 1.71 | 0.53 | 41 |
| late_vol_share | 0.85 | 1.10 | 0.49 | 41 |

**uncapped: ×2 in one session, 58 name-years; within-day percentile of the intraday feature at D−1 among the universe on D−1**

| feature | lift top quintile | lift bottom quintile | median percentile | n |
|---|---|---|---|---|
| fhh_ret | 1.05 | 2.11 | 0.37 | 19 |
| fhh_vol_share | 1.27 | 2.27 | 0.32 | 55 |
| close_loc | 1.20 | 1.39 | 0.51 | 54 |
| late_vol_share | 1.18 | 1.64 | 0.32 | 55 |

**uncapped: −50% in one session, 49 name-years; within-day percentile of the intraday feature at D−1 among the universe on D−1**

| feature | lift top quintile | lift bottom quintile | median percentile | n |
|---|---|---|---|---|
| fhh_ret | 1.36 | 1.59 | 0.55 | 22 |
| fhh_vol_share | 1.12 | 1.12 | 0.50 | 49 |
| close_loc | 1.43 | 1.73 | 0.50 | 49 |
| late_vol_share | 1.22 | 1.53 | 0.49 | 49 |

**Selection** (the locked procedure on the `uncapped` table, lift ≥ 1.5, three per group, ties
by event count then name): ×2 group, long: `fhh_vol_share` bottom quintile (2.27, n 55),
`fhh_ret` bottom (2.11, n 19), `late_vol_share` bottom (1.64, n 55). −50% group, short /
long-avoid: `close_loc` bottom (1.73, n 49), `fhh_ret` bottom (1.59, n 22), `late_vol_share`
bottom (1.53, n 49). Six rules, twelve ledger rows; `fhh_ret` bottom and `late_vol_share` bottom
are selected for both groups, so those two baskets are held long and short at once (the wave-1
`rvol_20` pattern). Pass 2 runs after this table is committed.

##### Interesting threshold

No row meets it: the highest z at base cost is +1.38 (i2-down `uncapped`, net +1 bps), and no row
has a trade-weighted mean net excess at base cost above +1 bps. **No catalog row goes to the
confirm era.** The i8 rules are run next (pass 2), in-sample by construction.

#### Interpretation

(After the tables.)

#### Next action (per the pre-registered decision rules)

(After the tables.)

#### Open questions / followups

(After the tables.)

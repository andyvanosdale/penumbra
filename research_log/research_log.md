# Research Log

This log is the source of truth for what was tried, why, and what happened. Every experiment gets an entry. Every entry is dated and committed to version control.

**Rules:**

1. Write the **pre-registration section BEFORE running the experiment.** Once you see results, you cannot honestly write down what you "expected."
2. Never edit a past entry to change results. If you find a bug, add a new dated entry that supersedes the old one and link back.
3. Tag every entry with the Git commit hash of the code that produced it.
4. Null results get the same treatment as positive results. They are not "failed experiments" — they are findings.
5. If you peek at the holdout era, log it. Once peeked at, that holdout slice is burned.

**Holdout status:** UNTOUCHED (do not edit this line until the final confirmation run; then change to TOUCHED with date)

**Era split (locked):**

- Development: 2015-01-01 → 2020-12-31
- Validation: 2021-01-01 → 2022-12-31
- Holdout: 2023-01-01 → present

---

## Entry Template

Copy this block for each new experiment. File naming: `research_log/YYYY-MM-DD-short-slug.md` OR append to this rolling log — pick one and stick with it.

```markdown
### YYYY-MM-DD — <experiment short name>

**Phase:** <1 / 2 / 3 / 4>
**Commit:** <git hash>
**Status:** <pre-registered | running | complete | superseded by ENTRY_DATE>

#### Pre-registration (written BEFORE running)

- **Hypothesis:** <the specific testable claim, in one sentence>
- **Feature(s):** <exact definition, including any thresholds and lookback windows>
- **Label:** <exact definition; reference labels.py version if it changed>
- **Universe:** <which tickers, which dates>
- **Era used:** <development | validation | holdout — and WHY this era is appropriate>
- **Model:** <logistic regression / XGBoost / etc., with hyperparams if non-default>
- **Costs assumed:** <spread bps, commission, slippage model>
- **Baselines compared against:** <buy-and-hold sector, random entry, others>
- **What would be "interesting":** <e.g., hit rate > 55% AND signal count > 200 AND beats random by > 0.3% per signal after costs>
- **What would be "not interesting":** <fallback definition>
- **Decision rule:** <if interesting → next step is X; if not interesting → next step is Y>

#### Run details

- **Dataset snapshot date:** <date of the raw data pull this run used>
- **Compute / runtime:** <minutes, machine, anything unusual>
- **Anomalies during run:** <any warnings, dropped rows, NaN handling, etc.>

#### Results

- **Hit rate:** <X%>
- **Signal count:** <N>
- **Avg excess return per signal (after costs):** <X bps or %>
- **Max drawdown:** <X%>
- **Baseline comparison:** <delta vs each baseline>
- **Plots / artifacts:** <path to plots, confusion matrix, equity curve>

#### Interpretation

- **Was the pre-registered "interesting" criterion met?** <yes / no>
- **What does this tell us about the hypothesis?**
- **What does it tell us about the harness?** (Did anything look suspicious? Was the result too good?)
- **Confidence in the result:** <high / medium / low — and why>

#### Next action (per the pre-registered decision rule)

- <concrete next step>

#### Open questions / followups

- <anything you want to come back to but won't chase right now>
```

---

## 2026-10-08 — Wave 2 of the screening program (2a, 2b, 2d; rank mode on daily bars): no graduate

**Pre-registered:** b799b52 · **engine, signals, tests:** 2256c57 · **dev tables:** 8a93b1a · **ledger:**
fb9bbc8 · **interpretation:** the commit after fb9bbc8 on `screen/wave-2`. Three classic
cross-sectional equity signals (12-1 momentum, 52-week-high proximity, weekly reversal in liquid
names), three variants each, as monthly or weekly long baskets against the equal-weight ranked
set on two universes, dev 2010–2020, under a new rank-mode v2 protocol (z_gate = min(plain,
Newey-West) ≥ 2.0, 5 pp net at base, a power statement with MDE80 on every row, random-slice,
lag-250 and lag-20 placebos, a mirror slice, a price-matched comparator, a family-wise p and a
graduate condition that needs delisting-complete data). 18 of 18 ledger rows below the bar: 12
`null` (6 flagged underpowered at an MDE80 of 12 to 16 pp), 6 `insufficient`; no confirm run;
zero graduates. 12-1 momentum +3.7 pp a year gross, +1.7 net (z +0.4; the three-month tranche
variant +3.4 net, z +0.8), with 2020 supplying most of the z; the 52-week high flat gross and −3.6
net at 86% monthly turnover; weekly reversal +8.3 pp gross (16 bps a week) and −1.0 net at 89%
weekly turnover, the pre-stated cost-schedule result. No row is a characteristic or a price
artifact (mirror and lag-250 placebos all within |z| < 1.5; price ratios 0.85 to 1.32). One
engine fault caught by the pre-registered engine check before any result was read (the 2b V3
random draws' pool) and corrected with the first-pass files kept. Holdout untouched; the confirm
era unread. The USD 2 floor on the day's own share basis (split pull complete, 71 minutes) flips 4.3% of
universe-days and moves the V1 nets by about 1 pp a year with no sign or verdict change. Full entry: `2026-10-08-wave-2-rank.md`; files in `2026-10-08-wave-2-rank/`; ledger:
`ledger.md`; protocol amendment proposed in `penumbra-specs`.

---

## 2026-10-07 — Intraday wave of the screening program (i1–i8 on 5-minute IEX bars): no graduate

**Pre-registered:** d979e2a · **data layer and shift tests:** 685f776 · **basis correction, dev tables,
i8 lift table:** a654efd · **i8 pass 2, ledger, interpretation:** the commit after a654efd on
`screen/intraday`. Eight catalog signals (opening-range breakout, gap continuation and fade,
first-half-hour and last-hour momentum, overnight versus intraday, wave 1's post-shock events at
intraday entries, VWAP give-back, and the intraday autopsy of one-session doublers and halvers) at
clock-time fills on Alpaca's IEX 5-minute bars, dev 2020-08 → 2022-06, two equity universes, under
the wave-1 protocol plus a coverage floor, a random-slice placebo and a power statement. 40 of 40
ledger rows `null` in dev; no confirm run; zero graduates. Every gross excess lies within −53 to
+34 bps per trade against 20 to 80 bps round trips. Gross effects of the right sign and the wrong
size: the overnight premium (+13 bps a night universe-wide, z +2.8, the same names −10 to −15 bps
intraday), up gaps fade and down gaps continue (−53 / +34 bps to the close, growing for days),
post-shock drift spread thinly through the next session (+3 to +7 bps), first-half-hour and
last-hour momentum absent (+1 bps with an SE of 1 to 3). Two data lessons: yfinance's `Close` is
split-adjusted, so a raw venue price must never be divided by it (returns are chained at the
session close; the pre-fix tables are kept); IEX half days carry after-hours prints, so early
closes are detected by density. The IEX coverage floor leaves 29 / 125 names a day. Holdout
untouched; the confirm era unread. Full entry: `2026-10-07-intraday-wave.md`; files in
`2026-10-07-intraday-wave/`; ledger: `ledger.md`.

---

## 2026-10-01 — Wave 1 of the signal-screening program (1a–1e, extreme movers, autopsy to rule): no graduate

**Pre-registered:** af23489 (amendment cbc3c67) · **engine:** 6343335, 59c8d43, f912434 · **data and
regression:** 07dd1de · **dev tables:** 40eac00 · **autopsy, confirm, ledger, interpretation:** the
commit after 40eac00 on `screen/wave-1`. Five catalog signals on three universes (plus BTC and ETH
for 1d), the extreme-movers counts and lifts, and twelve autopsy-derived rules, under the
proposal's common protocol (next-open fills, flat cost schedule, day-clustered z, placebo and
planted control, dev 2010–2020 / 2018–2022). Catalog: 18 of 18 ledger rows `null` in dev; no
confirm run. Post-shock continuation (1a) is gross-positive (+25 bps `smallcap`, +54 bps crypto at
five sessions, z +3.0 / +3.6) and negative at the base cost schedule; up-shock on volume (1b)
reverses in equities (−45 / −79 bps, z −3 to −4); slide-cohort (1c) flat in equities, +231 bps net
on 361 crypto trades (z +2.4, below the counts floor); crypto trend-following (1d) +8 / +16 pp a year
over buy-and-hold at z +0.3 / +0.5 (the rank-mode bar is underpowered by 10×); cross-sectional
momentum (1e) −12 pp a year. Autopsy to rule: 14 `null`, 4 `artifact`: long the cheapest and short
the most expensive price quintile both beat the universe by +330 to +915 bps per quarter in dev and
confirm with placebos as significant as the signal, the survivorship bias of a current listing made
visible. Zero graduates; 36 ledger rows; holdout untouched; the equity confirm era was read by the
four autopsy rows only. Full entry: `2026-10-01-wave-1-screen.md`; files in
`2026-10-01-wave-1-screen/`; ledger: `ledger.md`.

---

## 2026-09-30 — Screen 2: post-shock continuation, crypto (issue 39): null; the idea is dropped

**Pre-registered:** 3b3e98d · **code and results:** bef1c1c (branch `screen/continuation-crypto`).
Short at the 01:00 UTC open after a −2σ drop, fixed 5-session exit, 1.5×-range stop, on the
USD-M perpetual 2020–2022 with tier costs, spec/06 slippage and funding: mean net short
excess over the same-day universe **−37 bps** per trade (rule 1: ≥ +50), day-clustered z
**+0.58** (rule 2: ≥ 2.0), per year +8 / −7 / −79 (rule 3: all positive); placebo z +0.01
and top-10-day share 30% pass (rules 4, 5). Spot mirror 2018–2022 at tier cost −13 bps,
negative in three of five years. Issue 15's −228 bps day-mean read is a day-weighting
effect: the crash days with the most candidates are the days the shorted names rebound.
Decision per the pre-registration: the continuation idea is dropped for crypto. Full
entry: `2026-09-30-continuation-crypto.md`; tables in `2026-09-30-continuation-crypto/`.

---

## 2026-09-28 — Free-data screen of the v1 rule (issue 15): null in every lane

**Pre-registered:** 9a7721e · **code:** 256b98a · **results:** 911d146 (branch `screen/free-data`).
Next-open 5-session excess over the same-day universe at zero cost: `smallcap` −11 bps
(day-clustered z −2.5), uncapped +6 bps (z −1.6), crypto top-100 −42 bps (z −3.7),
against the +50 bps threshold. Placebo flat; planted +50 bps detectable. Decisions per
the pre-registration: the equity build for the v1 rule stops, and the crypto lane is
removed by spec change. Full entry: `2026-09-28-free-data-screen.md`; tables in
`2026-09-28-free-data-screen/`.

---

## 2026-09-28 — Legacy day-of-week plumbing test on real prices (issue 1)

**Commit:** `5a92cf0824a3cd34597481faa5d6d0b45039a812` · yfinance 1.7.0 · PASS —
z vs random = 0.073 (tolerance |z| < 2.0), 11,911 signals, 0 tickers failed
(58/58 pulled: 50 tickers + 8 sector ETFs, 2015-01-01 → 2020-12-31). Full
pre-registration and results: `2026-09-28-legacy-control-real-prices.md`.

---

## 0000-00-00 — Project bootstrap (placeholder)

**Phase:** 0 (setup)
**Commit:** TBD
**Status:** pre-registered

This entry exists so the log file is not empty. Replace with the first real experiment entry once Phase 1 begins.

#### Pre-registration

- **Hypothesis:** N/A — bootstrap entry, not a real experiment.
- **Intent:** Verify repository layout, environment, and that this log file is committed.

#### Notes

- First real entry will be Phase 1 Plumbing: dummy "is it Monday" feature, expected null result, decision rule = if a non-null edge appears, the harness has a bug and Phase 1 does not pass.

---

## Holdout Access Log

Every time the holdout era is touched, record it here. Once touched without an explicit "final confirmation run" justification, the holdout is contaminated.

| Date | Reason | Commit | Result summary | Holdout still valid? |
|---|---|---|---|---|
| — | — | — | — | yes (untouched) |

---

## Lessons File

Running list of hard-won lessons. Add to it whenever you find a bug or a near-miss. Re-read at the start of every new phase.

- (2026-10-01, wave 1) Binance reuses a pair's symbol across token swaps, redenominations and
  relists (LUNAUSDT 2022-05 jumps 177,400× across an 18-day gap; COCOS, DREP, SUN, VEN, BNX,
  QUICK, VIDT, BTCST, STRAX likewise). Any forward return longer than a few days on the raw 1d
  klines is contaminated. The screen's data layer now ends an instrument at a gap of more than
  three days; anything else that reads the klines must do the same.
- (2026-10-01, wave 1) The lag-20 stale-signal placebo tests whether a signal is an event. For a
  persistent characteristic (price level, size, liquidity) the lagged rule is the same basket and
  the placebo is as significant as the signal. Rank-type rules need a different placebo (random
  quintile, or a lag longer than the characteristic's persistence) and a power statement next to
  the z bar: with weekly SEs of 50–70 bps, z ≥ 3 over 260 weeks needs an 80–100 pp annual edge.
- (2026-10-01, wave 1) On a current-listing equity sample, a quarter-horizon price-sorted
  portfolio shows an 18 pp a year "premium" in both eras with every control that can pass
  passing. It is the survivorship bias, not an edge; no long, slow, cheap-name equity rule can be
  decided on free data.
- (2026-10-07, intraday wave) yfinance's `Close` is split-adjusted even with `auto_adjust=False`
  (only dividends are left out), so `adj_close / close` undoes dividends, not splits, and a raw
  venue price divided by a yfinance price is wrong by every later split (KUST: a factor of
  millions). A return that crosses two price sources must chain two legs at a shared timestamp
  (here the session close), never divide across them. A test that scales one source by 10 and
  asserts every return is unchanged catches it.
- (2026-10-07, intraday wave) IEX 13:00 half days still carry a handful of after-hours prints from
  13:00 on, so "no bar after 13:00" finds no early close. Detect them by the afternoon bar share
  across all names (< 30% of the morning's), and drop the afternoon bars as extended hours.
- (2026-10-07, intraday wave) On a 2–3%-share venue the coverage floor is the binding constraint:
  60 prints a session on 20 consecutive sessions leaves 29 of 732 `smallcap` names, and 25 to 40%
  of clock-time fills are a bar late. Session-shape rules on IEX bars are tests on the liquid tail
  only; a consolidated feed is the fix, and it costs money.
- (2026-10-08, wave 2) A random-slice placebo must draw from the comparator set, not the
  signal's ranked set: when a variant ranks within a subset (2b V3 inside the 2a top half), a
  draw from the subset carries the subset's tilt and the placebo "passes" the signal's own
  effect. The pre-registered engine check (draw medians near zero) is what caught it; keep
  one in every rank-mode wave, with a tolerance that scales with the draw spread.
- (2026-10-08, wave 2) On 130 monthly observations at a 5% tracking volatility the MDE80 at
  z = 2 is 12 to 15 pp a year; the classic long-only premia are 2 to 5. A null here is a
  statement about power first and the signal second, and must carry its MDE80; the only way
  to decide a 3-pp premium is 500 or more months, i.e. the delisting-complete history.
- (2026-10-08, wave 2) A single calendar year can supply most of a momentum row's z (2020:
  +0.5 to +0.8 z-units, +36 to +46 pp a year); a sign-only artifact rule does not catch it. A
  rule-4 condition on z without that year is load-bearing for any trend signal.
- (2026-10-07, intraday wave) Intraday horizons measure zero very precisely (day-mean SEs of 1 to
  7 bps on the dense rows), so the 50-bps bar is purely the cost schedule's. An intraday row on
  this universe can only pass if a quote sample shows round trips near 10 bps; intraday screening
  is a cost-calibration question before it is a signal question.

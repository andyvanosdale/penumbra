### 2026-09-30 — Screen 2: post-shock continuation, crypto first (pre-build)

**Phase:** 0 (screen before any build; follows issue 15's null on the v1 reversal rule)
**Commit:** 3b3e98d (pre-registration) · bef1c1c (code and result files that produced every number below)
**Status:** complete
**Issue:** andyvanosdale/penumbra#39
**Spec:** `andyvanosdale/penumbra-specs` `main` at `3e2e6c11` — `spec/01`, `04`, `05`, `06`, `07`
and the DECISIONS entry "2026-09-28 · Free-data screen outcome: null in every lane; the v1
rule is retired" (its "Read, not decided" paragraph is why this screen exists).

**In-sample caveat, stated up front (transcribed from the issue).** The read came from the
2018–2022 crypto data this screen reuses. It was a single reported diagnostic, not a search,
but the bar is stricter than issue 15's for that reason, and the crypto validation era
(2023-01-01 to 2024-12-31) is *not* touched: it stays reserved for the harness. The holdout era
(2025 onward) and the validation era (2023–2024) are not downloaded, for either instrument.

#### Pre-registration (written BEFORE running)

- **Hypothesis:** A −2σ one-day drop in a top-100 Binance USDT pair is followed by five
  sessions of continued *under*performance against the same-day universe (issue 15's read:
  day-mean −228 bps, SE 61), large enough that a short entered at the next 01:00 UTC open on
  the USD-M perpetual earns at least +50 bps per trade over the same-day universe after
  taker fee, tier spread, spec/06 slippage and funding.
- **Rule (locked in issue 39; transcribed, nothing fitted):**
  - **Universe:** as issue 15's crypto universe. Binance USDT spot pairs, top 100 by trailing
    30-day quote volume as of D, base not a stablecoin, leveraged or wrapped token, 1d kline on
    each of the 30 days ending D, 30-day annualized vol above 20%.
  - **Candidate:** `shock ≤ −2.0` on D (1-day log return at or below −2 × trailing daily vol
    measured over the 20 days ending D−1). No candidate in a name the lane already holds.
  - **Position:** short, USD 10,000 notional, entered at the open of the 01:00 UTC 1h kline
    on D+1.
  - **Exit:** the open of the 01:00 UTC kline on the 5th session after the fill session
    (fixed horizon), or earlier at a hard stop of entry fill + 1.5 × the signal day's range
    (evaluated against the session high, filled at the level or at the open if the open is
    through it). 1-, 3- and 10-session holds are reported as a horizon read; they do not decide.
  - **Two instruments, both reported:**
    - *Spot mirror* (2018-01-01 to 2022-12-31): the return a short would earn on spot prices,
      with tier costs (10 bps taker + 5 or 15 bps spread per side) and the spec/06 model
      reported separately. Not implementable as a short; it is the comparability check
      against issue 15.
    - *Perpetual* (2020-01-01 to 2022-12-31, where the USD-M perpetual exists for the base
      asset): entered and exited on the perpetual's 1h klines from the public bucket, taker
      fee 5 bps per side, tier spread, slippage per spec/06 form, and funding settled every
      8 hours over the hold (a short *receives* positive funding and pays negative).
      Spot-to-perpetual mapping strips a leading numeric multiplier (1000SHIBUSDT ↔
      SHIBUSDT). This is the implementable strategy and the decision instrument.
  - **Decision quantity:** the 5-session net short excess return per trade: universe mean
    return over the same window (equal-weight, same-day eligible universe, long) minus the
    short position's net return sign-adjusted so that positive means the short beat the
    universe, net of the instrument's costs and funding.
  - **Statistic:** day-clustered z as in issue 15 (mean over entry days of the daily
    difference over its standard error), plus the z with the top 10 entry days removed.
- **Feature(s):** `ret_1` = ln(close_D / close_{D−1}) on the spot 1d klines;
  `rvol_20_prev` = annualized (√365) sample std of the 20 1-day log returns ending D−1;
  `shock` = `ret_1` / (`rvol_20_prev` / √365). `rvol_30` for the universe vol floor.
  `zscore_20` = (close − 20-day mean close) / 20-day sample std of close, ending D (read only).
- **Label:** the decision quantity above, realized per trade from the fills the rule
  produces; no `labels.py`.
- **Universe:** as above, evaluated per UTC day D on the spot 1d klines; the exclusion sets
  are the ones in `experiments/screen_free_data.py` (issue 15).
- **Era used:** spot mirror 2018-01-01 → 2022-12-31 (the crypto dev era); perpetual
  2020-01-01 → 2022-12-31 (the perpetual bucket's coverage inside the dev era). Signal days D
  in those windows. This is a screen on the dev era, with the in-sample caveat above; the
  validation era is not touched.
- **Model:** none. Fixed rule.
- **Costs assumed (per instrument):**
  - Spot mirror, `tier`: 10 bps taker + 5 bps (top 20 by trailing 30-day quote volume on D)
    or 15 bps (otherwise) spread, per side; 30 or 50 bps round trip.
  - Spot mirror, `spec`: the spec/06 crypto model as implemented for issue 15: half the
    Abdi–Ranaldo spread over the 20 sessions ending D−1 (negative two-day estimates zeroed),
    floored at 5 / 15 bps by tier on the full estimate before halving; entry leg at 2× with
    participation against 10% of the median 20-day quote volume ending D−1, exit leg at 1×
    against the full median; slippage 0.5 × σ_d × √participation per leg with σ_d =
    `rvol_20` / √365 and participation = USD 10,000 / median quote volume; 10 bps taker per side.
  - Perpetual (the decision cost): 5 bps taker per side, tier spread of 5 / 15 bps per side
    (tier by the spot 30-day quote-volume rank on D, as the universe is defined), slippage
    in the spec/06 form above (entry against 10% of the median, exit against the full median)
    computed on the perpetual's own median 20-day quote volume ending D−1 with σ_d =
    `rvol_20` / √365 from spot, and funding as below. Also reported at zero funding.
  - No cost is charged to the universe comparator.
- **Baselines compared against:** the same-day equal-weight eligible universe (long), as in
  issue 15. No random-draw benchmark.
- **What would be "interesting":** all five decision rules hold on the perpetual and the
  spot mirror has the same sign in four of five years.
- **What would be "not interesting":** any rule fails.
- **Decision rules (locked in issue 39; transcribed):** The lane is worth building only if
  all hold on the **perpetual** instrument over 2020-01-01 to 2022-12-31:
  1. Mean net short excess per trade ≥ +50 bps at the tier cost model with funding.
  2. Day-clustered z ≥ 2.0, and z with the top 10 entry days removed ≥ 2.0.
  3. Positive net excess in each calendar year 2020, 2021 and 2022 (a bull, a bull and a bear).
  4. The stale-signal placebo (shock lagged 20 sessions) has |z| < 2.0.
  5. Share of absolute P&L from the top 10 entry days below 35%.

  And the spot mirror over 2018–2022 shows the same sign in at least four of five years.
  Failure on any rule: the continuation idea is dropped for crypto and recorded in the specs
  decision log. Success: a spec PR promoting a crypto continuation lane (the momentum epic's
  crypto half) and the crypto ingest (issue 4) resumes.
- **Also reported, not decided (from the issue):** regime split by BTCUSDT trailing 20-day vol
  above or below its era median; exit mix, mean hold, candidates skipped for being held,
  unfilled candidates; funding's share of the net return and the result at zero funding; the
  same rule with `shock ≤ −3.0` and with a 20-session `zscore_20 ≤ −2` band trigger, as a read
  on where the effect lives; never a decision input.

##### Readings chosen where the issue leaves a detail open (conservative; fixed before the run)

- **Sessions** are UTC days, the spot 1d klines' days, as in issue 15. The fill session F is
  D+1. The fixed exit is the 01:00 UTC open on the 5th session after F that has a bar (a
  session with no bar evaluates no exit and does not advance the count, issue 15's rule).
- **Stop evaluation** runs on the sessions strictly after the fill session and before the exit
  session (F+1 … F+4), as in issue 15, on the instrument's own 1d kline: if the session's open
  (00:00 UTC) is at or above the stop level, the stop fills at that open; else if the session
  high is at or above the level, it fills at the level. The stop is not evaluated on the fill
  session's remaining hours nor on the exit session's first hour. The signal-day range is
  the spot 1d kline's high − low on D; for the perpetual it is scaled by the symbol's
  numeric multiplier so it is in the perpetual's price units. A candidate whose signal-day
  range is zero is recorded as unfilled.
- **Fill:** the open of the 01:00 UTC 1h kline of the instrument on F. If that kline is
  missing, the candidate is recorded as unfilled (no fallback to the 1d open).
- **Sign convention of the decision quantity:** excess = universe return over the trade's
  window (long, equal-weight over the names eligible on D, measured on spot 01:00 UTC opens,
  to the 01:00 open of the exit session for a fixed exit, or to the stop session's close for
  a stop, issue 15's comparator) **plus** the short's net return, where the short's net
  return = −(exit / entry − 1) − costs + funding. Positive means the short beat the universe.
  The universe is the spot universe for both instruments (the universe is defined on spot;
  the perpetual comparator is the same names on spot, so basis between instruments is not
  part of the decision quantity).
- **Funding:** from the bucket's `fundingRate` files for the perpetual symbol; every
  settlement with calc_time strictly after the entry time and before the exit time is
  applied, at rate × (perpetual 1h open at the settlement / entry) so it is the notional at
  the settlement, sign-adjusted so the short receives positive rates. Exit time: 01:00 UTC on
  the exit session for the fixed exit; 00:00 UTC of the stop session when the stop fills at
  the open (that settlement excluded); for a stop filled at the level the intra-session time
  is unknown, so the 00:00 UTC settlement of the stop session is included and later ones
  that session are not.
- **Trades not closed by the data end (2022-12-31)** are closed at the last available bar
  and flagged `truncated`, counted, and kept in the tables (issue 15's rule). Because 2023 is
  never downloaded, every signal in the last week of December 2022 is one.
- **Spot-to-perpetual map:** USDT-quoted USD-M symbols listed under
  `data/futures/um/monthly/klines/` with a leading numeric multiplier stripped; delivery
  contracts (`_YYMMDD` suffix) and `SETTLED` symbols are ignored. If both the plain and a
  multiplied symbol exist for one base, the one with klines inside 2020–2022 is used, the
  plain one if both have them. The map and the pairs without a perpetual are recorded in
  the results folder. A candidate on a pair without a perpetual is not a perpetual candidate;
  a candidate whose perpetual has no bar on F is unfilled.
- **Per-year rule (3) and the spot four-of-five check** use the trade-weighted mean net
  excess of trades by signal year. Rule 1 is the trade-weighted mean; rule 2 the
  day-clustered z on the daily mean excess over entry days.
- **Top-10 entry days** are the ten days with the largest absolute summed net excess
  contribution; the share is their absolute sum over the absolute sum of all days (issue 15).
- **Placebo:** the candidate on D is the name whose `shock` was ≤ −2.0 on D−20 (issue 15's
  `_shift(shock, −20)`), same fills, costs and funding, on the perpetual.
- **Regime split:** BTCUSDT spot `rvol_20` as of D (the last value known at the fill) above
  or below its median over the instrument's era.
- **Alternative triggers (reads):** identical rule with `shock ≤ −3.0`; identical rule with
  `zscore_20 ≤ −2.0` on D in place of the shock condition.
- **Horizon read:** the same rule with the fixed exit at the 1st, 3rd and 10th session after
  F (stop still active), on the perpetual and the spot mirror.

#### Run details

- **Dataset snapshot date:** 2026-09-30 (all pulls, Binance public bucket via
  `data.binance.vision`; nothing dated 2023 or later was requested for either instrument, and
  the run asserts every kline and funding table ends before 2023-01-01).
  - Spot: 1d klines for every USDT pair with files in 2018-01 → 2022-12 (735 symbols listed in
    the bucket today; 354 with data in the window after the stablecoin / leveraged / wrapped
    exclusions), plus 1h klines for the 316 pairs that ever enter the top-100 universe, from
    which the 01:00 UTC open is taken (coverage 99.98% of universe cells). Same code, same
    universe as issue 15 (316 names ever eligible, median 100 per day).
  - USD-M perpetual: 864 USDT-quoted perpetual symbols listed in the bucket; 166 have 1d
    klines inside 2020-01 → 2022-12; 1d, 1h and `fundingRate` monthly files pulled for those
    (3,671 months each). 108,816 1d rows, 2.61 M 1h rows, 323,433 funding settlements.
  - Spot → perpetual map: 159 spot pairs map to a perpetual, four through a multiplier
    (`1000BTTCUSDT`, `1000LUNCUSDT`, `1000SHIBUSDT`, `1000XECUSDT`); no base had both a plain
    and a multiplied symbol. Of the 312 pairs ever in the universe in 2020–2022, 158 have a
    perpetual and 154 do not (`meta.json`, `spot_to_perp_map.csv`).
- **Compute / runtime:** spot pull 47 min (16 threads), perpetual pull 12 min (12 threads);
  the screen itself 8 s on 4 cores. Script `experiments/screen_continuation_crypto.py`
  (`perp` and `run` stages; the spot stage is issue 15's `screen_free_data.py crypto`).
- **Checks before reading a number:** synthetic hand-built panel exercising the fixed exit at
  the 01:00 open of the 5th session, the stop at the level, the gap-through stop at the
  session open, the "no stop on the fill session" convention, the skip of a candidate in a
  held name, a missing session not advancing the count, the 1-session hold and the lag-20
  placebo (all pass); a UNIUSDT 2021-05-19 perpetual trade recomputed from the raw 1h and
  1d zips (entry, exit, stop level and gross match to the last digit); an ADAUSDT 2020-02-15
  funding leg recomputed from the raw funding file (matches).
- **Anomalies during run:**
  - **Perpetual coverage.** 375 of the 2,820 spot candidates on mapped names in 2020–2022 fall
    on days before the perpetual was listed (or on which it had a zero-volume placeholder
    bar) and are not perpetual candidates; 4 more had no 01:00 UTC 1h kline on D+1 and are
    unfilled. Zero-quote-volume perpetual bars (1,494 daily rows, around listings and
    delistings) are treated as missing bars, as issue 15 treated zero-open placeholder rows.
  - **Slippage denominator fallback.** 35 perpetual trades (1.8%) fall within the perpetual's
    first 20 sessions, where its 20-day median quote volume is undefined; the spot median
    dollar volume stands in. Perpetual volume is normally the larger, so this overstates
    their slippage. Recorded per trade (`vol_fallback`).
  - **Funding intervals.** 182 of 323,433 settlements are at 2- or 4-hour intervals (Binance
    switched FTTUSDT, SOLUSDT, HNTUSDT and OMGUSDT to shorter intervals in November 2022);
    every recorded settlement inside the hold is applied, not an assumed 8-hour grid.
  - **The stop does not cover the fill session.** Under the pre-registered (issue 15)
    convention the stop is first evaluated on the session after the fill session, so a
    squeeze that starts within the 23 hours after the 01:00 fill runs to the next session's
    open. DOGEUSDT, signal 2021-01-27: fill 0.007569 at 01:00 on the 28th, stop 0.00906, the
    29th's open 0.036367 (the January 2021 DOGE squeeze), short gross −380%. That one trade
    is −18 bps of the perpetual's −37 bps trade-weighted mean (−18 bps without it). Six
    positions in all exited at a gap-through open (mean excess −79%); 157 at the stop level
    (mean −16%). This is the rule as locked and pre-registered; it is listed under open
    questions, not changed here.
  - **Truncation.** 12 perpetual trades (0.6%) and 11 spot trades (0.3%) were closed at the
    last available bar: signals in the last days of December 2022 (2023 is never
    downloaded) and perpetuals delisted mid-hold (LUNAUSDT after 2022-05-07, exit at 0.008,
    short gross +99.99%; SRMUSDT 2022-11-13, funding −16.7% over the hold as the contract
    wound down).
  - **Cost model.** The spec/06 crypto cost (Abdi–Ranaldo spread over the 20 sessions ending
    D−1, 2× on entry, floors, slippage, 10 bps taker) averages 600 bps round trip on these
    candidates, as in issue 15 (the estimator question raised there stands); it is reported
    on the spot mirror only, as the issue asks. The perpetual's tier cost averages 53 bps
    round trip: 10 bps taker, about 25 bps tier spread (most candidates are outside the top 20),
    18 bps spec/06-form slippage.
  - No host was blocked; `data.binance.vision` and its S3 listing endpoint served everything.

#### Results

All figures are basis points per trade unless stated. "excess" is the decision quantity:
universe return over the trade's window (spot, equal-weight, same-day eligible, long) plus the
short's net return (−price return − costs + funding); positive means the short beat the
universe. "mean" is trade-weighted (rules 1 and 3); "day-mean / SE" are over entry days
(rule 2's z). Full tables, including per-year for every variant: `2026-09-30-continuation-crypto/tables.md`.

**Headline (fixed 5-session exit, stop 1.5 × signal-day range)**

| instrument / cost | candidates | trades | days | mean excess | median | hit | day-mean | SE | z | z w/o top 10 | top-10 share | short gross | universe | cost | funding |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **perpetual, tier + funding (decision)** | 2,445 | 1,994 | 187 | **−37** | +106 | 0.553 | +71 | 123 | **+0.58** | +2.64 | **30.2%** | −67 | +85 | 53 | −1.4 |
| perpetual, tier, zero funding | 2,445 | 1,994 | 187 | −35 | +97 | 0.553 | +78 | 118 | +0.66 | +2.39 | 30.3% | −67 | +85 | 53 | 0 |
| perpetual, zero cost, with funding | 2,445 | 1,994 | 187 | +16 | +160 | 0.587 | +126 | 123 | +1.03 | +3.14 | 28.4% | −67 | +85 | 0 | −1.4 |
| spot mirror, tier (2018–2022) | 4,351 | 3,491 | 371 | **−13** | +113 | 0.563 | +119 | 65 | +1.84 | +2.63 | 20.1% | −2 | +34 | 45 | — |
| spot mirror, spec/06 | 4,351 | 3,491 | 371 | −568 | −413 | 0.266 | −454 | 67 | −6.73 | −6.42 | 27.0% | −2 | +34 | 600 | — |
| spot mirror, zero cost | 4,351 | 3,491 | 371 | +32 | +155 | 0.590 | +164 | 65 | +2.52 | +3.30 | 20.0% | −2 | +34 | 0 | — |

**Per year (trade-weighted mean excess; day-mean; z; trades)**

| year | perpetual, tier + funding | perpetual, zero funding | spot mirror, tier | spot mirror, zero cost |
|---|---|---|---|---|
| 2018 | — | — | −54; +2; +0.03; 154 | −24; +32; +0.53; 154 |
| 2019 | — | — | +3; +89; +1.22; 481 | +45; +133; +1.82; 481 |
| 2020 | **+8**; +161; +1.21; 352 | −2; +159; +1.19 | −13; +111; +1.15; 862 | +33; +157; +1.63; 862 |
| 2021 | **−7**; +91; +0.41; 753 | −20; +56; +0.25 | +23; +110; +0.48; 905 | +69; +156; +0.68; 905 |
| 2022 | **−79**; −2; −0.01; 889 | −61; +41; +0.19 | −45; +191; +1.32; 1,089 | +1; +239; +1.64; 1,089 |

**Decision rules, applied literally to the perpetual (2020-01-01 → 2022-12-31)**

| rule | value | verdict |
|---|---|---|
| 1. mean net excess ≥ +50 bps at tier cost with funding | −37 bps | **FAIL** |
| 2. day-clustered z ≥ 2.0 and z without the top 10 entry days ≥ 2.0 | +0.58 / +2.64 | **FAIL** (z) |
| 3. positive net excess in 2020, 2021 and 2022 | +8 / −7 / −79 | **FAIL** (2021, 2022) |
| 4. placebo (shock lagged 20 sessions) has abs z < 2.0 | +0.01 (2,007 trades, 192 days) | PASS |
| 5. share of absolute P&L from the top 10 entry days < 35% | 30.2% | PASS |
| spot mirror same sign in ≥ 4 of 5 years | 2018 −54, 2019 +3, 2020 −13, 2021 +23, 2022 −45: 3 of 5 negative, 2 of 5 positive | **FAIL** either way |
| **all five and the spot check** | | **FAIL** |

**Controls and reads (not decisions)**

| read | perpetual (tier + funding) | spot mirror (tier) |
|---|---|---|
| placebo, shock lagged 20: mean; day-mean; z; trades | −30; +0; +0.01; 2,007 | −52; −74; −1.64; 3,535 |
| horizon, 1 session: mean; day-mean; z | −63; −99; −1.23 | −49; −42; −0.89 |
| horizon, 3 sessions | −46; −4; −0.04 | −26; +54; +0.93 |
| horizon, 5 sessions (the rule) | −37; +71; +0.58 | −13; +119; +1.84 |
| horizon, 10 sessions | −49; +129; +0.92 | −23; +161; +1.98 |
| regime, BTC `rvol_20` above era median (0.63): mean; day-mean; z; trades | −59; −181; −0.68; 970 | −11; +36; +0.29; 1,635 |
| regime, BTC `rvol_20` below era median | −15; +232; +2.17; 1,024 | −15; +176; +2.55; 1,856 |
| trigger `shock ≤ −3.0`: mean; day-mean; z; trades; top-10 share | −76; +82; +0.37; 789; 58% | −7; +193; +1.91; 1,357; 36% |
| trigger `zscore_20 ≤ −2.0`: mean; day-mean; z; trades | −61; −65; −0.49; 1,420 | −40; +66; +1.24; 2,572 |
| funding: mean per trade; share of net; positive-rate share | −1.4 bps; 1.1% of net; 64% of trades receive | — |
| exit mix: fixed / stop at level / stop at open / truncated | 0.912 / 0.079 / 0.003 / 0.006 | 0.905 / 0.090 / 0.003 / 0.003 |
| mean sessions held | 4.77 | 4.75 |
| candidates skipped for a held name / unfilled (no 01:00 bar; zero range) | 445 / 4; 2 | 857 / 1; 2 |

Top 10 entry days by absolute contribution (perpetual, summed excess; trades): 2021-01-27
−323% (3, the DOGE squeeze), 2020-03-08 −250% (23), 2021-10-27 −194% (57), 2022-11-08 −191%
(57), 2021-05-19 −168% (82), 2022-05-05 −150% (33), 2022-11-13 −137% (1, SRM), 2020-08-02
+131% (14), 2020-06-11 +119% (18), 2021-06-21 −119% (80). Seven of the ten are losses: the
days after the largest drops are the days the shorted names bounce hardest against the
universe.

#### Interpretation

- **Was the pre-registered "interesting" criterion met?** No. Rules 1, 2 and 3 fail on the
  perpetual (−37 bps per trade against +50; z +0.58 against 2.0; negative in 2021 and 2022),
  and the spot mirror is negative in three of five years. Rules 4 and 5 pass: the placebo is
  flat (z +0.01) and no ten days carry more than 30% of the absolute P&L, so the null is not
  a concentration artefact and the signal is not stale drift.
- **What does this tell us about the hypothesis?** Issue 15's read (candidates underperform
  the universe by 228 bps per day over five sessions) does not survive being traded. Three
  things separate the read from the rule:
  1. *Weighting.* The read was a day-mean. The days with the most candidates (2020-03-08,
     2021-05-19, 2021-10-27, 2022-05-05, 2022-11-08: market-wide crashes) are the days the
     shorted names rebound against the universe, so the trade-weighted mean is 100–130 bps
     below the day-mean on both instruments (perpetual day-mean +71, trade mean −37; spot
     +119 vs −13). A strategy trades trades, not days.
  2. *The stop.* A short's hard stop is hit on squeezes, and post-crash squeezes are large:
     the 163 stopped perpetual trades average −18% of excess, against +1.3% for the 1,819
     fixed exits. The 8% of trades that stop out cost more than the 91% that run.
  3. *Costs.* Even at zero cost the perpetual's trade mean is +16 bps and the spot mirror's
     +32, a third of the threshold; 53 bps of tier cost take it negative. Funding is
     immaterial (−1.4 bps per trade, 1% of net): the names that just crashed do not carry
     the positive funding a short would collect.
  The horizon read says the same thing at every hold: 1, 3, 5 and 10 sessions are all
  negative trade-weighted on the perpetual (−63, −46, −37, −49). The `shock ≤ −3.0` and
  `zscore_20 ≤ −2.0` triggers are worse, not better (−76 and −61 on the perpetual), and the
  `−3.0` trigger's top-10-day share is 58%. The low-BTC-vol regime has a positive day-mean
  (+232, z +2.17 on the perpetual) but a negative trade mean (−15); it is the same
  weighting effect, not a regime where the rule works.
- **What does it tell us about the harness?** Nothing new about the harness; this is a
  standalone screen. About the screen's own engine: the hand-built checks and the raw-file
  recomputations pass, the placebo is flat, the perpetual and spot mirror agree in sign and
  magnitude on the overlapping names and years (spot 2020–2022 on perpetual-mapped names:
  −6 bps at tier cost, +40 at zero cost; perpetual −37 / +16), and nothing looked too good.
  The one modelling weakness worth carrying forward is the stop convention: with UTC-day
  sessions and a 01:00 fill, the first 23 hours of the position are unprotected, and one
  DOGE trade in that window is worth 18 bps of the mean. Removing it does not change any
  verdict (−18 bps, still below +50).
- **Confidence in the result:** high for the failure of rules 1 and 3, which are decided by
  100–130 bps on 1,994 trades; the sign of the trade-weighted mean is negative on both
  instruments, at every horizon, on both alternative triggers, and in the 2020–2022 spot
  overlap. Medium for rule 2's exact z (187 entry days, SE 123 bps, heavy day clustering),
  but a z of +0.58 is not near 2.0. The in-sample caveat cuts the other way: this is the
  same 2018–2022 data the read came from, so a real effect would have had every chance.

#### Next action (per the pre-registered decision rule)

1. **The continuation idea is dropped for crypto.** Rules 1, 2 and 3 fail and the spot mirror
   fails the four-of-five check. No spec PR promoting a crypto continuation lane; the crypto
   ingest (issue 4) stays stopped.
2. **Record the outcome in `penumbra-specs` DECISIONS** (issue 39 acceptance). Proposed entry,
   for the product architect to make on that repo (this session's access to it is read-only):

   > ## 2026-09-30 · Screen 2 outcome: post-shock continuation in crypto is a null; the idea is dropped
   > **Decision.** The pre-registered continuation screen ("Pre-build screen 2", product repo
   > issue 39, branch `screen/continuation-crypto`, research log
   > `research_log/2026-09-30-continuation-crypto.md`, commits 3b3e98d–bef1c1c) fails its
   > decision rules as written on the USD-M perpetual over 2020-01-01 → 2022-12-31: mean net
   > short excess −37 bps per trade against +50 (rule 1), day-clustered z +0.58 against 2.0
   > (rule 2), negative in 2021 and 2022 (rule 3); the placebo is flat and the top-10-day
   > share is 30% (rules 4 and 5 pass). The spot mirror is negative in three of five years.
   > The continuation idea is dropped for crypto; no crypto continuation lane is added to
   > the momentum epic and the crypto ingest stays stopped.
   > **Why.** Issue 15's −228 bps day-mean read was a day-weighted diagnostic; traded, the
   > days with the most candidates (market-wide crashes) are the days the shorted names
   > rebound against the universe, the hard stop turns squeezes into −18% trades, and 53 bps
   > of tier cost take a +16 bps zero-cost mean negative. Funding is immaterial. Every
   > horizon (1, 3, 5, 10 sessions) and both alternative triggers are negative.
   > **Rejected.** Loosening any rule after the fact; a stop or exit variant search (the
   > alternative triggers and horizons were reads, and all are worse).

3. Issue 39 comment posted with the headline table and each rule's verdict:
   https://github.com/andyvanosdale/penumbra/issues/39#issuecomment-5915664103 (PR #40).

#### Open questions / followups

- **Stop coverage on the fill session.** A 01:00 fill with UTC-day sessions leaves the first
  23 hours unprotected; the 1h klines could evaluate the stop hourly from the fill. Not run
  here (the rule was locked), and it would not rescue the verdict (the fixed-exit trades
  alone average +126 bps per trade, but the weighting and cost problems remain); worth
  fixing in any future crypto rule with an intraday fill.
- **Day-mean versus trade-mean.** Any future read reported as a day-mean should carry the
  trade-weighted mean beside it; the gap here is 100–130 bps and it reverses the sign.
- **spec/06 crypto spread.** The Abdi–Ranaldo estimate still charges ~600 bps round trip on
  these names, ten times the tier constants. Issue 15's note stands: no crypto rule should be
  costed with it until a quote sample calibrates it.
- **Perpetual coverage.** Only 158 of the 312 pairs that enter the top-100 spot universe in
  2020–2022 have a USD-M perpetual, and 375 candidates fall before the perpetual's listing.
  Any future perpetual lane should define its universe on the perpetuals themselves.

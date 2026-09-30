### 2026-09-30 — Screen 2: post-shock continuation, crypto first (pre-build)

**Phase:** 0 (screen before any build; follows issue 15's null on the v1 reversal rule)
**Commit:** pre-registration: (this commit; filled in once known) · code that produced every number: (filled in after the run)
**Status:** pre-registered
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

- **Dataset snapshot date:** (filled in after the run)
- **Compute / runtime:** (filled in after the run)
- **Anomalies during run:** (filled in after the run)

#### Results

(filled in after the run; no result exists at the pre-registration commit)

#### Interpretation

(filled in after the run)

#### Next action (per the pre-registered decision rule)

(filled in after the run)

#### Open questions / followups

(filled in after the run)

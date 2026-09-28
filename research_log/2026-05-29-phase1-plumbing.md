### 2026-05-29 — Phase 1 plumbing (dummy "is it Monday" feature)

**Phase:** 1
**Commit:** <fill in with `git rev-parse HEAD` of the run>
**Status:** complete

#### Pre-registration (written BEFORE running)

- **Hypothesis:** None — this is a *negative control*. A calendar feature ("is the
  decision day a Monday?") carries no plausible information about a stock's 5-day
  excess return over its sector. The harness should therefore report NO edge.
- **Feature(s):** `is_monday` ∈ {0,1}. No lookback, no thresholds.
- **Label:** `labels.Labeler`, horizon = 5 trading days, threshold = 2% excess
  return vs the ticker's SPDR sector ETF. Binary: 1 if excess > 2% else 0.
- **Universe:** 50 large-cap S&P 500 tickers (config/universe.py).
- **Era used:** development (2018-01-01 → 2020-12-31, clamped to available data).
  Appropriate because this is plumbing validation, not a result; the validation
  and holdout eras remain untouched.
- **Model:** logistic regression (numpy fallback backend; sklearn if installed).
- **Costs assumed:** 4 bps spread (half per leg) + 1 bp commission/leg + 2 bps
  slippage/leg → 0.10% round trip.
- **Baselines compared against:** random entry with the same trade count
  (500-iteration bootstrap); buy-and-hold sector (sanity check, ~0 by construction).
- **What would be "interesting":** ANY edge — strategy net excess materially above
  random (|z| ≥ 2). Per the plan this would be a RED FLAG, not a success.
- **What would be "not interesting" (and is the desired outcome):** strategy
  indistinguishable from random entry, |z| < 2.
- **Decision rule:** if an edge appears → STOP, the harness has a leakage/logic
  bug; audit feature builder and labeler. If no edge → Phase 1 passes; proceed to
  Phase 2 (PEAD).

#### Run details

- **Dataset snapshot date:** 2026-05-29 (SYNTHETIC snapshot, `data/raw/SYNTH_prices_2026-05-29.csv`).
  ⚠️ Synthetic GBM data, generated offline because the build environment had no
  network/yfinance. Day-of-week has zero effect by construction, so the null is
  the *only* honest outcome here. Re-run on a real yfinance pull before trusting
  any non-null result in later phases.
- **Compute / runtime:** ~4 s, single core. Walk-forward: 252-day train / 63-day
  test, 9 folds.
- **Anomalies during run:** none. Model backend = numpy (sklearn not installed in
  the build env). 26,600 (ticker, date) cells scored; 5,320 signals fired
  (top-20% cross-sectional each day).

#### Results

- **Hit rate (net excess > 0):** 0.4889  (random baseline: 0.4825)
- **Label hit rate (y = 1):** 0.2675  (base rate of the 2% / 5-day event)
- **Signal count:** 5,320
- **Avg excess per signal (net of costs):** −0.0246%  (random: −0.0650% ± 0.0418%)
- **Avg excess per signal (gross):** +0.0754%
- **Max drawdown:** −445% on the *additive* per-trade equity curve. NOTE: this is
  the cumulative sum of 5,320 small per-trade excess returns, not a compounded /
  position-sized curve, so the magnitude is a diagnostic, not a portfolio P&L.
- **Baseline comparison:** z vs random = **0.965** (|z| < 2).
- **Plots / artifacts:** `data/processed/phase1_report.json`.

#### Interpretation

- **Was the pre-registered "interesting" criterion met?** No — and that is the
  pass condition. The dummy feature is statistically indistinguishable from random
  entry (z = 0.97). Hit rates match to within ~0.6 points.
- **What does this tell us about the hypothesis?** Nothing about real signal (there
  was no hypothesis); it confirms the negative control behaves as a negative
  control.
- **What does it tell us about the harness?** The end-to-end pipeline (PIT store →
  as-of feature builder → quarantined labeler → walk-forward → cost-aware
  evaluation → baselines) runs and does NOT manufacture an edge from noise. No sign
  of lookahead leakage in this configuration.
- **Confidence in the result:** Medium-high for *plumbing*. The 14 leakage/labeler
  unit tests pass. Caveat: data is synthetic, so this validates mechanics, not
  market behavior.

#### Next action (per the pre-registered decision rule)

- Phase 1 **PASSES**. Before Phase 2: (1) re-run on a REAL yfinance snapshot to
  confirm the null holds on real prices; (2) implement Phase 2 (PEAD) per
  `experiments/phase2_pead.py`, pre-registering a new entry first.

#### Open questions / followups

- Replace the static, survivorship-biased universe with point-in-time S&P 500
  membership before Phase 4 (tracked in config/universe.py).
- Consider reporting a compounded / position-sized equity curve alongside the
  additive one so max-drawdown reads in intuitive units.
- Decide signal threshold policy for real features (cross-sectional top-quantile
  vs absolute probability) — current top-20% rule guarantees a comparable trade
  count even for a degenerate model, which is what makes the Phase 1 null clean.

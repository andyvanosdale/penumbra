### 2026-09-28 — Free-data screen of the v1 mean-reversion rule (pre-build)

**Phase:** 0 (screen before the Sharadar purchase and before any other v1 issue)
**Commit:** pre-registration committed first; the run's hash is filled in under "Run details"
**Status:** pre-registered
**Issue:** andyvanosdale/penumbra#15
**Spec:** `andyvanosdale/penumbra-specs` branch `spec/mean-reversion-v1` at `b1616412` —
`spec/01`, `spec/04`, `spec/05`, `spec/06`, `spec/07`, and the DECISIONS entry
"2026-09-27 · Free-data screen before the build".

#### Pre-registration (written BEFORE running)

- **Hypothesis:** A one-day drop of at least 2.0 trailing daily vols in a liquid,
  volatile US small-cap (and, separately, a top-100 Binance USDT pair) is followed by
  a positive excess return over the next 5 sessions that survives a realistic next-open
  fill and round-trip costs. The screen asks the narrower question the DECISIONS entry
  poses: is the next-open 5-day excess return at zero cost at least 50 bps per trade?
- **Rule (locked, `spec/05`; nothing here is fitted):**
  - `ret_1` = ln(close_D / close_{D−1}) on the as-of-adjusted series (yfinance
    `Adj Close` ratio applied to O/H/L/C).
  - `rvol_20_prev` = annualized sample std of the 20 1-day log returns ending D−1
    (√252 equities, √365 crypto). `shock` = `ret_1` / (`rvol_20_prev` / √annualization).
  - Candidate on D when `shock` ≤ −2.0 and the lane does not hold the name at D's close.
    A candidate whose signal day has high = low is recorded as unfilled.
  - Entry at fixed USD 10,000 notional. Three fills are tested: (a) signal-day close
    (the spec's close-fill diagnostic), (b) next session's open (the spec's primary
    fill), (c) next session's close (a delayed fill, as the issue asks).
  - Exit, evaluated from the first session after the fill session, in this order:
    hard stop (level = entry fill − 1.5 × signal-day (high − low), fixed at entry; fills
    at the open if open ≤ level, else at the level if low < level; stop wins ties),
    target (close_t ≥ mean of the 20 closes ending D, fixed at entry; fills at the next
    open, except in the close-fill variant where it fills at the triggering close),
    time stop (t = 10th session after the fill session → exit at the next open).
  - A session with no bar evaluates no exit and does not advance the time stop. A
    position still open at the end of the data is closed at the last close and flagged.
- **Universe (equities), evaluated per day D:** listed common stock on NYSE, Nasdaq,
  NYSE American (Arca and BATS retained if the directory lists common stock there);
  bar on each of the 250 sessions ending D; median unadjusted dollar volume over
  D−20..D−1 ≥ USD 500,000; `rvol_20` (20 returns ending D) > 40% annualized;
  unadjusted close on D ≥ USD 2.00. `smallcap`: current yfinance market cap < USD 2B
  (the free data has no point-in-time cap; recorded as a known bias). `uncapped`: no
  cap limit (the `discovered` lane's analogue).
  - **Source:** the iShares IWM/IWC holdings host is blocked by the egress proxy
    (403 CONNECT). Per the issue's fallback, the list is built from the Nasdaq Trader
    symbol directory (`nasdaqlisted.txt`, `otherlisted.txt`, pulled 2026-09-28),
    filtered to common stock (names matching common stock / ordinary shares / class
    share; ETFs, test issues, preferreds, warrants, rights, units, notes, ADRs/ADSs and
    funds excluded), and to names yfinance returns prices for. This is the current
    listing, so the sample is survivorship-biased in the strategy's favour, which is
    what makes a null conclusive. The size of the list at each filtering step is
    recorded under "Run details".
- **Universe (crypto), evaluated per UTC day D:** Binance spot USDT pairs from the
  public bucket (`data.binance.vision`); 1d kline on each of the 30 days ending D; base
  asset not a stablecoin / fiat-pegged token, not a leveraged token (UP/DOWN/BULL/BEAR),
  not a wrapped or staked derivative (WBTC, BETH, and the like); top 100 by trailing
  30-day quote volume as of D; 30-day annualized vol > 20%. Entry at the open of the
  01:00 UTC 1h kline on D+1 (from the bucket's 1h klines) if the 1h download completes;
  otherwise at the 1d open of D+1, which is the signal close, and the entry says so.
- **Label / decision quantity:** (1) the 5-day forward return from the entry fill
  (same price type 5 sessions after the fill session: open→open for the next-open fill,
  close→close for the close fills) minus the equal-weight mean of the same quantity
  over every name eligible on D (the "same-day universe mean"); (2) the realized net
  exit return of the rule, entry fill to exit fill. (1) is the pre-registered decision
  quantity per the DECISIONS entry; (2) is reported alongside.
- **Era used:** equities 2015-01-01 → 2023-12-31 (dev + validation of `spec/03`; the
  2024-onward holdout is excluded from every table and is not downloaded). Crypto
  2018-01-01 → 2022-12-31 (the dev era; 2023-onward validation and 2025-onward holdout
  are not downloaded). This is a screen, not a validation run; the spec says dev results
  are a screen for whether to spend the build.
- **Model:** none. Fixed rule.
- **Costs assumed (round trip, subtracted from each trade's gross return):**
  0 bps, 50 bps, 100 bps, and the spec's own model (`spec/06`): per side, half the
  Abdi–Ranaldo (2017) close-high-low spread over the 20 sessions ending D−1 with
  negative two-day estimates zeroed, floored at max(0.25%, USD 0.01 / unadjusted close);
  entry leg at 2× the spread estimate with participation against 10% of the median
  dollar volume, exit leg at 1× against the full median; slippage 0.5 × σ_d ×
  √participation with σ_d = `rvol_20` / √252 and participation = USD 10,000 / median
  dollar volume; no fees. Crypto: 10 bps taker per side plus the spread floor of 5 bps
  per side (top 20 by 30-day quote volume) or 15 bps otherwise, and the same
  Abdi–Ranaldo/slippage form above the floor with σ_d = `rvol_20` / √365.
- **Statistic:** for each metric, the day-clustered z = mean over entry days of the
  daily difference (mean over that day's candidates of the candidate quantity minus the
  same-day universe mean) divided by the standard error of that daily mean over entry
  days (std / √days). For the realized net return, the universe comparator is the
  equal-weight return of the same-day eligible universe from the same entry fill type
  to the exit session (open for open exits, close for stop exits), with no cost charged
  to the universe.
- **Baselines compared against:** the same-day equal-weight universe (above). No
  random-draw benchmark in the screen; the universe mean is the screen's analogue.
- **What would be "interesting" (per lane):** next-open fill, zero cost: mean 5-day
  candidate return minus same-day universe mean ≥ 50 bps per trade, with the day-
  clustered z ≥ 2.0 as a sanity floor on the sign (the DECISIONS threshold is the 50
  bps; the z is reported so a 50-bps mean driven by three days is visible as such).
- **What would be "not interesting":** the next-open zero-cost 5-day excess under
  50 bps per trade.
- **Decision rules (from the DECISIONS entry, applied literally):**
  1. Equities: next-open 5-day excess at zero cost under 50 bps on the `smallcap`
     universe → the equity build stops (issue 15 outcome recorded, DECISIONS entry
     proposed in `penumbra-specs`). The `uncapped` universe is reported and does not
     rescue the decision.
  2. Equities: excess present (≥ 50 bps) at the signal-close fill and absent (< 50 bps)
     at the next-open fill → recorded as bid-ask bounce, not a tradeable effect; same
     stop as 1.
  3. Crypto: the same threshold on the Binance klines at the 01:00 UTC (or next-day)
     open fill, zero cost: under 50 bps → the crypto lane is removed by spec change
     before its ingest, universe builder or cost model are built.
  4. Realized net returns under the spec cost model are reported with each decision so
     the gap between the 5-day excess and what the rule actually captures is visible;
     they do not decide here.
- **What this screen cannot show:** point-in-time caps, delistings (the current
  listing has none), intraday fills, or the spec's 1,000-draw benchmark. All four biases
  favour the strategy. A null here is therefore conclusive; a positive here is only a
  reason to build.

#### Run details

- **Dataset snapshot date:** (filled after the run)
- **Compute / runtime:** (filled after the run)
- **Anomalies during run:** (filled after the run)

#### Results

(filled after the run)

#### Interpretation

(filled after the run)

#### Next action (per the pre-registered decision rule)

(filled after the run)

#### Open questions / followups

(filled after the run)

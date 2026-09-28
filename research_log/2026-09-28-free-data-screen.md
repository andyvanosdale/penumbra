### 2026-09-28 — Free-data screen of the v1 mean-reversion rule (pre-build)

**Phase:** 0 (screen before the Sharadar purchase and before any other v1 issue)
**Commit:** 9a7721e (pre-registration) · 256b98a (code that produced every number below)
**Status:** complete
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

- **Dataset snapshot date:** 2026-09-28 (all pulls). Equities: yfinance daily bars,
  `auto_adjust=False`, 2015-01-01 → 2023-12-31, for the 4,887-symbol common-stock list;
  4,166 symbols returned bars in that window, 721 did not (post-2023 listings and
  renames; list in `data/raw/yf/tickers_without_data.json`, not committed). Market caps:
  4,761 from the owner's Nasdaq screener export (`api.nasdaq.com` screener, supplied
  2026-09-28), 126 from yfinance `fast_info`; 2,465 names under USD 2B. Crypto: Binance
  public bucket, 1d klines for every USDT pair with data in 2018-01-01 → 2022-12-31
  (418 pairs; 354 after the stablecoin / leveraged / wrapped exclusions), plus 1h klines
  for the 316 pairs that ever enter the top-100 universe, from which the 01:00 UTC open
  on D+1 is taken (coverage 99.98% of universe cells). No holdout-era bar was
  downloaded for either market.
- **Universe list steps:** Nasdaq Trader `nasdaqlisted.txt` 5,636 rows + `otherlisted.txt`
  7,652 rows → 7,131 after exchange (NYSE, Nasdaq, NYSE American, Arca, BATS), ETF and
  test-issue filters → 5,547 matching common stock / ordinary shares / class shares →
  4,887 after excluding warrants, rights, units, preferreds, ADRs/ADSs, notes, funds,
  SPACs and partnerships. All 4,887 are NYSE (1,002), Nasdaq (1,501 on the Global
  Select tier, the rest on the other tiers) and NYSE American (139); no common stock
  is listed on Arca or BATS in the directory.
- **Daily universe sizes:** `smallcap` median 332 names per day (p90 809; 2,040 names
  ever eligible); `uncapped` median 642 (p90 1,536; 3,685 ever). Both are below the
  spec's 500–1,500 / 600–2,000 targets, because (a) the current listing drops every
  name delisted since 2015, and (b) the 250-session full-history rule empties 2015
  entirely (5 candidates in 2015). Crypto: median 100 per day, p10 12 (early 2018 had
  few USDT pairs), 316 ever.
- **Compute / runtime:** yfinance pull 28 min (82 batches of 60, 4 threads); Binance
  pull 70 min (44k monthly 1d files, 19k 1h files, 8 threads); the screen itself 80 s
  for both markets on 4 cores / 15 GB. Script `experiments/screen_free_data.py`.
- **Anomalies during run:**
  - `www.ishares.com` is blocked by the egress proxy (403 CONNECT), so the universe is
    the Nasdaq Trader common-stock listing rather than the Russell 2000 + Microcap
    lists. The `smallcap` cut (current cap < USD 2B) is the closest free proxy.
  - `api.polygon.io`, `cloud.iexapis.com` and `api.iex.cloud` are blocked: the spread
    sample is skipped. No signup was attempted. `api.binance.com` is blocked but not
    needed (symbol list from the S3 listing endpoint). `fc.yahoo.com` is blocked, so
    yfinance runs without a crumb; the chart endpoint works without one.
  - yfinance's `Close` is split-adjusted, not raw (AAPL shows USD 125 on 2020-08-27,
    before its 4:1 split). The USD 2.00 price floor and the one-tick spread floor
    therefore run on split-adjusted prices: names that later reverse-split pass the
    floor at prices that were under USD 2 at the time (e.g. MLGO, IMUX), and the tick
    floor is understated for them. `Volume` is split-adjusted too, so dollar volume is
    consistent. Sharadar's unadjusted series removes this.
  - The first prices run crashed on the ticker `NA` (parsed as a missing value by
    pandas); fixed with `keep_default_na=False` and the last batch re-pulled. Six
    tickers returned no data on retry.
  - 15 bars with a zero low and 5 with a zero open (placeholder rows on no-trade days)
    are treated as missing bars.
  - The spec's Abdi–Ranaldo spread estimate is large on these names: median 2.35% on
    equity universe names (60% median vol), mean 3.4% round trip on candidates after the
    2× entry multiplier; the 0.25% floor binds on 0.02% of candidates. On crypto it is
    larger still (mean 6.0% round trip, floors rarely binding). The estimator is
    implemented as written (two-day products of close-to-midrange log distances,
    negatives zeroed, 20-session mean ending D−1, square root, half per side). The
    issue's literal crypto cost (10 bps taker + 5/15 bps tier spread per side, 30–50 bps
    round trip) is reported separately as `tier`.
  - Hard stops can sit below zero when the signal day's range exceeds two-thirds of the
    fill price (LUNAUSDT 2022-05-09: fill 38.61, range 55). Those positions ride to the
    time stop or, for LUNA, to the last bar before delisting (−99.999%). This is the rule
    as written; it is why the crypto 1st percentile is −43%.
  - Trades still open at the data end are closed at the last close and flagged
    `truncated`: 23 of 27,107 `smallcap` next-open trades, 5 of 3,532 crypto.

#### Results

All figures are basis points per trade unless stated. "5d excess" is the 5-session
forward return from the fill minus the same-day universe mean of the same quantity,
net of the column's round-trip cost. "net" is the realized rule return net of cost. z
is day-clustered (mean over entry days of the daily strategy-minus-universe difference
over its standard error) at zero cost. `spec` is the `spec/06` cost model; `tier` is
taker + tier spread. Full tables per year, fill, universe and cost level are in
`data/processed/screen_free_data_results.csv` and `screen_free_data_tables.md`; trade
files are under `data/raw/` (not committed).

**Equities, `smallcap` (2015-01-02 → 2023-12-29)**

| fill | candidates | trades | 5d excess @0 | @50 | @100 | @spec | net @0 | @50 | @100 | @spec | hit @0 | z 5d | z net | days |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| signal close | 31,940 | 27,549 | +4 | −46 | −96 | −417 | −29 | −79 | −129 | −443 | 0.515 | −1.01 | −1.52 | 1,970 |
| next open | 31,927 | 27,107 | **−11** | −61 | −111 | −432 | −65 | −115 | −165 | −478 | 0.496 | −2.49 | −2.41 | 1,962 |
| next close | 31,927 | 26,855 | +3 | −47 | −97 | −418 | −50 | −100 | −150 | −464 | 0.503 | −0.42 | −1.02 | 1,964 |

**Equities, `uncapped`**

| fill | candidates | trades | 5d excess @0 | @50 | @100 | @spec | net @0 | @50 | @100 | @spec | hit @0 | z 5d | z net | days |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| signal close | 59,230 | 51,249 | +9 | −41 | −91 | −369 | −10 | −60 | −110 | −380 | 0.527 | −0.13 | −1.03 | 1,999 |
| next open | 59,213 | 50,570 | **+6** | −44 | −94 | −372 | −39 | −89 | −139 | −408 | 0.510 | −1.56 | −1.99 | 1,996 |
| next close | 59,213 | 50,283 | +10 | −40 | −90 | −368 | −38 | −88 | −138 | −408 | 0.513 | −0.46 | −1.20 | 1,997 |

**Crypto, top-100 USDT pairs (2018-01-01 → 2022-12-31; next open = 01:00 UTC on D+1)**

| fill | candidates | trades | 5d excess @0 | @50 | @100 | @tier | @spec | net @0 | @50 | @100 | @tier | @spec | hit @0 | z 5d | z net | days |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| signal close | 4,351 | 3,595 | −44 | −94 | −144 | −88 | −646 | +11 | −39 | −89 | −33 | −600 | 0.531 | −3.67 | −2.41 | 369 |
| next open | 4,351 | 3,532 | **−42** | −92 | −142 | −86 | −643 | +142 | +92 | +42 | +97 | −471 | 0.526 | −3.73 | −2.24 | 368 |
| next close | 4,351 | 3,527 | −52 | −102 | −152 | −97 | −654 | −2 | −52 | −102 | −47 | −614 | 0.525 | −4.40 | −4.11 | 368 |

**Day-clustered means and standard errors, next-open fill, zero cost (bps)**

| market / universe | day-mean 5d excess | SE | day-mean net − universe | SE |
|---|---|---|---|---|
| equity `smallcap` | −30.0 | 12.1 | −34.7 | 14.4 |
| equity `uncapped` | −14.7 | 9.4 | −22.3 | 11.2 |
| crypto top-100 | −227.7 | 61.1 | −164.8 | 73.6 |

The trade-weighted means in the headline tables (−11, +6, −42) sit above the
day-weighted means because high-candidate days (March 2020, May 2022) have the better
outcomes; on either weighting no market is within one standard error of +50 bps.

**Per year, next-open fill, zero cost (5d excess / net per trade, bps; hit; days)**

| year | `smallcap` | `uncapped` | crypto |
|---|---|---|---|
| 2015 | −404 / −1,608; 0.00; 2 | −260 / −1,194; 0.20; 2 | — |
| 2016 | +19 / +110; 0.554; 236 | +9 / +160; 0.584; 250 | — |
| 2017 | −53 / −28; 0.486; 246 | −43 / +4; 0.509; 248 | — |
| 2018 | −5 / −1; 0.511; 243 | +12 / +44; 0.530; 249 | +12 / −312; 0.483; 34 |
| 2019 | −76 / −109; 0.489; 247 | −32 / −12; 0.528; 250 | −79 / +8; 0.503; 60 |
| 2020 | −28 / −177; 0.465; 244 | +14 / −220; 0.446; 249 | −24 / +558; 0.633; 99 |
| 2021 | +24 / +27; 0.535; 249 | +15 / +40; 0.552; 251 | −65 / +627; 0.650; 66 |
| 2022 | −10 / −97; 0.481; 249 | +9 / −42; 0.502; 250 | −29 / −480; 0.350; 109 |
| 2023 | +2 / −82; 0.484; 246 | +8 / −1; 0.521; 247 | — |

No year clears +50 bps on the 5d excess in any market. The best equity year (2016
`smallcap`, +19 bps, z +1.03) is a third of the threshold. The crypto rule's raw net
return is positive in 2020–2021 (+558, +627 bps) and negative in 2022 (−480): it is
the universe's drift, and the universe-relative figure is negative every year but 2018.

**Exit mix (next-open fill):** equities stop / target / time = 0.22 / 0.36 / 0.41
(`smallcap`), 0.24 / 0.36 / 0.40 (`uncapped`); crypto 0.13 / 0.36 / 0.50. Mean
sessions held 6.9 (equities), 7.5 (crypto). Mean `shock` of candidates −3.7 (equities),
−3.2 (crypto). Candidates skipped because the name was already held: 4,810 of 31,927
(`smallcap`), 8,632 of 59,213 (`uncapped`), 816 of 4,351 (crypto).

**Controls and sanity checks (next-open fill, zero cost):**

| check | `smallcap` | `uncapped` | crypto |
|---|---|---|---|
| stale-signal placebo (shock lagged 20 sessions), z net / z 5d | −0.31 / +0.90 | −0.13 / +1.04 | +0.57 / −0.17 |
| planted +50 bps on every candidate, z net / z 5d | +1.06 / +1.29 | +2.47 / +3.29 | −1.56 / −2.95 |
| z net / z 5d with the top 10 entry days removed | −2.55 / −2.79 | −2.07 / −1.83 | −3.95 / −4.50 |
| share of absolute P&L from the top 10 entry days | 7.3% | 12.6% | 29.7% |
| mean gross vs 1–99% winsorized mean gross | −0.65% / −0.74% | −0.39% / −0.47% | +1.42% / +1.16% |

The placebo is flat everywhere. The planted effect shifts z by +3.5 to +3.8 units in
equities (the shift is what the control measures; the absolute z stays low because the
underlying estimate is negative), so a true +50 bps would have been seen at 3.5–5
standard errors. In crypto the shift is +0.8 units on the 5d excess (SE 61 bps), so the
crypto sample would not have resolved a true +50 bps against zero, but the estimate
sits 4.5 SE below the threshold, which is a decisive null on the threshold itself.

**Fill comparison (the bounce test):** equities, next-open entry is on average 41 bps
above the signal close (overnight rebound), and the rule's net return is lower at next
open than at the close fill by 36 bps (`smallcap`) and 29 bps (`uncapped`); the 5d
excess is under +10 bps at all three fills. Crypto: the 01:00 UTC open is 12 bps below
the signal close on average, and the 5d excess is −42 to −52 bps at every fill.

**Spread sample:** not run; Polygon and IEX hosts are blocked (see anomalies).

**Plots / artifacts:** `data/processed/screen_free_data_results.csv`,
`screen_free_data_tables.md`, `screen_free_data_meta.json` (universe sizes,
diagnostics, extreme trades, unfilled reasons).

#### Interpretation

- **Was the pre-registered "interesting" criterion met?** No, in every market and at
  every fill. Next-open 5d excess at zero cost: −11 bps (`smallcap`), +6 bps
  (`uncapped`), −42 bps (crypto), against +50 bps. Day-clustered z is negative in all
  three (−2.49, −1.56, −3.73).
- **What does this tell us about the hypothesis?** On the survivorship-biased free
  sample, a −2σ one-day drop in a volatile, liquid small-cap is followed by nothing
  that a next-open fill can collect: the 5-session path of candidates matches the
  same-day universe within about 10 bps, and the rule's realized return is negative
  before any cost. There is no bid-ask-bounce signature to record either: the
  signal-close fill is also under +10 bps of 5d excess. Costs are not what kills it;
  the gross is already flat to negative. In crypto the rule's raw return is positive in
  the 2020–2021 bull market and strongly negative in 2022, and it is below the
  universe's own drift in every year but 2018: the −2σ drop names continue to
  underperform the top-100 for the next five days (day-mean −228 bps, SE 61).
- **What does it tell us about the harness?** The engine is the screen script, not the
  harness. Hand-checked trades fill and exit as the rule says; the placebo is flat and
  the planted effect moves z by the expected amount in equities; removing the top 10
  entry days does not change any sign; winsorizing does not change any mean by more
  than 25 bps. Nothing looked too good. The spec's cost model deserves attention
  before any build: the Abdi–Ranaldo estimator on 60%-vol names yields spreads of
  2–5%, so the entry leg alone is charged 2–3% of notional. Whether that is right for
  these names is exactly what the (blocked) quote sample was for.
- **Confidence in the result:** high for the equity null. Every bias in this sample
  (survivorship, current caps, no delistings, no intraday cost) favours the strategy
  and the estimate is 3–5 standard errors under the threshold on 27k–51k trades over
  1,960–2,000 entry days. Medium-high for crypto: 368 entry days and heavy day
  clustering (30% of P&L from 10 days), but the estimate is 4.5 SE below the threshold
  and negative in four of five years. Two free-data caveats do not point toward a
  hidden edge: the split-adjusted price floor admits sub-USD 2 names (more noise, not
  less), and the universe is smaller than the spec's target (fewer names, same sign).

#### Next action (per the pre-registered decision rule)

1. **Equities: the build stops.** Rule 1 fires on `smallcap` (−11 bps < 50 bps); the
   `uncapped` universe does not rescue it (+6 bps). No Sharadar purchase for this rule.
2. **Bid-ask bounce: nothing to record.** Rule 2 needs edge at the close fill; there is
   none (+4 / +9 bps).
3. **Crypto: the lane is removed by spec change.** Rule 3 fires (−42 bps at the 01:00
   UTC open, zero cost, and negative at every cost level). Proposed for
   `penumbra-specs`: a DECISIONS entry recording this screen and removing the `crypto`
   lane before its ingest, universe builder and cost model are built.
4. **Record the outcome in `penumbra-specs` DECISIONS** (issue 15 acceptance): this
   entry, the commit hashes above, and the three decisions. The spec change is a
   separate PR on that repo and is not made from this branch.
5. Issue 15 comment posted with the headline table:
   https://github.com/andyvanosdale/penumbra/issues/15#issuecomment-5861653847

#### Open questions / followups

- The spec's Abdi–Ranaldo spread on daily bars is 2–5% for 60%+ vol names, an order of
  magnitude above quoted spreads one would expect for USD 500k+ ADV names. Before any
  future rule is costed with it, compare it against a real quote sample (the blocked
  Polygon/IEX step) or switch to a quoted-spread floor by liquidity bucket.
- Equity next-open entries average 41 bps above the signal close: the overnight
  rebound exists but is spent by the open. A rule that could trade the close (which
  this one cannot, by the spec's own fill convention) would still only see +4 bps of
  5d excess, so the rebound is not a tradeable effect at daily resolution either.
- The crypto rule's raw net return (+142 bps at zero cost, +97 at tier cost) is the
  top-100 universe's 2020–2021 drift; anyone tempted by it should look at the
  universe-relative row and at 2022.
- If the true Russell 2000 + Microcap lists become available (iShares host allowed or
  the CSVs dropped into `data/raw/universe/`), the `universe` stage can be re-pointed
  at them in a few lines; the expected change is a larger universe with the same sign.
- The 250-session full-history rule empties 2015 on free data; with a longer download
  (2014 onward) 2015 would be populated. Not done, to keep the download inside the
  pre-registered window.

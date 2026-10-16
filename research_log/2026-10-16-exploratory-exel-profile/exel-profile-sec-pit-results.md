# EXEL's profile on 16 years of point-in-time filings: what survives

Run 2026-10-16. Supersedes the three-vintage yfinance run in `exel-profile-screen-results.md`
(same three profiles, same thresholds, now on SEC filing dates from 2010 to 2026).
Exploratory, owner-requested, not pre-registered; nothing here is evidence in the sense of
`spec/03`. Scripts: `sec_pull.py`, `sec_build.py`, `sec_screen.py`, `yf_prices.py`.
Every table: `sec_screen_out.txt`; per-name rows: `results_sec/rows_scored.csv.gz`.

## 1. Data

- **Fundamentals.** SEC EDGAR XBRL company facts for every CIK that maps to a ticker in the
  current Nasdaq Trader common-stock listing: 3,584 companies pulled, 0 failures, 129 MB
  of extracts (73 tags). One row per 10-K: the fiscal year's values and the prior-year
  comparatives *as printed in that filing*, keyed by the filing date. 37,757 10-Ks for
  3,122 companies, fiscal 2009 to 2026. Sector is the SIC code from the submissions file;
  activism is the count of SC 13D filings against the company in the 12 months before the
  10-K, from the same file.
- **Prices.** yfinance daily bars 2009 to 2026 for the mapped tickers.
- **Entry.** The first session strictly after the 10-K's filing date, at that session's
  close. Forward returns 126, 252 and 756 sessions later on adjusted closes. Floors: median
  dollar volume over the prior 20 sessions ≥ USD 2m, price ≥ USD 2.
- **Universe per vintage** (filing year): 261 names in 2010 rising to 1,000 by 2014 and
  1,700–1,850 from 2021. The early years are thin because small filers only began XBRL in
  fiscal 2011 and because only companies still listed today are in the price data.
  21,808 filing-years in all, 2,305 tickers. EXEL excluded from every group statistic.
- **Statistic.** Median 12-month return of the group minus the vintage's universe median
  (and, separately, minus the same-SIC-2 median where the sector has ≥ 10 names), plus the
  share of the group above the universe median ("hit").

## 2. The three profiles, pooled over vintages with at least 5 names

| Profile | Vintages | Positive | Mean of median excess | Mean hit | Name-years |
|---|---|---|---|---|---|
| Level, all conditions (EXEL at FY2022) | 16 | 9 | +4.5 pts | 54% | 222 |
| Level, sector-neutral | 16 | 10 | +6.2 pts | 53% | 222 |
| Inflection, 5 of 5 (EXEL at FY2024) | 11 | 8 | +2.6 pts | 60% | 107 |
| Inflection, sector-neutral | 11 | 7 | +2.7 pts | 62% | 107 |
| Inflection, 4 of 5 | 16 | 4 | −6.4 pts | 42% | 1,205 |
| Inflection, 0 of 5 | 15 | 4 | −3.9 pts | 43% | 737 |
| Deterioration, 3 of 4 | 15 | 6 | −1.6 pts | 46% | 858 |
| Deterioration, 4 of 4 | 10 | 2 | −14.2 pts | 34% | 242 |
| Deterioration, 0 of 4 | 16 | 11 | +1.3 pts | 52% | 8,575 |

A sign test on vintages is the right first read, since names inside a vintage are not
independent. 9 of 16 and 8 of 11 are both inside what a coin gives (one-sided p ≈ 0.40
and 0.11). 2 of 10 for the deterioration cohort is p ≈ 0.05.

## 3. What each profile actually did

**Level profile (the pre-move state).** 8 to 22 names a year. Median excess by vintage:
+7, +12, −5, +16, −7, 0, +10, +29, +23, −11, +31, −10, +3, −5, 0, −22 (2010 to 2025). The
positive mean comes from 2013, 2017, 2018 and 2020; the last four years are 0, −5, 0, −22.
The rank composite of the same variables has a positive top-minus-bottom decile spread
in 8 of 16 years (mean +1.9 pts) with decile medians that run the wrong way in six of
them. Over 16 years, as over three, the state that EXEL was in before its move does not
pick winners. It picks cheap, cash-rich, under-earning companies, half of which stay that
way. The 13D split inside this group is too thin to read (0 to 6 names a year).

**Inflection profile (the move once it shows in the filing).** Rare: 0.3% to 1.2% of the
universe a year, 1 to 8 names before 2022 and 13 to 21 since. Median excess by vintage
where n ≥ 5: +5 (2012), −17 (2013), −4 (2015), +2 (2016), +5 (2017), +16 (2019), −26
(2020), +12 (2022), +9 (2023), +18 (2024), +9 (2025). The last four, where the sample is
largest, are all positive with hit rates of 69%, 67%, 77% and 56%; the earlier seven are
a coin flip on single digits of names. Two things temper it:

- The 4-of-5 group is *below* the universe in 12 of 16 years. The relation is not
  monotone; it switches on only when every condition holds, which with 13 to 21 names a
  year is where luck lives. The rank composite is more honest: positive spread in 11 of
  16 years, mean +3.3 pts, with the decile medians clearly monotone in 2013, 2017, 2022
  and 2023 and clearly inverted in 2010 and 2025.
- The four good years overlap the period in which the profile was first noticed
  (the yfinance run covered 2023 to 2026), so they are not out-of-sample for the choice of
  profile. 2022 is the one clean year, at +12 pts on 16 names.

**Deterioration profile (the sell side).** The most reliable signal in the data, and the
most regime-dependent. Four-of-four names: −33 (2015), −26 (2018), −49 (2019), −59
(2021), −32 (2022), −14 (2023), −23 (2024); and +90 (2020) and +23 (2025). Three-of-four
in the large recent vintages: −24, −29, −18, −20 (2021 to 2024) and +8 (2025). The cohort
collapses in most years and rallies violently in the junk rallies (2020 after the COVID
low, 2025–26), which is also what the literature says about low-quality names.
Survivorship bias understates all of it: the names that went to zero are not in the
listing.

**Placebo.** The inflection score the same company had two fiscal years earlier, with
forward returns from today's entry, is flat: 4-of-5 lag group median excess between −7
and +15 pts with no pattern across 14 vintages. The signal, such as it is, is not a stale
company attribute.

**EXEL.** Level-full at its FY2021 through FY2024 10-Ks (filed 2022-02 to 2025-02);
inflection-full at the FY2024 10-K, filed 2025-02-11, entry 2025-02-12 at 32.80, +34%
over the next 12 months and +90% to date. The filing date matters: EXEL files five weeks
after year end, not the 75 days the yfinance run assumed, which is 4 dollars of entry
price.

## 4. What this settles and what it does not

1. **The level profile is retired as a predictor.** Sixteen years, two data sources, with
   and without sector control, with thresholds and with ranks: nothing reliable.
2. **The inflection as a 5-condition conjunction is not established.** Eight of eleven
   vintages positive is p ≈ 0.11 on tiny groups, the 4-of-5 group is negative, and the
   convincing years are the ones the profile was found in. What survives is the
   *direction*: improving margins, falling cost ratios, shrinking share counts and growing
   revenue rank-ordered across the universe have a positive decile spread in 11 of 16
   years. That is a fundamental-momentum factor of ordinary size (a few points a year on
   a decile spread), not a 4× detector.
3. **The deterioration cohort is the one result strong enough to act on now**, as an
   exit rule for any long book, with the explicit caveat that it reverses in junk
   rallies and that the harness's regime split must report it.
4. **Regime is the first-order effect.** Both change-based profiles flip sign in 2020 and
   2025. Any lane built on them needs the regime diagnostic to be a reported split from
   day one, and the long dev era to average over several regimes.

## 5. What to carry into Penumbra

- Screen 3's hypothesis should be the **rank composite of fundamental momentum**
  (opm_chg, opex_rev_chg, −dshares, rev_g, netpayout) with the **deterioration cohort as
  the exit**, not the EXEL conjunction. The decision quantity is the top-decile excess
  over a cap- and sector-matched benchmark per rebalance, and the gate is the sign-test
  across years plus the spec's per-period z on the harness's own data.
- The point-in-time fundamentals pipeline here (pull, build, screen) runs on free data and
  covers 2010 onward with real filing dates. Its two gaps are the ones the Sharadar bundle
  closes: delisted names, and prices for them.
- The 13D count per company-year is now available for free and should be a reported split
  in the fundamental lane; it was too thin to read here.

## 6. Caveats

Current listing only (survivorship; both profiles' bad names are under-counted, the
deterioration cohort's most of all). XBRL phase-in thins 2010–2012. Tag fallbacks
(revenue, operating costs) differ across filers; changes are computed within one filing so
the basis is consistent, but levels (gross margin, EV/sales) are not comparable for banks,
insurers and REITs, which the level profile mostly excludes by its own conditions. No
costs. Thresholds taken from EXEL. yfinance adjusted closes.

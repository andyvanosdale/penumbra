# Does EXEL's profile predict success in other equities? An informal screen on 2,955 US stocks

Run 2026-10-16 in this session. Companion to `modeling-why-exel.md` (the profile's
derivation) and `penumbra-trend-lane-proposal.md`. Scripts and outputs in the same folder:
`model.py`, `model_out2.txt` (every table), `model_rows_scored.csv` (every name-year with its
ratios, scores and forward returns), `exel_profile_screen.png`.

**Short answer.** A fixed, easy-to-build model was built and run. The version of EXEL's
profile that describes its *state before the move* (FY2022: high gross margin, big opex
relative to gross profit, net cash, cheap on sales, growing, profitable) does **not**
predict 12-month returns on other names in any of three formation vintages. The version
that describes the *inflection once it shows in the filings* (FY2024: operating margin
up, opex ratio down, share count down, revenue growing, profitable) **does** in two of
three vintages plus the partial fourth, monotonically, and inverts in one. The mirror
profile for selling (dilution, cash burn, operating losses, margin falling) is the
strongest of the three where the sample is large. None of this is evidence in Penumbra's
sense; it is a screen result that says which hypothesis deserves the pre-registered test.

## 1. What was built

- **Universe.** The current Nasdaq Trader common-stock listing (4,886 symbols after the
  screen-1 filters), yfinance annual statements (FY2022–FY2025, 4,886 pulled, 0 failures)
  and daily prices 2022–2026 (0 failures). Names enter a vintage when they have a
  statement, a price history, a 20-session median dollar volume of at least USD 2m and a
  price of at least USD 2. 2,955 names qualify at least once.
- **Timing.** Each fiscal-year statement is assumed public 75 days after the fiscal year
  end (the 10-K window). Entry is the first session on or after that day; forward returns
  are 126 and 252 sessions later, on adjusted closes. Vintage = calendar year of entry.
  Complete 12-month windows exist for the 2023, 2024 and 2025 vintages (about 2,240,
  2,320 and 2,360 names each); the 2026 vintage has 6–7 months.
- **Benchmark.** The same vintage's universe. The statistic is the median forward return
  of the group minus the universe median, with the share of names beating the universe
  median ("hit"). Medians are used because the mean is dominated by a few ten-baggers.
- **EXEL is excluded** from every group statistic. Its own rows are shown separately as
  a sanity check.
- **Three fixed profiles, no fitting.** Thresholds were written down from EXEL's own
  ratios before any other name's outcome was read (and are therefore hindsight-informed
  with respect to EXEL, not with respect to the universe).

| Profile | Conditions | What it describes |
|---|---|---|
| **Level** (EXEL at FY2022) | gross margin ≥ 60%; operating income and operating cash flow > 0; gross margin − operating margin ≥ 40 pts; net cash ≥ 10% of market cap; EV/sales ≤ 4; revenue growth ≥ 5% where a prior year exists | the coiled spring before anything happened |
| **Inflection** (EXEL at FY2024) | operating margin up ≥ 5 pts; opex/revenue down ≥ 3 pts; shares outstanding down ≥ 2%; revenue growth ≥ 5%; profitable | the "why" once it is in the numbers |
| **Deterioration** (the mirror) | shares up ≥ 10%; FCF < 0; operating income < 0; operating margin down ≥ 2 pts | the sell side |

Each profile is scored as the count of conditions met, and also as a rank composite of
the same variables (deciles), so the result does not hinge on the exact thresholds.

## 2. Results

### 2a. Level profile: no

Median 12-month return of names meeting every condition, versus the universe median:

| Vintage | n | Profile median | Universe median | Hit vs universe |
|---|---|---|---|---|
| 2023 | 19 | −7.7% | +11.9% | 47% |
| 2024 | 12 | +3.3% | +3.2% | 50% |
| 2025 | 19 | −7.0% | +7.4% | 47% |
| 2026 (6-month) | 42 | +20.2% | +8.5% | 60% |

Score is not monotonic. Names meeting four of five or six conditions sit *below* the
universe median in 2023 (−14 pts) and 2025 (−15 pts). The rank composite's top decile
minus bottom decile (median 12-month return) is 0, +9 and −16 points in the three
vintages; restricted to profitable names it is −14, +5 and −29 points.

Condition by condition (mean 12-month return, met minus not met, three vintages):

| Condition | 2023 | 2024 | 2025 |
|---|---|---|---|
| Gross margin ≥ 60% | −9 | +1 | −23 |
| Opex gap ≥ 40 pts | −10 | −5 | −11 |
| Net cash ≥ 10% | −2 | +4 | +2 |
| EV/sales ≤ 4 | +8 | −1 | +4 |
| Revenue growth ≥ 5% | +6 | +7 | +2 |
| Profitable | +5 | −4 | +1 |

The value and growth conditions helped a little; the quality-shaped conditions (high gross
margin, heavy spending relative to gross profit) hurt in every vintage. EXEL's profile
mixes both.

The 2023 full-profile list says why. It contains KNSA (+586% to date), IDCC (+350%),
PRDO (+170%) and a Pandora-style re-rating in P (+378%), and it contains USNA (−75%),
RILY (−83%), VNDA (−37%), YELP (−33%) and Liberty Global (−20%). The state "cheap,
cash-rich, under-earning, high gross margin" holds coiled springs and value traps in
roughly equal numbers, and nothing in the state separates them. What separated them was
what happened next: a catalyst and the subsequent change in the numbers.

### 2b. Inflection profile: yes in two vintages and the partial fourth, no in one

Median 12-month return minus the universe median, by number of inflection conditions met
(the 2023 vintage has only the 130 non-December fiscal-year names, since a change needs
a prior year, and is shown for completeness):

| Score | 2023 (n=130) | 2024 (n=2,017) | 2025 (n=2,013) |
|---|---|---|---|
| 0 | −26 (n=11) | −19 (n=144) | +5 (n=138) |
| 1 | −5 | −2 | +1 |
| 2 | +2 | +1 | +1 |
| 3 | +3 | +3 | −3 |
| 4 | +45 (n=3) | **+18 (n=83, hit 66%)** | −10 (n=116, hit 40%) |
| 5 | — | **+14 (n=10, hit 60%)** | −1 (n=15) |
| 2026 vintage, score 5, 6-month | | **+22 (n=15, hit 80%)** | |

Rank composite, top minus bottom decile (median): +42, +15 and −14 points; profitable
names only: +30, +12 and −12.

In 2024 the relation is monotonic across all six score levels on 2,017 names. In 2025 it
reverses: the names with the *worst* fundamentals (score 0, mean +32%) led, which is the
signature of a junk rally, and the literature's documented failure mode for fundamental
momentum (it also failed in 2009 and 2020–21). The 2026 partial vintage is back in line.

**EXEL under this profile.** Flagged with all five conditions at the FY2024 filing
(entry 2025-03-17 at 37.02; +11% over the next 12 months, +68% to date). Not flagged at
FY2023 (operating margin had fallen 3 points that year; the cut in R&D came the year
after). So the inflection model finds EXEL 2.3× off its low, with two thirds of the
subsequent gain still ahead, and without the value traps.

2024 inflection names: IDCC (+118% 12-month), DOCS (+91%), GLNG (+63%), META (+21%),
SPGI (+18%), HRMY (+8%); and DOCN (−7%), COLL (−24%), MGM (−24%), DCBO (−42%).

### 2c. Deterioration profile (the sell side): strongest where the sample is large

| Score | 2024 (n=2,320) | 2025 (n=2,359) |
|---|---|---|
| 0 | +5 (n=1,231, hit 57%) | 0 (n=1,319) |
| 1 | −4 | +1 |
| 2 | −8 | −2 |
| 3 | **−30 (n=168, hit 32%)** | +3 (n=162) |
| 4 | **−36 (n=39, hit 28%)** | −11 (n=62, hit 45%) |

Names meeting three or four deterioration conditions in 2024 lost 30–36 points against
the universe over the next year. 2025 is again the junk-rally year and the effect is
weak. Survivorship bias works *against* this result: the names that went bankrupt are
not in the listing, so the true underperformance is larger.

## 3. What this says about "modeling why"

1. **The pre-move state does not generalize; the inflection does.** EXEL's FY2022 state
   is shared by a few dozen names a year, half of which go nowhere or down. EXEL's FY2024
   state (margin expanding, spending ratio falling, shares shrinking, revenue growing) is
   shared by 10–80 names a year and, in two of three vintages, those names beat the
   universe by 14–18 points with a 60–66% hit rate. The "why" is detectable, but only
   once it has begun, and the detectable version is a *change*, not a *level*.
2. **The sell side has the most reliable signal in this data**, which matches the
   literature (net issuance, losses and cash burn are among the most robust negative
   predictors) and is understated here.
3. **One year in three inverts everything.** The 2025 vintage (March 2025 to March
   2026) rewarded the worst fundamentals and punished the best. Three vintages inside one
   market regime cannot establish an average effect; that is exactly what the 2010–2020
   dev era and the validation era exist for. A screen can only say which hypothesis
   deserves that test, and this one says: the inflection profile, not the level profile.
4. **EXEL-sized outcomes are not what the model predicts.** The inflection top decile in
   2024 doubled 21% of the time against 15% for the universe. The model's claim, if it
   holds, is a 10–20 point edge on a basket, not the next 4×.

## 4. Caveats (all of them bias the test, several in opposite directions)

- Current listing: delisted names are missing. Takeovers (which favour cheap cash-rich
  names) and bankruptcies (which punish the deterioration cohort) are both absent.
- Three overlapping vintages in a single regime; not independent observations.
- Filing lag assumed at 75 days; a small filer's 10-K can take 90. Non-December fiscal
  years are handled the same way.
- No sector control; the level profile's failure is partly "software and biotech
  lagged" in 2023–2025. A sector-neutral version was not run because no sector field is
  available without a blocked endpoint.
- yfinance statement fields are vendor-normalized, not point-in-time, and the FY2022
  rows have no prior year, so the growth and change conditions are missing for them.
- No costs. At a 12-month hold they are second-order, but not zero.
- Thresholds were chosen from EXEL. The rank-composite deciles are the check that the
  conclusion does not depend on them, and they agree.

## 5. What to do with it

1. **Pre-register the inflection profile as screen 3's hypothesis**, in place of the
   level profile. Decision rules of the kind screens 1 and 2 used: monotone score-return
   relation and a top-score median excess of at least +10 points in each of at least
   three of four non-overlapping formation years, hit rate ≥ 58%, placebo (score lagged
   two years) flat.
2. **Get point-in-time fundamentals with filing dates.** The right free source is the
   SEC's XBRL "company facts" API (every reported value with the date it was filed, back
   to 2009), which this environment's network policy blocks. Allowing `data.sec.gov`
   (and `www.sec.gov` for the index files) turns screen 3 into a real 2010–2020 dev-era
   test at zero cost; the Sharadar bundle remains the clean path and adds delistings.
3. **Build the deterioration cohort into any long lane as an exit**, which the fundamental
   lane proposal already does; this screen is the first data behind it.
4. **Add the inflection variables to the feature spec** (`opm_chg`, `opex_rev_chg`,
   `dshares_12m`, `rev_accel`, `netpayout_yield`), which the fundamental lane proposal
   lists; the level variables stay as reported splits, not rule inputs.

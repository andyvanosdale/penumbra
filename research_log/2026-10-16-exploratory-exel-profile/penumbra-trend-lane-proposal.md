# Detecting sustained moves early, in both directions: what EXEL shows and how Penumbra would test it

Prepared 2026-10-16 from free yfinance daily bars (2019-01-02 to 2026-10-16). Every signal
below is computed as-of its own day with no lookahead, and every fill is the next session's
open, the convention `spec/05` uses. This is an illustration on one hand-picked name and a
hand-picked basket, not a screen: nothing here is evidence in the sense of `spec/03`.

Chart: `exel_trend.png` in the same folder.

## 1. EXEL, the up direction

EXEL closed at 61.86 on 2026-10-16. Its post-2022 low was 14.96 on 2022-10-10, so the
move is +313% over four years, and it has been a *slide*, not a jump: 51–54% up days,
20-day realized vol mostly 20–35%, largest single day in any 12-month window 5–19%.

### 1a. When would a point-in-time rule have flagged it?

| Entry condition (standard in the momentum / trend literature) | First day true after the low | Price | Return to 2026-10-16 |
|---|---|---|---|
| 12-month return turns positive (time-series momentum, Moskowitz–Ooi–Pedersen 2012) | 2022-11-30 | 17.08 | +262% |
| 12-1 month momentum turns positive (Jegadeesh–Titman 1993) | 2022-12-01 | 17.04 | +263% |
| Close above 200-day SMA (Faber 2007, 10-month SMA) | 2023-03-20 | 18.33 | +237% |
| 50-day SMA above 200-day SMA ("golden cross") | 2023-04-10 | 20.11 | +208% |
| Within 5% of its 52-week high (George–Hwang 2004) | 2023-08-10 | 21.15 | +192% |
| Closes above its prior 52-week high | 2023-08-28 | 22.18 | +179% |

Every one of them fired in the first year of a four-year move. "Early" is available from
price alone. The catch is in 1b.

### 1b. The same rules on the same name, 2021–2022

The 12-month-return rule entered EXEL three times in 2021–2022 before the real move and
lost 22%, 15% and 6%. Faber's 200-SMA rule, checked monthly, entered four times in
2021–2022 and lost 20%, 22%, 11% and 15%. The signals that caught the 2023 move are the
same signals that lost money for two years before it. On one name, a trend signal is a
coin toss per firing; the documented edge is a *cross-sectional* one, averaged over
hundreds of names and many months (winners-minus-losers about 1% per month in the
1965–2010 US sample; long-only top decile over the market a fraction of that).

### 1c. Exit rules on EXEL (what "when to start selling" costs on a winner)

All rules enter on the 52-week-high breakout above the 200-SMA on 2023-08-29 at 22.15,
and may re-enter on a later breakout. Buy-and-hold from that day is +179%.

| Exit rule | Trades | Compounded | What happened |
|---|---|---|---|
| Close below 200-SMA, checked daily | 47 | −7% | Whipsaw; 30 of 47 trades held under 5 sessions |
| Close below 200-SMA, checked at month end only | 8 | +10% | Four losing entries in 2021–22, then +62% and +41% |
| 12-1 momentum > 0 and above 200-SMA, month end | 8 | +41% | Same shape, fewer bad entries |
| 12-month return > 0, month end | 6 | +85% | Held 2023-09-01 to today, +174%, through a 22% drawdown |
| 20% below highest close since entry, daily | 2 | +107% | Out 2025-07-30 at 37.14 (the June–July 2025 drop), back in 2026-05-12 at 50.00 |
| 3 × ATR(22) below highest close ("chandelier"), daily | 9 | −20% | Too tight for a 25%-vol name; stopped out of every leg |

Two things carry over to any design:

- A rule evaluated daily against a slow line (a 200-day average) is a whipsaw machine.
  The literature's rules are evaluated on a rebalance calendar (monthly) for a reason.
- There is a straight trade between how fast an exit limits a loss and how much of a
  winner it gives up. The 20% trailing stop gave up about 70 points of EXEL's 179 to buy
  a bounded loss; the slowest rule kept it all and rode a 22% drawdown.

## 2. The down direction

The basket's four worst 12-month performers, where each exit rule would have fired after
the two-year peak, and the further decline each avoided. (These are in-sample worst
cases, chosen after the fact; they show the *speed* of each rule, not its expected value.)

| Name | Peak | Now | 15% trailing stop fired at | 200-SMA (daily) fired at | 12-1 momentum < 0 at | Further decline avoided by the 20% stop |
|---|---|---|---|---|---|---|
| ORCL | 323 (2025-09) | 128 (−60%) | −15% | −40% | −55% | −50% |
| APP | 734 (2025-12) | 267 (−64%) | −16% | −31% | −56% | −51% |
| IREN | 76 (2025-11) | 27 (−64%) | −14% | −52% | −40% | −54% |
| LCID | 35 (2025-02) | 3 (−91%) | −18% | −18% | 0% | −89% |

The ordering is general: a trailing stop from the peak is fastest (exits 15–20% off the
high), moving-average exits are intermediate (30–50% off the high on a steep decline, since
the average lags), and momentum-sign exits are slowest (40–56%). The slow rules cost the
least on winners (section 1c) and the most on losers. That is the whole design space.

A separate question is whether the down direction should be *shorted* rather than just
*exited*. Screen 2 already found that shorting post-drop names in crypto fails on squeezes
and costs, and in equities the loser leg of momentum carries borrow fees and the 2009-style
crash (Daniel–Moskowitz 2016). Recommendation: in v1 of this lane the down signals are
exits for a long-only book, not shorts. Epic #7 already allows this reading
("long-avoidance").

## 3. Why the current spec would not have seen EXEL at all

- **Vol floor.** `spec/01` requires 20-day realized vol above 40%. EXEL was above it on
  8% of sessions in 2023, 16% in 2024, 40% in 2025, 24% in 2026. The universe rule built for
  reversal in volatile names excludes the smooth climbers this question is about. The floor
  has to go (or invert) for this lane.
- **Trigger.** Screens 1 and 2 keyed on a one-day −2σ shock. EXEL had 4–11 such days per
  year throughout, in both directions, and none of them is the signal. The signal is the
  slow, continuous drift: the "frog in the pan" result (Da–Gurun–Warachka 2014) is that
  momentum is strongest when the past return arrived in many small moves rather than a
  few jumps. EXEL's information-discreteness measure sat between −0.04 and −0.10 through
  the run (negative = continuous), which is the continuing kind.
- **Horizon.** The decision quantity was a 5-day realized exit. This lane's decision
  quantity is the 63- and 252-day forward return already stored by the labeler (`spec/04`
  Labels) but never allowed to decide.
- **Costs.** This is the one place the new lane is *easier*. A 50–100 bps round trip on a
  position held 6–12 months is 1–2% a year against a documented long-only premium of
  several percent. For the 5-day rules, the same costs ate the entire gross. The
  uncalibrated Abdi–Ranaldo spread (open item) matters much less here.

## 4. Proposed lane: `trend` (equities, long-only, monthly rebalance)

This is epic #4 (long-horizon lane) narrowed to price-only signals, with epic #7's
`winners` cohort folded in as a reported variant. Everything is a fixed rule with no fitted
parameter, as the decision log requires. Values marked (p) are proposals for the owner to
lock; none has been tuned on data.

**Universe (per rebalance date R).** `spec/01` eligibility (domestic common stock on the
five exchanges, listed on R, 250-session history), price floor USD 2.00, liquidity floor
raised to USD 2m (p) median dollar volume over the 20 sessions ending R−1 (positions are
held months, so the book needs to exit without moving the name). No market-cap ceiling and
no vol floor. One lane, not two.

**Features (added to `spec/04`, all scale-invariant, all as-of R).**

| Feature | Definition |
|---|---|
| `mom_12_1` | close_{R−21} / close_{R−252} − 1 |
| `mom_6_1` | close_{R−21} / close_{R−126} − 1 (reported, not in the rule) |
| `dist_52w_high` | close / max(high over 252 sessions ending R) − 1 |
| `sma200_rel` | close / mean(close over 200 sessions ending R) − 1 |
| `info_disc` | sign(`mom_12_1`) × (share of down days − share of up days) over sessions R−252..R−21 |
| `rvol_250` | annualized sample std of daily log returns over 250 sessions ending R |

**Rule.** On the last session of each month, rank the universe by `mom_12_1`. A name is a
candidate when it is in the top decile (p), `sma200_rel` > 0, and `dist_52w_high` ≥ −10%
(p). Enter every candidate not already held at the next session's open at the fixed order
size. Hold until, at a month-end check, it is no longer in the top quintile (p) **or** its
close is below the 200-SMA; exit at the next open. Independently of the calendar, exit at
the next open on any session whose close is 20% (p) below the highest close since entry
(Han–Zhou–Zhu 2016 show a stop-loss of this kind removes most of momentum's crash risk).
No target: the book never sells on strength.

**Decision quantity.** Realized net exit return per position, as now. The horizon curve
(21/63/252) is reported alongside and the 63-day read is the gate to validation.

**Statistic.** This is where `spec/07` cannot be reused as written. The decision rule asks
for day-clustered z ≥ 3.0 over ≥ 500 trades; it was built for a strategy with tens of
thousands of five-day events. A monthly portfolio strategy has one independent
observation per rebalance: 132 in the 2010–2020 dev era. A long-only momentum sleeve with
the literature's annualized information ratio of roughly 0.5–0.7 against the market gives
an expected z of about 1.7–2.3 over 11 years *when the effect is real*. Three options,
in order of preference:

1. Extend this lane's dev era back to 2000-01-01 (Sharadar SEP starts 1998). The
   decision log rejected pre-2007 data for the *reversion* rule because it inflates
   reversion results; that reasoning does not apply to momentum, and 21 years gives
   z ≈ 2.4–3.3 at the same information ratio. Validation 2021–2023 and holdout 2024+
   stay as they are.
2. State the unit as the rebalance month: z = mean monthly excess over the matched
   benchmark / its standard error over months, Newey–West with 6 lags for overlapping
   holds. Gate to validation at z ≥ 2.0 (epic #4's existing number); validation passes on
   sign and a point estimate inside the dev confidence interval, not on a fresh z ≥ 3.
3. Keep z ≥ 3.0 and accept that only a much larger effect than the literature's can pass.
   Not recommended: it makes a true positive unreachable, which is a different failure
   from a false positive.

**Benchmark.** The `spec/05` construction carries over with the day replaced by the
rebalance date: on each R, draw the same number of names from the eligible universe,
excluding candidates and names the benchmark holds, matched by `rvol_250` quintile, with
the same exits and costs; 1,000 seeded draws. Vol matching matters more here than for the
reversal rule, since momentum winners are not a random vol slice.

**Controls.** The stale-signal placebo becomes the rule on `mom_12_1` lagged 12 months
(|z| < 2.0). The planted-effect positive control adds +2% (p) to every candidate's realized
exit return and must give z ≥ the gate value, which is what tells a null from a power
failure. Both unchanged in spirit from `spec/07`.

**Costs.** `spec/06` as written, applied to both legs, with the stress cases. Turnover
is reported as a share of lane capital per year; the expected figure is well under the
reversal rule's.

**Reported, never deciding.** The `winners` cohort from epic #7 (20-day slide up, high
turnover, 21-day hold); the 15% stop and the 3 × ATR chandelier as exit variants; the rule
without the 52-week-high filter; the rule restricted to `info_disc` < 0; a short `losers`
sleeve on paper, with a flat borrow fee, so the owner can see what a short book would have
added before any short-sale modeling is built.

## 5. What has to change, and in what order

1. **Screen 3 first, on free data, pre-registered**, as screens 1 and 2 were. yfinance
   bars for the current common-stock listing, 2010–2020, monthly rebalance, the rule
   above, the same-day-universe comparator, costs at 0 / 50 / 100 bps round trip, the
   lagged-signal placebo and the planted effect. Two honesty notes for the pre-registration:
   (a) survivorship bias is *not* one-directional for momentum the way it was for reversal,
   because the collapsed names a long book would have held are missing, so a null here is
   less conclusive than screens 1–2's were; (b) the trade-weighted and the month-weighted
   means must both be reported, the lesson from screen 2.
2. **If the screen passes:** a spec change that adds `spec/01` lane `trend` (universe
   above), the six features to `spec/04`, the rule as a new `spec/05` section, the
   restated statistic in `spec/07`, a new row in `spec/03` for the lane's dev era, and a
   decision-log entry for each. Epic #4's gate is rewritten to "screen 3 passes" since the
   v1 horizon curve it names will never be produced; epic #7's winners cohort becomes a
   variant of this lane.
3. **Then the Sharadar purchase.** The 2026-09-28 decision was "no purchase *for the v1
   rule*". Delisted names, point-in-time listing and a dev era before 2015 are exactly
   what this lane needs and free data cannot provide.
4. **Code.** The store, calendars, run record, invariance tests, universe builder,
   feature builder, labeler and cost model carry over. New: the six features
   (`harness/features.py`, trivial), a rebalance-calendar position manager and the
   trailing stop in the exit simulator (`harness/labels.py`), a cross-sectional ranking
   step and the monthly benchmark draw (`harness/strategy.py`, `harness/benchmark.py`,
   both owed anyway), and the month-unit statistic in the evaluator (owed).

## 6. What "earlier than price" would take

A price-only system detects a trend after it starts, by construction. EXEL's 2023–2026
run tracked cabozantinib revenue growth, buybacks, the 2025 neuroendocrine-tumor label
and the zanzalintinib pipeline. The literature's earlier signals are fundamental momentum:
post-earnings-announcement drift, analyst revisions, and revenue or margin acceleration.
Sharadar SF1 carries fundamentals with point-in-time `datekey`, so a `fund_mom` feature is
a v2 of this lane, not a blocker for v1, and it belongs in the lane only after the
price-only version has a result to improve on.

## References

Jegadeesh and Titman (1993) J. Finance; Moskowitz, Ooi and Pedersen (2012) JFE; George and
Hwang (2004) J. Finance; Faber (2007) J. Wealth Management; Da, Gurun and Warachka (2014)
RFS; Daniel and Moskowitz (2016) JFE; Barroso and Santa-Clara (2015) JFE; Han, Zhou and Zhu
(2016) JFE; Novy-Marx (2012) JFE; Frazzini, Israel and Moskowitz (2014) working paper on
trading costs; Medhat and Schmeling (2022) RFS, already cited in the decision log.

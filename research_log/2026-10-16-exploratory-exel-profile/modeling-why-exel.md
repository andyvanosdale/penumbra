# Modeling *why* EXEL worked, so Penumbra can find the next one

Companion to `penumbra-trend-lane-proposal.md` (same folder). That document is about
catching a move once it is underway from price alone. This one is about the question you
actually asked: what was true about EXEL *before* the move, in terms a harness can measure
on every other name, and how Penumbra would test whether that state predicts the same
outcome elsewhere.

Sources: EXEL's reported annual statements FY2022–FY2025 and quarterly statements through
Q2 2026 (yfinance's copy of the 10-K/10-Q figures; not point-in-time, which matters for the
harness and not for a case study), daily prices to 2026-10-16. SEC EDGAR's own API is
blocked by this environment's network policy, so filing dates, 13D filings and insider
Form 4s were not pulled; those statements below are from public record, not from data in
this session, and are marked (public record).

## 1. The measurable why: it was earnings, not the multiple

Decompose the log price change into earnings growth and multiple change, and earnings
growth into revenue, margin and share count. Price at fiscal year end; EPS = net income /
diluted shares; 2026 uses the H1-2026 run rate.

| | FY2022 | FY2023 | FY2024 | FY2025 | H1-2026 run rate |
|---|---|---|---|---|---|
| Price | 16.04 | 23.99 | 33.30 | 43.83 | 61.86 |
| Revenue, USD m | 1,611 | 1,830 | 2,169 | 2,320 | 2,479 |
| Revenue growth | | +14% | +18% | +7% | +7% |
| Gross margin | 96% | 96% | 96% | 96% | |
| R&D / revenue | 55% | 57% | 42% | 36% | 33% |
| Operating margin | 13% | 9% | 32% | 38% | 40% |
| Net income, USD m | 182 | 208 | 521 | 783 | 845 |
| Diluted shares, m | 325 | 321 | 296 | 282 | 260 |
| EPS | 0.56 | 0.65 | 1.76 | 2.78 | 3.25 |
| P/E | 28.5 | 35.0 | 18.0 | 14.7 | 18.1 |
| Buybacks, USD m | 0 | 550 | 652 | 948 | 1,507 |
| Net cash / market cap | 36% | 21% | 17% | 13% | |
| EV / sales | 2.1 | 3.1 | 3.6 | 4.3 | |
| R&D / market cap | 17% | 14% | 10% | 7% | 5% |

FY2022 end to 2026-10-16: price +286% (log +1.35).

| Component | Log contribution | Share of the move |
|---|---|---|
| EPS growth (0.56 to 3.25) | +1.76 | 130% |
| of which revenue growth (+54%) | +0.43 | 32% |
| of which net margin expansion (11% to 34%) | +1.10 | 82% |
| of which share count shrink (325m to 260m) | +0.22 | 17% |
| P/E change (28.5 to 18.1) | −0.41 | −30% |

The multiple *fell*. The whole move, and then some, is earnings; and the biggest piece of
earnings is margin, not revenue. Revenue grew a respectable 54% over the period. Operating
margin tripled because R&D was cut from 57% of revenue to 33% while revenue kept growing,
and the share count fell by a fifth because a company with net cash equal to a third of
its market value started buying back 7–10% of itself every year.

So the honest statement of why is: **a 96%-gross-margin business whose earnings were
hidden under discretionary R&D and an idle cash pile, which then stopped hiding them.**

## 2. The pre-move state, as a harness would see it

What was observable at the FY2022 10-K (filed early 2023, (public record)), before any of
the above happened, and what the literature says about each:

| State variable at FY2022 | EXEL | Documented effect |
|---|---|---|
| Gross margin | 96% | Gross profitability predicts returns (Novy-Marx 2013) |
| R&D / market value | 17% | High R&D-to-market firms earn excess returns; expensed R&D depresses reported earnings (Lev–Sougiannis 1996; Chan–Lakonishok–Sougiannis 2001) |
| Net cash / market cap | 36% | Part of value; also the fuel for the next row |
| Buybacks | none yet | Repurchase announcements show multi-year drift, strongest in value names (Ikenberry–Lakonishok–Vermaelen 1995); net payout yield predicts returns (Boudoukh et al. 2007); net share issuance is one of the most robust cross-sectional signals in either direction (Pontiff–Woodgate 2008) |
| EV / sales | 2.1 | Cheap on sales for the margin structure; value |
| Operating margin vs gross margin | 13% vs 96% | "Latent operating leverage": no single paper, but it is what the R&D-to-market and gross-profitability results are capturing together |
| Revenue growth | +14% and accelerating | Fundamental momentum (Novy-Marx 2015): earnings and revenue surprises predict returns, and explain most of price momentum |
| Catalyst | activist 13D, Q1 2023 (public record) | Hedge-fund activism: ~7% abnormal return at filing, no reversal, and improved operating performance over the following years (Brav–Jiang–Partnoy–Thomas 2008) |

Every row is a feature a point-in-time store can carry, and every row has a published
cross-sectional premium behind it. That is the sense in which history repeats: not that
the next EXEL will be a biotech with a cancer drug, but that firms in this *state* have,
on average and over decades, outperformed, for reasons the papers above argue are
structural (expensing rules, investor under-reaction to slow-moving fundamentals,
governance that does not return cash until forced).

## 3. A small check on peers (illustration, not evidence)

22 commercial-stage biotechs, FY2022 statements, valued at the 2023-03-01 close (after the
10-Ks were filed), returns to 2026-10-16. A profile written down *after* seeing EXEL's
numbers (profitable, gross margin > 80%, R&D > 30% of revenue, net cash > 15% of market
cap, EV/sales < 5):

| | Matched the profile | Did not |
|---|---|---|
| Names | EXEL, INCY, CORT | 19 others |
| Return to date | +255%, +44%, +447% | mean +63%, median +34% |

Read this correctly. The profile was built from the answer, the set is hand-picked and
survivorship-biased, and three names prove nothing. What it shows is the *shape* of the
test the harness has to run: not "did winners have the profile" (they did, by
construction) but "did names with the profile win", measured on everyone who had it, with
a benchmark, before the outcome is known. The two questions have different answers in
general and only the second one is a strategy.

Also note the big winners that did *not* match: INSM (+376%) and LGND (+299%) are launch
and royalty stories, HALO (+154%) a royalty-growth story. There is more than one archetype,
which is an argument for a small number of fixed, named profiles rather than one.

## 4. How Penumbra models "why" without fooling itself

The decision log already contains the constraints that matter here: no fitted parameters
in v1, no LLM judgment on historical rows ("contaminated by hindsight"), dev results are a
screen and never evidence, every dev configuration is counted. "Model why" has to live
inside them, and it can:

1. **"Why" is a state vector, not a story.** The lane's signal is a fixed list of
   point-in-time fundamental features (section 5) and a fixed rule over them. The story
   ("activist forced buybacks") is how the owner chooses which features to include; it is
   never an input to the backtest.
2. **Winner autopsies are hypothesis generation and count as dev runs.** A study that takes
   the top 2% of 3-year returns in the dev era and tabulates their state vector at t−0 is
   legitimate and useful, and it is the thing most likely to produce a false "why". It is
   logged, its configuration hash is counted, and nothing it finds is evidence. The profile
   it suggests is then written down, pre-registered, and run forward.
3. **Both conditional directions are reported.** P(profile | winner) from the autopsy,
   P(winner | profile) from the lane. The decision rule reads only the second.
4. **"History repeats" is a testable claim: era stability.** The profile's excess return
   must have the same sign in dev and validation, and the regime split and era halves in
   `spec/07` already exist to show whether it survives 2015–2020 as well as 2010–2014.
5. **The catalyst is not predicted; the coiled spring is.** No feature set predicts that
   an activist will file a 13D on a particular name. What the lane can find is the state in
   which a catalyst, if one comes, unlocks a large re-rating: hidden earnings power plus
   the cash to act. Catalysts that *have* happened (a 13D, a buyback 8-K, an earnings
   surprise) are features with their own documented drift, and belong in the vector.
6. **Where an LLM can go.** Not into the backtest. The LLM-classified news filter (epic #3)
   is the right home for a prospective, forward-only classifier of live filings (is this
   8-K a buyback, a label expansion, a guidance cut), run on documents as they arrive so
   that no hindsight is possible. Its output becomes a feature only after the lane without
   it has a result.

## 5. Proposed lane: `fundamental` (equities, long-only, quarterly rebalance)

Everything marked (p) is a proposal for the owner to lock before any data is read.

**Data.** Sharadar SF1 (fundamentals; `datekey` is the filing date, which makes every row
point-in-time), SF2 (insider Form 4, by filing date), DAILY (point-in-time market cap, EV,
P/E, P/S, P/B), EVENTS (8-K item codes, already in `spec/02`), ACTIONS. All are in the
Sharadar bundle the decision log already priced. 13D filings are not in Sharadar; the
EDGAR daily index is free and gives subject company and filing date. Analyst estimates are
not available at this budget; earnings surprise against the firm's own seasonal history
(SUE) stands in.

**Universe.** `spec/01` eligibility, price floor, liquidity floor USD 2m (p); the name has
an SF1 row with `datekey` in the trailing 120 days (a filer), and trailing-12-month revenue
above USD 50m (p) so that margins mean something. No vol floor, no cap ceiling.

**Features (as-of D, from the latest SF1 row with `datekey` ≤ D; all ratios, so
scale-invariant).**

| Feature | Definition | Why |
|---|---|---|
| `gross_margin` | gross profit / revenue, TTM | profitability |
| `rd_mv` | R&D TTM / market cap | R&D-to-market |
| `netcash_mv` | (cash + investments − debt) / market cap | balance sheet, value |
| `ev_sales` | EV / revenue TTM | value |
| `fcf_yield` | FCF TTM / market cap | value |
| `netpayout_yield` | (buybacks − issuance + dividends) TTM / market cap | net payout |
| `dshares_12m` | diluted shares now / 12 months ago − 1 | net issuance (sign matters both ways) |
| `opm_gap` | gross margin − operating margin | latent operating leverage |
| `rev_accel` | revenue growth TTM − revenue growth prior TTM | fundamental momentum |
| `sue` | (EPS − EPS four quarters ago) / std of that difference over 8 quarters | earnings surprise |
| `margin_chg` | operating margin TTM − prior TTM | fundamental momentum |
| `insider_net_3m` | net open-market insider buys, 3 months, / market cap | insiders |
| `act_13d_12m` | flag: a 13D (not 13G) on the name in the last 12 months | activism |
| `ev_8k_bb` | flag: an 8-K in the last 63 days whose item code set includes a repurchase announcement | repurchase drift |

**Rule.** On the first session after each calendar quarter end (p), rank the universe on
a fixed equal-weight composite of ranks (p): `gross_margin`, `rd_mv`, `netcash_mv`,
−`ev_sales`, `netpayout_yield`, −`dshares_12m`, `rev_accel`, `sue`. Candidates are the top
decile (p) that are profitable on an operating basis TTM. Enter at the next open at the
fixed order size; hold 12 months (p) with the trend lane's 20% trailing stop from the
highest close; exit early at a quarterly check if the name falls below the median composite
rank. Flags (`act_13d_12m`, `ev_8k_bb`, `insider_net_3m`) are not in the composite in v1;
they are reported as splits, the way `news`/`noise` is today, so their marginal value is
visible before anything is built on them.

**Deterioration mirror (the other direction).** The same composite's bottom decile, plus
`dshares_12m` > +10% (dilution), `margin_chg` < 0 and `sue` < 0, is reported as a
`deteriorating` cohort with its forward returns, never traded short in v1. For the long
book it is an exit: a held name that enters the cohort at a quarterly check is sold.
(Net issuance, Pontiff–Woodgate 2008; accruals, Sloan 1996; asset growth, Cooper–Gulen–Schill
2008; low F-score, Piotroski 2000.)

**Decision quantity, statistic, benchmark, controls.** As in the trend proposal: realized
net exit return; the unit is the rebalance quarter (44 in a 2010–2020 dev era, 84 if the
era is extended to 2000, which SF1 supports); z over rebalance periods with Newey–West;
gate to validation at z ≥ 2.0 (p); benchmark draws matched by market-cap quintile and
sector (p) rather than vol; placebo = the composite lagged four quarters; positive control
= +2% (p) planted on every candidate.

**Costs.** `spec/06` as written. At quarterly rebalance and a 12-month hold, turnover is a
fraction of the reversal rule's.

**What it cannot do.** It will not find EXEL at 15 in October 2022 and say "this one".
It will say that names in EXEL's state earned, on average, X% a year over the benchmark
over twenty years, with a confidence interval, or that they did not. That is what "model
why to find others" means once hindsight is removed.

## 6. Order of work

1. Decide between the two lanes, or run both: `trend` (price only; can be screened on free
   data this week) and `fundamental` (needs the Sharadar bundle; no free point-in-time
   fundamentals exist, and EDGAR is blocked from this environment). They are complementary
   in the literature's sense (value and momentum are negatively correlated, Asness–Moskowitz–
   Pedersen 2013), which is what the portfolio epic needs.
2. Rewrite epic #4 as these two lanes with a screen-based gate, replacing the v1 horizon
   curve gate that will never be produced.
3. Spec changes: `spec/02` adds SF1/SF2 and the 13D index to Sources; `spec/04` adds the
   features; `spec/05` a section per lane; `spec/07` the per-period statistic; `spec/03` the
   lane's dev era.
4. Code: SF1/SF2 loaders with `datekey` as `available_at`; the fundamental feature block;
   the rebalance-calendar position manager; the composite rank; evaluator unit change. The
   store, calendars, run record, invariance tests and cost model carry over unchanged.

## References

Novy-Marx (2013) JFE, gross profitability; Novy-Marx (2015) working paper, fundamental
momentum; Lev and Sougiannis (1996) JAE; Chan, Lakonishok and Sougiannis (2001) J. Finance,
R&D and market value; Ikenberry, Lakonishok and Vermaelen (1995) JFE; Boudoukh, Michaely,
Richardson and Roberts (2007) J. Finance, net payout yield; Pontiff and Woodgate (2008)
J. Finance, share issuance; Brav, Jiang, Partnoy and Thomas (2008) J. Finance, hedge fund
activism; Sloan (1996) TAR, accruals; Cooper, Gulen and Schill (2008) J. Finance, asset
growth; Piotroski (2000) JAR; Asness, Moskowitz and Pedersen (2013) J. Finance, value and
momentum everywhere; Asness, Frazzini and Pedersen (2019) RAS, quality minus junk.

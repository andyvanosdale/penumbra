### 2026-10-16 — Exploratory: does EXEL's fundamental profile predict success in other equities?

**Phase:** 0 (exploratory, owner-requested; **not pre-registered, not evidence**)
**Commit:** the commit that adds this entry on branch `claude/clever-feynman-dcnfu8`
**Status:** complete
**Code:** `experiments/exploratory/exel_profile/` · **Results and write-ups:** `2026-10-16-exploratory-exel-profile/`

#### Why this exists

The owner asked what made EXEL (Exelixis) rise from 15 to 62 over 2022–2026 and whether
the *reason* can be modelled to find other names early, in both directions. This entry
records the analysis so the question is not re-answered from memory and so the data can be
reviewed locally. It follows the research-log rules for a result (dated, committed, null
treated as a finding) but it was not pre-registered: the profiles were written down from
EXEL's own filings after the outcome was known, which is exactly the hindsight the spec's
protocol exists to exclude. Nothing below changes the spec, the decision log, or any era.

#### What was done

1. **Return decomposition** (`modeling-why-exel.md`). FY2022 close to 2026-10-16: price
   +286%, EPS +479%, P/E 28.5 to 18.1. Of the log move, net-margin expansion is 82%,
   revenue growth 32%, share-count shrink 17%, multiple compression −30%. R&D fell from
   57% to 33% of revenue while revenue grew 54%; buybacks took the share count down a
   fifth; an activist (seven 13D filings in 2023) preceded the change.
2. **Three fixed profiles** from EXEL's own ratios: *level* (FY2022 state: gross margin
   ≥ 60%, profitable, gross-minus-operating margin ≥ 40 pts, net cash ≥ 10% of market
   cap, EV/sales ≤ 4, revenue growth ≥ 5%); *inflection* (FY2024 state: operating margin
   up ≥ 5 pts, opex ratio down ≥ 3 pts, diluted shares down ≥ 2%, revenue growth ≥ 5%,
   profitable); *deterioration* (shares up ≥ 10%, FCF < 0, operating loss, margin down
   ≥ 2 pts). Scored as counts and as rank composites.
3. **Run 1, yfinance statements** (`exel-profile-screen-results.md`): 2,955 liquid US
   common stocks, three formation vintages 2023–2025, 75-day filing-lag assumption.
4. **Run 2, SEC EDGAR point-in-time** (`exel-profile-sec-pit-results.md`): XBRL company
   facts for 3,584 CIKs (0 failures), 37,757 10-Ks for 3,122 companies fiscal 2009–2026,
   entry on the first session after each filing date, 21,808 filing-years with prices
   passing the floors, 16 vintages 2010–2025, sector-neutral variant on SIC-2, two-year-lag
   placebo, 13D split. EXEL excluded from every group statistic.

#### Results (run 2; median 12-month return minus the vintage's universe median)

| Profile | Vintages (n ≥ 5) | Positive | Mean excess | Mean hit | Name-years |
|---|---|---|---|---|---|
| Level, all conditions | 16 | 9 | +4.5 pts | 54% | 222 |
| Inflection, 5 of 5 | 11 | 8 | +2.6 pts | 60% | 107 |
| Inflection, 4 of 5 | 16 | 4 | −6.4 pts | 42% | 1,205 |
| Deterioration, 4 of 4 | 10 | 2 | −14.2 pts | 34% | 242 |
| Deterioration, 0 of 4 | 16 | 11 | +1.3 pts | 52% | 8,575 |

Sign tests on vintages: level 9/16 (p ≈ 0.40), inflection 8/11 (p ≈ 0.11), deterioration
2/10 positive (p ≈ 0.05). Rank-composite top-minus-bottom decile spread: level positive in
8 of 16 years (mean +1.9 pts), inflection positive in 11 of 16 (mean +3.3 pts). Placebo
flat. Both change-based profiles flip sign in the 2020 and 2025 junk rallies. EXEL itself is
level-full at its FY2021–FY2024 10-Ks and inflection-full at FY2024 (filed 2025-02-11,
entry 32.80, +34% in 12 months, +90% to date).

Run 1 agreed on the level profile (median −8, +3, −7 pts in 2023–2025 against universe
medians of +12, +3, +7) and was more favourable to the inflection and deterioration
profiles on its three vintages, which are the years run 2 also finds favourable.

#### Interpretation

- The state EXEL was in *before* its move does not pick winners. It picks cheap,
  cash-rich, under-earning companies, half of which stay that way (KNSA, IDCC, PRDO
  against USNA, RILY, VNDA in the 2023 list). Nothing in the state separates them.
- The move once it is *in the filing* (margins up, cost ratio down, shares down, revenue
  up) has a positive but ordinary-sized and regime-dependent association with the next
  year: a few points on a decile spread, not a 4× detector, and not established as a
  5-condition conjunction (rare, non-monotone, strongest in the years it was found in).
- The sell side is the reliable one: names meeting all four deterioration conditions
  trail the universe by 14 pts on average and by 23–59 pts in seven of ten years, with
  survivorship bias understating it. It reverses in junk rallies.
- The filing date matters: EXEL files five weeks after year end; a 75-day assumption
  cost four dollars of entry price.

#### What this feeds

- Screen 3's hypothesis, if the owner pursues the fundamental direction: a rank composite
  of fundamental momentum (`opm_chg`, `opex_rev_chg`, −`dshares`, `rev_g`, `netpayout`),
  the deterioration cohort as the exit, the regime split reported from day one, and the
  per-period statistic in place of the per-trade z (`penumbra-trend-lane-proposal.md`,
  "Statistic").
- The point-in-time fundamentals pipeline (`experiments/exploratory/exel_profile/`) runs on
  free data from 2010 with real filing dates; its gaps (delisted names and their prices)
  are what the Sharadar bundle closes.
- A free 13D-per-company-year count now exists; too thin here to read, worth a reported
  split in any fundamental lane.

#### Caveats

Hindsight in the profile definitions (the point of the exercise, and the reason this is
not evidence); current listing only; XBRL phase-in thins 2010–2012; tag fallbacks across
filers; no costs; `www.sec.gov` blocks requests without a contact address in the
User-Agent, `data.sec.gov` did not on the day; yfinance adjusted closes.

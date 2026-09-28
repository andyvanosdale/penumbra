# Research Log

This log is the source of truth for what was tried, why, and what happened. Every experiment gets an entry. Every entry is dated and committed to version control.

**Rules:**

1. Write the **pre-registration section BEFORE running the experiment.** Once you see results, you cannot honestly write down what you "expected."
2. Never edit a past entry to change results. If you find a bug, add a new dated entry that supersedes the old one and link back.
3. Tag every entry with the Git commit hash of the code that produced it.
4. Null results get the same treatment as positive results. They are not "failed experiments" — they are findings.
5. If you peek at the holdout era, log it. Once peeked at, that holdout slice is burned.

**Holdout status:** UNTOUCHED (do not edit this line until the final confirmation run; then change to TOUCHED with date)

**Era split (locked):**

- Development: 2015-01-01 → 2020-12-31
- Validation: 2021-01-01 → 2022-12-31
- Holdout: 2023-01-01 → present

---

## Entry Template

Copy this block for each new experiment. File naming: `research_log/YYYY-MM-DD-short-slug.md` OR append to this rolling log — pick one and stick with it.

```markdown
### YYYY-MM-DD — <experiment short name>

**Phase:** <1 / 2 / 3 / 4>
**Commit:** <git hash>
**Status:** <pre-registered | running | complete | superseded by ENTRY_DATE>

#### Pre-registration (written BEFORE running)

- **Hypothesis:** <the specific testable claim, in one sentence>
- **Feature(s):** <exact definition, including any thresholds and lookback windows>
- **Label:** <exact definition; reference labels.py version if it changed>
- **Universe:** <which tickers, which dates>
- **Era used:** <development | validation | holdout — and WHY this era is appropriate>
- **Model:** <logistic regression / XGBoost / etc., with hyperparams if non-default>
- **Costs assumed:** <spread bps, commission, slippage model>
- **Baselines compared against:** <buy-and-hold sector, random entry, others>
- **What would be "interesting":** <e.g., hit rate > 55% AND signal count > 200 AND beats random by > 0.3% per signal after costs>
- **What would be "not interesting":** <fallback definition>
- **Decision rule:** <if interesting → next step is X; if not interesting → next step is Y>

#### Run details

- **Dataset snapshot date:** <date of the raw data pull this run used>
- **Compute / runtime:** <minutes, machine, anything unusual>
- **Anomalies during run:** <any warnings, dropped rows, NaN handling, etc.>

#### Results

- **Hit rate:** <X%>
- **Signal count:** <N>
- **Avg excess return per signal (after costs):** <X bps or %>
- **Max drawdown:** <X%>
- **Baseline comparison:** <delta vs each baseline>
- **Plots / artifacts:** <path to plots, confusion matrix, equity curve>

#### Interpretation

- **Was the pre-registered "interesting" criterion met?** <yes / no>
- **What does this tell us about the hypothesis?**
- **What does it tell us about the harness?** (Did anything look suspicious? Was the result too good?)
- **Confidence in the result:** <high / medium / low — and why>

#### Next action (per the pre-registered decision rule)

- <concrete next step>

#### Open questions / followups

- <anything you want to come back to but won't chase right now>
```

---

## 2026-09-28 — Free-data screen of the v1 rule (issue 15): null in every lane

**Pre-registered:** 9a7721e · **code:** 256b98a · **results:** 911d146 (branch `screen/free-data`).
Next-open 5-session excess over the same-day universe at zero cost: `smallcap` −11 bps
(day-clustered z −2.5), uncapped +6 bps (z −1.6), crypto top-100 −42 bps (z −3.7),
against the +50 bps threshold. Placebo flat; planted +50 bps detectable. Decisions per
the pre-registration: the equity build for the v1 rule stops, and the crypto lane is
removed by spec change. Full entry: `2026-09-28-free-data-screen.md`; tables in
`2026-09-28-free-data-screen/`.

---

## 2026-09-28 — Legacy day-of-week plumbing test on real prices (issue 1)

**Commit:** `5a92cf0824a3cd34597481faa5d6d0b45039a812` · yfinance 1.7.0 · PASS —
z vs random = 0.073 (tolerance |z| < 2.0), 11,911 signals, 0 tickers failed
(58/58 pulled: 50 tickers + 8 sector ETFs, 2015-01-01 → 2020-12-31). Full
pre-registration and results: `2026-09-28-legacy-control-real-prices.md`.

---

## 0000-00-00 — Project bootstrap (placeholder)

**Phase:** 0 (setup)
**Commit:** TBD
**Status:** pre-registered

This entry exists so the log file is not empty. Replace with the first real experiment entry once Phase 1 begins.

#### Pre-registration

- **Hypothesis:** N/A — bootstrap entry, not a real experiment.
- **Intent:** Verify repository layout, environment, and that this log file is committed.

#### Notes

- First real entry will be Phase 1 Plumbing: dummy "is it Monday" feature, expected null result, decision rule = if a non-null edge appears, the harness has a bug and Phase 1 does not pass.

---

## Holdout Access Log

Every time the holdout era is touched, record it here. Once touched without an explicit "final confirmation run" justification, the holdout is contaminated.

| Date | Reason | Commit | Result summary | Holdout still valid? |
|---|---|---|---|---|
| — | — | — | — | yes (untouched) |

---

## Lessons File

Running list of hard-won lessons. Add to it whenever you find a bug or a near-miss. Re-read at the start of every new phase.

- (Add lessons here as they accumulate.)

# News-Driven Stock Signal Project

**Plan & Working Brief for Backtest Harness Development**

---

## 1. Project Overview

This project builds a research harness for testing whether public news (direct and indirect) provides a tradeable predictive signal for equity price moves. The deliverable for the first phase is not a trading strategy—it is a trustworthy backtest harness capable of correctly identifying both real signal and noise.

### Core Hypothesis

Public information about a company (and about its suppliers, competitors, and customers) contains predictive signal for that company's near-term excess return over its sector. The indirect-effect link (news about A predicts moves in related B) is the primary bet because it is less crowded than direct sentiment trading.

### Primary Output

A predictive indicator that flags entry points ("start to buy") for a given ticker. Exit logic is out of scope for the first phase.

### Guiding Principles

- Marathon, not sprint. Trustworthy nulls are wins.
- Harness before hypothesis. A mediocre model on a trustworthy harness beats a great model on a buggy one.
- Point-in-time discipline is non-negotiable. Every datum has an as-of timestamp; every query filters on it.
- Pre-register experiments before running them. Backtests are not for exploration; they are for confirmation.
- Null results are first-class outcomes. Do not tune until you get a result you like.

---

## 2. Prediction Framing

### Horizon

5 trading days. Fast enough for news-driven causation to be plausible, slow enough that retail execution is realistic and the signal is not already arbitraged by HFT.

### Target

Excess return vs. the ticker's sector ETF (not raw return). This isolates company-specific signal from market beta.

### Form

Binary classification: does the ticker outperform its sector by more than a chosen threshold (initial value: 2%) over the next 5 trading days, yes or no? Classification is preferred over regression for the first phase because it is more robust to outliers and easier to evaluate.

---

## 3. Harness Architecture

Five components with strict interfaces. Data leakage between components is the primary failure mode of these projects; clean interfaces are the main defense.

### 3.1 Point-in-Time Data Store

The heart of the system. Every table has an as-of timestamp column. Every query must be of the form "what did I know about X as of time T?"

- Recommended backend: DuckDB or SQLite (sufficient for years of work at this scale).
- Tables: prices, news, fundamentals, relationships, universe membership.
- Every row records both event time (when it happened) and knowledge time (when it became knowable).

### 3.2 Feature Builder

Function with signature: `build_features(ticker, timestamp) -> feature_vector`. Strictly forbidden from accessing any data with as-of timestamp greater than the input timestamp. This is the chokepoint where lookahead bias would otherwise enter.

### 3.3 Labeler

Function with signature: `label(ticker, timestamp) -> binary_outcome`. The **ONLY** component permitted to look into the future. Quarantine it: it should never be importable from feature-building code.

### 3.4 Model Wrapper

Trains on (features, label) pairs from a training window; predicts on a test window. Start dead simple:

- Phase 1–2: logistic regression.
- Phase 3–4: gradient boosted trees (XGBoost or LightGBM).
- Do NOT use deep learning in the first phase. You want to debug data, not architecture.

### 3.5 Backtest Runner & Evaluator

Walks forward through time, generates signals, simulates trades with realistic costs and slippage, produces a standard report.

**Required report metrics:**

- Hit rate (% of signals that were correct).
- Average excess return per signal, AFTER costs.
- Signal count (a 70% hit rate on 6 trades is luck).
- Max drawdown.
- Comparison to baselines: buy-and-hold sector, random entry with same trade count.

---

## 4. Phased Execution Plan

Each phase produces an artifact that must be trusted before the next phase begins. Do not skip ahead.

### Phase 1: Plumbing

**Goal: harness end-to-end with a deliberately useless feature.**

- Universe: 50 large-cap S&P 500 tickers.
- Data: daily OHLCV for tickers and sector ETFs, 2018 through the most recent full year.
- Feature: a trivial placeholder (e.g., "is it Monday").
- Success criterion: harness correctly reports no edge, with hit rate indistinguishable from the random baseline.
- If the harness finds an "edge" in a useless feature, STOP and find the bug.

### Phase 2: Calibration with a Known Effect

**Goal: confirm the harness can detect real signal when it exists.**

- Add feature: post-earnings announcement drift (PEAD). One of the most documented anomalies in finance.
- Earnings surprise > X standard deviations → positive drift expected over following weeks.
- Success criterion: harness detects a small but real positive effect, consistent with published literature (~0.5–1% over the drift window in modern data).
- If PEAD is not detected, the harness has a bug. Do not move forward.

### Phase 3: Direct News Effect

**Goal: validate the news ingestion and timestamping pipeline.**

- Ingest news data with reliable publish timestamps (NOT scrape timestamps).
- Simple sentiment: off-the-shelf model or keyword list. Do not optimize NLP yet.
- Test: does news sentiment about company A predict A's own 5-day excess return?
- Expectation: small or null effect. Large-cap direct news is a crowded trade.
- Success criterion: pipeline functions correctly, results are sensible (not absurdly large), timestamps verified.

### Phase 4: The Real Hypothesis

**Goal: test indirect news effects. This is where original work begins.**

- Build relationship graph: start with sector membership and named competitors / customers / suppliers from 10-K risk factors (SEC EDGAR).
- Relationships must be as-of-date. Use filing dates as the as-of timestamp.
- Test: does negative news about A predict B's 5-day excess return, where B is a related entity?
- Compare against direct effect from Phase 3 and against random baseline.

---

## 5. Data Sources

Start free and lean. Upgrade only when a free source becomes the bottleneck. The point of starting small is iteration speed, not cost.

| Data Type | Source | Notes |
|---|---|---|
| Prices (OHLCV) | yfinance (free) or Polygon.io (paid, cleaner) | Adjust for splits and dividends. |
| Sector / ETF data | yfinance, SPDR sector ETFs (XLF, XLK, etc.) | Used for excess return calculation. |
| Fundamentals | SEC EDGAR (free, point-in-time defensible) | Each filing has a filing date = natural as-of timestamp. |
| Earnings dates / surprises | yfinance, EDGAR 8-K filings | Needed for Phase 2 PEAD calibration. |
| News | GDELT (free), NewsAPI (limited), RavenPack (expensive) | **CRITICAL:** must use real publish timestamps, not scrape dates. |
| Relationships | SEC EDGAR 10-K risk factor sections (free) | Extract named competitors/customers/suppliers with NLP. |
| Historical universe | Wikipedia revision history of S&P 500 list (workable workaround) | Dodges survivorship bias. Document limitations. |

---

## 6. Anti-Fooling-Yourself Protocols

These are the disciplines that separate trustworthy research from exciting nonsense. They feel bureaucratic; they are not optional.

### 6.1 The Three-Era Split

- **Development era (2015–2020):** explore freely, build features, tune.
- **Validation era (2021–2022):** peek sparingly, only to confirm a locked design.
- **Holdout era (2023–present):** touch ONCE, at the very end. If re-touched after tweaking, it is burned and becomes development data.

### 6.2 Walk-Forward Within Development

Train on a rolling window, predict the next slice, roll forward. Mimics real deployment and catches strategies that only worked in one market regime.

### 6.3 Pre-Registration

Before EVERY backtest, write down in a dated log entry:

1. The exact hypothesis being tested.
2. The feature(s) and threshold(s).
3. What outcome would be "interesting" vs. "not."
4. What you will do with each possible outcome.

This is the single best defense against p-hacking yourself into believing noise is signal.

### 6.4 Research Log

Every experiment, every hypothesis, every result—dated and written down. Without it, after three months you will not remember why you tried something.

### 6.5 Cost Realism From Day One

Bake in spread + commission + slippage from the first backtest, not later. Slippage on smaller-cap names is often what kills paper-profitable strategies.

### 6.6 Always Compare to Baselines

- Buy-and-hold the sector.
- Random entry with the same number of trades.
- If you cannot beat random after costs, the signal is noise.

---

## 7. Common Traps to Avoid

- **Lookahead bias:** using information not available at decision time. Most often via news scrape timestamps or restated fundamentals.
- **Survivorship bias:** testing on today's index constituents ignores companies that went bankrupt or got delisted.
- **Overfitting:** with enough features and tuning, anything fits history and predicts nothing. A backtest that looks amazing is a warning sign.
- **Transaction cost denial:** paper strategies that ignore spreads, fees, and slippage often die on contact with reality.
- **Holdout contamination:** re-running against the holdout after seeing results turns it into training data.
- **Relationship-graph leakage:** using today's known supply chain to label a 2021 trade leaks future knowledge.

---

## 8. Recommended Tech Stack

| Layer | Choice |
|---|---|
| Language | Python 3.11+ |
| Data manipulation | pandas, polars (for larger datasets) |
| Point-in-time store | DuckDB (preferred) or SQLite |
| Modeling | scikit-learn (Phase 1–2), XGBoost or LightGBM (Phase 3–4) |
| News / NLP | VADER or FinBERT for off-the-shelf sentiment; spaCy for entity extraction |
| Backtest framework | Custom (recommended for learning) or vectorbt / backtesting.py |
| Notebook / scripts | Jupyter for exploration; `.py` modules for harness components |
| Version control | Git. Tag every backtest run with a commit hash in the research log. |
| Data versioning | Snapshot raw data with date; never re-pull silently. |

---

## 9. Proposed Module Layout

Suggested repository structure. Strict separation of concerns is what makes data leakage detectable.

```
signal-project/
  data/
    raw/              # immutable snapshots, dated
    processed/        # point-in-time tables
  harness/
    store.py          # point-in-time data store interface
    features.py       # build_features(ticker, ts) -> vector
    labels.py         # label(ticker, ts) -> binary    [QUARANTINED]
    model.py          # train/predict wrapper
    backtest.py       # walk-forward runner
    evaluate.py       # metrics, baselines, reports
    costs.py          # transaction cost / slippage models
  experiments/
    phase1_plumbing.py
    phase2_pead.py
    phase3_direct_news.py
    phase4_indirect_news.py
  research_log/
    YYYY-MM-DD-experiment-name.md
  notebooks/          # exploration only; never the source of truth
  tests/              # unit tests, especially for lookahead
```

---

## 10. First-Week Concrete Tasks

Tractable starting sprint. Goal at end of week one: end-to-end pipeline running on a dummy feature and correctly reporting no edge.

1. Set up repository, virtual environment, install Python 3.11+, pandas, duckdb, scikit-learn, yfinance.
2. Pull daily OHLCV for 50 large-cap tickers and their sector ETFs, 2018 through last full year. Save as immutable raw snapshot with date.
3. Build the as-of-aware price table in DuckDB. Every row: `(ticker, date, OHLCV, knowledge_date)`. Confirm queries cannot return rows where `knowledge_date > query_date`.
4. Write the labeler: given `(ticker, date)`, return 5-day forward excess return vs sector ETF, plus binary label using 2% threshold.
5. Write the harness skeleton: feature builder with a dummy "is it Monday" feature.
6. Wire up logistic regression model wrapper with train/predict interface.
7. Write backtest runner with walk-forward over development era; produce report with hit rate, average excess return, signal count, baseline comparison.
8. Run end to end. Confirm null result. Commit. Start research log entry.

---

## 11. Phase Success Criteria & Exit Conditions

Each phase has a binary go/no-go. Do not advance until the criterion is met.

| Phase | Success Criterion | Failure Action |
|---|---|---|
| 1: Plumbing | Harness reports no edge for dummy feature; metrics match random baseline within noise. | Bug in harness. Do not proceed. Audit feature builder and labeler for leakage. |
| 2: PEAD | Detects small positive drift effect consistent with published literature. | Bug in harness OR data issue. Verify earnings dates and timestamps. |
| 3: Direct News | Pipeline runs cleanly; results are sensible (small or null). Timestamp audit passes. | Fix news ingestion / timestamping before proceeding. |
| 4: Indirect News | Statistically meaningful edge over baselines, AFTER costs, on validation era. Confirm once on holdout. | Honest null. Document. Consider narrower hypothesis or different relationship type. |

---

## 12. Honest Expectations

The realistic outcome for most solo projects in this space is that you build something fascinating, learn a great deal of applied ML and finance, and discover that the edge is thinner than hoped after costs. A smaller fraction find a durable niche edge, usually in a corner too small for large firms to bother with.

The right framing is: "this is an excellent way to get sharp at applied ML on messy real-world data, and MAYBE it makes money." Not: "I am going to make money with this."

This document is a research and engineering plan, not financial advice. Whether and how to trade based on any signal produced is a separate decision that this plan does not address.

---

## Appendix: Glossary

- **As-of timestamp:** the time at which a piece of information became knowable. Distinct from event time.
- **Excess return:** return of a security minus return of a benchmark (here, sector ETF) over the same period.
- **Lookahead bias:** accidentally using future information in a backtest. The most common bug in this space.
- **PEAD:** Post-Earnings Announcement Drift. Documented tendency for stocks to drift in the direction of an earnings surprise for weeks after.
- **Survivorship bias:** testing only on entities that survived to today, ignoring failures.
- **Walk-forward:** training on a rolling window and testing on the next slice, advancing through time.
- **Slippage:** the gap between expected and realized fill price; the cost of your own order moving the market.

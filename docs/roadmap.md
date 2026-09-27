# Roadmap

Future work is tracked here, not in code. The codebase reflects only what is
currently shipped; each item below becomes an `experiments/` script (and the
necessary harness additions) when it is actually started — pre-registered in the
research log first.

The phased plan and rationale live in [`signal_project_plan.md`](signal_project_plan.md);
this file is the short, actionable to-do view.

## Shipped

- Point-in-time store, as-of feature builder, quarantined labeler, logistic-
  regression model, cost model, walk-forward runner, cost-aware evaluator.
- Negative control: `experiments/dummy_feature.py` ("is it Monday") confirms the
  harness reports no edge on an uninformative feature.

## Next: PEAD calibration (confirm the harness can detect a real effect)

Add a post-earnings-announcement-drift signal and confirm a small positive effect
consistent with published literature (~0.5–1% over the drift window). If it is not
detected, the harness has a bug — do not move on (plan §4, §11).

- Ingest earnings dates + surprises (yfinance / EDGAR 8-K). `knowledge_date` =
  announcement timestamp, NOT the period-end date.
- Add an `earnings_surprise_z` feature (lookback-standardized surprise).

## Then: direct news effect (validate the news + timestamping pipeline)

Does news sentiment about company A predict A's own 5-day excess return? Expect a
small or null effect (large-cap direct news is crowded). Success = pipeline runs
cleanly, results sensible, timestamps verified (publish time, NOT scrape time).

- Ingest news with reliable PUBLISH timestamps (GDELT / NewsAPI); `knowledge_date`
  = publish timestamp.
- Off-the-shelf sentiment (VADER / FinBERT). Do not optimize NLP yet.
- Add a `news_sentiment_5d` feature.

## Then: indirect news effect (the real hypothesis)

Does negative news about A predict a related entity B's 5-day excess return? This
is where original work begins. Success (plan §11): a statistically meaningful edge
over baselines, after costs, on the validation era; confirmed ONCE on the holdout.
Otherwise: an honest null, documented.

- Build an as-of-dated relationship graph (sector membership + named
  competitors/customers/suppliers from 10-K risk factors via SEC EDGAR; filing
  date = as-of timestamp). Beware relationship-graph leakage (plan §7).
- Add a `relationships` table to the store with as-of (filing) dates.
- Add an indirect-sentiment feature over graph neighbors.

## Cross-cutting to-dos

- Replace the static, survivorship-biased universe (`config/universe.py`) with
  point-in-time S&P 500 membership before any time-varying-universe result.
- Re-verify the negative control on a REAL yfinance snapshot (current pass is on
  synthetic data).
- Consider a compounded / position-sized equity curve alongside the additive one
  so max-drawdown reads in intuitive units.
- Upgrade the store backend from SQLite to DuckDB if/when scale demands it.

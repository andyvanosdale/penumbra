# Penumbra

A research harness for testing whether public news (direct **and** indirect)
provides a tradeable predictive signal for equity price moves.

The early deliverable is **not** a trading strategy — it is a *trustworthy
backtest harness* that can correctly distinguish real signal from noise.
Trustworthy nulls are wins. See [`docs/signal_project_plan.md`](docs/signal_project_plan.md)
for the full brief, [`docs/roadmap.md`](docs/roadmap.md) for what's next, and
[`research_log/`](research_log/) for the experiment log.

## Status

Currently shipped: the full harness (point-in-time store, as-of feature builder,
quarantined labeler, logistic-regression model, cost model, walk-forward runner,
cost-aware evaluator) plus a negative-control experiment that confirms the harness
reports **no edge** on a deliberately useless "is it Monday" feature.

This currently passes on a **synthetic** snapshot (the build environment had no
network). Re-run on a real yfinance pull to validate on real prices. Planned work
is tracked in [`docs/roadmap.md`](docs/roadmap.md).

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1. Get data.
#    Real (needs network):
python -m ingest.pull_prices --start 2018-01-01 --end 2024-12-31
#    OR offline synthetic (plumbing only):
python -m ingest.make_synthetic --start 2018-01-01 --end 2022-12-31

# 2. Load it into the point-in-time store.
python -m ingest.load_to_store

# 3. Run the negative control and check the null result.
python -m experiments.dummy_feature

# 4. Run the test suite (leakage tests are the important ones).
pytest -q
```

The negative control runs on only the stdlib + pandas + numpy (logistic regression
has a pure-numpy fallback), so step 3 works even before the heavier deps install.

## Architecture (plan §3)

Five components with strict interfaces. Clean interfaces are the main defense
against data leakage — the primary failure mode of this kind of project.

```
harness/
  store.py      point-in-time data store. Two read paths:
                  get_known_prices(as_of) / known_bar(...)  — RESTRICTED (features use this)
                  get_prices_oracle()                       — future-aware, LABELER ONLY
  features.py   build_features(ticker, ts) -> vector. Never sees the future.
  labels.py     label(ticker, ts) -> 0/1.   QUARANTINED — the only future-aware code.
  model.py      logistic regression wrapper (numpy fallback / sklearn).
  costs.py      spread + commission + slippage, applied from day one.
  backtest.py   walk-forward runner (precomputes the panel once).
  evaluate.py   hit rate, net excess, signal count, drawdown, baselines.
```

The point-in-time contract: every row has a `knowledge_date`; every feature query
is *"what did I know as of time T?"*. It is structurally impossible for the
restricted read paths to return a row with `knowledge_date > T`, and the test
suite asserts the feature builder never imports the labeler or calls the oracle.

## Discipline (plan §6)

- **Era split (locked):** development 2015–2020, validation 2021–2022, holdout
  2023–present. The holdout is touched **once**, at the very end. Status lives in
  `research_log/research_log.md`.
- **Pre-registration:** every backtest gets a dated log entry written *before* it
  runs. Backtests confirm; they do not explore.
- **Null results are first-class.** Do not tune until you get a result you like.
- **Costs from day one.** Baselines (random entry, buy-and-hold sector) on every run.

## Layout

```
config/        universe (50 tickers -> sector ETF), locked era split
harness/       the five components above
ingest/        pull_prices (real), make_synthetic (offline), load_to_store
experiments/   phase1_plumbing (runnable) + phase2-4 stubs
research_log/   the source of truth for what was tried and what happened
tests/         unit tests, especially lookahead/quarantine
data/raw/      immutable, dated snapshots (gitignored)
data/processed/ point-in-time store + run reports (gitignored)
```

## Caveats

This is a research and engineering plan, **not financial advice**. The realistic
outcome for most solo projects in this space is an excellent way to get sharp at
applied ML on messy real-world data, and *maybe* it makes money — not the other
way around (plan §12).

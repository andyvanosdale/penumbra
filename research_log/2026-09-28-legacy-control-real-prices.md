### 2026-09-28 — Legacy day-of-week plumbing test on real prices (issue 1)

**Phase:** legacy baseline (wave 5, issue 1)
**Commit:** 5a92cf0824a3cd34597481faa5d6d0b45039a812
**Status:** complete

#### Pre-registration (written BEFORE running)

- **Hypothesis:** None — this is a *plumbing test*, not a control and not a claim
  about the strategy. `spec/07-evaluation.md` (Controls, last line) keeps the
  day-of-week dummy from the legacy harness as a plumbing test only, so the only
  thing under test is whether the harness still runs a useless feature to a null
  result when fed real prices instead of synthetic GBM data. `2026-05-29-phase1-plumbing.md`
  ran this same dummy on synthetic data and got |z| = 0.965; this entry repeats it
  on real yfinance data.
- **Feature(s):** `is_monday` (legacy `dummy_feature.py` / `legacy/features.py`),
  unchanged from the synthetic run.
- **Label:** unchanged — `legacy.labels.Labeler`, horizon = 5 trading days,
  threshold = 2% excess return vs the ticker's SPDR sector ETF benchmark
  (`legacy.universe.benchmark_for`).
- **Universe:** the legacy 50 large-cap tickers plus their 8 SPDR sector ETFs,
  i.e. `legacy.universe.ALL_SYMBOLS` (58 symbols) — the ETFs are pulled too
  because they are the excess-return benchmark for every ticker.
- **Data:** yfinance daily OHLCV (`legacy/pull_prices.py`), 2015-01-01 through
  2020-12-31 — the legacy development era (`legacy.eras.DEVELOPMENT`). `spec/02-data.md`
  Sources lists yfinance for exactly this purpose ("the legacy negative control";
  never read by a committed run). Loaded into a fresh `legacy.store.PITStore` via
  `legacy/load_to_store.py`.
- **Model:** logistic regression (`legacy.model.LogisticRegressionModel`,
  numpy fallback unless sklearn is installed) — unchanged from the synthetic run.
  Walk-forward: 252-day train / 63-day test.
- **Costs assumed:** `legacy.costs.DEFAULT_COSTS` (unchanged).
- **Baselines compared against:** random entry with the same trade count
  (500-iteration bootstrap, `legacy.evaluate.evaluate`).
- **What a pass means:** |z_vs_random| < 2.0, exactly as `legacy/dummy_feature.py`'s
  `Z_TOLERANCE` checks. This confirms the harness plumbing (PIT store → as-of
  feature builder → quarantined labeler → walk-forward → cost-aware evaluation →
  random baseline) still does not manufacture an edge from a useless feature when
  the input is real market data rather than synthetic GBM. It says nothing about
  whether any real strategy in this codebase has an edge — there is no strategy
  under test here, `legacy/` is frozen, and the spec-built harness (`harness/`) is
  a separate, not-yet-built pipeline.
- **What a fail means:** |z_vs_random| >= 2.0 means STOP — do not re-run with
  different settings, do not tune the tolerance, and do not treat it as a strategy
  result either way. A fail means the legacy harness has a leakage or logic bug
  that the synthetic run didn't expose (most likely something that depends on real
  price structure — actual calendar effects, dividends/splits interacting with
  `adj_close`, or real cross-sectional correlation the GBM synthetic data lacked).
  The next step is to audit the legacy pipeline (`legacy/features.py`,
  `legacy/labels.py`, `legacy/store.py`) for lookahead, not to adjust the feature,
  the era, or the universe to get a different answer.
- **Decision rule:** record whatever the run produces, honestly, in this file and
  in `research_log/research_log.md`, with the commit hash of the code that ran it.
  If it fails, say so in the PR and stop; do not iterate settings to chase a pass.

#### Run details

- **yfinance version:** 1.7.0.
- **Data pulled:** `python -m legacy.pull_prices --start 2015-01-01 --end 2020-12-31
  --snapshot-date 2026-09-28`, with `PENUMBRA_DATA_ROOT` pointed at a scratch
  directory outside the repo. All 58 symbols (50 tickers + 8 sector ETFs)
  returned data; no ticker failed. yfinance logged repeated
  `Cookie fetch from fc.yahoo.com failed (ConnectionError), continuing without it`
  / `Cookie/crumb fetch failed` warnings (the proxy rejects yfinance's cookie
  hosts, `guce.yahoo.com` and `fc.yahoo.com`, as expected) but fell back
  successfully and every symbol returned full history. `XLC` (Communication
  Services Select Sector SPDR) returned only 639 of the expected ~1510 rows —
  expected, not a failure: XLC did not exist until mid-2018, so it has no
  history before then. Snapshot: `prices_2026-09-28.parquet`, 86,709 rows.
- **Loaded to store:** `python -m legacy.load_to_store --raw
  <snapshot>/prices_2026-09-28.parquet` → fresh `legacy.store.PITStore` SQLite
  file, 86,709 rows, 1,510 trading days.
- **Environment fix required:** `legacy/pull_prices.py` writes its snapshot as
  Parquet, but `requirements.txt` pinned no Parquet engine (only `pandas`,
  `numpy`, `fsspec`, `yfinance`, `pytest`); `df.to_parquet` raised
  `ImportError: Unable to find a usable engine`. Added `pyarrow>=14.0` to
  `requirements.txt` (commit 5a92cf0). No other code changes were needed — the
  legacy pipeline's real-data path (env-var-driven paths from issue 2, real
  yfinance pull, load-to-store, dummy_feature) ran unmodified.
- **Backtest run:** `python -m legacy.dummy_feature` against the loaded store,
  clamped to the development era as data allows: 2015-01-02 → 2020-12-30,
  50 tickers (the ETFs are read only as the excess-return benchmark, not
  scored). 20 walk-forward folds (252-day train / 63-day test), numpy model
  backend (sklearn not installed), 58,317 (ticker, date) cells scored, 11,911
  signals fired.
- **Anomalies:** none beyond the expected yfinance cookie-fetch warnings and
  XLC's shorter history, both noted above.

#### Results

- **z vs random:** **0.073** (tolerance |z| < 2.0).
- **Strategy hit rate (net > 0):** 0.4886 — random baseline hit rate: 0.4892.
- **Label hit rate (y = 1):** 0.1707.
- **Signal count:** 11,911 (out of 58,317 scored ticker-days).
- **Avg excess per signal, net of costs:** 0.03720% — random baseline:
  0.03537% (sd 0.02499%, 500-iteration bootstrap).
- **Avg excess per signal, gross:** 0.13720%.
- **Max drawdown:** −257.97% on the additive (non-compounded) per-trade equity
  curve — a diagnostic of cumulative small per-trade excess returns, not a
  portfolio P&L, consistent with the synthetic-data run's presentation.
- **Tickers that failed to pull:** none — all 58 symbols (50 tickers + 8
  sector ETFs) returned data.
- **Code commit:** `5a92cf0824a3cd34597481faa5d6d0b45039a812`.
- **yfinance version:** 1.7.0.
- **Full report:** written to `<PENUMBRA_DATA_ROOT>/legacy/processed/dummy_feature_report.json`
  during the run (scratch directory, not committed — data artifacts stay out
  of the repo per `docs/architecture.md`).

#### Interpretation

- **Outcome:** PASS. |z| = 0.073 is well inside the ±2.0 tolerance
  (`legacy/dummy_feature.py`'s own `Z_TOLERANCE`), matching the direction (and,
  closely, the magnitude) of the synthetic-data run in
  `2026-05-29-phase1-plumbing.md` (z = 0.965). The day-of-week dummy is
  statistically indistinguishable from random entry on real 2015–2020 prices
  for this universe.
- **What this confirms:** the legacy plumbing — real yfinance pull → PIT store
  load → as-of feature builder → quarantined labeler → walk-forward →
  cost-aware evaluation → random baseline — still does not manufacture an edge
  from a useless feature when fed real market data instead of synthetic GBM.
  Per the pre-registration and per `spec/07-evaluation.md` (Controls, last
  line), this is a plumbing result only. It is **not** a control and it says
  **nothing** about whether any strategy in this codebase has an edge — no
  strategy is under test, `legacy/` remains frozen, and the spec-built
  `harness/` pipeline is a separate, not-yet-built codepath.
- **Confidence:** medium-high for plumbing, same caveat as the synthetic run:
  this validates mechanics on one (universe, era) pair, not market behavior in
  general.

#### Next action (per the pre-registered decision rule)

- The plumbing test passed on real prices; no audit is triggered. No further
  action is required by this issue. The result stands as recorded here (there
  is no run record yet — issue 17 is building one — so this file plus the
  commit hash above is the record, as the issue says).

#### Open questions / followups

- Once `harness/` (the spec-built pipeline) can run the day-of-week dummy
  through its own components, `legacy/` is deleted per `docs/architecture.md`
  and this plumbing test moves with it.

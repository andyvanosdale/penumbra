### 2026-09-28 — Legacy day-of-week plumbing test on real prices (issue 1)

**Phase:** legacy baseline (wave 5, issue 1)
**Commit:** <fill in with `git rev-parse HEAD` of the run, written after running>
**Status:** pre-registered

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

(filled in after running — see Results below)

# Architecture

The spec (`andyvanosdale/penumbra-specs`, `spec/00`–`spec/07`, `spec/DECISIONS.md`)
says what Penumbra is. This document says how the code is shaped to do it: the
components, their interfaces, the store schema, which module owns which spec
requirement, and what is built versus owed. Where code and spec disagree, the spec
wins. Where this document and the spec disagree, this document is wrong; fix it.

Kept current by the change that makes it stale. Owner: the product architect.

## Shape

```
raw vendor files ──► ingest loaders ──► point-in-time store (SQLite)
 (PENUMBRA_DATA_ROOT)   ingest/           harness/store/
        ▲                                   │  as-of reads            │ oracle reads (bounded)
   ingest/fetch/                            ▼                         ▼
 (Binance, Sharadar,                 universe ─► features ─┐      labeler (quarantined)
  yfinance)                         harness/     harness/  │      harness/labels.py
                                    universe.py  features.py        │ exits, costs, forward returns
                                                           ▼        ▼
                                                     backtester (the only join)
                                                     harness/backtest.py
                                                  strategy · benchmark · variants · controls
                                                           │
                                                           ▼
                                                  evaluator ─► report + run record
                                                  harness/evaluate.py   harness/runrecord.py
```

A run is `(lane, era, configuration hash, snapshot id)`. The data flows one
way. The only component that reads prices after the as-of date is the labeler.
The labeler's output meets the features only inside the backtester.

## Packages and ownership

| Path | Component | Spec | Issue | Status |
| --- | --- | --- | --- | --- |
| `ingest/fetch/` | Raw-file fetcher: Binance, Sharadar and yfinance into a storage root (local, volume or S3); manifests; snapshot id | 02 Sources, Store | PR 19 | in review |
| `config/env.py` | Every environment variable, read in one place | 02 Configuration | 2 | owed |
| `config/eras.py` | Per-lane era bounds | 03 | 17 | owed (still carries the news-project split) |
| `config/params.py` | Every locked parameter as frozen data: the single input to the configuration hash | 01, 05, 06, 07 | 17 | owed |
| `config/exclusions/` | Dated crypto base-asset exclusion list | 01 Eligibility | 6 | owed |
| `harness/store/` | Schema, idempotent writer, as-of reader (single-date and windowed panel), read-time adjustment, lane calendars, bounded oracle reader | 02 Store, Trading calendars | 16, then 5 | owed |
| `ingest/sharadar.py` | SEP, TICKERS, ACTIONS, DAILY, EVENTS, SFP (SPY) raw exports → store | 02 | 3 | owed; built against fixtures until a key exists |
| `ingest/binance.py` | 1d and 1h klines → store; kline-derived listing; timestamp normalization | 02 | 4 | owed; gated on the screen's crypto result |
| `harness/universe.py` | Per-lane eligibility and screens → `lane_membership` | 01 | 6 | owed |
| `harness/features.py` | 14 features and `filing_2d`, as-of | 04 | 8 | owed |
| `harness/labels.py` | Quarantined labeler: exit simulation, realized net exit return, forward returns, ex-post bucket, delisting treatment, era censoring | 04 Labels, 03 Era boundaries, 01 Delisting | 9 (exits with 10) | owed |
| `harness/costs.py` | Abdi–Ranaldo spread, square-root slippage, fees, stress cases, breakeven multiple | 06 | 7 | owed |
| `harness/strategy.py` | Candidate rule, no re-entry, entry fills, capped and close-fill variants | 05 | 10 | owed |
| `harness/benchmark.py` | 1,000 seeded, quintile-matched random-entry draws | 05 Benchmark | 10 | owed |
| `harness/backtest.py` | The join: features × labels × costs → trades; runs strategy, benchmark, variants, controls | 05 | 10 | owed |
| `harness/evaluate.py` | Metrics, day-clustered z, equity curve, decision rule, regime split | 07 | 11 | owed |
| `harness/controls.py` | Stale-signal placebo, planted-effect positive control | 07 Controls | 11 | owed |
| `harness/runrecord.py` | Configuration hash, run log, dev-hash count, reproduce-from-snapshot | 03 Run record | 17 | owed |
| `harness/guards.py` | Holdout unlock; leakage-suite gate (no results written unless the leakage tests pass on this commit) | 02 Leakage tests, 03 | 18 (gate), 11 (holdout) | owed |
| `experiments/` | Pre-registered one-off studies (the free-data screen) | DECISIONS "Free-data screen" | 15 | running on `screen/free-data` |
| `legacy/` | The migrated news-project harness; only the day-of-week plumbing test uses it | 07 Controls (last line) | 1, 2 | baseline, frozen |
| `research_log/` | Pre-registration and outcome of every run | 03 | all runs | — |

Import rules, enforced by `tests/test_architecture.py`:

- Nothing outside `legacy/` and `tests/legacy/` imports `legacy`.
- Only `harness/labels.py` and `harness/backtest.py` import `harness.store.oracle`.
- Only `harness/backtest.py` imports `harness.labels`.
- The feature builder, the universe builder and the cost model read through
  `harness.store.reader` only.

## Store

SQLite, one file at `PENUMBRA_STORE_PATH`. The store is a derived artifact: it can
always be rebuilt from a snapshot's raw files and is never the only copy of
anything. The run log, which can't be rebuilt, lives under the data root instead
(below).

### Keys and availability

- Market data is keyed by `(market, symbol, date)`, with `market` ∈ {`us_equity`,
  `binance_spot`}. The equity symbol is the Sharadar permaticker (as text), with the
  ticker as an attribute. The crypto symbol is the Binance pair.
- Every row carries `available_at` (an ISO date, or an ISO UTC timestamp for hourly
  bars) and `snapshot_id`. Loads are idempotent on the primary key, which includes
  `snapshot_id`, so one store can hold two snapshots side by side. Every read names
  its snapshot.
- `available_at` rules (spec/02, spec/04): a daily bar dated D → D. A DAILY market
  cap dated D → D. An ACTIONS row → its action date. A listing event → its event
  date. An EVENTS row → the next NYSE session after the filing date, or the filing
  date when acceptance is known to be before 16:00 ET. An hourly kline → its close
  time. Vendor `lastupdated` is kept as metadata and never used.

### Tables (issue 16 is authoritative for the columns; this is the contract)

| Table | Key | Content |
| --- | --- | --- |
| `snapshots` | `snapshot_id` | Created at, file count, the snapshot document from `ingest/fetch/snapshot.py` |
| `calendar` | `(calendar, date)` | `nyse` (dates on which SEP carries any bar) and `utc` (every UTC day). Lanes map to calendars: `smallcap`, `discovered` → `nyse`; `crypto` → `utc` |
| `symbols` | `(market, symbol, snapshot_id)` | Ticker, name, category, exchange, sector (TICKERS; `sector` is the one allowlisted non-point-in-time input, spec/04). For crypto: base, quote |
| `bars_daily` | `(market, symbol, date, snapshot_id)` | Unadjusted `open, high, low, close, volume` (SEP OHLV imputed as `x × closeunadj / close`). Vendor `close` and `closeadj` kept for audit. `dollar_volume` (unadjusted close × volume, or kline quote volume) |
| `bars_hourly` | `(market, symbol, ts, snapshot_id)` | Crypto 1h klines: open time (UTC), OHLCV, quote volume. `available_at` = close time |
| `actions` | `(market, symbol, date, action, snapshot_id)` | Splits (factor), cash dividends (amount), ticker changes, spinoffs. Never merges or splits a permaticker |
| `listing` | `(market, symbol, event, date, snapshot_id)` | `listed` / `delisted` events from ACTIONS, with TICKERS first/last price date as fallback; crypto from first/last 1d kline. `reason` = ACTIONS action type; `exchange` at delisting (for the haircut class) |
| `marketcap` | `(market, symbol, date, snapshot_id)` | Sharadar DAILY `marketcap` |
| `events` | `(market, symbol, filing_date, snapshot_id)` | Sharadar EVENTS `eventcodes` |
| `lane_membership` | `(lane, market, symbol, date, snapshot_id)` | Derived by the universe builder, with the screen values that admitted the name |

### Read paths

- `harness.store.reader.AsOfReader(store, snapshot_id)`
  - `bars(market, symbols, start, end, as_of, adjust)`. A single-date read is
    `start = end = as_of`. `adjust` ∈ {`none`, `split`, `split_div`}.
  - `panel(lane, era, as_of)`: the one windowed read per (lane, era) that the
    feature builder uses. The `available_at <= :as_of` filter is inside the SQL.
  - `listed(market, date)`, `marketcap(...)`, `events(...)`, `calendar(lane, start, end)`.
  - Every method takes `as_of` and the SQL filters `available_at <= :as_of`. The
    store leakage test (issue 16) asserts this on every table and both paths.
- `harness.store.oracle.OracleReader(store, snapshot_id, era, unlock)`: the
  future-aware read, for the labeler only. Every read is bounded by the era's last
  trading day, and it refuses to read into the holdout unless the logged unlock is
  present (spec/03 Era boundaries).

### Adjustment

Prices are stored unadjusted. As-of D, a bar dated t < D is multiplied by the
product of the factors of actions with t < action date ≤ D. Actions dated after D
are never applied (spec/02).

Two consequences shape the design:

1. **Features can use one panel adjusted as-of the panel end.** For any D inside
   the panel, the panel-end series equals the as-of-D series times a constant C_D
   on every bar t ≤ D. All fourteen spec/04 features are scale-invariant (returns,
   ratios, ranks, `close_loc`). Issue 8 must include a test that multiplies every
   bar before D by a constant and shows every feature is unchanged. Any future
   feature that is not scale-invariant must be computed per as-of date.
2. **The labeler works in the entry's as-of-D basis.** The target level (mean of
   the 20 closes ending at D) and the hard stop (fill − 1.5 × D's range) are price
   levels fixed at entry. The labeler reads bars t > D through the oracle and
   converts them into D's basis by dividing by the factors of actions in (D, t].
   The share count scales with a split. This is what makes the exit-invariance
   test (issue 18) meaningful. Open question to the PM: the spec does not say how a
   split during an open position is treated; this is the proposed reading.

### Raw files, snapshots and reproduction

- `PENUMBRA_DATA_ROOT` holds `raw/`, `manifests/` and `snapshots/` (layout in
  `docs/ingest-data.md`, from PR 19). Raw files are never modified in place. A
  vendor restatement lands beside the old version (PR 19 review, item 1).
- A snapshot names exactly the files one store build reads: Binance klines and one
  export per Sharadar table. yfinance is excluded. The snapshot id is SHA-256 over
  the canonical JSON of (path, size, SHA-256) per file (spec/02).
- Where a monthly Binance file and daily files cover the same month, the loader
  (issue 4) prefers the monthly rows and dedupes on (symbol, date).
- `python -m harness.runrecord reproduce <snapshot_id>` (issue 17) rebuilds the
  store from that snapshot's files after verifying their hashes, and never fetches.

## Runs

- **Configuration hash** (spec/03): SHA-256 over the canonical JSON (sorted keys, no
  whitespace, decimals as strings) of `config/params.py`, the era bounds, the
  benchmark seed scheme, the stress cases, the control definitions and the code
  commit. A dirty working tree is refused for anything but a dev run, and the dirty
  flag is recorded.
- **Run log**: `PENUMBRA_DATA_ROOT/runs/<run_id>.json`, plus the append-only
  `runs/index.jsonl`. One record per run, including each control, each diagnostic
  variant and the benchmark: lane, era, kind, configuration hash, snapshot id,
  timestamp, the leakage-suite status for the commit, the unlock flag, and for
  validation runs, the count of distinct dev configuration hashes for the lane.
- **Gate** (`harness/guards.py`): before writing results, a run checks that the
  leakage suite (`pytest -m leakage`) passed on the same commit and refuses
  otherwise (spec/02 Leakage tests).
- **Holdout**: equities from 2024-01-01, crypto from 2025-01-01. It is readable only
  with `--unlock-holdout --holdout-end <date>`, which is written to the run record
  before any read. No environment variable unlocks it.
- **Pre-registration**: `research_log/<date>-<slug>.md` is committed before the run.
  The run record names the commit that holds it.

## Testing

- `pytest -q` runs everything in CI (`.github/workflows/tests.yml`) on every pull
  request and on `main`.
- Marker `leakage` (registered in `pytest.ini`) covers the store leakage test, feature invariance and exit
  invariance (spec/02). The run gate checks these.
- Tests run on synthetic data and vendor-shaped fixtures (`tests/fixtures/`). No
  test touches the network. No Sharadar key exists yet, so Sharadar paths are
  tested against fixtures in the vendor's published column layout, and the PR says
  so.

## Legacy baseline

PR 14 (the news-project harness migrated from `waviisoft/penumbra`) was merged as
PR 20 without its data artifacts, then moved under `legacy/`. Why merge it rather
than rebuild from nothing:

- `spec/07` keeps the day-of-week dummy as a plumbing test, and issues 1 and 2 are
  written against that code.
- The free-data screen branch is based on it.
- The store, the quarantine tests and the labeler are working patterns that the new
  modules follow.

The legacy code contradicts the spec in its keys (ticker instead of permaticker),
its availability model (`knowledge_date`), its adjustment (pre-adjusted close), its
calendar (inferred from price rows), its eras (2015/2021/2023), its universe (50
large caps), its label (a thresholded excess return, not a realized exit), its
model (logistic regression; the spec has no ML in v1), its costs (flat), its
benchmark (unmatched) and its statistic (per-trade z). None of that is patched.
Each is replaced by the spec-built module that owns it, and `legacy/` stays frozen
apart from issue 2's configuration change. Once the spec harness can run the
day-of-week dummy through its own pipeline, `legacy/` is deleted.

## Build order

```
wave 1 (parallel):  2 config · 16 store schema · 17 eras + run record · 18 invariance framework + gate
                    PR 19 fetcher (fixes)
wave 2:             3 Sharadar ingest (fixtures) · 5 listing + adjustment · 4 Binance ingest (if crypto survives 15)
wave 3:             6 universe · 8 features · 9 labeler
wave 4:             7 costs · 10 strategy + benchmark · 11 evaluator + controls
wave 5:             1 legacy control on real prices (any time after 2 and 17) · 12 dev run · 13 validation run
```

Issue 15 (the screen) runs outside this order. A null on the klines removes the
crypto lane by spec change: issue 4 and every crypto branch are dropped. A null on
equities stops the equity build.

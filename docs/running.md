# Running

How a run is identified, recorded and looked back up. See `docs/architecture.md`
("Runs") for how this fits the rest of the harness, and `spec/03-eras-and-holdout.md`
("Run record") for the contract this implements.

## What identifies a run

A run is `(lane, era, configuration hash, snapshot id)`. Lane and era come from
`config/eras.py`. The snapshot id is the fetcher's manifest hash (PR 19, in
review) and is out of scope here; the fields below carry it as an opaque
string until the store (issue 16) and loaders (issues 3 and 4) are built.

## Configuration hash

`harness.runrecord.config_hash(lane, code_commit, params=None, eras=None)`
returns a SHA-256 hex digest over the canonical JSON (sorted keys, no
whitespace, `Decimal` values as strings) of:

- every locked parameter in `config/params.py` (spec/01, spec/05, spec/06 and
  spec/07: universe thresholds, the strategy rule, both lanes' cost models,
  the three cost-stress cases, the label horizons and cohort-split threshold
  (spec/04, read by spec/07's diagnostics), the evaluation thresholds
  (including the regime-split proxy and window, and the mean-return
  confidence level) and the two control definitions), and
- the lane's era bounds (`config/eras.py`), and
- the code commit.

`config/params.py` also fixes a reading the spec leaves open: condition 5 of
the decision rule ("net return positive ... in each half of the era") does not
say how the era is split. `EvaluationParams.era_half_split` records the
reading this harness uses (`trading_day_midpoint`: the era's lane trading days
in date order, split at the midpoint by count) and is itself part of the
hash, so a later change to the reading is visible. This is a proposed reading
for the PM to confirm, not a locked spec value.

`params` and `eras` default to the real values (`config.params.ALL_LOCKED_PARAMS`
and this lane's `dev`/`validation`/`holdout` bounds) and are only overridden in
tests, to check that perturbing one field changes the hash.

Because every field above is locked — changed only by a spec change with a
decision-log entry (`spec/DECISIONS.md`, "Parameters re-locked") — two runs of
the same code commit produce the same hash, and a run's hash changes the
moment any locked parameter, an era bound, or the commit itself changes. That
is what makes the dev-hash count below meaningful: it is not "how many times
did this run", it is "how many distinct configurations were tried".

```
python -m harness.runrecord hash --lane smallcap
```

prints the hash for the current checkout's `HEAD`.

## The run record

`harness.runrecord.RunLog(root_url)` writes one JSON record per run to
`<root_url>/runs/<run_id>.json`, via `fsspec` — `root_url` can be a local path,
a mounted volume, or `s3://...`. Listing (`list()`, and the dev-hash count
below) is derived from a glob over `runs/*.json` rather than a maintained
index file: `s3fs` has no append semantics for S3 objects, and one JSON file
per run already carries everything an index would. The CLI reads the root
through `config.env.data_root()` (`PENUMBRA_DATA_ROOT`).

A record carries:

| Field | Meaning |
| --- | --- |
| `run_id` | Opaque id, generated unless supplied |
| `lane`, `era` | `config/eras.py` |
| `kind` | One of `primary`, `placebo`, `positive_control`, `capped`, `close_fill`, `benchmark`, `plumbing`, `screen` |
| `configuration_hash` | See above |
| `snapshot_id` | The ingest snapshot the run read (opaque here; see "What identifies a run") |
| `code_commit`, `dirty` | `harness.runrecord.code_commit()`: the git HEAD this run built, and whether the tree had uncommitted changes |
| `timestamp` | UTC, ISO 8601 |
| `leakage_gate_status` | Carried as a field only; issue 18's `harness/guards.py` sets it before any result is written |
| `holdout_unlocked`, `holdout_end` | The holdout unlock flag and the fixed holdout end date (below) |
| `seeds` | The seed(s) used (e.g. a control's fixed seed, or the benchmark draw seeds) |
| `research_log_entry` | Path to the pre-registration entry under `research_log/` that was committed before the run |
| `dev_config_hashes_before` | Validation runs only: the count of distinct configuration hashes previously run in dev for this lane, excluding controls and diagnostics (a control or diagnostic always shares its paired primary run's hash, so it never adds a distinct one) |

A record is written for every run kind, including each control, each
diagnostic variant and the benchmark (`docs/architecture.md`, "Runs").

### Refusals

- **Holdout without unlock.** `RunLog.record(era="holdout", ...)` raises unless
  both `holdout_unlocked=True` and a `holdout_end` date are given. There is no
  environment variable that unlocks the holdout; the flag and the date are
  arguments the caller must supply explicitly, and once supplied they are
  written to the record before anything else about the run.
- **Dirty tree outside dev.** `RunLog.record(era="validation" | "holdout", ...)`
  raises if `commit.dirty` is true. A dev run may be dirty; the flag is simply
  recorded.

## The dev configuration-hash count

`spec/03` ("Use of eras"): "the number of distinct configuration hashes run in
dev for that lane is reported next to the validation result." A validation
record's `dev_config_hashes_before` is computed at record time from the
existing `runs/*.json` files: every prior `dev`-era record for the same lane
whose kind is not a control or diagnostic (`placebo`, `positive_control`,
`capped`, `close_fill`, `benchmark`) contributes its `configuration_hash` to
the set; the field is the size of that set.

## CLI

```
python -m harness.runrecord hash --lane <smallcap|discovered|crypto>
python -m harness.runrecord list [--lane <lane>] [--era <dev|validation|holdout>]
python -m harness.runrecord show <run_id>
```

`list` and `show` read `PENUMBRA_DATA_ROOT` through `config.env.data_root()`;
`hash` does not (it only needs the checkout's git HEAD).

## Reproduce from a snapshot (owed)

`docs/architecture.md` names `python -m harness.runrecord reproduce
<snapshot_id>`: rebuild the store from a named snapshot's raw files, after
verifying their hashes, and never fetch. This needs the fetcher (PR 19, in
review), the point-in-time store (issue 16, in parallel) and the Sharadar and
Binance loaders (issues 3 and 4), none of which exist yet in this checkout.
Part of #17; the PA is tracking the remainder once those land.

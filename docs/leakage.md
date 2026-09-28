# Leakage tests and the gate

spec/02 "Leakage tests": three tests run in CI, and a harness that fails any
of them does not write results.

- **Store**: an as-of read at date D returns no row with `available_at` after
  D, on every table and both read paths (issue 16).
- **Feature invariance**: for a sample of (lane, name, D), every feature and
  flag value at D is unchanged when every bar and event dated after D is
  perturbed or deleted.
- **Exit invariance**: for a sample of positions filled on D+1, the target
  level and the hard-stop level are unchanged when every bar dated D+1 and
  later is perturbed.

All three are marked `leakage` in `pytest.ini` and run as part of `pytest -q`.
Run only this suite with:

```
pytest -m leakage -q
```

## The invariance machinery

Feature and exit invariance share one generic mechanism,
`harness/testing/invariance.py`:

- `perturbations(bars, events, D, rng)` yields four named variants of the
  input (`deleted`, `multiplied`, `shocked`, `shuffled`), each touching only
  what is dated after D.
- `assert_feature_invariance(compute, bars, events, samples, rng)` calls
  `compute(bars, events, D) -> Mapping[str, value]` once per sample D against
  every perturbed variant and asserts every value is bit-exact and NaN-aware
  unchanged.
- `assert_exit_invariance(levels, bars, fills, rng)` does the same for
  `levels(bars, position) -> (target, stop)`, holding the fill bar's open
  fixed (see the docstring for why).

`harness/features.py` (issue 8) and `harness/labels.py` (issues 9, 10) do not
exist yet. `tests/invariance/` proves this machinery against small reference
implementations written only in the test module, plus deliberately broken
mutants that must fail (a `center=True` rolling window; a hard-stop range
taken from the fill day; and others). **Issues 8, 9 and 10 must call
`assert_feature_invariance` and `assert_exit_invariance` on their own,
real modules** — the tests here do not exercise production code.

## The gate

`harness/guards.py` is the run gate: before anything writes results, it
checks that the leakage suite passed on the current commit.

```
python -m harness.guards check
```

Runs `pytest -m leakage -q` in a subprocess and writes a record to
`$PENUMBRA_DATA_ROOT/runs/leakage/<commit>.json`: the commit, whether the
working tree was dirty, whether the suite passed, how many tests were
collected, and a timestamp. `PENUMBRA_DATA_ROOT` is read directly from the
environment for now (issue 2's `config/env.py` will centralize this).

Anything that writes results calls:

```python
from harness.guards import require_leakage_passed

require_leakage_passed(data_root_url, commit)
```

which raises `LeakageGateError` unless a record for exactly that commit
exists, is a pass, was taken on a clean tree, and collected at least one
test — zero collected is a failure, not a pass.

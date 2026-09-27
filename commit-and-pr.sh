#!/usr/bin/env bash
# Run from the root of andyvanosdale/penumbra after migrating the harness code and copying the files in.
set -euo pipefail
git checkout -b chore/repo-split
git add -A
git commit -m "Migrate harness from waviisoft/penumbra; add docs index and issue templates

Brings the existing point-in-time store, feature builder, quarantined
labeler, walk-forward backtester, evaluator, and leakage tests into this
repo. Retires docs/roadmap.md (now epics in penumbra-specs). Adds the docs
index and the product issues that bring the code up to the v1 spec."
git push -u origin chore/repo-split
gh pr create \
  --title "Migrate harness and add v1 issue set" \
  --body "$(cat <<'BODY'
## What changed

- Harness code moved from `waviisoft/penumbra`, unchanged.
- `docs/roadmap.md` removed; roadmap items are epics in `andyvanosdale/penumbra-specs`.
- `docs/README.md` indexes the runbooks the v1 issues owe.
- `issues/` holds thirteen issue templates in build order; `create-issues.sh` creates them.

## Spec

Implements `andyvanosdale/penumbra-specs` at the v1 spec PR. Each issue cites its spec section and its acceptance criteria are the gate.

## After merge

Run `./create-issues.sh`, then open the product manager and product architect sessions against this repo.
BODY
)"

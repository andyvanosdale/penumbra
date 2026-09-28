"""Legacy news-project harness, migrated unchanged from waviisoft/penumbra.

Kept for one purpose: the day-of-week plumbing test (spec/07 Controls: "The
day-of-week dummy from the earlier harness is kept as a plumbing test and is not
a control"), run by ``python -m legacy.dummy_feature`` (issues 1 and 2).

Nothing outside ``legacy/`` and ``tests/legacy/`` may import from here. The
spec-built harness lives in ``harness/`` and ``ingest/``; see
docs/architecture.md ("Legacy baseline").

    python -m legacy.make_synthetic     # or legacy.pull_prices (network)
    python -m legacy.load_to_store
    python -m legacy.dummy_feature
"""

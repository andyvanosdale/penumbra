# docs

Technical documentation for running Penumbra. Kept current by whoever changes the
thing documented.

- `architecture.md` — components, interfaces, store schema, spec-to-module map, build status and order
- `environment.md` — every environment variable, its purpose, and an example value
- `ingest-data.md` — fetching raw vendor files into a local, volume or S3 root
- `ingest-sharadar.md` — loading Sharadar tables into the store
- `ingest-binance.md` — loading Binance public data into the store
- `store.md` — table layout, `available_at` semantics, as-of adjustment, read paths
- `features.md` — the feature builder: formulas as implemented, window alignment, NaN rules, tie handling, the `eligible` parameter
- `running.md` — running a backtest, the run record, reproducing from a snapshot, the holdout unlock

Files not yet present are owed by the issue that introduces the component
(`architecture.md`, "Packages and ownership").

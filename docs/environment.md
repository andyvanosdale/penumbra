# Environment variables

Nothing in the codebase assumes a machine, user directory or network location
(`spec/02-data.md`, Configuration). Everything below is read from the environment,
in one place: `config/env.py`.

| Variable | Purpose | Required by | Example |
| --- | --- | --- | --- |
| `PENUMBRA_DATA_ROOT` | Storage root for raw files, manifests and snapshots: a directory, a mounted volume, or an S3-compatible URL | Always | `/mnt/penumbra` or `s3://bucket/penumbra` |
| `PENUMBRA_STORE_PATH` | Path to the SQLite point-in-time store: a local or volume path, never a URL | Always | `/mnt/penumbra/store.sqlite` |
| `PENUMBRA_S3_ENDPOINT` | Endpoint for S3-compatible object stores (MinIO, R2, Backblaze). Omit for AWS | Only when `PENUMBRA_DATA_ROOT` is an S3-compatible URL not on AWS | `https://s3.us-west-002.backblazeb2.com` |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION` | Credentials for an `s3://` root, read by s3fs | Only when `PENUMBRA_DATA_ROOT` is `s3://...` | |
| `NASDAQ_DATA_LINK_API_KEY` | Sharadar bulk exports | Sharadar ingest only (not needed for anything else) | |

The legacy plumbing pipeline (`legacy/make_synthetic.py`, `legacy/pull_prices.py`,
`legacy/load_to_store.py`, `legacy/dummy_feature.py`) requires `PENUMBRA_DATA_ROOT`
to be a local path, not a URL: it writes its raw snapshot and its own SQLite file
under `$PENUMBRA_DATA_ROOT/legacy/`.

Variables owned by later issues (the holdout unlock flag) are added here by the
issue that introduces them.

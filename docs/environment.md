# Environment variables

Nothing in the codebase assumes a machine, user directory or network location
(`spec/02-data.md`, Configuration). Everything below is read from the environment.

| Variable | Purpose | Example |
| --- | --- | --- |
| `PENUMBRA_DATA_ROOT` | Storage root for raw files, manifests and snapshots: a directory, a mounted volume, or an S3-compatible URL | `/mnt/penumbra` or `s3://bucket/penumbra` |
| `PENUMBRA_S3_ENDPOINT` | Endpoint for S3-compatible object stores (MinIO, R2, Backblaze). Omit for AWS | `https://s3.us-west-002.backblazeb2.com` |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION` | Credentials for an `s3://` root, read by s3fs | |
| `NASDAQ_DATA_LINK_API_KEY` | Sharadar bulk exports | |

Variables owned by later issues (store path, holdout unlock flag) are added here
by the issue that introduces them.

"""The one place Penumbra reads environment variables (spec/02-data.md, Configuration).

Nothing in the codebase assumes a particular machine, user directory or network
location: every path and credential comes from here. A required variable that is
missing raises `MissingEnvVar`, naming the variable and pointing to
`docs/environment.md`, which lists every variable, its purpose and an example.

AWS credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`)
are read directly by s3fs when `PENUMBRA_DATA_ROOT` is an `s3://` URL. They are
documented in `docs/environment.md` but have no accessor here: wrapping them would
just be one more place to keep in sync with s3fs's own names.
"""

from __future__ import annotations

import os
from pathlib import Path

ENV_DOC = "docs/environment.md"


class MissingEnvVar(RuntimeError):
    """A required environment variable was not set."""

    def __init__(self, name: str):
        super().__init__(f"{name} is not set. See {ENV_DOC} for what it should hold.")


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise MissingEnvVar(name)
    return value


def data_root() -> str:
    """Storage root for raw files, manifests, snapshots and the run log.

    A local or mounted-volume path, or an fsspec URL such as `s3://bucket/prefix`.
    Required. Set via `PENUMBRA_DATA_ROOT`.
    """
    return _require("PENUMBRA_DATA_ROOT")


def is_local_root(root: str) -> bool:
    """True if `root` is a local path rather than a URL (e.g. `s3://...`)."""
    return "://" not in root


def legacy_data_root() -> Path:
    """Local directory for the legacy pipeline's raw snapshot and SQLite store.

    Always `<PENUMBRA_DATA_ROOT>/legacy`. The legacy pipeline writes straight to
    the filesystem and has no fsspec support, so it requires a local (non-URL)
    data root; a URL root such as `s3://...` raises `ValueError`.
    """
    root = data_root()
    if not is_local_root(root):
        raise ValueError(
            f"the legacy pipeline requires a local PENUMBRA_DATA_ROOT, got a URL: "
            f"{root!r}. See {ENV_DOC}."
        )
    return Path(root) / "legacy"


def store_path() -> Path:
    """Path to the SQLite point-in-time store.

    A local or volume path, never a URL. Required. Set via `PENUMBRA_STORE_PATH`.
    """
    return Path(_require("PENUMBRA_STORE_PATH"))


def s3_endpoint() -> str | None:
    """Endpoint URL for an S3-compatible object store (MinIO, R2, Backblaze, ...).

    Optional; omit for AWS. Set via `PENUMBRA_S3_ENDPOINT`.
    """
    return os.environ.get("PENUMBRA_S3_ENDPOINT") or None


def nasdaq_data_link_api_key() -> str:
    """API key for Nasdaq Data Link (Sharadar bulk exports).

    Not needed until Sharadar ingest runs, so most code never calls this. Set via
    `NASDAQ_DATA_LINK_API_KEY`. The value is never logged and never appears in a
    `repr` or an error message; only its name does.
    """
    return _require("NASDAQ_DATA_LINK_API_KEY")

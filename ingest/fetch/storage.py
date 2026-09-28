"""Storage abstraction over fsspec.

One object, one root. Everything under the root is addressed by a relative
POSIX path. Writes are atomic at the file level: the payload lands in a ``.part``
sibling and is moved into place only after it is complete and (where the source
provides one) its checksum verified. A crash mid-download therefore never
leaves a file that later runs would mistake for a finished one.
"""

from __future__ import annotations

import hashlib
import json
import os
import posixpath
from typing import BinaryIO, Iterator

import fsspec


class Storage:
    def __init__(self, root: str):
        root = root.rstrip("/")
        if "://" not in root:
            root = os.path.abspath(os.path.expanduser(root))
        self.root_url = root
        opts = {}
        if root.startswith("s3://"):
            endpoint = os.environ.get("PENUMBRA_S3_ENDPOINT") or os.environ.get("AWS_ENDPOINT_URL")
            if endpoint:
                opts["client_kwargs"] = {"endpoint_url": endpoint}
        self.fs, self.base = fsspec.core.url_to_fs(root, **opts)
        self.base = self.base.rstrip("/")

    # -- paths -------------------------------------------------------------
    def full(self, rel: str) -> str:
        rel = rel.strip("/")
        return f"{self.base}/{rel}" if rel else self.base

    def exists(self, rel: str) -> bool:
        return self.fs.exists(self.full(rel))

    def size(self, rel: str) -> int | None:
        try:
            return int(self.fs.size(self.full(rel)))
        except FileNotFoundError:
            return None

    def sizes(self, rel: str) -> dict[str, int]:
        """One listing call: {relative path: size} for every file under ``rel``.
        Lets a manifest check presence without one HEAD request per file."""
        p = self.full(rel)
        if not self.fs.exists(p):
            return {}
        out = {}
        for full, info in self.fs.find(p, detail=True).items():
            if info.get("type", "file") == "file":
                out[full[len(self.base) + 1:]] = int(info.get("size", 0))
        return out

    def listdir(self, rel: str) -> list[str]:
        p = self.full(rel)
        if not self.fs.exists(p):
            return []
        return sorted(posixpath.basename(x.rstrip("/")) for x in self.fs.ls(p, detail=False))

    def walk(self, rel: str) -> Iterator[str]:
        p = self.full(rel)
        if not self.fs.exists(p):
            return
        for dirpath, _dirs, files in self.fs.walk(p):
            for f in files:
                full = f"{dirpath.rstrip('/')}/{f}"
                yield full[len(self.base) + 1:]

    # -- io ------------------------------------------------------------------
    def read_bytes(self, rel: str) -> bytes:
        with self.fs.open(self.full(rel), "rb") as fh:
            return fh.read()

    def read_text(self, rel: str) -> str:
        return self.read_bytes(rel).decode("utf-8")

    def read_json(self, rel: str, default=None):
        if not self.exists(rel):
            return default
        return json.loads(self.read_text(rel))

    def write_json(self, rel: str, obj) -> None:
        self.write_bytes(rel, json.dumps(obj, indent=2, sort_keys=True).encode("utf-8"))

    def write_bytes(self, rel: str, data: bytes) -> None:
        with self.open_atomic(rel) as w:
            w.write(data)
            w.commit()

    def open_atomic(self, rel: str) -> "AtomicWriter":
        return AtomicWriter(self, rel)

    def remove(self, rel: str) -> None:
        p = self.full(rel)
        if self.fs.exists(p):
            self.fs.rm(p)

    def sha256(self, rel: str) -> str:
        h = hashlib.sha256()
        with self.fs.open(self.full(rel), "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()


class AtomicWriter:
    """Context manager: stream into ``<path>.part``; ``commit()`` moves it into
    place. Leaving the ``with`` block without ``commit()`` discards the part."""

    def __init__(self, storage: Storage, rel: str):
        self.storage = storage
        self.rel = rel
        self.part = rel + ".part"
        self._fh: BinaryIO | None = None
        self._hash = hashlib.sha256()
        self.size = 0
        self._committed = False

    def __enter__(self):
        fs = self.storage.fs
        parent = posixpath.dirname(self.storage.full(self.rel))
        fs.makedirs(parent, exist_ok=True)
        self._fh = fs.open(self.storage.full(self.part), "wb")
        return self

    def write(self, data: bytes) -> None:
        self._fh.write(data)
        self._hash.update(data)
        self.size += len(data)

    def commit(self) -> None:
        if self._fh and not self._fh.closed:
            self._fh.close()
        fs = self.storage.fs
        src, dst = self.storage.full(self.part), self.storage.full(self.rel)
        if getattr(fs, "protocol", None) in ("file", ("file", "local"), "local"):
            os.replace(src, dst)            # atomic on a local root or a mounted volume
        else:
            fs.mv(src, dst)                 # object stores: copy then delete; never a rm first
        self._committed = True

    @property
    def sha256(self) -> str:
        return self._hash.hexdigest()

    def __exit__(self, exc_type, exc, tb):
        if self._fh and not self._fh.closed:
            self._fh.close()
        if not self._committed:
            self.storage.remove(self.part)
        return False

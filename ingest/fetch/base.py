"""Source plug-in contract and registry.

A source turns "what should be in the store" into a list of ``Task`` objects
(one per file) and knows how to fetch one. The runner does the rest: skipping
tasks the manifest already has, downloading with retries, recording results,
and saving the manifest. To add a source, subclass ``Source``, implement
``plan`` and ``fetch``, and decorate with ``@register``.
"""

from __future__ import annotations

import argparse
import dataclasses
import logging
from typing import Any, Callable, Iterable

from .manifest import Manifest
from .storage import Storage

log = logging.getLogger("penumbra.fetch")


@dataclasses.dataclass
class Task:
    rel: str                       # path under the storage root
    version: str | None = None     # vendor identifier for this version (etag, snapshot time, ...)
    size: int | None = None        # expected size when the vendor lists one
    sha256: str | None = None      # expected sha256 when the vendor publishes one
    meta: dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class Result:
    planned: int = 0
    skipped: int = 0
    fetched: int = 0
    failed: int = 0
    bytes: int = 0
    errors: list[str] = dataclasses.field(default_factory=list)


class Source:
    name: str = ""
    help: str = ""

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Source-specific CLI options."""

    def plan(self, storage: Storage, manifest: Manifest, args: argparse.Namespace) -> Iterable[Task]:
        raise NotImplementedError

    def fetch(self, task: Task, storage: Storage, args: argparse.Namespace) -> tuple[int, str]:
        """Fetch one task into storage. Returns (size, sha256)."""
        raise NotImplementedError

    def should_skip(self, task: Task, manifest: Manifest) -> bool:
        return manifest.has(task.rel, size=task.size, version=task.version)

    def run(self, storage: Storage, args: argparse.Namespace,
            progress: Callable[[str], None] | None = None) -> Result:
        manifest = Manifest(storage, self.name)
        res = Result()
        try:
            for task in self.plan(storage, manifest, args):
                res.planned += 1
                if self.should_skip(task, manifest):
                    res.skipped += 1
                    continue
                if getattr(args, "dry_run", False):
                    log.info("would fetch %s", task.rel)
                    continue
                try:
                    size, digest = self.fetch(task, storage, args)
                except Exception as exc:  # one bad file must not stop the run
                    res.failed += 1
                    res.errors.append(f"{task.rel}: {exc}")
                    log.warning("failed %s: %s", task.rel, exc)
                    continue
                manifest.record(task.rel, size=size, sha256=digest, version=task.version, **task.meta)
                res.fetched += 1
                res.bytes += size
                if progress:
                    progress(task.rel)
                if res.fetched % 50 == 0:
                    manifest.save()
        finally:
            manifest.save()
        return res


REGISTRY: dict[str, Source] = {}


def register(cls):
    inst = cls()
    if not inst.name:
        raise ValueError(f"{cls.__name__} has no name")
    REGISTRY[inst.name] = inst
    return cls

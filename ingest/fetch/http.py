"""HTTP with retries and streaming download into storage."""

from __future__ import annotations

import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .storage import Storage

USER_AGENT = "penumbra-fetch/1.0"


def redact(text: str, secrets: list[str | None]) -> str:
    """Blank every secret out of a message before it reaches a log or traceback."""
    for sec in secrets:
        if sec:
            text = text.replace(sec, "***")
    return text


class RedactedError(RuntimeError):
    """An HTTP failure whose message has had credentials removed."""


def get_json(sess: requests.Session, url: str, *, params: dict, secrets: list[str | None],
             timeout: int = 120) -> dict:
    """GET and parse JSON; any failure surfaces with ``secrets`` redacted."""
    try:
        r = sess.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as exc:  # requests errors carry the full URL, query string included
        raise RedactedError(redact(f"{type(exc).__name__}: {exc}", secrets)) from None


def session(total: int = 5) -> requests.Session:
    s = requests.Session()
    retry = Retry(total=total, backoff_factor=1.0,
                  status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=frozenset({"GET", "HEAD"}))
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://", HTTPAdapter(max_retries=retry))
    s.headers["User-Agent"] = USER_AGENT
    return s


def download(sess: requests.Session, url: str, storage: Storage, rel: str,
             *, expect_sha256: str | None = None, timeout: int = 120) -> tuple[int, str]:
    """Stream ``url`` into ``rel``. Returns (size, sha256). Raises on checksum
    mismatch, leaving no file behind."""
    attempts = 0
    while True:
        attempts += 1
        with sess.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            with storage.open_atomic(rel) as w:
                for chunk in r.iter_content(chunk_size=1 << 20):
                    if chunk:
                        w.write(chunk)
                if expect_sha256 and w.sha256 != expect_sha256:
                    if attempts < 3:
                        time.sleep(2 * attempts)
                        continue
                    raise IOError(f"checksum mismatch for {url}: got {w.sha256}, expected {expect_sha256}")
                w.commit()
                return w.size, w.sha256

"""Module-boundary rules from docs/architecture.md, checked statically.

- Nothing outside legacy/ and tests/legacy/ imports the legacy harness.
- Only the labeler (harness/labels.py) and the backtester (harness/backtest.py)
  may import the future-aware store read path (harness.store.oracle), and only the
  backtester may import the labeler (spec/04: the labeler is quarantined and its
  output is joined to features only inside the backtester).
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE_DIRS = ("harness", "ingest", "config", "experiments")


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            mods.add(node.module)
            mods.update(f"{node.module}.{a.name}" for a in node.names)
    return mods


def _files():
    for d in CODE_DIRS:
        yield from (ROOT / d).rglob("*.py") if (ROOT / d).exists() else ()


def test_nothing_outside_legacy_imports_legacy():
    offenders = [str(p.relative_to(ROOT)) for p in _files()
                 if any(m == "legacy" or m.startswith("legacy.") for m in _imports(p))]
    assert not offenders, f"imports legacy/: {offenders}"


def test_oracle_and_labeler_are_quarantined():
    allowed_oracle = {"harness/labels.py", "harness/backtest.py"}
    allowed_labeler = {"harness/backtest.py"}
    bad = []
    for p in _files():
        rel = str(p.relative_to(ROOT))
        mods = _imports(p)
        if rel not in allowed_oracle and any(m.startswith("harness.store.oracle") for m in mods):
            bad.append(f"{rel} imports harness.store.oracle")
        if rel not in allowed_labeler and rel != "harness/labels.py" and any(
                m == "harness.labels" or m.startswith("harness.labels.") for m in mods):
            bad.append(f"{rel} imports harness.labels")
    assert not bad, bad

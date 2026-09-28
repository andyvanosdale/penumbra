"""Tests enforcing the feature/labeler quarantine (plan §3.2, §3.3).

The feature builder must never touch future data or the labeler. We check this
two ways: statically (source inspection) and dynamically (behavioural).
"""

import ast
import inspect

import pandas as pd

import legacy.features as features
from legacy.features import build_features
from legacy.store import PITStore


def _feature_source_tree():
    return ast.parse(inspect.getsource(features))


def _imported_modules(tree):
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module)
    return mods


def _attribute_names(tree):
    """Every attribute access name (e.g. the `foo` in `x.foo`). Ignores strings,
    docstrings and comments, so describing forbidden calls in prose is fine."""
    return {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}


def _store():
    store = PITStore(":memory:")
    store.write_prices(pd.DataFrame({
        "ticker": ["AAPL", "AAPL"],
        "date": ["2020-01-06", "2020-01-07"],   # Mon, Tue
        "open": [10, 11], "high": [11, 12], "low": [9, 10],
        "close": [10.5, 11.5], "adj_close": [10.5, 11.5],
        "volume": [1e6, 1e6],
    }))
    return store


def test_features_module_does_not_import_labeler():
    mods = _imported_modules(_feature_source_tree())
    assert not any("labels" in m for m in mods), \
        f"features.py must not import the labeler (quarantine violation): {mods}"


def test_features_module_never_uses_oracle():
    """The future-aware read path must never be CALLED in features.py.
    (Mentioning it in the docstring to warn future maintainers is fine.)"""
    attrs = _attribute_names(_feature_source_tree())
    assert "get_prices_oracle" not in attrs, \
        "features.py calls the oracle read path — lookahead risk."


def test_is_monday_feature_is_correct():
    store = _store()
    mon = build_features(store, "AAPL", "2020-01-06")   # Monday
    tue = build_features(store, "AAPL", "2020-01-07")   # Tuesday
    assert mon["is_monday"] == 1.0
    assert tue["is_monday"] == 0.0


def test_features_none_when_bar_not_known():
    store = _store()
    # No bar exists/knowable for this date -> feature must be None, not fabricated.
    assert build_features(store, "AAPL", "2019-12-31") is None


def test_build_features_only_reads_as_of(monkeypatch):
    """build_features must read via an as-of path with as_of == the decision date,
    and must NOT call the oracle. We spy on the store to prove it."""
    store = _store()
    calls = {"as_of": [], "oracle": 0}

    real_known_bar = store.known_bar
    real_oracle = store.get_prices_oracle

    def spy_known_bar(ticker, date, as_of, *a, **k):
        calls["as_of"].append(as_of)
        return real_known_bar(ticker, date, as_of, *a, **k)

    def spy_oracle(*a, **k):
        calls["oracle"] += 1
        return real_oracle(*a, **k)

    monkeypatch.setattr(store, "known_bar", spy_known_bar)
    monkeypatch.setattr(store, "get_prices_oracle", spy_oracle)

    build_features(store, "AAPL", "2020-01-07")
    assert calls["oracle"] == 0, "feature builder must never call the oracle"
    assert calls["as_of"] == ["2020-01-07"], \
        "feature builder must read as-of the decision date only"

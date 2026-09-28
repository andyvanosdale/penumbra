"""`filing_2d` (spec/04 Flags; equities only).

True when an EVENTS row's `available_at` (as the store holds it — never
recomputed from the filing date) falls on D-1 or D-2 lane trading days.
"""

from __future__ import annotations

from harness.features import build_features
from harness.store import AsOfReader
from tests.fixtures.features import all_eligible, build_equity_store, flat_bar, nyse_sessions


def _flat_panel(dates: list[str]) -> dict[str, dict]:
    return {d: flat_bar(100.0 + i) for i, d in enumerate(dates)}


def test_filing_2d_true_on_D_minus_1_and_D_minus_2():
    dates = nyse_sessions(5)
    d_minus_2, d_minus_1, d = dates[-3], dates[-2], dates[-1]

    conn = build_equity_store(
        {"A": _flat_panel(dates)},
        events=[dict(symbol="A", filing_date=d_minus_2, available_at=d_minus_2)])
    reader = AsOfReader(conn, "feat-a")
    out = build_features(reader, "smallcap", [d], eligible=all_eligible("A", [d]))
    assert bool(out.loc[0, "filing_2d"]) is True

    conn2 = build_equity_store(
        {"A": _flat_panel(dates)}, snapshot_id="feat-b",
        events=[dict(symbol="A", filing_date=d_minus_1, available_at=d_minus_1)])
    reader2 = AsOfReader(conn2, "feat-b")
    out2 = build_features(reader2, "smallcap", [d], eligible=all_eligible("A", [d]))
    assert bool(out2.loc[0, "filing_2d"]) is True


def test_filing_2d_false_outside_the_window_and_with_no_event():
    dates = nyse_sessions(5)
    d_minus_3, d = dates[-4], dates[-1]

    conn_none = build_equity_store({"A": _flat_panel(dates)})
    reader_none = AsOfReader(conn_none, "feat-a")
    out_none = build_features(reader_none, "smallcap", [d], eligible=all_eligible("A", [d]))
    assert bool(out_none.loc[0, "filing_2d"]) is False

    conn_far = build_equity_store(
        {"A": _flat_panel(dates)}, snapshot_id="feat-b",
        events=[dict(symbol="A", filing_date=d_minus_3, available_at=d_minus_3)])
    reader_far = AsOfReader(conn_far, "feat-b")
    out_far = build_features(reader_far, "smallcap", [d], eligible=all_eligible("A", [d]))
    assert bool(out_far.loc[0, "filing_2d"]) is False


def test_filing_2d_false_when_available_only_on_D_itself():
    dates = nyse_sessions(5)
    d = dates[-1]
    conn = build_equity_store(
        {"A": _flat_panel(dates)},
        events=[dict(symbol="A", filing_date=d, available_at=d)])
    reader = AsOfReader(conn, "feat-a")
    out = build_features(reader, "smallcap", [d], eligible=all_eligible("A", [d]))
    assert bool(out.loc[0, "filing_2d"]) is False

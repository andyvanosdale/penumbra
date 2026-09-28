"""`sector_rel_ret_1` (spec/04 Features; equities only).

Today's simple return minus the equal-weight today's return of all *eligible*
equities in the same sector, excluding the name itself.
"""

from __future__ import annotations

import pandas as pd
import pytest

from harness.features import FeatureError, build_features
from harness.store import AsOfReader
from tests.fixtures.features import all_eligible, build_equity_store, flat_bar, nyse_sessions


def _panel(prev_close: float, today_close: float, dates: list[str]) -> dict[str, dict]:
    return {dates[0]: flat_bar(prev_close), dates[1]: flat_bar(today_close)}


def test_sector_rel_ret_1_equal_weight_excluding_self():
    dates = nyse_sessions(2)
    # Sector "Tech": A +10%, B +0%, C -10%. Sector "Other": D +50% (must not
    # contaminate Tech's average).
    bars = {
        "A": _panel(100.0, 110.0, dates),
        "B": _panel(100.0, 100.0, dates),
        "C": _panel(100.0, 90.0, dates),
        "D": _panel(100.0, 150.0, dates),
    }
    sectors = {"A": "Tech", "B": "Tech", "C": "Tech", "D": "Other"}
    conn = build_equity_store(bars, sectors=sectors)
    reader = AsOfReader(conn, "feat-a")

    out = build_features(reader, "smallcap", [dates[-1]],
                        eligible=all_eligible(["A", "B", "C", "D"], [dates[-1]]))
    row = out.set_index("symbol")

    # A's peers are B (0%) and C (-10%): peer avg = -5%.
    assert row.loc["A", "sector_rel_ret_1"] == pytest.approx(0.10 - (-0.05))
    # B's peers are A (10%) and C (-10%): peer avg = 0%.
    assert row.loc["B", "sector_rel_ret_1"] == pytest.approx(0.0 - 0.0)
    # C's peers are A (10%) and B (0%): peer avg = 5%.
    assert row.loc["C", "sector_rel_ret_1"] == pytest.approx(-0.10 - 0.05)
    # D is alone in "Other": undefined.
    assert pd.isna(row.loc["D", "sector_rel_ret_1"])


def test_sector_rel_ret_1_respects_the_eligible_set():
    dates = nyse_sessions(2)
    bars = {
        "A": _panel(100.0, 110.0, dates),
        "B": _panel(100.0, 100.0, dates),
        "C": _panel(100.0, 90.0, dates),
    }
    sectors = {"A": "Tech", "B": "Tech", "C": "Tech"}
    conn = build_equity_store(bars, sectors=sectors)
    reader = AsOfReader(conn, "feat-a")

    # C is not eligible on D: A's only peer is B (0%).
    eligible = pd.DataFrame({"date": [dates[-1], dates[-1]], "symbol": ["A", "B"]})
    out = build_features(reader, "smallcap", [dates[-1]], eligible=eligible)
    row = out.set_index("symbol")
    assert row.loc["A", "sector_rel_ret_1"] == pytest.approx(0.10 - 0.0)
    # C is ineligible, so it is excluded from A and B's peer average, but it
    # still gets its own value, computed against its (eligible) peers A and B.
    assert row.loc["C", "sector_rel_ret_1"] == pytest.approx(-0.10 - 0.05)


def test_eligible_is_required_for_equity_lanes():
    dates = nyse_sessions(2)
    bars = {"A": _panel(100.0, 110.0, dates)}
    conn = build_equity_store(bars, sectors={"A": "Tech"})
    reader = AsOfReader(conn, "feat-a")

    for lane in ("smallcap", "discovered"):
        with pytest.raises(FeatureError, match="eligible"):
            build_features(reader, lane, [dates[-1]])


def test_sector_rel_ret_1_is_nan_for_crypto():
    from tests.fixtures.features import build_crypto_store, utc_sessions

    cdates = utc_sessions(2)
    bars = {"BTCUSDT": {cdates[0]: dict(open=100.0, high=101.0, low=99.0, close=100.0,
                                        volume=1.0, dollar_volume=100.0),
                       cdates[1]: dict(open=100.0, high=112.0, low=99.0, close=110.0,
                                       volume=1.0, dollar_volume=110.0)}}
    conn = build_crypto_store(bars)
    reader = AsOfReader(conn, "feat-a")

    out = build_features(reader, "crypto", [cdates[-1]])
    assert pd.isna(out.loc[0, "sector_rel_ret_1"])
    assert pd.isna(out.loc[0, "filing_2d"])

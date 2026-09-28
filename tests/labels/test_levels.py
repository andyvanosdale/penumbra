"""Entry levels from as-of data (harness/levels.py) and exit invariance on them
(spec/02 Leakage tests, "Exit invariance").

The invariance test drives the real `entry_levels` through a real store: each
perturbed bar frame from `harness.testing.invariance` is written to a fresh
store and read back through `AsOfReader`, so a level that reached any bar dated
after the signal day, by any path, would move.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from harness.levels import entry_levels, hard_stop_level
from harness.store import AsOfReader, build_nyse_calendar, connect, register_snapshot, upsert
from harness.testing import Position, assert_exit_invariance, sample_dates
from tests.fixtures.label_store import SNAPSHOT, flat, scenario_store, sessions_between
from tests.invariance._synth import build_panel

SYM = "100100"


def test_target_is_the_mean_of_20_closes_ending_at_D_and_range_is_Ds():
    sessions = sessions_between("2021-06-01", "2021-07-30")
    bars = {d: (100.0 + i, 101.0 + i, 99.0 + i, 100.0 + i) for i, d in enumerate(sessions)}
    D = sessions[30]
    bars[D] = (130.0, 134.0, 127.0, 130.0)
    conn = scenario_store(sessions, {SYM: bars})
    lv = entry_levels(AsOfReader(conn, SNAPSHOT), "smallcap", [SYM], D).iloc[0]
    assert lv["target_level"] == pytest.approx(np.mean([100.0 + i for i in range(11, 31)]))
    assert lv["stop_range"] == pytest.approx(7.0)
    assert hard_stop_level(131.0, lv["stop_range"]) == pytest.approx(131.0 - 10.5)


def test_levels_are_nan_with_a_missing_bar_in_the_window():
    sessions = sessions_between("2021-06-01", "2021-07-30")
    bars = flat(sessions)
    bars.pop(sessions[25])
    conn = scenario_store(sessions, {SYM: bars})
    lv = entry_levels(AsOfReader(conn, SNAPSHOT), "smallcap", [SYM], sessions[30]).iloc[0]
    assert np.isnan(lv["target_level"]) and np.isnan(lv["stop_range"])


def test_levels_are_in_the_as_of_D_basis_across_a_split():
    # A 2-for-1 split with ex-date inside the 20-session window: as-of D every
    # earlier bar is halved, so the target is in D's (post-split) basis.
    sessions = sessions_between("2021-06-01", "2021-07-30")
    D, ex = sessions[30], sessions[25]
    bars = {d: ((50.0, 50.5, 49.5, 50.0) if d >= ex else (100.0, 101.0, 99.0, 100.0))
            for d in sessions}
    conn = scenario_store(sessions, {SYM: bars}, actions=[dict(
        market="us_equity", symbol=SYM, date=ex, action="split", value=2.0)])
    lv = entry_levels(AsOfReader(conn, SNAPSHOT), "smallcap", [SYM], D).iloc[0]
    assert lv["target_level"] == pytest.approx(50.0)
    assert lv["stop_range"] == pytest.approx(1.0)
    # As-of the day before the split, the same window is in the pre-split basis.
    lv = entry_levels(AsOfReader(conn, SNAPSHOT), "smallcap", [SYM], sessions[24]).iloc[0]
    assert lv["target_level"] == pytest.approx(100.0)


# --- Exit invariance ----------------------------------------------------------------------

def _store_levels(bars: pd.DataFrame, position: Position) -> tuple[float, float]:
    """`entry_levels` on a store holding exactly `bars`: (target, hard stop)."""
    conn = connect(":memory:")
    register_snapshot(conn, "inv", "2021-12-31T00:00:00Z", 0, {"snapshot_id": "inv"})
    rows = []
    for r in bars.to_dict("records"):
        d = pd.Timestamp(r["date"]).strftime("%Y-%m-%d")
        rows.append(dict(market="us_equity", symbol=SYM, date=d, open=r["open"],
                         high=r["high"], low=r["low"], close=r["close"], volume=r["volume"],
                         dollar_volume=r["dollar_volume"], available_at=d))
    upsert(conn, "bars_daily", "inv", rows)
    build_nyse_calendar(conn, "inv")
    lv = entry_levels(AsOfReader(conn, "inv"), "smallcap", [SYM], position.signal_date).iloc[0]
    return float(lv["target_level"]), hard_stop_level(position.fill_price, lv["stop_range"])


@pytest.mark.leakage
def test_exit_invariance_of_the_real_level_function():
    name = build_panel(lanes=("smallcap",), names_per_lane=1, seed=11)[0]
    bars = name.bars.copy()
    bars["date"] = [d.isoformat() for d in bars["date"]]
    dates = bars["date"].tolist()
    rng = np.random.default_rng(2021)
    eligible = dates[19:-1]
    picked = set(sample_dates(eligible, 5, rng)) | {dates[19], dates[20], dates[-2]}
    opens = bars.set_index("date")["open"]
    fills = [Position(signal_date=D, fill_date=dates[dates.index(D) + 1],
                      fill_price=float(opens[dates[dates.index(D) + 1]]))
             for D in sorted(picked)]
    base = _store_levels(bars, fills[0])
    assert np.isfinite(base[0]) and np.isfinite(base[1])
    assert_exit_invariance(_store_levels, bars, fills, rng)


@pytest.mark.leakage
def test_exit_invariance_catches_a_level_that_reads_past_D():
    """The adapter is not vacuous: a level read as-of the last bar moves."""
    name = build_panel(lanes=("smallcap",), names_per_lane=1, seed=12)[0]
    bars = name.bars.copy()
    bars["date"] = [d.isoformat() for d in bars["date"]]
    dates = bars["date"].tolist()

    def leaky(b, position):
        conn = connect(":memory:")
        register_snapshot(conn, "inv", "2021-12-31T00:00:00Z", 0, {"snapshot_id": "inv"})
        upsert(conn, "bars_daily", "inv", [dict(market="us_equity", symbol=SYM, date=r["date"],
               open=r["open"], high=r["high"], low=r["low"], close=r["close"],
               volume=r["volume"], dollar_volume=r["dollar_volume"], available_at=r["date"])
               for r in b.to_dict("records")])
        build_nyse_calendar(conn, "inv")
        last = max(b["date"])
        lv = entry_levels(AsOfReader(conn, "inv"), "smallcap", [SYM], last).iloc[0]
        return float(lv["target_level"]), hard_stop_level(position.fill_price, lv["stop_range"])

    D = dates[100]
    fill = Position(signal_date=D, fill_date=dates[101], fill_price=float(bars["open"].iloc[101]))
    with pytest.raises(AssertionError, match="perturbation"):
        assert_exit_invariance(leaky, bars, [fill], np.random.default_rng(5))

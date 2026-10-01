"""research_log/ledger.md: one row per (signal, variant, universe), always current.

The ledger is the program's multiple-testing correction: every signal run goes in, whether
or not it survived its first table. Rows are upserted on (signal, universe); a variant is
its own signal name (1b-5d, 1b-21d), so a reader can count the variants per signal.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

LEDGER = Path(__file__).resolve().parents[2] / "research_log" / "ledger.md"
COLUMNS = ["date", "signal", "variant", "universe", "pre_reg_commit", "mode", "decision_horizon",
           "dev_z", "dev_mean_net", "dev_n", "confirm_z", "confirm_mean_net", "verdict", "entry"]
HEADER = """# Signal ledger

One row per signal, variant and universe that has been run through the screening engine
(`experiments/screen/`), under the protocol in
`proposals/2026-09-30-signal-screening-pivot.md` section 6. Every run goes in, including
the ones that were dead after the first table; the count of rows is the multiple-testing
correction a reader applies to any graduate. Columns: `dev z` is the day-clustered z on the
pre-registered decision horizon at the base cost schedule; `dev mean net` is the trade-
weighted mean net excess per trade in bps (event mode) or the annualized net excess over
the comparator in percentage points (rank mode); `dev n` is trades / entry days (event) or
weeks (rank). Verdicts: `null`, `confirm`, `graduate`, `fails confirm`, `artifact`
(definitions in the entry's pre-registration). A fourth variant of a signal raises its dev
z bar to 3.5 and is flagged here.

| date | signal | variant | universe | pre-reg commit | mode | decision horizon | dev z | dev mean net | dev n | confirm z | confirm mean net | verdict | entry |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
"""


def read() -> pd.DataFrame:
    if not LEDGER.exists():
        return pd.DataFrame(columns=COLUMNS)
    rows = []
    for line in LEDGER.read_text().splitlines():
        if not line.startswith("| ") or line.startswith("| date") or line.startswith("|---"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == len(COLUMNS):
            rows.append(dict(zip(COLUMNS, cells)))
    return pd.DataFrame(rows, columns=COLUMNS)


def write(df: pd.DataFrame) -> None:
    lines = [HEADER.rstrip("\n")]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(str(r[c]) for c in COLUMNS) + " |")
    LEDGER.write_text("\n".join(lines) + "\n")


def upsert(rows: list[dict]) -> pd.DataFrame:
    df = read()
    for row in rows:
        row = {c: str(row.get(c, "")) for c in COLUMNS}
        m = (df["signal"] == row["signal"]) & (df["variant"] == row["variant"]) & (df["universe"] == row["universe"])
        if m.any():
            for c in COLUMNS:
                if row[c] != "":
                    df.loc[m, c] = row[c]
        else:
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    write(df)
    return df

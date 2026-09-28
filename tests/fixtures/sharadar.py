"""Hand-written Sharadar bulk-export fixtures, zipped at test time (issue 3, 5).

Column layouts follow the assumptions stated in `ingest/sharadar.py`'s module
docstring (no Sharadar API key exists to verify them against a real export;
`docs/ingest-sharadar.md` lists what a first real load must check).

One March-2021 window, `2021-03-01`..`2021-03-31` business days, with
`2021-03-29` (a Monday) left out of every table to simulate an exchange
holiday: a filing on Friday `2021-03-26` is available the *Tuesday* after,
since the next session is `2021-03-30`.

Permatickers:

- `200001` AAA -> AAB, renamed 2021-03-15 (a ticker change inside the range);
  2-for-1 split ex-date 2021-03-17. NYSE, Domestic Common Stock.
- `200002` BBB. NASDAQ, Domestic Common Stock. Cash dividend 1.00, ex-date
  2021-03-10. Two EVENTS filings: Friday 2021-03-12 (available Monday
  2021-03-15) and Friday 2021-03-26 (available Tuesday 2021-03-30, the day
  after the simulated holiday).
- `200003` CCC. NASDAQ, Domestic Common Stock. `bankruptcyliquidation`
  delisting 2021-03-24.
- `200004` DDD. NYSE, Domestic Common Stock. `acquisitionby` delisting
  2021-03-20.
- `200005` EEE. NYSE, Domestic Common Stock, no ACTIONS listing rows at all:
  both `listed` and `delisted` come from the TICKERS fallback
  (firstpricedate 2015-06-01, lastpricedate 2021-03-18, isdelisted).
- `200006` FFF. NYSE, `ADR Common Stock` (issue 6 excludes it by category).
- `200007` GGG. `OTC`, Domestic Common Stock (issue 6 excludes it by exchange).
- Recycled ticker `ZZZ`: `200008` (2018-01-02..2018-01-08, NYSE,
  `voluntarydelisting`) and `200009` (2019-01-02.., NASDAQ, active through the
  main window) share the ticker over disjoint windows.

SFP: `SPY` (kept) and `QQQ` (another fund, filtered out) across the main
window.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd

START, END = "2021-03-01", "2021-03-31"
HOLIDAY = "2021-03-29"


def weekdays(start: str = START, end: str = END) -> list[str]:
    return [d.strftime("%Y-%m-%d") for d in pd.bdate_range(start, end)
           if d.strftime("%Y-%m-%d") != HOLIDAY]


WEEKDAYS = weekdays()

# ------------------------------------------------------------------ symbols

RENAME_PT, RENAME_OLD_TICKER, RENAME_NEW_TICKER = "200001", "AAA", "AAB"
RENAME_DATE = "2021-03-15"
SPLIT_DATE, SPLIT_RATIO = "2021-03-17", 2.0

DIV_PT, DIV_TICKER = "200002", "BBB"
DIV_DATE, DIV_AMOUNT = "2021-03-10", 1.00
EVENT_FRIDAY, EVENT_FRIDAY_AVAILABLE = "2021-03-12", "2021-03-15"
EVENT_HOLIDAY_FRIDAY, EVENT_HOLIDAY_AVAILABLE = "2021-03-26", "2021-03-30"

BANKRUPTCY_PT, BANKRUPTCY_TICKER = "200003", "CCC"
BANKRUPTCY_LISTED, BANKRUPTCY_DATE = "2021-03-03", "2021-03-24"

ACQUIRED_PT, ACQUIRED_TICKER = "200004", "DDD"
ACQUIRED_LISTED, ACQUIRED_DATE = "2015-01-02", "2021-03-20"

FALLBACK_PT, FALLBACK_TICKER = "200005", "EEE"
FALLBACK_FIRST, FALLBACK_LAST = "2015-06-01", "2021-03-18"

ADR_PT, ADR_TICKER = "200006", "FFF"
OTC_PT, OTC_TICKER = "200007", "GGG"

RECYCLED_TICKER = "ZZZ"
RECYCLED_OLD_PT, RECYCLED_OLD_FIRST, RECYCLED_OLD_LAST = "200008", "2018-01-02", "2018-01-08"
RECYCLED_NEW_PT, RECYCLED_NEW_FIRST = "200009", "2019-01-02"

SFP_KEEP, SFP_DROP = "SPY", "QQQ"


def _series(dates: list[str], base: float, step: float = 0.5,
           split_date: str | None = None, split_ratio: float = 1.0) -> pd.DataFrame:
    """closeunadj increasing by `step`/day; vendor close/closeadj is the SEP
    convention of always being split-adjusted to the current share count, so a
    date before `split_date` is closeunadj / split_ratio and a date on or after
    it is closeunadj unchanged."""
    raw = [base + step * i for i in range(len(dates))]
    vendor = [r / split_ratio if split_date and d < split_date else r
             for d, r in zip(dates, raw)]
    return pd.DataFrame({"date": dates, "closeunadj": raw, "vendor_close": vendor})


def _sep_rows(ticker: str, prices: pd.DataFrame, volume: float = 1_000_000.0) -> list[dict]:
    rows = []
    for _, r in prices.iterrows():
        vc = r["vendor_close"]
        rows.append(dict(ticker=ticker, date=r["date"], open=round(vc - 0.5, 4),
                         high=round(vc + 1.0, 4), low=round(vc - 1.0, 4),
                         close=round(vc, 4), volume=volume, closeadj=round(vc, 4),
                         closeunadj=round(r["closeunadj"], 4), lastupdated="2021-04-30"))
    return rows


def sep_df() -> pd.DataFrame:
    rows: list[dict] = []
    rename_i = WEEKDAYS.index(RENAME_DATE)
    pre, post = WEEKDAYS[:rename_i], WEEKDAYS[rename_i:]
    prices = _series(WEEKDAYS, base=100.0, step=0.5, split_date=SPLIT_DATE, split_ratio=SPLIT_RATIO)
    rows += _sep_rows(RENAME_OLD_TICKER, prices[prices["date"].isin(pre)])
    rows += _sep_rows(RENAME_NEW_TICKER, prices[prices["date"].isin(post)])

    rows += _sep_rows(DIV_TICKER, _series(WEEKDAYS, base=40.0, step=0.1))
    bankrupt_dates = [d for d in WEEKDAYS if BANKRUPTCY_LISTED <= d <= BANKRUPTCY_DATE]
    rows += _sep_rows(BANKRUPTCY_TICKER, _series(bankrupt_dates, base=5.0, step=-0.1))
    acquired_dates = [d for d in WEEKDAYS if d <= ACQUIRED_DATE]
    rows += _sep_rows(ACQUIRED_TICKER, _series(acquired_dates, base=20.0, step=0.05))
    fallback_dates = [d for d in WEEKDAYS if d <= FALLBACK_LAST]
    rows += _sep_rows(FALLBACK_TICKER, _series(fallback_dates, base=15.0, step=0.05))
    rows += _sep_rows(ADR_TICKER, _series(WEEKDAYS, base=30.0, step=0.05))
    rows += _sep_rows(OTC_TICKER, _series(WEEKDAYS, base=3.0, step=0.02))

    old_dates = [d.strftime("%Y-%m-%d") for d in pd.bdate_range(RECYCLED_OLD_FIRST, RECYCLED_OLD_LAST)]
    rows += _sep_rows(RECYCLED_TICKER, _series(old_dates, base=8.0, step=0.1))
    rows += _sep_rows(RECYCLED_TICKER, _series(WEEKDAYS, base=12.0, step=0.03))
    return pd.DataFrame(rows)


def tickers_df() -> pd.DataFrame:
    def row(permaticker, ticker, name, exchange, category, first, last, isdelisted="N", sector="Industrials"):
        return dict(table="SEP", permaticker=permaticker, ticker=ticker, name=name,
                   exchange=exchange, isdelisted=isdelisted, category=category,
                   sector=sector, firstpricedate=first, lastpricedate=last,
                   lastupdated="2021-04-30")

    day_before_rename = WEEKDAYS[WEEKDAYS.index(RENAME_DATE) - 1]
    rows = [
        row(RENAME_PT, RENAME_OLD_TICKER, "Alpha Corp", "NYSE", "Domestic Common Stock",
            "2015-01-02", day_before_rename),
        row(RENAME_PT, RENAME_NEW_TICKER, "Alpha Corp", "NYSE", "Domestic Common Stock",
            RENAME_DATE, WEEKDAYS[-1]),
        row(DIV_PT, DIV_TICKER, "Beta Inc", "NASDAQ", "Domestic Common Stock",
            "2015-01-02", WEEKDAYS[-1]),
        row(BANKRUPTCY_PT, BANKRUPTCY_TICKER, "Gamma Ltd", "NASDAQ", "Domestic Common Stock",
            BANKRUPTCY_LISTED, BANKRUPTCY_DATE, isdelisted="Y"),
        row(ACQUIRED_PT, ACQUIRED_TICKER, "Delta Corp", "NYSE", "Domestic Common Stock",
            ACQUIRED_LISTED, ACQUIRED_DATE, isdelisted="Y"),
        row(FALLBACK_PT, FALLBACK_TICKER, "Epsilon Co", "NYSE", "Domestic Common Stock",
            FALLBACK_FIRST, FALLBACK_LAST, isdelisted="Y"),
        row(ADR_PT, ADR_TICKER, "Foreign Bank Ltd", "NYSE", "ADR Common Stock",
            "2015-01-02", WEEKDAYS[-1]),
        row(OTC_PT, OTC_TICKER, "Grey Micro Inc", "OTC", "Domestic Common Stock",
            "2015-01-02", WEEKDAYS[-1]),
        row(RECYCLED_OLD_PT, RECYCLED_TICKER, "Zenith One Inc", "NYSE", "Domestic Common Stock",
            RECYCLED_OLD_FIRST, RECYCLED_OLD_LAST, isdelisted="Y"),
        row(RECYCLED_NEW_PT, RECYCLED_TICKER, "Zenith Two Inc", "NASDAQ", "Domestic Common Stock",
            RECYCLED_NEW_FIRST, WEEKDAYS[-1]),
    ]
    return pd.DataFrame(rows)


def actions_df() -> pd.DataFrame:
    def row(date, action, ticker, value=None, contraticker=None, contraname=None, name=None):
        return dict(date=date, action=action, ticker=ticker, name=name, value=value,
                   contraticker=contraticker, contraname=contraname)

    rows = [
        row("2015-01-02", "listed", RENAME_OLD_TICKER),
        row(RENAME_DATE, "tickerchangeto", RENAME_NEW_TICKER, contraticker=RENAME_OLD_TICKER),
        row(SPLIT_DATE, "split", RENAME_NEW_TICKER, value=SPLIT_RATIO),
        row("2015-01-02", "listed", DIV_TICKER),
        row(DIV_DATE, "dividend", DIV_TICKER, value=DIV_AMOUNT),
        row(BANKRUPTCY_LISTED, "listed", BANKRUPTCY_TICKER),
        row(BANKRUPTCY_DATE, "bankruptcyliquidation", BANKRUPTCY_TICKER,
            contraname="Chapter 7 liquidation"),
        row(ACQUIRED_LISTED, "listed", ACQUIRED_TICKER),
        row(ACQUIRED_DATE, "acquisitionby", ACQUIRED_TICKER, contraname="Acme Holdings Inc"),
        row("2015-01-02", "listed", ADR_TICKER),
        row("2015-01-02", "listed", OTC_TICKER),
        row(RECYCLED_OLD_FIRST, "listed", RECYCLED_TICKER),
        row(RECYCLED_OLD_LAST, "voluntarydelisting", RECYCLED_TICKER),
        row(RECYCLED_NEW_FIRST, "listed", RECYCLED_TICKER),
        # FALLBACK_TICKER has no ACTIONS rows at all: the TICKERS fallback case.
    ]
    return pd.DataFrame(rows)


def daily_df() -> pd.DataFrame:
    sep = sep_df()
    return pd.DataFrame({
        "ticker": sep["ticker"], "date": sep["date"],
        "marketcap": sep["closeunadj"] * 5_000_000.0, "lastupdated": "2021-04-30",
    })


def events_df() -> pd.DataFrame:
    return pd.DataFrame([
        dict(ticker=DIV_TICKER, date=EVENT_FRIDAY, eventcodes="21|81", lastupdated="2021-04-30"),
        dict(ticker=DIV_TICKER, date=EVENT_HOLIDAY_FRIDAY, eventcodes="23", lastupdated="2021-04-30"),
    ])


def sfp_df() -> pd.DataFrame:
    rows = []
    for ticker, base in ((SFP_KEEP, 390.0), (SFP_DROP, 330.0)):
        for i, d in enumerate(WEEKDAYS):
            c = base + 0.3 * i
            rows.append(dict(ticker=ticker, date=d, open=c - 0.2, high=c + 0.4, low=c - 0.4,
                             close=c, volume=5_000_000.0, closeadj=c, closeunadj=c,
                             lastupdated="2021-04-30"))
    return pd.DataFrame(rows)


TABLE_BUILDERS = {
    "SEP": sep_df, "TICKERS": tickers_df, "ACTIONS": actions_df,
    "DAILY": daily_df, "EVENTS": events_df, "SFP": sfp_df,
}


def _zip_csv(df: pd.DataFrame, dest: Path, inner_name: str) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(inner_name, buf.getvalue())
    return dest


def write_files(tmp_dir: Path) -> dict[str, Path]:
    """Zip each table's CSV into `tmp_dir` and return the `files` mapping
    `ingest.sharadar.load` expects."""
    tmp_dir = Path(tmp_dir)
    files = {}
    for table, build in TABLE_BUILDERS.items():
        dest = tmp_dir / f"{table}.zip"
        files[table] = _zip_csv(build(), dest, f"SHARADAR_{table}.csv")
    return files

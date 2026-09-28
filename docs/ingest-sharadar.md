# Ingest: Sharadar

`ingest/sharadar.py` loads SEP, TICKERS, ACTIONS, DAILY, EVENTS and SFP into the
point-in-time store. Spec: `spec/02-data.md` (Sources, Store); `spec/01-lanes-and-universe.md`
(Eligibility, Point-in-time construction, Delisting while a position is open);
`spec/04-features-and-labels.md` (`filing_2d` availability, TICKERS `sector`).
Issues 3 and 5.

**No Sharadar API key exists in this environment.** Every column layout and
every semantic below is reconstructed from public third-party documentation
and schema reproductions (cited in the PR), not verified against a real
export. "First real load" below marks what must be checked once
`NASDAQ_DATA_LINK_API_KEY` exists and PR 19's fetcher (`ingest/fetch/sharadar.py`)
has pulled real files.

## Running it

```bash
python -m ingest.sharadar load --snapshot-id <id> \
    --file SEP=raw/sharadar/SEP/SEP-2026...zip \
    --file TICKERS=raw/sharadar/TICKERS/TICKERS-...zip \
    --file ACTIONS=raw/sharadar/ACTIONS/ACTIONS-...zip \
    --file DAILY=raw/sharadar/DAILY/DAILY-...zip \
    --file EVENTS=raw/sharadar/EVENTS/EVENTS-...zip \
    --file SFP=raw/sharadar/SFP/SFP-...zip
```

All six `--file NAME=PATH` are required; each path is a raw export (a zip of
one CSV, as Nasdaq Data Link bulk exports deliver it, or a bare CSV). The
store path comes from `config.env.store_path()` (`PENUMBRA_STORE_PATH`); the
loader never imports `ingest.fetch` and never fetches anything itself — PR 19
supplies the paths, from a snapshot document if one is passed programmatically
(`load(conn, snapshot_id, files, snapshot_doc=...)`).

Unmapped rows (a ticker/date pair with no matching TICKERS window) are never
dropped silently: they are logged, returned in the `LoadReport`, and written to
`<rejects-dir>/<snapshot_id>-<TABLE>-rejects.csv` (`--rejects-dir`, default
`<PENUMBRA_DATA_ROOT>/rejects`).

Loading is idempotent: every row's primary key includes `snapshot_id`, so
`harness.store.writer.upsert` re-writes the same rows on a re-run and the
store's counts don't change.

## Assumed vendor schemas

| Table | Assumed columns | Used here |
| --- | --- | --- |
| SEP, SFP | `ticker, date, open, high, low, close, volume, closeadj, closeunadj, lastupdated` | all |
| TICKERS | `table, permaticker, ticker, name, exchange, isdelisted, category, sector, firstpricedate, lastpricedate, lastupdated` (of a larger vendor column set) | all |
| ACTIONS | `date, action, ticker, name, value, contraticker, contraname` (no `permaticker`, no `lastupdated`) | all |
| DAILY | `ticker, date, lastupdated, marketcap` (of a larger vendor column set: ev, evebit, evebitda, pe, pb, ps) | `ticker, date, marketcap, lastupdated` |
| EVENTS | `ticker, date, eventcodes, lastupdated`, `date` being the EDGAR filing date | all |

`close` is split-adjusted only; `closeadj` is split-and-dividend adjusted;
`closeunadj` is raw. All of open/high/low/volume in SEP and SFP are assumed
split-adjusted like `close` (not dividend-adjusted), which is what makes
`x × closeunadj / close` the correct imputation for the store's unadjusted
series (spec/02).

**First real load must check:** the actual column names and order in one real
export of each table (a header mismatch fails loudly — `KeyError` on a missing
column — rather than silently mis-mapping, since columns are read by name).

## Ticker -> permaticker mapping

SEP, ACTIONS, DAILY and EVENTS are all keyed by `ticker`, and Sharadar recycles
tickers. The loader maps every (ticker, date) to a permaticker using the
TICKERS rows for `table == 'SEP'`, each carrying a `firstpricedate`/
`lastpricedate` window:

- **Recycled ticker**: two different permatickers each have one TICKERS row
  for the same ticker, over disjoint windows. The date decides which one a
  (ticker, date) pair maps to.
- **Ticker change**: one permaticker has *two* TICKERS rows — one per ticker
  symbol it has held — each with its own window (the old ticker's window ending
  at the rename, the new one's starting there). This is the assumption that
  makes the join well-defined without a separate ticker-history table.

**First real load must check:** whether a real TICKERS export actually carries
one row per historical ticker symbol per permaticker, as assumed above, or
only the current ticker. If only the current ticker is present, historical
SEP/ACTIONS rows under an old ticker would need `tickerchangefrom`/
`tickerchangeto` ACTIONS rows to reconstruct the old ticker's window instead —
a follow-up fix, not a silent wrong answer, since an unmapped row is rejected
and reported, never guessed.

A row that doesn't fall inside any window is unmapped: logged, reported, and
written to the rejects CSV, never merged into the wrong permaticker and never
dropped silently (issue 3).

## SEP -> `bars_daily`

`market='us_equity'`, symbol = the mapped permaticker. Unadjusted OHLV is
imputed as `x × closeunadj / close` for open, high, low and volume; the stored
`close` is `closeunadj` (prices are stored unadjusted, per `docs/store.md`).
The vendor `close` and `closeadj` are kept as `close_vendor`/`closeadj_vendor`
(audit only, never read by `harness.store.reader`). `dollar_volume` is
`closeunadj × volume_unadj`. `available_at` is the bar date; `lastupdated` is
carried as metadata only, never used for availability.

## ACTIONS -> `actions`, and the split value assumption

Normalized to the store's convention: `split.value` = shares after / shares
before (2.0 for a 2-for-1); `dividend.value` = cash per share, in the ex-date
share basis. Ticker changes (`tickerchangefrom`/`tickerchangeto`) are stored as
plain `actions` rows and never merge or split a permaticker. Every other
action type (`spinoff`, `spinoffdividend`, `adrratiosplit`, `relation`, ...) is
stored as-is with its own type and untouched `value`; `harness/store/adjust.py`
does not interpret them.

**Flagged assumption, most conservative reading available:** whether
Sharadar's own `split.value` is already "shares after / shares before" (this
loader's assumption, passed through unchanged) or its reciprocal. No
Sharadar documentation text was reachable from this environment to confirm the
direction; the fixture (`tests/fixtures/sharadar.py`) is built on the assumed
direction, not derived from a real export. **First real load must check:** take
one well-known split, and confirm `harness/store/adjust.py` (which multiplies
by `1 / value`) turns the post-split closing price back into the pre-split one
for a date before the split, as-of a date after it. If it doubles instead of
halves (or vice versa), invert the assumption at the one line in
`ingest/sharadar.py` that reads `mapped["value"]` for splits.

## Listing (issue 5) -> `listing`

`listed` and `delisted` events come from ACTIONS: an ACTIONS row with
`action == 'listed'` is a `listed` event; a row whose action is one of the
delisting-reason types spec/01 names for the haircut classes —
`acquisitionby`, `mergerto`, `voluntarydelisting`, `bankruptcyliquidation`,
`regulatorydelisting` — or the generic `delisted` (assumed present as a
catch-all when no specific reason is known) is a `delisted` event, with
`reason` set to that action type. `exchange` is the exchange of the TICKERS
window the row mapped through (the listing exchange in effect at the event),
so the labeler can select the Nasdaq 0.45× vs. NYSE/American 0.70× haircut
class (spec/01) without parsing strings.

Where a permaticker has no ACTIONS `listed` row, its earliest TICKERS
`firstpricedate` becomes a `listed` event with `source='tickers_fallback'`.
Where it has no ACTIONS delisting-reason row but TICKERS marks it
`isdelisted`, its latest `lastpricedate` becomes a `delisted` event the same
way, with `reason=None` (the fallback carries no reason). `available_at` is
always the event date.

## TICKERS -> `symbols`

One row per permaticker: `ticker` (current), `name`, `category`, `exchange`,
`sector` (current values from the TICKERS row with the latest
`lastpricedate`), `available_at` = the earliest `firstpricedate` across that
permaticker's TICKERS rows (the first-ever listing, not the most recent
rename).

**Open gap, for the PM:** `category` and `exchange` are current TICKERS
values, exactly like `sector` (`docs/store.md` "Open points"), but only
`sector` is allowlisted as a non-point-in-time input by the store leakage test
(spec/04). A name whose category or exchange changed (an OTC name that
up-listed to NYSE, for instance) would be screened by issue 6's eligibility
rule using its *current* category/exchange at every historical as-of date,
not the one that applied on that date. This loader does not attempt to
reconstruct historical category/exchange — there is no ACTIONS row type for
it — so the gap is inherited by issue 6's universe builder, which should
flag it rather than assume point-in-time correctness.

## DAILY -> `marketcap`

`marketcap`, `available_at` = the date.

## EVENTS -> `events`

`available_at` is always the next NYSE session after the filing date, using
`harness.store.calendar.next_session` against the `nyse` calendar this loader
builds right after SEP loads. The filing-date exception in spec/04
(`available_at` = the filing date itself, "when acceptance is known to be
before 16:00 ET") never applies here: Sharadar EVENTS carries no acceptance
time, only a filing date, so this loader always takes the conservative
(next-session) branch. A filing on the last date the `nyse` calendar knows
about (no next session yet) is deferred rather than guessed: it is not written,
and `LoadReport.deferred_events` counts it; a later load, once more SEP dates
extend the calendar, will pick it up.

## SFP -> `bars_daily` (SPY only)

Filtered to `ticker == 'SPY'`; every other fund in the file (SFP's own scope
per PR 19's fetcher is already narrowed to SPY via a table filter, but this
loader filters again defensively) is dropped. Stored under
`market='us_equity'`, symbol `SFP:SPY` — never a bare permaticker, so it can
never collide with one — with the same unadjusted-OHLV imputation and audit
columns as SEP.

## Calendar

`harness.store.calendar.build_nyse_calendar` runs immediately after SEP loads,
before ACTIONS/DAILY/EVENTS/SFP, since EVENTS needs it for `available_at`.

## Fixtures

`tests/fixtures/sharadar.py` hand-writes one CSV per table (columns per the
assumed schemas above) and zips each at test time
(`tests/ingest/test_sharadar.py` calls `write_files`). One March-2021 window
with a simulated holiday (`2021-03-29` omitted from every table, so a Friday
filing two weeks later is available the Tuesday after, not the Monday) covers:

- a recycled ticker (`ZZZ`, two permatickers, disjoint 2018 / 2019+ windows);
- a ticker change inside the range (`AAA` -> `AAB`, one permaticker);
- a 2:1 split and a cash dividend;
- a `bankruptcyliquidation` delisting on NASDAQ and an `acquisitionby` on NYSE;
- a name with no ACTIONS listing rows at all (the TICKERS fallback);
- an ADR (`ADR Common Stock` category) and an OTC name (`OTC` exchange),
  stored but left for issue 6 to exclude;
- an EVENTS row filed on a Friday (available the next Monday) and one filed on
  the Friday before the simulated holiday (available the Tuesday after);
- SFP rows for SPY and another fund, the other fund filtered out.

`tests/ingest/test_sharadar.py` reuses `tests/store/test_leakage.py`'s `READS`,
`_bound` and `_truncated` helpers against the loaded store, scoped to the
tables this loader writes (`calendar`, `symbols`, `bars_daily`, `actions`,
`listing`, `marketcap`, `events`; `bars_hourly` and `lane_membership` are other
units' concern and are never populated here).

## What has not been verified

Nothing in this loader has run against a real Sharadar export. Beyond the two
flagged assumptions above (TICKERS carrying one row per historical ticker per
permaticker; the split value's direction), a first real load should also
confirm: `isdelisted` is encoded as one of the truthy strings this loader
recognizes (`Y`/`yes`/`true`/`1`, case-insensitive) rather than a boolean
column pandas would read differently; ACTIONS carries no `permaticker` column
that would make this join unnecessary; and DAILY's `marketcap` is already in
dollars (not thousands or another scale).

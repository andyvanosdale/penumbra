# Store

The point-in-time store: `harness/store/`. Spec: `spec/02` (Store, Trading
calendars, Leakage tests), `spec/01` (Point-in-time construction), `spec/04`
(`sector`, `filing_2d`). Contract: `docs/architecture.md`, "Store". Issue 16.

The store is one SQLite file. The caller resolves its path (`PENUMBRA_STORE_PATH`,
read by `config/env.py`) and opens it with `harness.store.connect(path)`, which
creates the schema or refuses a store written under another schema version. The
store is derived: it is rebuilt from a snapshot's raw files, never migrated in
place.

## Tables

Every point-in-time table has `snapshot_id` in its primary key and an
`available_at` column. `harness/store/schema.py` (`TABLES`) is the source of truth
for keys and columns. `lastupdated` is vendor metadata and is never used as
`available_at`.

| Table | Key | Columns | `available_at` |
| --- | --- | --- | --- |
| `meta` | `key` | `schema_version` | not point-in-time |
| `snapshots` | `snapshot_id` | `created_at`, `file_count`, `document` (snapshot JSON) | not point-in-time; registered before any of its rows |
| `calendar` | `calendar, date, snapshot_id` | `nyse` or `utc` | the date |
| `symbols` | `market, symbol, snapshot_id` | `ticker, name, category, exchange, sector` (TICKERS); `base, quote` (crypto); `lastupdated` | the first listing date (TICKERS `firstpricedate` or the first 1d kline). A symbol isn't known before it lists |
| `bars_daily` | `market, symbol, date, snapshot_id` | unadjusted `open, high, low, close, volume`; `dollar_volume`; `close_vendor`, `closeadj_vendor` (SEP audit); `lastupdated` | the bar date |
| `bars_hourly` | `market, symbol, ts, snapshot_id` | `ts` = open time; `open, high, low, close, volume, quote_volume` | the kline close time (`ts` + 1h − 1ms) |
| `actions` | `market, symbol, date, action, snapshot_id` | `value`; `ticker, contraticker, contraname`; `lastupdated` | the action date |
| `listing` | `market, symbol, event, date, snapshot_id` | `event` ∈ {`listed`, `delisted`}; `reason` (ACTIONS action type); `exchange` at delisting; `source` ∈ {`actions`, `tickers`, `klines`} | the event date |
| `marketcap` | `market, symbol, date, snapshot_id` | `marketcap` (Sharadar DAILY); `lastupdated` | the date |
| `events` | `market, symbol, filing_date, snapshot_id` | `eventcodes`; `lastupdated` | the next NYSE session after `filing_date`, or `filing_date` when acceptance is known to be before 16:00 ET (spec/04 `filing_2d`) |
| `lane_membership` | `lane, market, symbol, date, snapshot_id` | `screen_values` (JSON: the screen values that admitted the name) | the date |

Conventions:

- `market` ∈ {`us_equity`, `binance_spot`}. The equity `symbol` is the Sharadar
  permaticker as text; the ticker is an attribute. The crypto `symbol` is the pair.
- Dates are ISO `YYYY-MM-DD`. Hourly timestamps are ISO UTC with milliseconds,
  `YYYY-MM-DDTHH:MM:SS.fffZ`.
- Prices are unadjusted. SEP OHLV is imputed at ingest as `x × closeunadj / close`.
  `dollar_volume` is unadjusted close × volume for equities and the 1d kline quote
  volume for crypto.
- `actions.value`: for `split`, shares after ÷ shares before (2.0 for a 2-for-1);
  for `dividend`, cash per share. `ingest/sharadar.py` (issues 3, 5) normalizes the
  vendor value to this; `docs/ingest-sharadar.md` flags the split-direction
  assumption it could not verify against a real export. Ticker changes are rows
  in `actions`; they never merge or split a permaticker.
- Indexes: each market-data table has a `(snapshot_id, market, date, …)` index for
  the windowed panel read.

`symbols` holds the vendor's current attributes. `sector` is the one allowlisted
non-point-in-time input (spec/04 Features). `category`, `exchange` and `ticker` are
also TICKERS current values; see "Open points" below.

## Writing

`harness.store.writer`:

- `register_snapshot(conn, snapshot_id, created_at, file_count, document)` comes
  first. Rows that name an unregistered snapshot are refused.
- `upsert(conn, table, snapshot_id, rows)` inserts or updates on the table's
  primary key. A reload of the same snapshot changes nothing, and a second
  snapshot sits beside the first. Nothing is deleted or rebuilt from filesystem
  state. A batch is all-or-nothing, and it is refused when a row has:
  - a missing or malformed `available_at`;
  - an `available_at` earlier than the date that dates the row;
  - a missing key column or an unknown column;
  - a different `snapshot_id`.

## Trading calendars

Calendars are table rows, built at load time and never inferred at read time.

- `build_nyse_calendar(conn, snapshot_id)` writes `nyse` from the distinct dates of
  the snapshot's `us_equity` daily bars (SEP). Crypto rows never add a date. A
  weekend equity date is refused as a data error.
- `build_utc_calendar(conn, snapshot_id, start, end)` writes `utc`, every calendar
  day in the range.
- `next_session(conn, snapshot_id, calendar, date)` gives the first session after a
  date. The EVENTS loader uses it for `available_at`.
- Lanes map to calendars (`LANE_CALENDAR`, `calendar_for_lane`): `smallcap` and
  `discovered` use `nyse`, and `crypto` uses `utc`.

## Adjustment

Prices are stored unadjusted and adjusted at read time (`harness/store/adjust.py`).
`adjust` ∈ {`none`, `split`, `split_div`}.

As-of D, a bar dated t < D is multiplied by the product of the factors of the
adjusting actions with t < action date ≤ D. An action dated after D is never
applied: the reader doesn't fetch it, and the arithmetic below gives it no weight.

- Split, ratio r = `value`: prices × 1/r, volume × r.
- Cash dividend of amount `div`: prices × (1 − div / close<sub>ex−1</sub>), where
  close<sub>ex−1</sub> is the **unadjusted** close of the symbol's last bar before
  the ex-date. Volume is unchanged. This is the standard (CRSP-style) factor. The
  spec gives no formula, so this choice is flagged on issue 16's PR. A dividend with
  no earlier bar has factor 1. A dividend at or above the prior close is refused.
- `split` applies splits only. `split_div` applies splits and cash dividends. No
  other action type adjusts prices. `dollar_volume` is never adjusted.

Implementation: P(x) is the product of the factors of the actions dated ≤ x. A bar
dated t, in the basis of date B, is multiplied by P(B) / P(t). For t < B this is
the spec's rule. For t > B (the labeler converting later bars into the entry's
basis through the oracle) it divides by the factors of actions in (B, t].

### Worked example: a 2-for-1 split

A split with ex-date 2021-03-17. Unadjusted closes: 111 on 03-16 and 56 on 03-17 (the fixture's values).

| Read | close on 03-16 | close on 03-17 |
| --- | --- | --- |
| as-of 03-16, any `adjust` | 111 (split not yet known) | — (not yet available) |
| as-of 03-17, `none` | 111 | 56 |
| as-of 03-17, `split` or `split_div` | 111 × ½ = 55.5 (volume × 2) | 56 |
| oracle, basis 03-16, `split` | 111 | 56 × 2 = 112 |

The adjusted series as-of 03-17 gives a 03-16→03-17 return of 56 / 55.5 − 1 = +0.9%. The
unadjusted series would show a −50% "shock". `tests/store/test_store.py` checks
this reconstruction.

## Read paths

### `AsOfReader(conn, snapshot_id)`

The only read path for the universe, the features and the cost model (`harness/store/reader.py`).

Every public method takes `as_of`: an ISO date, read as "after the close of D".
Every query filters `available_at <= :as_of` in SQL. For hourly klines, the bound
is the end of UTC day D, `DT23:59:59.999Z`. Every returned frame includes
`available_at`.

| Method | Returns |
| --- | --- |
| `bars(market, symbols, date, as_of, adjust="none")` | Daily bars dated `date` (the single-date read) |
| `panel(market, symbols \| None, start, end, as_of, adjust="none")` | Daily bars dated in [start, end] (the one windowed read per (lane, era); `None` = all symbols). The caller passes the lane's market and the era window |
| `hourly(market, symbols, start, end, as_of)` | Hourly klines opening on UTC dates [start, end] |
| `symbols(market, symbols, as_of)` | Symbol attributes, including `sector` |
| `actions(market, symbols, start, end, as_of, kinds=None)` | ACTIONS rows |
| `listing(market, symbols, start, end, as_of)` | Listing events |
| `listed(market, date, as_of)` | Symbols listed on `date`: a `listed` event on or before the date and no `delisted` event on or before it (spec/02 Store), using events known as-of |
| `exchange_on(market, symbols, date, as_of)` | Point-in-time exchange for eligibility (spec/01): the most recent `listing` row's exchange dated on or before `date`, else `symbols.exchange` flagged `source='tickers_fallback'` |
| `marketcap(market, symbols, start, end, as_of)` | DAILY market cap |
| `events(market, symbols, start, end, as_of)` | EVENTS rows by filing date |
| `calendar(calendar_name, start, end, as_of)` | Sessions of `nyse` or `utc` |
| `lane_membership(lane, start, end, as_of)` | Derived lane membership |

### `OracleReader(conn, snapshot_id, last_date, holdout_start, unlocked=False)`

The future-aware read, for the labeler only (`harness/store/oracle.py`). Only
`harness/labels.py` and `harness/backtest.py` may import it
(`tests/test_architecture.py`).

It has no `available_at` filter, and it is bounded instead:

- A read whose end is after `last_date` raises `OracleBoundError`. `last_date` is
  the last trading day of the run's era (spec/03 Era boundaries).
- A read whose end is on or after `holdout_start` raises `HoldoutLockedError`
  unless `unlocked` is true.
- The SQL also caps every read at the effective bound, which is `last_date`, or the
  day before `holdout_start` when locked.

The run supplies the era bounds and the unlock (issue 17 owns `config/eras.py` and
the run record). Methods: `bars` (with `adjust` and `basis`, the entry's as-of
date), `hourly`, `actions`, `listing`, `events` and `calendar`.

## Leakage test

`tests/store/test_leakage.py` is marked `leakage` and implements spec/02 Leakage
tests, "Store". It is parametrized over `TABLES`, so a table added to the schema
without a read there fails. For every table and every as-of date in the fixture
range, it checks two things:

- no row returned by the single-date read or the windowed read has an
  `available_at` after the as-of date;
- each read returns the same frame, adjusted values included, as the same read of a
  copy of the store with every later row deleted.

`symbols` has no date dimension, so only its single read applies. The
allowlisted exceptions are `symbols.sector` (spec/04), `symbols.category`
(spec/01: a current value with no vendor history, like `sector`) and
`symbols.exchange` only as `exchange_on`'s fallback (spec/01) — the primary,
point-in-time answer for eligibility's exchange is `exchange_on`, not
`symbols.exchange` directly.

The fixture, `tests/fixtures/store.py`, is a reusable synthetic store. It contains:

- a split, a dividend and a ticker change;
- a NASDAQ bankruptcy delisting;
- market cap rows;
- an EVENTS row filed after the close;
- two crypto pairs with daily and hourly klines, weekends included.

## Resolved points

- **`listed` on the delisting date.** spec/02 said a name is not listed on its
  delisting date ("no delisting event on or before D"); spec/01 said "after
  their delisting date". The store always followed spec/02, the stricter of
  the two, and spec/01 was reworded to match ("excluded on and after their
  delisting date", penumbra-specs PR 10, "A name is not listed on its
  delisting date") — no code change, the wording caught up.
- **Point-in-time exchange.** spec/01 now says eligibility's exchange on D
  comes from the most recent ACTIONS listing/exchange-change event, TICKERS
  `exchange` only as the fallback (penumbra-specs PR 10, "Eligibility fields
  that are not point-in-time"). `AsOfReader.exchange_on` (`docs/ingest-sharadar.md`)
  implements this from the `listing` table; `symbols.exchange` remains the
  current TICKERS value and is now allowlisted, like `sector`, rather than an
  open gap.

## Open points

- **`category`.** `symbols.category` is a current TICKERS value with no
  vendor history, like `sector`; spec/01 now allowlists it explicitly and
  accepts the risk (a name reclassified out of common stock mid-era reads as
  never having been common stock) rather than asking for a reconstruction
  Sharadar's data can't support (penumbra-specs PR 10).
- **Point-in-time ticker.** `symbols.ticker` is the current ticker; the
  historical value at any date comes from the `actions` ticker-change rows,
  not from `symbols`.

## Availability invariant

For `calendar`, `bars_daily`, `actions`, `listing`, `marketcap` and `lane_membership`,
the writer refuses any row whose `available_at` differs from its date
(`harness.store.schema.AVAILABLE_ON_DATE`; spec/02 dates each of these on its own
date). Consumers that read one panel as of the last date of a range (the universe
builder, the feature builder) rely on this: every row dated t ≤ D is then known by
D, so D's values cannot depend on which later dates share the batch. `events`
(available the session after filing) and `bars_hourly` (available at the kline
close) are the exceptions, and every consumer filters them on `available_at`
explicitly, per date.

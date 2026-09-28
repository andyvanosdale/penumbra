# Fetching and updating raw data

`python -m ingest.fetch_data` pulls the raw vendor files the spec names
(`spec/02-data.md`) into a storage root and keeps them current. It is the same
command on a laptop, on a mounted volume, and on the hosting service against an
S3-compatible bucket. It never downloads a file it already holds.

## Storage root

Set `PENUMBRA_DATA_ROOT` (or pass `--root`):

| Where | Value |
| --- | --- |
| Laptop | `/Users/you/penumbra-data` |
| Mounted volume | `/mnt/penumbra` |
| S3 or S3-compatible | `s3://my-bucket/penumbra` plus `PENUMBRA_S3_ENDPOINT=https://...` for non-AWS endpoints and the usual `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` |

The `s3://` scheme needs `pip install s3fs`. Any other fsspec scheme (`gs://`,
`abfs://`) works the same way with its own driver installed.

Layout under the root:

```
raw/binance/data/spot/monthly/klines/<PAIR>/<1d|1h>/<PAIR>-<iv>-YYYY-MM.zip
raw/binance/data/spot/daily/klines/<PAIR>/<1d|1h>/<PAIR>-<iv>-YYYY-MM-DD.zip   (current month only)
raw/binance/data/futures/um/monthly/fundingRate/<PAIR>/...                     (--funding)
raw/sharadar/<TABLE>/<TABLE>-<snapshot-time>.zip                               (one per export; never overwritten)
raw/yfinance/<TICKER>.csv
manifests/<source>.json      what is held, with size, sha256 and the vendor's version id
snapshots/<id>.json          the file set a run was built from (spec/03 run record)
snapshots/latest.json
```

Raw files are never modified. Sharadar snapshots accumulate because the vendor
restates history; a run names the snapshot it used and is rebuilt from that,
never from a fresh download.

## Commands

```bash
python -m ingest.fetch_data binance                      # all USDT pairs, 1d and 1h klines
python -m ingest.fetch_data binance --funding            # plus USD-M funding rates (carry epic)
python -m ingest.fetch_data binance --pairs BTCUSDT,ETHUSDT --intervals 1d
python -m ingest.fetch_data sharadar                     # needs NASDAQ_DATA_LINK_API_KEY
python -m ingest.fetch_data sharadar --tables SEP,ACTIONS --max-age-days 0
python -m ingest.fetch_data yfinance --tickers-file universe.txt --start 2015-01-01
python -m ingest.fetch_data all                          # every source
python -m ingest.fetch_data status                       # counts and bytes per source
python -m ingest.fetch_data snapshot                     # write and print the snapshot id
python -m ingest.fetch_data verify <snapshot_id>         # re-hash the files a snapshot names
```

`--dry-run` on any source plans without downloading. Exit code is 0 when every
planned file is present, 1 when some failed (they are retried next run), 2 on
configuration errors.

## How "already there" is decided

Each source records every file it fetched in its manifest with the size, the
sha256 of the bytes written, and the vendor's identifier for that version:

- Binance: the bucket's ETag and size from the listing. Files are immutable, so a
  matching entry plus a matching object size means skip. Every download is
  verified against the bucket's `.CHECKSUM` file before it is kept.
- Sharadar: the export's `data_snapshot_time`. A table whose newest local
  snapshot is younger than `--max-age-days` is not even requested.
- yfinance: the last complete session. A ticker already fetched through
  yesterday is skipped; otherwise a short overlap is re-downloaded and compared,
  and a restated history (split or dividend) triggers a full refetch.

Downloads stream into a `.part` file and are moved into place only when
complete and verified, so an interrupted run leaves nothing a later run would
mistake for a finished file.

## Keeping it current

Run `all` on a schedule (daily after the US close and after 00:30 UTC for
Binance). Each run fetches only what is new: the current month's daily Binance
files, a new Sharadar export when one is available, and yesterday's rows for
yfinance tickers. Follow with `snapshot` before any backtest run so the run
record can name the file set.

## Adding a source

Subclass `ingest.fetch.base.Source`, implement `plan` (yield one `Task` per
file, with the vendor's version id and size when known) and `fetch` (stream
the file into storage and return `(size, sha256)`), and decorate the class
with `@register`. Import the module in `ingest/fetch/cli.py`. The runner
handles skipping, retries, manifests and reporting.

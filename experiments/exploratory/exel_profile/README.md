# Exploratory: EXEL's profile as a predictor (2026-10-16)

Owner-requested exploratory analysis, **not pre-registered and not evidence** in the sense
of `spec/03`. It asks whether the fundamental state EXEL was in before and during its
2022–2026 run predicts 12-month returns for other US common stocks. Findings and every
table are in `research_log/2026-10-16-exploratory-exel-profile/`.

Nothing here touches the harness, the store or the eras. The scripts are standalone
(pandas, numpy, requests, yfinance) and are kept so the pull can be reproduced locally and
the data reviewed.

## Pipeline (point-in-time, SEC EDGAR)

```
python universe.py                                      # Nasdaq Trader listing -> uni/common_stock_list.csv (screen-1 filters)
python sec_pull.py --out secdata --ticker-map ticker.txt # XBRL company facts + submissions, one file per CIK (resumable, 8 req/s)
python sec_build.py --data secdata --out secdata/annual.csv.gz   # one row per 10-K: current and prior-year values as filed, filing date, SIC, 13D count
python yf_prices.py --tickers secdata/ticker_cik.csv --mapped-only --out px_hist --start 2009-01-01 --end 2022-01-05
python yf_prices.py --tickers secdata/ticker_cik.csv --mapped-only --out px      --start 2022-01-01 --end 2026-10-18
python sec_screen.py --annual secdata/annual.csv.gz --map secdata/ticker_cik.csv --prices px_hist px --out results_sec
```

- `universe.py` expects `uni/nasdaqlisted.txt` and `uni/otherlisted.txt` from
  `https://www.nasdaqtrader.com/dynamic/SymDir/`.
- `sec_pull.py` needs the ticker-to-CIK map `https://www.sec.gov/include/ticker.txt`; pass a
  saved copy with `--ticker-map`. SEC asks automated tools to identify themselves with a
  contact address in the User-Agent: set `SEC_USER_AGENT="Name contact@example.com"` before
  running. `www.sec.gov` refuses requests without it; `data.sec.gov` was lenient on
  2026-10-16. `--keep-raw` stores the untouched JSON responses (about 1 GB compressed for
  3,600 companies); the extracts alone are about 130 MB. `manifest.jsonl` records a SHA-256
  for every file written.
- `sec_build.py` picks tags by a fixed fallback list per concept (see `CONCEPTS`), keeps
  annual flows (340–390 day durations) and instants dated at the fiscal year end, and takes
  the prior-year comparative from the same filing so changes are on one basis. Cover-page
  shares (`dei:EntityCommonStockSharesOutstanding`) are the share count for market cap.
- `sec_screen.py` enters each filing on the first session after its filing date and applies
  three fixed profiles (level, inflection, deterioration) plus rank composites, a sector-
  neutral variant, a two-year-lag placebo and a 13D split. Thresholds are in `score()` and
  were fixed from EXEL's own ratios before any other name was read.

## Pipeline (first pass, yfinance statements)

`yf_fund_pull.py` pulls four fiscal years of normalized statements per ticker from yfinance
in one request each; `yf_screen.py` runs the same three profiles on them with a 75-day
filing-lag assumption. Superseded by the SEC pipeline (real filing dates, 16 vintages) and
kept for the record.

## Known limits

Current listings only (survivorship); XBRL phase-in thins 2010–2012; tag fallbacks are
not comparable across financials; no costs; yfinance adjusted closes. The Sharadar bundle
closes the first gap (delisted names and their prices).

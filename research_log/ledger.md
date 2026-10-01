# Signal ledger

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
| 2026-10-01 | 1a | — | smallcap | af23489 | event short | 5s | -0.71 | -18 bps | 18722 / 2507 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1a | — | uncapped | af23489 | event short | 5s | -1.29 | -34 bps | 37854 / 2666 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1a | — | crypto | af23489 | event short | 5s | +2.61 | -6 bps | 3462 / 369 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1b | 5d | smallcap | af23489 | event long | 5s | -6.35 | -91 bps | 11409 / 2504 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1b | 5d | uncapped | af23489 | event long | 5s | -6.45 | -67 bps | 21587 / 2689 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1b | 5d | crypto | af23489 | event long | 5s | -0.41 | +20 bps | 2570 / 913 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1b | 21d | smallcap | af23489 | event long | 21s | -5.92 | -125 bps | 9799 / 2426 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1b | 21d | uncapped | af23489 | event long | 21s | -5.11 | -91 bps | 19043 / 2639 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1b | 21d | crypto | af23489 | event long | 21s | -1.57 | -100 bps | 1957 / 813 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1c | short | smallcap | af23489 | event short | 21s | -1.56 | -24 bps | 5711 / 1860 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1c | short | uncapped | af23489 | event short | 21s | -2.32 | -43 bps | 11578 / 2245 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1c | short | crypto | af23489 | event short | 21s | +2.41 | +231 bps | 361 / 122 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1c | long | smallcap | af23489 | event long | 21s | -1.46 | -56 bps | 8969 / 2210 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1c | long | uncapped | af23489 | event long | 21s | -2.30 | -56 bps | 18460 / 2510 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1c | long | crypto | af23489 | event long | 21s | +0.99 | +187 bps | 1634 / 671 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1d | — | BTCUSDT | af23489 | rank | 7d | +0.29 | +7.8 pp | 259 wk | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1d | — | ETHUSDT | af23489 | rank | 7d | +0.47 | +16.4 pp | 259 wk | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1e | — | crypto | af23489 | rank | 7d | -0.53 | -12.4 pp | 255 wk | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | up-rvol_20 | smallcap | af23489 + cbc3c67 (A2) | event long | 63s | -2.23 | -70 bps | 6021 / 2261 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | up-close_to_high_250 | smallcap | af23489 + cbc3c67 (A2) | event long | 63s | -1.39 | -29 bps | 4287 / 1919 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | up-close | smallcap | af23489 + cbc3c67 (A2) | event long | 63s | +5.28 | +440 bps | 4000 / 1915 | +5.91 | +709 bps | artifact | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | up-rvol_20 | uncapped | af23489 + cbc3c67 (A2) | event long | 63s | -2.21 | -16 bps | 11430 / 2543 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | up-close_to_high_250 | uncapped | af23489 + cbc3c67 (A2) | event long | 63s | -2.74 | -36 bps | 8517 / 2308 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | up-close | uncapped | af23489 + cbc3c67 (A2) | event long | 63s | +5.10 | +346 bps | 7776 / 2273 | +4.80 | +445 bps | artifact | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | down-close | smallcap | af23489 + cbc3c67 (A2) | event short | 63s | +7.00 | +530 bps | 3834 / 1878 | +6.96 | +915 bps | artifact | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | down-rvol_20 | smallcap | af23489 + cbc3c67 (A2) | event short | 63s | +0.65 | -33 bps | 6021 / 2261 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | down-ret_20 | smallcap | af23489 + cbc3c67 (A2) | event short | 63s | -1.25 | +20 bps | 9495 / 2535 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | down-close | uncapped | af23489 + cbc3c67 (A2) | event short | 63s | +7.88 | +333 bps | 8908 / 2389 | +5.37 | +415 bps | artifact | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | down-rvol_20 | uncapped | af23489 + cbc3c67 (A2) | event short | 63s | +0.18 | -72 bps | 11430 / 2543 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | down-ret_20 | uncapped | af23489 + cbc3c67 (A2) | event short | 63s | -0.45 | +33 bps | 19391 / 2676 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | up-close | crypto | af23489 + cbc3c67 (A2) | event long | 63s | +1.47 | +1841 bps | 547 / 454 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | up-med_dv_20_prev | crypto | af23489 + cbc3c67 (A2) | event long | 63s | +0.91 | +419 bps | 1013 / 698 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | up-rvol_20 | crypto | af23489 + cbc3c67 (A2) | event long | 63s | +0.18 | -202 bps | 1149 / 821 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | down-vol_pctl_250 | crypto | af23489 + cbc3c67 (A2) | event short | 63s | -0.47 | -42 bps | 1102 / 722 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | down-rvol_20 | crypto | af23489 + cbc3c67 (A2) | event short | 63s | -0.49 | +82 bps | 1149 / 821 | — | — | null | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | down-ret_60 | crypto | af23489 + cbc3c67 (A2) | event short | 63s | +0.54 | +322 bps | 929 / 677 | — | — | null | 2026-10-01-wave-1-screen.md |

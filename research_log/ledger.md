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
z bar to 3.5 and is flagged here. Wave 2 (`2026-10-08-wave-2-rank.md`, rank mode on
equities under the rank-mode v2 bar) adds `family_n` (rows that can graduate in the wave),
`p_sidak` = 1 − (1 − p_dev)^family_n, and the three placebo columns `random` (rank of the
actual net excess among itself and the 200 random slices), `lag250` (the lag-250 placebo's
zero-cost z) and `mirror` (the opposite slice's zero-cost z); for wave-2 rows `dev z` is
z_gate = min(z_plain, z_nw) at base and `dev n` carries the MDE80. Earlier rows read `n/a`
in the new columns. Wave-2 verdicts add `characteristic`, `insufficient` and
`diagnostic-pass` (`smallcap`, non-graduating); `graduate` is not awarded in wave 2 (C8).

| date | signal | variant | universe | pre-reg commit | mode | decision horizon | dev z | dev mean net | dev n | confirm z | confirm mean net | verdict | family_n | p_sidak | random | lag250 | mirror | entry |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-01 | 1a | — | smallcap | af23489 | event short | 5s | -0.71 | -18 bps | 18722 / 2507 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1a | — | uncapped | af23489 | event short | 5s | -1.29 | -34 bps | 37854 / 2666 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1a | — | crypto | af23489 | event short | 5s | +2.61 | -6 bps | 3462 / 369 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1b | 5d | smallcap | af23489 | event long | 5s | -6.35 | -91 bps | 11409 / 2504 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1b | 5d | uncapped | af23489 | event long | 5s | -6.45 | -67 bps | 21587 / 2689 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1b | 5d | crypto | af23489 | event long | 5s | -0.41 | +20 bps | 2570 / 913 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1b | 21d | smallcap | af23489 | event long | 21s | -5.92 | -125 bps | 9799 / 2426 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1b | 21d | uncapped | af23489 | event long | 21s | -5.11 | -91 bps | 19043 / 2639 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1b | 21d | crypto | af23489 | event long | 21s | -1.57 | -100 bps | 1957 / 813 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1c | short | smallcap | af23489 | event short | 21s | -1.56 | -24 bps | 5711 / 1860 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1c | short | uncapped | af23489 | event short | 21s | -2.32 | -43 bps | 11578 / 2245 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1c | short | crypto | af23489 | event short | 21s | +2.41 | +231 bps | 361 / 122 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1c | long | smallcap | af23489 | event long | 21s | -1.46 | -56 bps | 8969 / 2210 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1c | long | uncapped | af23489 | event long | 21s | -2.30 | -56 bps | 18460 / 2510 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1c | long | crypto | af23489 | event long | 21s | +0.99 | +187 bps | 1634 / 671 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1d | — | BTCUSDT | af23489 | rank | 7d | +0.29 | +7.8 pp | 259 wk | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1d | — | ETHUSDT | af23489 | rank | 7d | +0.47 | +16.4 pp | 259 wk | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | 1e | — | crypto | af23489 | rank | 7d | -0.53 | -12.4 pp | 255 wk | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | up-rvol_20 | smallcap | af23489 + cbc3c67 (A2) | event long | 63s | -2.23 | -70 bps | 6021 / 2261 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | up-close_to_high_250 | smallcap | af23489 + cbc3c67 (A2) | event long | 63s | -1.39 | -29 bps | 4287 / 1919 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | up-close | smallcap | af23489 + cbc3c67 (A2) | event long | 63s | +5.28 | +440 bps | 4000 / 1915 | +5.91 | +709 bps | artifact | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | up-rvol_20 | uncapped | af23489 + cbc3c67 (A2) | event long | 63s | -2.21 | -16 bps | 11430 / 2543 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | up-close_to_high_250 | uncapped | af23489 + cbc3c67 (A2) | event long | 63s | -2.74 | -36 bps | 8517 / 2308 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | up-close | uncapped | af23489 + cbc3c67 (A2) | event long | 63s | +5.10 | +346 bps | 7776 / 2273 | +4.80 | +445 bps | artifact | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | down-close | smallcap | af23489 + cbc3c67 (A2) | event short | 63s | +7.00 | +530 bps | 3834 / 1878 | +6.96 | +915 bps | artifact | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | down-rvol_20 | smallcap | af23489 + cbc3c67 (A2) | event short | 63s | +0.65 | -33 bps | 6021 / 2261 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | down-ret_20 | smallcap | af23489 + cbc3c67 (A2) | event short | 63s | -1.25 | +20 bps | 9495 / 2535 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | down-close | uncapped | af23489 + cbc3c67 (A2) | event short | 63s | +7.88 | +333 bps | 8908 / 2389 | +5.37 | +415 bps | artifact | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | down-rvol_20 | uncapped | af23489 + cbc3c67 (A2) | event short | 63s | +0.18 | -72 bps | 11430 / 2543 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | down-ret_20 | uncapped | af23489 + cbc3c67 (A2) | event short | 63s | -0.45 | +33 bps | 19391 / 2676 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | up-close | crypto | af23489 + cbc3c67 (A2) | event long | 63s | +1.47 | +1841 bps | 547 / 454 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | up-med_dv_20_prev | crypto | af23489 + cbc3c67 (A2) | event long | 63s | +0.91 | +419 bps | 1013 / 698 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | up-rvol_20 | crypto | af23489 + cbc3c67 (A2) | event long | 63s | +0.18 | -202 bps | 1149 / 821 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | down-vol_pctl_250 | crypto | af23489 + cbc3c67 (A2) | event short | 63s | -0.47 | -42 bps | 1102 / 722 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | down-rvol_20 | crypto | af23489 + cbc3c67 (A2) | event short | 63s | -0.49 | +82 bps | 1149 / 821 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-01 | a2r | down-ret_60 | crypto | af23489 + cbc3c67 (A2) | event short | 63s | +0.54 | +322 bps | 929 / 677 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-01-wave-1-screen.md |
| 2026-10-07 | i1 | — | smallcap | d979e2a | intraday long 10:00 | close | -0.41 | +0 bps | 251 / 156 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i1 | — | uncapped | d979e2a | intraday long 10:00 | close | -0.37 | +1 bps | 1367 / 339 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i2 | up | smallcap | d979e2a | intraday long 09:35 | close | -2.14 | -94 bps | 1677 / 426 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i2 | up | uncapped | d979e2a | intraday long 09:35 | close | -2.30 | -54 bps | 2646 / 456 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i2 | down | smallcap | d979e2a | intraday short 09:35 | close | +0.39 | -3 bps | 1060 / 368 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i2 | down | uncapped | d979e2a | intraday short 09:35 | close | +1.38 | +1 bps | 1699 / 414 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i3 | top | smallcap | d979e2a | intraday long 10:00 | close | -2.40 | -23 bps | 1492 / 464 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i3 | top | uncapped | d979e2a | intraday long 10:00 | close | -2.03 | -10 bps | 7089 / 464 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i3 | bottom | smallcap | d979e2a | intraday short 10:00 | close | -0.88 | -8 bps | 1493 / 464 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i3 | bottom | uncapped | d979e2a | intraday short 10:00 | close | -2.38 | -9 bps | 7094 / 464 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i4 | — | smallcap | d979e2a | intraday long 15:30 | close | -6.42 | -19 bps | 1481 / 464 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i4 | — | uncapped | d979e2a | intraday long 15:30 | close | -12.59 | -19 bps | 7041 / 464 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i5 | all | smallcap | d979e2a | intraday long 15:55 | nopen | -4.77 | -23 bps | 284996 / 478 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i5 | all | uncapped | d979e2a | intraday long 15:55 | nopen | -3.95 | -18 bps | 512725 / 478 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i5 | q5 | smallcap | d979e2a | intraday long 15:55 | nopen | -13.30 | -29 bps | 57218 / 478 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i5 | q5 | uncapped | d979e2a | intraday long 15:55 | nopen | -13.63 | -26 bps | 102729 / 478 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i5 | q1 | smallcap | d979e2a | intraday long 15:55 | nopen | -21.40 | -44 bps | 56767 / 478 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i5 | q1 | uncapped | d979e2a | intraday long 15:55 | nopen | -19.44 | -36 bps | 102247 / 478 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i6-1a | 0935 | smallcap | d979e2a | intraday short 09:35 | close | -1.75 | -33 bps | 8490 / 471 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i6-1a | 0935 | uncapped | d979e2a | intraday short 09:35 | close | -1.87 | -27 bps | 15794 / 476 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i6-1a | 1030 | smallcap | d979e2a | intraday short 10:30 | close | -2.19 | -28 bps | 8518 / 470 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i6-1a | 1030 | uncapped | d979e2a | intraday short 10:30 | close | -2.99 | -23 bps | 15889 / 477 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i6-1b | 0935 | smallcap | d979e2a | intraday long 09:35 | close | -3.81 | -69 bps | 5592 / 474 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i6-1b | 0935 | uncapped | d979e2a | intraday long 09:35 | close | -3.25 | -54 bps | 8962 / 475 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i6-1b | 1030 | smallcap | d979e2a | intraday long 10:30 | close | -2.20 | -40 bps | 5359 / 471 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i6-1b | 1030 | uncapped | d979e2a | intraday long 10:30 | close | -2.20 | -38 bps | 8717 / 475 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i7 | — | smallcap | d979e2a | intraday short 12:00 | close | -0.75 | -4 bps | 282 / 180 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i7 | — | uncapped | d979e2a | intraday short 12:00 | close | -0.46 | -20 bps | 957 / 292 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i8 | up-fhh_vol_share | smallcap | d979e2a | intraday long 09:35 | close | -12.29 | -37 bps | 30543 / 479 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i8 | up-fhh_ret | smallcap | d979e2a | intraday long 09:35 | close | -6.66 | -30 bps | 19983 / 479 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i8 | up-late_vol_share | smallcap | d979e2a | intraday long 09:35 | close | -13.75 | -39 bps | 39349 / 476 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i8 | up-fhh_vol_share | uncapped | d979e2a | intraday long 09:35 | close | -15.75 | -32 bps | 62346 / 479 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i8 | up-fhh_ret | uncapped | d979e2a | intraday long 09:35 | close | -7.93 | -29 bps | 48298 / 479 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i8 | up-late_vol_share | uncapped | d979e2a | intraday long 09:35 | close | -15.16 | -33 bps | 79249 / 476 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i8 | down-close_loc | smallcap | d979e2a | intraday short 09:35 | close | -15.72 | -38 bps | 42666 / 479 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i8 | down-fhh_ret | smallcap | d979e2a | intraday short 09:35 | close | -6.30 | -30 bps | 19983 / 479 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i8 | down-late_vol_share | smallcap | d979e2a | intraday short 09:35 | close | -13.14 | -39 bps | 39349 / 476 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i8 | down-close_loc | uncapped | d979e2a | intraday short 09:35 | close | -16.32 | -33 bps | 82877 / 479 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i8 | down-fhh_ret | uncapped | d979e2a | intraday short 09:35 | close | -6.06 | -22 bps | 48298 / 479 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-07 | i8 | down-late_vol_share | uncapped | d979e2a | intraday short 09:35 | close | -13.65 | -31 bps | 79249 / 476 | — | — | null | n/a | n/a | n/a | n/a | n/a | 2026-10-07-intraday-wave.md |
| 2026-10-08 | 2a | v1 | uncapped | b799b52 | rank long (v2 bar) | 1mo | +0.36 | +1.7 pp | 130 mo (MDE80 13.9 pp) | — | — | null (underpowered below 14 pp) | 9 | 0.982 | 186 / 201 | +0.16 | -0.81 | 2026-10-08-wave-2-rank.md |
| 2026-10-08 | 2a | v2 | uncapped | b799b52 | rank long (v2 bar) | 1mo | +0.15 | +0.5 pp | 130 mo (MDE80 8.9 pp) | — | — | null | 9 | 0.995 | 188 / 201 | +0.09 | -0.95 | 2026-10-08-wave-2-rank.md |
| 2026-10-08 | 2a | v3 | uncapped | b799b52 | rank long (v2 bar) | 1mo | +0.81 | +3.4 pp | 130 mo (MDE80 11.9 pp) | — | — | null | 9 | 0.879 | 201 / 201 | -0.48 | -1.10 | 2026-10-08-wave-2-rank.md |
| 2026-10-08 | 2a | v1 | smallcap | b799b52 | rank long (v2 bar) smallcap non-graduating | 1mo | -1.43 | -7.4 pp | 126 mo (MDE80 15.6 pp) | — | — | null (underpowered below 16 pp) | 9 | 1.000 | 24 / 201 | -0.21 | -0.92 | 2026-10-08-wave-2-rank.md |
| 2026-10-08 | 2a | v2 | smallcap | b799b52 | rank long (v2 bar) smallcap non-graduating | 1mo | -1.24 | -4.0 pp | 130 mo (MDE80 9.8 pp) | — | — | null | 9 | 1.000 | 64 / 201 | -0.04 | -0.55 | 2026-10-08-wave-2-rank.md |
| 2026-10-08 | 2a | v3 | smallcap | b799b52 | rank long (v2 bar) smallcap non-graduating | 1mo | -0.40 | -1.7 pp | 130 mo (MDE80 12.3 pp) | — | — | null (underpowered below 12 pp) | 9 | 1.000 | 80 / 201 | -0.40 | -0.67 | 2026-10-08-wave-2-rank.md |
| 2026-10-08 | 2b | v1 | uncapped | b799b52 | rank long (v2 bar) | 1mo | -1.01 | -3.6 pp | 130 mo (MDE80 11.1 pp) | — | — | null | 9 | 1.000 | 98 / 201 | +0.48 | -0.77 | 2026-10-08-wave-2-rank.md |
| 2026-10-08 | 2b | v2 | uncapped | b799b52 | rank long (v2 bar) | 1mo | -0.24 | -0.7 pp | 130 mo (MDE80 9.3 pp) | — | — | null | 9 | 1.000 | 190 / 201 | +0.10 | -0.34 | 2026-10-08-wave-2-rank.md |
| 2026-10-08 | 2b | v3 | uncapped | b799b52 | rank long (v2 bar) | 1mo | -0.93 | -3.3 pp | 122 mo (MDE80 13.6 pp) | — | — | null (underpowered below 14 pp) | 9 | 1.000 | 117 / 201 | +0.29 | +0.29 | 2026-10-08-wave-2-rank.md |
| 2026-10-08 | 2b | v1 | smallcap | b799b52 | rank long (v2 bar) smallcap non-graduating | 1mo | -1.25 | -5.4 pp | 126 mo (MDE80 13.8 pp) | — | — | null (underpowered below 14 pp) | 9 | 1.000 | 80 / 201 | +0.35 | -1.17 | 2026-10-08-wave-2-rank.md |
| 2026-10-08 | 2b | v2 | smallcap | b799b52 | rank long (v2 bar) smallcap non-graduating | 1mo | -0.88 | -3.2 pp | 130 mo (MDE80 10.9 pp) | — | — | null | 9 | 1.000 | 148 / 201 | +1.48 | +0.34 | 2026-10-08-wave-2-rank.md |
| 2026-10-08 | 2b | v3 | smallcap | b799b52 | rank long (v2 bar) smallcap non-graduating | 1mo | -0.82 | -5.9 pp | 79 mo (MDE80 21.5 pp) | — | — | insufficient | 9 | 1.000 | 88 / 201 | -1.14 | +0.45 | 2026-10-08-wave-2-rank.md |
| 2026-10-08 | 2d | v1 | uncapped | b799b52 | rank long (v2 bar) | 1wk | -0.16 | -1.0 pp | 458 wk (MDE80 18.1 pp) | — | — | insufficient | 9 | 0.999 | 198 / 201 | -0.11 | -1.32 | 2026-10-08-wave-2-rank.md |
| 2026-10-08 | 2d | v2 | uncapped | b799b52 | rank long (v2 bar) | 1wk | -0.79 | -3.4 pp | 563 wk (MDE80 12.3 pp) | — | — | null (underpowered below 12 pp) | 9 | 1.000 | 190 / 201 | +0.06 | -1.46 | 2026-10-08-wave-2-rank.md |
| 2026-10-08 | 2d | v3 | uncapped | b799b52 | rank long (v2 bar) | 1wk | -0.30 | -1.8 pp | 458 wk (MDE80 18.8 pp) | — | — | insufficient | 9 | 1.000 | 197 / 201 | -1.16 | -0.53 | 2026-10-08-wave-2-rank.md |
| 2026-10-08 | 2d | v1 | smallcap | b799b52 | rank long (v2 bar) smallcap non-graduating | 1wk | +0.36 | +14.8 pp | 81 wk (MDE80 91.1 pp) | — | — | insufficient | 9 | 0.982 | 181 / 201 | +0.39 | -1.26 | 2026-10-08-wave-2-rank.md |
| 2026-10-08 | 2d | v2 | smallcap | b799b52 | rank long (v2 bar) smallcap non-graduating | 1wk | -0.28 | -2.6 pp | 271 wk (MDE80 27.0 pp) | — | — | insufficient | 9 | 1.000 | 152 / 201 | -1.37 | -1.45 | 2026-10-08-wave-2-rank.md |
| 2026-10-08 | 2d | v3 | smallcap | b799b52 | rank long (v2 bar) smallcap non-graduating | 1wk | +0.81 | +31.6 pp | 81 wk (MDE80 97.7 pp) | — | — | insufficient | 9 | 0.879 | 199 / 201 | +0.76 | -0.97 | 2026-10-08-wave-2-rank.md |

# Wave 1 tables — dev era

**1a / crypto / dev — direction short, decision horizon 5 sessions, next-open fill**

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @alt80 | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4351 | 872 | 3462 | 369 | +54 | +14 | -6 | -46 | -26 | -546 | 0.569 | +161 | +62 | +2.61 | 18.7% | +3.33 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 3462 | -8 | -0.30 | -68 | -1.43 |
| 5 * | 3462 | +54 | +3.58 | -6 | +2.61 |
| 21 | 3365 | +102 | +1.91 | +42 | +1.51 |
| 63 | 3235 | +148 | +1.28 | +88 | +1.05 |
| 126 | 3065 | -405 | -0.72 | -465 | -0.78 |
| 252 | 2571 | -1192 | -0.36 | -1252 | -0.39 |
| i04 | 3411 | +1 | +0.01 | -59 | -5.40 |
| i12 | 3462 | +3 | +1.10 | -57 | -2.25 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2018 | 153 | 36 | -52 | -0.31 |
| 2019 | 478 | 62 | +38 | +2.60 |
| 2020 | 856 | 99 | -16 | +1.57 |
| 2021 | 900 | 66 | +18 | +0.67 |
| 2022 | 1075 | 106 | -32 | +1.80 |
| half1 | 1052 | 143 | +28 | +2.74 |
| half2 | 2410 | 226 | -21 | +1.85 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 3590 | +44 | +3.25 | -16 |
| next_open | 3462 | +54 | +3.58 | -6 |
| next_close | 3464 | +60 | +5.10 | +0 |

Controls: placebo (lag 20) z @0 +0.13, @base -1.14 on 3400 trades; planted +50 bps z +4.39 vs actual +3.58 (shift +0.81).

**1a / smallcap / dev — direction short, decision horizon 5 sessions, next-open fill**

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 23023 | 4216 | 18722 | 2507 | +25 | +4 | -18 | -61 | -351 | 0.491 | -8 | +12 | -0.71 | 6.4% | -0.53 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 18722 | +18 | +2.83 | -25 | -4.73 |
| 5 * | 18722 | +25 | +3.04 | -18 | -0.71 |
| 21 | 18533 | +29 | +1.07 | -14 | -0.92 |
| 63 | 17907 | +28 | +1.01 | -15 | -0.14 |
| 126 | 16987 | +41 | +1.40 | -2 | +0.60 |
| 252 | 14297 | -0 | +0.16 | -43 | -0.35 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2010 | 1189 | 202 | -52 | -0.66 |
| 2011 | 1475 | 200 | +6 | +0.59 |
| 2012 | 790 | 206 | -31 | -1.01 |
| 2013 | 761 | 218 | -15 | -0.33 |
| 2014 | 1189 | 230 | -49 | -0.50 |
| 2015 | 1519 | 237 | -15 | -0.02 |
| 2016 | 1677 | 237 | -42 | -1.69 |
| 2017 | 1398 | 245 | +8 | +0.43 |
| 2018 | 2215 | 246 | -28 | -0.36 |
| 2019 | 2084 | 247 | +22 | +0.87 |
| 2020 | 4425 | 239 | -19 | +0.34 |
| half1 | 5988 | 1172 | -26 | -0.41 |
| half2 | 12734 | 1335 | -14 | -0.60 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 19197 | +15 | +1.85 | -28 |
| next_open | 18722 | +25 | +3.04 | -18 |
| next_close | 18722 | +1 | +1.24 | -42 |

Controls: placebo (lag 20) z @0 -1.08, @base -4.46 on 21153 trades; planted +50 bps z +7.25 vs actual +3.04 (shift +4.21).

**1a / uncapped / dev — direction short, decision horizon 5 sessions, next-open fill**

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 47073 | 9108 | 37854 | 2666 | +1 | -16 | -34 | -69 | -336 | 0.485 | -12 | +9 | -1.29 | 11.7% | -1.14 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 37854 | +9 | +2.22 | -27 | -5.85 |
| 5 * | 37854 | +1 | +2.82 | -34 | -1.29 |
| 21 | 37599 | +2 | +1.16 | -34 | -1.03 |
| 63 | 36385 | -13 | +1.68 | -48 | +0.41 |
| 126 | 34702 | +12 | +2.26 | -23 | +1.36 |
| 252 | 28440 | -11 | +1.28 | -47 | +0.71 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2010 | 2818 | 234 | -39 | +0.31 |
| 2011 | 3774 | 231 | +6 | -1.03 |
| 2012 | 1724 | 238 | -38 | -0.61 |
| 2013 | 1436 | 236 | -41 | -1.43 |
| 2014 | 2047 | 243 | -14 | +0.62 |
| 2015 | 2822 | 244 | -12 | +0.93 |
| 2016 | 3470 | 249 | -37 | -1.81 |
| 2017 | 2410 | 248 | +7 | +0.85 |
| 2018 | 4172 | 249 | -45 | -0.72 |
| 2019 | 3767 | 250 | -15 | -0.12 |
| 2020 | 9414 | 244 | -69 | -0.95 |
| half1 | 12811 | 1302 | -19 | -0.32 |
| half2 | 25043 | 1364 | -41 | -1.52 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 38941 | +8 | +2.14 | -27 |
| next_open | 37854 | +1 | +2.82 | -34 |
| next_close | 37854 | -13 | +1.16 | -48 |

Controls: placebo (lag 20) z @0 -0.30, @base -4.65 on 44068 trades; planted +50 bps z +8.20 vs actual +2.82 (shift +5.38).

**1b-21d / crypto / dev — direction long, decision horizon 21 sessions, next-open fill**

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @alt80 | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3326 | 1348 | 1957 | 813 | -40 | -80 | -100 | -140 | -120 | -692 | 0.343 | -175 | +111 | -1.57 | 11.4% | -3.66 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 1955 | -41 | -1.56 | -101 | -2.91 |
| 5 | 1956 | +29 | +0.26 | -31 | -0.75 |
| 21 * | 1957 | -40 | -1.04 | -100 | -1.57 |
| 63 | 1885 | -301 | -1.01 | -361 | -1.22 |
| 126 | 1785 | -460 | +0.00 | -520 | -0.06 |
| 252 | 1613 | -1760 | -1.05 | -1820 | -1.09 |
| i04 | 1945 | +16 | +0.11 | -44 | -3.88 |
| i12 | 1952 | +11 | +0.50 | -49 | -1.57 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2018 | 49 | 28 | +348 | +1.65 |
| 2019 | 240 | 109 | -90 | -0.97 |
| 2020 | 609 | 236 | -133 | -1.85 |
| 2021 | 616 | 245 | +72 | +0.10 |
| 2022 | 443 | 195 | -347 | -2.22 |
| half1 | 565 | 249 | -30 | -0.92 |
| half2 | 1392 | 564 | -128 | -1.33 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 1985 | -24 | -1.35 | -84 |
| next_open | 1957 | -40 | -1.04 | -100 |
| next_close | 1957 | +19 | +0.08 | -41 |

Controls: placebo (lag 20) z @0 -0.43, @base -1.06 on 2102 trades; planted +50 bps z -0.59 vs actual -1.04 (shift +0.45).

**1b-21d / smallcap / dev — direction long, decision horizon 21 sessions, next-open fill**

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 13039 | 2814 | 9799 | 2426 | -79 | -102 | -125 | -171 | -477 | 0.429 | -149 | +25 | -5.92 | 5.0% | -6.20 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 9799 | -25 | -4.21 | -71 | -9.71 |
| 5 | 9799 | -49 | -3.47 | -95 | -6.59 |
| 21 * | 9799 | -79 | -4.07 | -125 | -5.92 |
| 63 | 9272 | -102 | -3.07 | -148 | -4.15 |
| 126 | 8716 | -59 | -0.96 | -105 | -1.66 |
| 252 | 7803 | -50 | -1.96 | -96 | -2.45 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2010 | 645 | 212 | -75 | -2.59 |
| 2011 | 735 | 195 | -75 | -2.53 |
| 2012 | 517 | 196 | -134 | -1.65 |
| 2013 | 558 | 215 | -27 | -0.58 |
| 2014 | 691 | 220 | -72 | -1.73 |
| 2015 | 730 | 218 | +42 | -0.03 |
| 2016 | 812 | 228 | -81 | -0.79 |
| 2017 | 924 | 241 | -82 | -1.18 |
| 2018 | 1082 | 240 | -105 | -1.09 |
| 2019 | 1109 | 237 | -215 | -3.76 |
| 2020 | 1996 | 224 | -265 | -4.00 |
| half1 | 3496 | 1150 | -67 | -3.82 |
| half2 | 6303 | 1276 | -158 | -4.53 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 9884 | -62 | -3.10 | -108 |
| next_open | 9799 | -79 | -4.07 | -125 |
| next_close | 9799 | -60 | -3.07 | -106 |

Controls: placebo (lag 20) z @0 -0.67, @base -2.25 on 9817 trades; planted +50 bps z -2.08 vs actual -4.07 (shift +1.99).

**1b-21d / uncapped / dev — direction long, decision horizon 21 sessions, next-open fill**

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 24012 | 4410 | 19043 | 2639 | -53 | -72 | -91 | -129 | -399 | 0.438 | -99 | +19 | -5.11 | 6.7% | -5.29 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 19043 | -19 | -4.09 | -57 | -10.36 |
| 5 | 19043 | -33 | -3.50 | -71 | -7.11 |
| 21 * | 19043 | -53 | -3.06 | -91 | -5.11 |
| 63 | 17959 | -69 | -2.21 | -108 | -3.43 |
| 126 | 17043 | +3 | +0.44 | -36 | -0.31 |
| 252 | 15335 | +78 | +0.96 | +39 | +0.51 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2010 | 1351 | 237 | -52 | -1.99 |
| 2011 | 1876 | 237 | -57 | -4.19 |
| 2012 | 1146 | 226 | -62 | -1.85 |
| 2013 | 1086 | 241 | +9 | +0.15 |
| 2014 | 1256 | 241 | -73 | -1.73 |
| 2015 | 1371 | 244 | +38 | +0.08 |
| 2016 | 1699 | 245 | -77 | -1.23 |
| 2017 | 1575 | 246 | -40 | +0.05 |
| 2018 | 1976 | 249 | -58 | -1.73 |
| 2019 | 1999 | 245 | -141 | -2.44 |
| 2020 | 3708 | 228 | -234 | -3.18 |
| half1 | 7329 | 1304 | -38 | -3.82 |
| half2 | 11714 | 1335 | -124 | -3.45 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 19181 | -40 | -2.16 | -79 |
| next_open | 19043 | -53 | -3.06 | -91 |
| next_close | 19043 | -39 | -1.98 | -77 |

Controls: placebo (lag 20) z @0 +0.12, @base -1.66 on 16571 trades; planted +50 bps z -0.49 vs actual -3.06 (shift +2.57).

**1b-5d / crypto / dev — direction long, decision horizon 5 sessions, next-open fill**

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @alt80 | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3326 | 750 | 2570 | 913 | +80 | +40 | +20 | -20 | -0 | -591 | 0.356 | -27 | +67 | -0.41 | 11.8% | -3.04 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 2568 | -24 | -1.66 | -84 | -3.11 |
| 5 * | 2570 | +80 | +0.49 | +20 | -0.41 |
| 21 | 2556 | +75 | -0.67 | +15 | -1.20 |
| 63 | 2441 | -288 | -1.87 | -348 | -2.12 |
| 126 | 2325 | +287 | +0.21 | +227 | +0.13 |
| 252 | 2117 | -1027 | -1.98 | -1087 | -2.04 |
| i04 | 2556 | +13 | +0.07 | -47 | -4.45 |
| i12 | 2564 | +17 | +0.34 | -43 | -1.99 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2018 | 57 | 34 | +95 | +0.78 |
| 2019 | 306 | 137 | -116 | -3.07 |
| 2020 | 840 | 257 | +49 | -0.34 |
| 2021 | 813 | 268 | +194 | +1.46 |
| 2022 | 554 | 217 | -214 | -1.66 |
| half1 | 759 | 289 | -21 | -1.19 |
| half2 | 1811 | 624 | +37 | +0.20 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 2659 | +72 | +0.38 | +12 |
| next_open | 2570 | +80 | +0.49 | +20 |
| next_close | 2571 | +81 | +1.20 | +21 |

Controls: placebo (lag 20) z @0 +0.65, @base -0.82 on 2890 trades; planted +50 bps z +1.24 vs actual +0.49 (shift +0.75).

**1b-5d / smallcap / dev — direction long, decision horizon 5 sessions, next-open fill**

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 13039 | 1541 | 11409 | 2504 | -45 | -68 | -91 | -136 | -458 | 0.418 | -100 | +16 | -6.35 | 6.2% | -6.67 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 11409 | -29 | -4.27 | -75 | -9.77 |
| 5 * | 11409 | -45 | -3.39 | -91 | -6.35 |
| 21 | 11154 | -95 | -4.26 | -141 | -6.09 |
| 63 | 10534 | -116 | -3.32 | -162 | -4.42 |
| 126 | 9855 | -43 | -0.74 | -88 | -1.38 |
| 252 | 8769 | -82 | -0.51 | -128 | -0.80 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2010 | 738 | 220 | -14 | -1.54 |
| 2011 | 819 | 204 | -109 | -3.78 |
| 2012 | 582 | 202 | -136 | -2.76 |
| 2013 | 647 | 221 | -32 | -1.39 |
| 2014 | 777 | 228 | -59 | -1.08 |
| 2015 | 810 | 224 | -62 | -2.83 |
| 2016 | 902 | 231 | -44 | -0.66 |
| 2017 | 1050 | 246 | -35 | -0.56 |
| 2018 | 1220 | 240 | -106 | -2.67 |
| 2019 | 1224 | 243 | -128 | -3.25 |
| 2020 | 2640 | 245 | -142 | -2.04 |
| half1 | 3963 | 1189 | -74 | -5.02 |
| half2 | 7446 | 1315 | -99 | -4.15 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 11593 | -23 | -1.97 | -69 |
| next_open | 11409 | -45 | -3.39 | -91 |
| next_close | 11409 | -25 | -2.22 | -71 |

Controls: placebo (lag 20) z @0 -0.39, @base -3.77 on 12365 trades; planted +50 bps z -0.20 vs actual -3.39 (shift +3.19).

**1b-5d / uncapped / dev — direction long, decision horizon 5 sessions, next-open fill**

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 24012 | 2322 | 21587 | 2689 | -28 | -48 | -67 | -105 | -388 | 0.433 | -78 | +12 | -6.45 | 6.6% | -6.47 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 21587 | -20 | -3.93 | -58 | -9.97 |
| 5 * | 21587 | -28 | -3.15 | -67 | -6.45 |
| 21 | 21235 | -60 | -3.39 | -99 | -5.42 |
| 63 | 20000 | -79 | -2.51 | -118 | -3.76 |
| 126 | 18923 | +11 | +0.36 | -27 | -0.30 |
| 252 | 16980 | +63 | +1.36 | +24 | +1.09 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2010 | 1532 | 242 | -30 | -1.80 |
| 2011 | 2031 | 241 | -68 | -4.30 |
| 2012 | 1284 | 232 | -67 | -2.79 |
| 2013 | 1235 | 242 | -20 | -0.90 |
| 2014 | 1394 | 245 | -50 | -1.84 |
| 2015 | 1506 | 247 | -32 | -2.62 |
| 2016 | 1856 | 248 | -29 | -1.76 |
| 2017 | 1762 | 249 | -32 | -0.57 |
| 2018 | 2192 | 249 | -82 | -2.95 |
| 2019 | 2188 | 248 | -65 | -2.80 |
| 2020 | 4607 | 246 | -130 | -1.85 |
| half1 | 8168 | 1325 | -50 | -5.39 |
| half2 | 13419 | 1364 | -77 | -4.09 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 21865 | -13 | -1.94 | -52 |
| next_open | 21587 | -28 | -3.15 | -67 |
| next_close | 21587 | -17 | -1.96 | -55 |

Controls: placebo (lag 20) z @0 -0.39, @base -4.20 on 20406 trades; planted +50 bps z +1.01 vs actual -3.15 (shift +4.15).

**1c-long / crypto / dev — direction long, decision horizon 21 sessions, next-open fill**

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @alt80 | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3174 | 1517 | 1634 | 671 | +247 | +207 | +187 | +147 | +167 | -472 | 0.373 | +165 | +167 | +0.99 | 15.0% | -0.43 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 1634 | +26 | -0.08 | -34 | -1.89 |
| 5 | 1634 | +75 | +0.40 | +15 | -0.47 |
| 21 * | 1634 | +247 | +1.35 | +187 | +0.99 |
| 63 | 1558 | +121 | +0.82 | +61 | +0.68 |
| 126 | 1492 | +1152 | +1.90 | +1092 | +1.84 |
| 252 | 1366 | +587 | +0.16 | +527 | +0.14 |
| i04 | 1616 | -12 | -2.34 | -72 | -8.09 |
| i12 | 1633 | -17 | -1.56 | -77 | -4.84 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2018 | 31 | 21 | -254 | -1.36 |
| 2019 | 153 | 90 | -156 | -0.40 |
| 2020 | 524 | 202 | +358 | +0.94 |
| 2021 | 576 | 220 | +424 | +1.31 |
| 2022 | 350 | 138 | -268 | -1.79 |
| half1 | 452 | 207 | +141 | +0.01 |
| half2 | 1182 | 464 | +205 | +1.03 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 1653 | +241 | +1.01 | +181 |
| next_open | 1634 | +247 | +1.35 | +187 |
| next_close | 1634 | +219 | +1.30 | +159 |

Controls: placebo (lag 20) z @0 +0.32, @base -0.15 on 1669 trades; planted +50 bps z +1.65 vs actual +1.35 (shift +0.30).

**1c-long / smallcap / dev — direction long, decision horizon 21 sessions, next-open fill**

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 16379 | 6910 | 8969 | 2210 | -12 | -34 | -56 | -101 | -454 | 0.445 | -40 | +27 | -1.46 | 7.0% | -1.67 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 8969 | +1 | +0.81 | -44 | -2.07 |
| 5 | 8969 | -8 | +0.39 | -53 | -2.03 |
| 21 * | 8969 | -12 | +0.21 | -56 | -1.46 |
| 63 | 8410 | +24 | +0.51 | -21 | -0.37 |
| 126 | 7829 | +52 | +1.00 | +8 | +0.49 |
| 252 | 6793 | +97 | +0.77 | +52 | +0.38 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2010 | 658 | 189 | -18 | +0.23 |
| 2011 | 544 | 165 | +2 | +0.24 |
| 2012 | 450 | 173 | -41 | -0.25 |
| 2013 | 459 | 192 | -58 | -0.81 |
| 2014 | 553 | 184 | +47 | -0.11 |
| 2015 | 616 | 205 | +16 | -0.49 |
| 2016 | 784 | 209 | -65 | +0.08 |
| 2017 | 738 | 224 | -16 | -0.66 |
| 2018 | 859 | 224 | -9 | -0.27 |
| 2019 | 1132 | 229 | -141 | -2.86 |
| 2020 | 2176 | 216 | -118 | +0.09 |
| half1 | 2976 | 1009 | -13 | -0.59 |
| half2 | 5993 | 1201 | -78 | -1.40 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 9050 | -11 | +0.25 | -55 |
| next_open | 8969 | -12 | +0.21 | -56 |
| next_close | 8969 | -3 | +0.65 | -48 |

Controls: placebo (lag 20) z @0 -0.83, @base -2.29 on 9207 trades; planted +50 bps z +2.03 vs actual +0.21 (shift +1.82).

**1c-long / uncapped / dev — direction long, decision horizon 21 sessions, next-open fill**

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 33254 | 14012 | 18460 | 2510 | -19 | -37 | -56 | -92 | -415 | 0.443 | -47 | +20 | -2.30 | 8.3% | -2.38 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 18460 | -8 | +1.16 | -44 | -4.15 |
| 5 | 18460 | -11 | +0.22 | -47 | -3.10 |
| 21 * | 18460 | -19 | -0.39 | -56 | -2.30 |
| 63 | 17212 | +11 | -0.47 | -25 | -1.52 |
| 126 | 16101 | +74 | +1.33 | +37 | +0.68 |
| 252 | 13823 | +127 | +0.89 | +90 | +0.44 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2010 | 1473 | 222 | -9 | +0.48 |
| 2011 | 1359 | 203 | -30 | -1.14 |
| 2012 | 1080 | 214 | -48 | -0.48 |
| 2013 | 940 | 229 | +11 | -0.05 |
| 2014 | 1030 | 219 | +47 | -0.42 |
| 2015 | 1175 | 236 | -51 | -1.04 |
| 2016 | 1778 | 237 | -85 | -0.80 |
| 2017 | 1282 | 242 | -35 | -1.03 |
| 2018 | 1539 | 240 | +10 | -0.44 |
| 2019 | 2167 | 245 | -94 | -2.68 |
| 2020 | 4637 | 223 | -115 | -0.23 |
| half1 | 6461 | 1206 | -10 | -0.92 |
| half2 | 11999 | 1304 | -80 | -2.25 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 18610 | -19 | -0.18 | -55 |
| next_open | 18460 | -19 | -0.39 | -56 |
| next_close | 18460 | -10 | -0.25 | -46 |

Controls: placebo (lag 20) z @0 -0.15, @base -1.86 on 17432 trades; planted +50 bps z +2.07 vs actual -0.39 (shift +2.46).

**1c-short / crypto / dev — direction short, decision horizon 21 sessions, next-open fill**

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @alt80 | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 488 | 111 | 361 | 122 | +291 | +251 | +231 | +191 | +211 | -430 | 0.593 | +357 | +148 | +2.41 | 37.7% | +2.19 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 361 | +23 | +2.97 | -37 | +1.30 |
| 5 | 361 | +36 | +2.93 | -24 | +2.12 |
| 21 * | 361 | +291 | +2.82 | +231 | +2.41 |
| 63 | 354 | +873 | +3.60 | +813 | +3.46 |
| 126 | 341 | +1353 | +2.75 | +1293 | +2.69 |
| 252 | 282 | -3566 | +0.01 | -3626 | -0.00 |
| i04 | 361 | +1 | +1.53 | -59 | -3.33 |
| i12 | 361 | +4 | +0.20 | -56 | -2.11 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2018 | 3 | 3 | -432 | -1.72 |
| 2019 | 25 | 12 | -132 | -1.67 |
| 2020 | 94 | 30 | +321 | +2.26 |
| 2021 | 147 | 36 | +340 | +1.71 |
| 2022 | 92 | 41 | +84 | +0.85 |
| half1 | 72 | 27 | +211 | +0.16 |
| half2 | 289 | 95 | +236 | +2.56 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 361 | +307 | +2.95 | +247 |
| next_open | 361 | +291 | +2.82 | +231 |
| next_close | 361 | +252 | +2.40 | +192 |

Controls: placebo (lag 20) z @0 +0.93, @base +0.50 on 334 trades; planted +50 bps z +3.16 vs actual +2.82 (shift +0.34).

**1c-short / smallcap / dev — direction short, decision horizon 21 sessions, next-open fill**

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 8812 | 3007 | 5711 | 1860 | +18 | -3 | -24 | -65 | -382 | 0.512 | -47 | +30 | -1.56 | 7.1% | -1.29 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 5711 | -6 | -0.72 | -47 | -6.18 |
| 5 | 5711 | -6 | -1.82 | -48 | -4.08 |
| 21 * | 5711 | +18 | -0.17 | -24 | -1.56 |
| 63 | 5605 | -6 | -1.05 | -47 | -1.87 |
| 126 | 5343 | +99 | +0.34 | +58 | -0.24 |
| 252 | 4696 | +52 | -0.23 | +11 | -0.61 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2010 | 336 | 125 | +2 | +1.24 |
| 2011 | 467 | 148 | -130 | -0.86 |
| 2012 | 279 | 135 | -1 | +0.15 |
| 2013 | 280 | 151 | +67 | +0.38 |
| 2014 | 410 | 169 | +1 | -0.62 |
| 2015 | 517 | 184 | -110 | -1.30 |
| 2016 | 486 | 167 | -38 | -0.06 |
| 2017 | 542 | 188 | -15 | -0.40 |
| 2018 | 739 | 203 | -139 | -2.21 |
| 2019 | 640 | 207 | -67 | -0.69 |
| 2020 | 1015 | 183 | +132 | +0.02 |
| half1 | 1962 | 817 | -27 | -0.12 |
| half2 | 3749 | 1043 | -22 | -1.88 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 5735 | +14 | -0.29 | -27 |
| next_open | 5711 | +18 | -0.17 | -24 |
| next_close | 5711 | +14 | -0.15 | -27 |

Controls: placebo (lag 20) z @0 +0.03, @base -1.32 on 5406 trades; planted +50 bps z +1.48 vs actual -0.17 (shift +1.65).

**1c-short / uncapped / dev — direction short, decision horizon 21 sessions, next-open fill**

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 17580 | 5880 | 11578 | 2245 | -9 | -26 | -43 | -77 | -363 | 0.502 | -53 | +23 | -2.32 | 7.9% | -2.22 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 11578 | -0 | -0.92 | -34 | -6.91 |
| 5 | 11578 | -6 | -1.91 | -40 | -4.52 |
| 21 * | 11578 | -9 | -0.76 | -43 | -2.32 |
| 63 | 11397 | +0 | -0.92 | -34 | -1.83 |
| 126 | 10947 | +53 | -0.02 | +19 | -0.64 |
| 252 | 9526 | +62 | -0.02 | +27 | -0.43 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2010 | 819 | 175 | +7 | +0.39 |
| 2011 | 1176 | 189 | -82 | -0.90 |
| 2012 | 600 | 189 | -35 | -0.11 |
| 2013 | 547 | 190 | +127 | +1.02 |
| 2014 | 735 | 204 | -16 | -0.54 |
| 2015 | 986 | 213 | -129 | -1.98 |
| 2016 | 1105 | 205 | -50 | +0.33 |
| 2017 | 937 | 221 | -42 | -0.98 |
| 2018 | 1436 | 226 | -141 | -2.70 |
| 2019 | 1185 | 233 | -71 | -1.47 |
| 2020 | 2052 | 200 | +32 | -0.21 |
| half1 | 4222 | 1050 | -25 | -0.36 |
| half2 | 7356 | 1195 | -53 | -2.73 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 11624 | -11 | -1.04 | -45 |
| next_open | 11578 | -9 | -0.76 | -43 |
| next_close | 11578 | -14 | -0.72 | -48 |

Controls: placebo (lag 20) z @0 +0.64, @base -0.87 on 11720 trades; planted +50 bps z +1.41 vs actual -0.76 (shift +2.17).

**1d / BTCUSDT / dev — weekly, Sunday close → Monday 01:00 UTC fill**

| cost | weeks | ann. excess (pp) | mean weekly diff (bps) | SE | z | hit | ann. ret strat | ann. ret comp | vol strat | vol comp | max DD strat | max DD comp | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 259 | +9.9 | +19 | +52 | +0.37 | 0.340 | +34.9% | +1.1% | 40% | 73% | -38% | -76% | 19.9% | -0.10 |
| low | 259 | +8.5 | +16 | +52 | +0.31 | 0.336 | +33.0% | +1.1% | 40% | 73% | -40% | -76% | 19.8% | -0.16 |
| base | 259 | +7.8 | +15 | +52 | +0.29 | 0.336 | +32.0% | +1.1% | 40% | 73% | -40% | -76% | 19.8% | -0.19 |
| high | 259 | +6.3 | +12 | +52 | +0.23 | 0.336 | +30.1% | +1.1% | 41% | 73% | -42% | -76% | 19.7% | -0.26 |
| alt80 | 259 | +7.0 | +14 | +52 | +0.26 | 0.336 | +31.1% | +1.1% | 40% | 73% | -41% | -76% | 19.8% | -0.22 |

time in market 0.29, round trips per year 3.6. Per period at base cost:
| period | weeks | ann. excess (pp) | z |
|---|---|---|---|
| 2018 | 52 | +76.1 | +0.90 |
| 2019 | 52 | -1.2 | -0.03 |
| 2020 | 52 | -69.5 | -1.35 |
| 2021 | 52 | -45.2 | -0.83 |
| 2022 | 51 | +80.0 | +1.39 |
| half1 | 130 | +8.2 | +0.19 |
| half2 | 129 | +7.3 | +0.23 |

Controls: placebo (lag 20 days) z @0 +0.49, @base +0.41; planted +50 bps/week z +1.33 vs actual +0.37 (shift +0.96).

**1d / ETHUSDT / dev — weekly, Sunday close → Monday 01:00 UTC fill**

| cost | weeks | ann. excess (pp) | mean weekly diff (bps) | SE | z | hit | ann. ret strat | ann. ret comp | vol strat | vol comp | max DD strat | max DD comp | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 259 | +18.2 | +35 | +67 | +0.52 | 0.336 | +65.4% | +0.5% | 59% | 98% | -48% | -94% | 19.9% | -0.38 |
| low | 259 | +17.0 | +33 | +67 | +0.48 | 0.336 | +63.5% | +0.5% | 59% | 98% | -49% | -94% | 19.8% | -0.43 |
| base | 259 | +16.4 | +32 | +67 | +0.47 | 0.336 | +62.5% | +0.5% | 59% | 98% | -49% | -94% | 19.8% | -0.45 |
| high | 259 | +15.2 | +29 | +67 | +0.43 | 0.336 | +60.6% | +0.5% | 58% | 98% | -49% | -94% | 19.7% | -0.49 |
| alt80 | 259 | +15.8 | +30 | +67 | +0.45 | 0.336 | +61.6% | +0.5% | 59% | 98% | -49% | -94% | 19.8% | -0.47 |

time in market 0.33, round trips per year 3.0. Per period at base cost:
| period | weeks | ann. excess (pp) | z |
|---|---|---|---|
| 2018 | 52 | +120.3 | +0.97 |
| 2019 | 52 | +18.5 | +0.33 |
| 2020 | 52 | -71.3 | -1.34 |
| 2021 | 52 | -55.6 | -1.16 |
| 2022 | 51 | +71.1 | +0.84 |
| half1 | 130 | +35.9 | +0.62 |
| half2 | 129 | -3.2 | -0.08 |

Controls: placebo (lag 20 days) z @0 -0.15, @base -0.19; planted +50 bps/week z +1.26 vs actual +0.52 (shift +0.74).

**1e / crypto / dev — weekly, Sunday close → Monday 01:00 UTC fill**

| cost | weeks | ann. excess (pp) | mean weekly diff (bps) | SE | z | hit | ann. ret strat | ann. ret comp | vol strat | vol comp | max DD strat | max DD comp | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 255 | -1.9 | -4 | +45 | -0.08 | 0.455 | -17.4% | -10.6% | 104% | 95% | -93% | -89% | 20.4% | -0.76 |
| low | 255 | -8.9 | -17 | +45 | -0.38 | 0.427 | -23.1% | -10.6% | 104% | 95% | -94% | -89% | 20.3% | -1.17 |
| base | 255 | -12.4 | -24 | +45 | -0.53 | 0.416 | -25.8% | -10.6% | 104% | 95% | -95% | -89% | 20.3% | -1.38 |
| high | 255 | -19.4 | -37 | +45 | -0.83 | 0.404 | -30.9% | -10.6% | 104% | 95% | -95% | -89% | 20.2% | -1.79 |
| alt80 | 255 | -15.9 | -31 | +45 | -0.68 | 0.404 | -28.4% | -10.6% | 104% | 95% | -95% | -89% | 20.3% | -1.59 |

round trips per year 17.3. Per period at base cost:
| period | weeks | ann. excess (pp) | z |
|---|---|---|---|
| 2018 | 48 | -6.6 | -0.13 |
| 2019 | 52 | -2.0 | -0.06 |
| 2020 | 52 | +36.8 | +0.64 |
| 2021 | 52 | -30.9 | -0.41 |
| 2022 | 51 | -59.9 | -1.89 |
| half1 | 126 | +1.6 | +0.06 |
| half2 | 129 | -26.1 | -0.67 |

Controls: placebo (lag 20 days) z @0 -1.84, @base -2.43; planted +50 bps/week z +1.03 vs actual -0.08 (shift +1.11).
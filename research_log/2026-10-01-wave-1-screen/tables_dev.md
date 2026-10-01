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

**a2r-down-close / smallcap / dev — direction short, decision horizon 63 sessions, next-open fill**

Autopsy rule on `close` (top quintile, selection lift 2.24): match rate 20.3% of the universe per day; 28 of 3834 trades made the original 63-session move (0.73%) against a universe base rate of 0.24% (realized lift 2.99).

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 140565 | 127966 | 3834 | 1878 | +577 | +553 | +530 | +483 | +31 | 0.622 | +502 | +72 | +7.00 | 6.2% | +9.83 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 3834 | +19 | +1.85 | -28 | -2.62 |
| 5 | 3834 | +87 | +4.13 | +40 | +1.76 |
| 21 | 3834 | +204 | +5.05 | +157 | +3.87 |
| 63 * | 3834 | +577 | +7.67 | +530 | +7.00 |
| 126 | 3658 | +1002 | +10.14 | +955 | +9.62 |
| 252 | 3200 | +1679 | +12.16 | +1632 | +11.80 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2010 | 290 | 144 | +391 | +1.48 |
| 2011 | 329 | 160 | +300 | +2.27 |
| 2012 | 218 | 144 | +242 | +1.40 |
| 2013 | 208 | 143 | +519 | +2.41 |
| 2014 | 261 | 159 | +589 | +2.33 |
| 2015 | 294 | 167 | +543 | +3.58 |
| 2016 | 365 | 189 | +819 | +5.35 |
| 2017 | 340 | 187 | +444 | +0.70 |
| 2018 | 434 | 205 | +676 | +4.21 |
| 2019 | 461 | 207 | +463 | +0.79 |
| 2020 | 634 | 173 | +614 | +2.85 |
| half1 | 1435 | 835 | +431 | +5.38 |
| half2 | 2399 | 1043 | +589 | +4.83 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 3884 | +582 | +9.75 | +535 |
| next_open | 3834 | +577 | +7.67 | +530 |
| next_close | 3834 | +565 | +7.40 | +518 |

Controls: placebo (lag 20) z @0 +7.95, @base +7.37 on 2729 trades; planted +50 bps z +8.36 vs actual +7.67 (shift +0.70).

**a2r-down-close / uncapped / dev — direction short, decision horizon 63 sessions, next-open fill**

Autopsy rule on `close` (top quintile, selection lift 2.24): match rate 20.2% of the universe per day; 31 of 8908 trades made the original 63-session move (0.35%) against a universe base rate of 0.18% (realized lift 1.95).

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 277825 | 252808 | 8908 | 2389 | +366 | +349 | +333 | +299 | -16 | 0.577 | +352 | +45 | +7.88 | 4.7% | +9.36 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 8908 | +13 | +2.21 | -21 | -3.52 |
| 5 | 8908 | +43 | +4.41 | +9 | +1.48 |
| 21 | 8908 | +122 | +6.41 | +88 | +4.88 |
| 63 * | 8908 | +366 | +8.70 | +333 | +7.88 |
| 126 | 8525 | +617 | +10.44 | +583 | +9.87 |
| 252 | 7390 | +1109 | +15.63 | +1074 | +15.20 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2010 | 804 | 210 | +242 | +3.46 |
| 2011 | 929 | 216 | +148 | +2.03 |
| 2012 | 506 | 196 | +213 | +2.81 |
| 2013 | 441 | 211 | +552 | +2.29 |
| 2014 | 514 | 208 | +414 | +2.23 |
| 2015 | 659 | 228 | +195 | +3.04 |
| 2016 | 900 | 233 | +635 | +6.23 |
| 2017 | 662 | 229 | +279 | +0.35 |
| 2018 | 996 | 236 | +357 | +4.15 |
| 2019 | 979 | 239 | +227 | +1.41 |
| 2020 | 1518 | 183 | +398 | +3.50 |
| half1 | 3445 | 1149 | +288 | +5.90 |
| half2 | 5463 | 1240 | +361 | +5.32 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 9006 | +367 | +11.10 | +333 |
| next_open | 8908 | +366 | +8.70 | +333 |
| next_close | 8908 | +361 | +8.32 | +328 |

Controls: placebo (lag 20) z @0 +9.12, @base +8.44 on 5240 trades; planted +50 bps z +9.82 vs actual +8.70 (shift +1.12).

**a2r-down-ret_20 / smallcap / dev — direction short, decision horizon 63 sessions, next-open fill**

Autopsy rule on `ret_20` (top quintile, selection lift 2.14): match rate 20.3% of the universe per day; 34 of 9495 trades made the original 63-session move (0.36%) against a universe base rate of 0.24% (realized lift 1.46).

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 140574 | 122313 | 9495 | 2535 | +69 | +44 | +20 | -30 | -453 | 0.558 | -53 | +42 | -1.25 | 5.9% | -0.98 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 9495 | +3 | -0.40 | -47 | -7.64 |
| 5 | 9495 | +21 | +0.73 | -28 | -3.03 |
| 21 | 9495 | +27 | +0.79 | -22 | -1.27 |
| 63 * | 9495 | +69 | -0.05 | +20 | -1.25 |
| 126 | 9006 | +44 | -1.24 | -5 | -2.00 |
| 252 | 7820 | -21 | -0.74 | -70 | -1.14 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2010 | 722 | 228 | -124 | -1.09 |
| 2011 | 816 | 235 | -41 | -1.46 |
| 2012 | 503 | 213 | -169 | -0.99 |
| 2013 | 470 | 216 | -134 | -0.70 |
| 2014 | 643 | 227 | -91 | -1.37 |
| 2015 | 774 | 243 | -3 | +0.22 |
| 2016 | 876 | 242 | +191 | +2.09 |
| 2017 | 811 | 243 | +4 | +0.08 |
| 2018 | 1075 | 248 | +103 | +0.47 |
| 2019 | 1130 | 251 | +3 | -0.27 |
| 2020 | 1675 | 189 | +140 | -0.90 |
| half1 | 3475 | 1237 | -89 | -2.18 |
| half2 | 6020 | 1298 | +82 | +0.39 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 9575 | +68 | +0.29 | +19 |
| next_open | 9495 | +69 | -0.05 | +20 |
| next_close | 9495 | +56 | -0.31 | +7 |

Controls: placebo (lag 20) z @0 +0.49, @base -0.40 on 6600 trades; planted +50 bps z +1.14 vs actual -0.05 (shift +1.19).

**a2r-down-ret_20 / uncapped / dev — direction short, decision horizon 63 sessions, next-open fill**

Autopsy rule on `ret_20` (top quintile, selection lift 2.14): match rate 20.2% of the universe per day; 42 of 19391 trades made the original 63-session move (0.22%) against a universe base rate of 0.18% (realized lift 1.21).

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 277823 | 242323 | 19391 | 2676 | +73 | +53 | +33 | -6 | -368 | 0.552 | -13 | +29 | -0.45 | 6.5% | -0.43 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 19391 | +3 | +0.27 | -37 | -9.83 |
| 5 | 19391 | +15 | +0.38 | -25 | -4.12 |
| 21 | 19391 | +23 | +0.68 | -16 | -1.76 |
| 63 * | 19391 | +73 | +0.98 | +33 | -0.45 |
| 126 | 18461 | +56 | -0.62 | +17 | -1.54 |
| 252 | 15734 | -41 | -1.49 | -81 | -1.97 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2010 | 1751 | 251 | +0 | +0.34 |
| 2011 | 2173 | 249 | +44 | -0.96 |
| 2012 | 1100 | 244 | -32 | -0.55 |
| 2013 | 874 | 248 | -158 | -1.29 |
| 2014 | 1166 | 245 | -75 | -0.71 |
| 2015 | 1476 | 248 | -37 | +0.03 |
| 2016 | 1813 | 250 | +205 | +2.19 |
| 2017 | 1331 | 250 | -62 | -0.26 |
| 2018 | 2041 | 250 | +53 | +0.79 |
| 2019 | 2009 | 252 | -17 | -0.79 |
| 2020 | 3657 | 189 | +137 | +0.19 |
| half1 | 7631 | 1358 | -23 | -1.22 |
| half2 | 11760 | 1318 | +70 | +0.64 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 19541 | +74 | +1.42 | +34 |
| next_open | 19391 | +73 | +0.98 | +33 |
| next_close | 19391 | +65 | +0.58 | +26 |

Controls: placebo (lag 20) z @0 +1.01, @base -0.01 on 12641 trades; planted +50 bps z +2.69 vs actual +0.98 (shift +1.70).

**a2r-down-ret_60 / crypto / dev — direction short, decision horizon 63 sessions, next-open fill**

Autopsy rule on `ret_60` (top quintile, selection lift 3.20): match rate 20.0% of the universe per day; 5 of 929 trades made the original 63-session move (0.54%) against a universe base rate of 0.15% (realized lift 3.60).

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @alt80 | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 25248 | 22732 | 929 | 677 | +382 | +342 | +322 | +282 | +302 | -434 | 0.656 | +232 | +431 | +0.54 | 17.7% | +4.04 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 929 | +7 | -0.35 | -53 | -1.43 |
| 5 | 929 | +8 | -0.69 | -52 | -1.36 |
| 21 | 929 | +173 | +0.89 | +113 | +0.49 |
| 63 * | 929 | +382 | +0.68 | +322 | +0.54 |
| 126 | 872 | +855 | +0.90 | +795 | +0.83 |
| 252 | 747 | +876 | +1.25 | +816 | +1.21 |
| i04 | 928 | -44 | -1.79 | -104 | -4.45 |
| i12 | 929 | -39 | -1.18 | -99 | -3.03 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2018 | 34 | 32 | -427 | -0.96 |
| 2019 | 106 | 95 | +5 | -0.24 |
| 2020 | 245 | 180 | +233 | +0.84 |
| 2021 | 279 | 193 | +580 | +0.15 |
| 2022 | 265 | 177 | +357 | +0.77 |
| half1 | 262 | 217 | -79 | -0.09 |
| half2 | 667 | 460 | +480 | +0.58 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 937 | +398 | +0.55 | +338 |
| next_open | 929 | +382 | +0.68 | +322 |
| next_close | 929 | +292 | +0.53 | +232 |

Controls: placebo (lag 20) z @0 -0.83, @base -0.93 on 859 trades; planted +50 bps z +0.79 vs actual +0.68 (shift +0.12).

**a2r-down-rvol_20 / crypto / dev — direction short, decision horizon 63 sessions, next-open fill**

Autopsy rule on `rvol_20` (top quintile, selection lift 3.23): match rate 22.0% of the universe per day; 4 of 1149 trades made the original 63-session move (0.35%) against a universe base rate of 0.15% (realized lift 2.33).

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @alt80 | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 27044 | 24187 | 1149 | 821 | +142 | +102 | +82 | +42 | +62 | -806 | 0.694 | -187 | +381 | -0.49 | 18.3% | +1.82 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 1148 | -17 | -0.64 | -77 | -1.84 |
| 5 | 1149 | -4 | -0.78 | -64 | -1.49 |
| 21 | 1149 | +131 | +0.08 | +71 | -0.30 |
| 63 * | 1149 | +142 | -0.33 | +82 | -0.49 |
| 126 | 1088 | -364 | -1.24 | -424 | -1.29 |
| 252 | 945 | +2136 | +0.78 | +2076 | +0.75 |
| i04 | 1144 | -16 | -1.04 | -76 | -5.09 |
| i12 | 1148 | -31 | -1.45 | -91 | -3.73 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2018 | 45 | 42 | +393 | +1.47 |
| 2019 | 153 | 124 | +535 | +1.62 |
| 2020 | 299 | 210 | +53 | -0.37 |
| 2021 | 363 | 246 | -253 | -0.86 |
| 2022 | 289 | 199 | +244 | +0.41 |
| half1 | 344 | 273 | -64 | -0.20 |
| half2 | 805 | 548 | +144 | -0.45 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 1157 | +158 | +0.05 | +98 |
| next_open | 1149 | +142 | -0.33 | +82 |
| next_close | 1149 | +45 | -0.58 | -15 |

Controls: placebo (lag 20) z @0 -0.97, @base -1.12 on 1050 trades; planted +50 bps z -0.20 vs actual -0.33 (shift +0.13).

**a2r-down-rvol_20 / smallcap / dev — direction short, decision horizon 63 sessions, next-open fill**

Autopsy rule on `rvol_20` (top quintile, selection lift 2.21): match rate 20.3% of the universe per day; 29 of 6021 trades made the original 63-session move (0.48%) against a universe base rate of 0.24% (realized lift 1.97).

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 140574 | 125787 | 6021 | 2261 | +18 | -8 | -33 | -85 | -653 | 0.571 | +43 | +67 | +0.65 | 7.2% | +2.29 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 6021 | +28 | +2.64 | -24 | -2.46 |
| 5 | 6021 | +43 | +2.98 | -8 | +0.26 |
| 21 | 6021 | +63 | +2.06 | +11 | +0.64 |
| 63 * | 6021 | +18 | +1.44 | -33 | +0.65 |
| 126 | 5704 | +37 | +1.16 | -15 | +0.59 |
| 252 | 4901 | +279 | +0.55 | +227 | +0.23 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2010 | 435 | 192 | -72 | -1.58 |
| 2011 | 489 | 206 | +43 | +0.76 |
| 2012 | 315 | 178 | +12 | +0.48 |
| 2013 | 304 | 182 | +145 | +0.56 |
| 2014 | 407 | 198 | +5 | +0.42 |
| 2015 | 482 | 214 | +239 | +1.72 |
| 2016 | 522 | 220 | -136 | -0.26 |
| 2017 | 529 | 213 | +203 | +1.16 |
| 2018 | 695 | 232 | +219 | +2.31 |
| 2019 | 723 | 240 | +126 | +0.70 |
| 2020 | 1120 | 186 | -567 | -1.40 |
| half1 | 2152 | 1059 | +60 | +0.88 |
| half2 | 3869 | 1202 | -85 | +0.21 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 6066 | -20 | +1.44 | -71 |
| next_open | 6021 | +18 | +1.44 | -33 |
| next_close | 6021 | -24 | +0.99 | -75 |

Controls: placebo (lag 20) z @0 +0.28, @base -0.37 on 4669 trades; planted +50 bps z +2.19 vs actual +1.44 (shift +0.75).

**a2r-down-rvol_20 / uncapped / dev — direction short, decision horizon 63 sessions, next-open fill**

Autopsy rule on `rvol_20` (top quintile, selection lift 2.21): match rate 20.2% of the universe per day; 32 of 11430 trades made the original 63-session move (0.28%) against a universe base rate of 0.18% (realized lift 1.57).

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 277822 | 250283 | 11430 | 2543 | -28 | -50 | -72 | -116 | -590 | 0.553 | +8 | +46 | +0.18 | 6.8% | +0.75 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 11430 | +19 | +2.25 | -25 | -4.39 |
| 5 | 11430 | +38 | +2.15 | -6 | -0.93 |
| 21 | 11430 | +46 | +2.02 | +2 | +0.20 |
| 63 * | 11430 | -28 | +1.20 | -72 | +0.18 |
| 126 | 10908 | -85 | +0.69 | -128 | +0.02 |
| 252 | 9213 | +67 | +0.88 | +23 | +0.47 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2010 | 962 | 228 | +26 | +0.26 |
| 2011 | 1206 | 239 | +4 | +0.95 |
| 2012 | 661 | 228 | -0 | +0.06 |
| 2013 | 540 | 215 | -40 | -0.30 |
| 2014 | 661 | 219 | +24 | +0.05 |
| 2015 | 854 | 242 | +86 | +1.82 |
| 2016 | 1028 | 244 | -156 | -0.57 |
| 2017 | 830 | 244 | +68 | +0.17 |
| 2018 | 1242 | 245 | +24 | +0.83 |
| 2019 | 1229 | 250 | +39 | +0.13 |
| 2020 | 2217 | 189 | -403 | -1.91 |
| half1 | 4378 | 1248 | +21 | +0.57 |
| half2 | 7052 | 1295 | -130 | -0.26 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 11535 | -46 | +0.77 | -90 |
| next_open | 11430 | -28 | +1.20 | -72 |
| next_close | 11430 | -52 | +0.71 | -96 |

Controls: placebo (lag 20) z @0 +0.47, @base -0.35 on 8938 trades; planted +50 bps z +2.29 vs actual +1.20 (shift +1.10).

**a2r-down-vol_pctl_250 / crypto / dev — direction short, decision horizon 63 sessions, next-open fill**

Autopsy rule on `vol_pctl_250` (top quintile, selection lift 3.33): match rate 12.0% of the universe per day; 0 of 1102 trades made the original 63-session move (0.00%) against a universe base rate of 0.15% (realized lift 0.00).

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @alt80 | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 18005 | 15444 | 1102 | 722 | +18 | -22 | -42 | -82 | -62 | -705 | 0.644 | -172 | +366 | -0.47 | 17.3% | +2.29 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 1102 | +11 | -0.09 | -49 | -1.42 |
| 5 | 1102 | -122 | -1.60 | -182 | -2.43 |
| 21 | 1102 | -216 | -1.49 | -276 | -1.79 |
| 63 * | 1102 | +18 | -0.31 | -42 | -0.47 |
| 126 | 1018 | -504 | -0.76 | -564 | -0.81 |
| 252 | 856 | +422 | +0.45 | +362 | +0.41 |
| i04 | 1098 | -14 | -1.67 | -74 | -5.75 |
| i12 | 1102 | -9 | -0.83 | -69 | -3.16 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2018 | 12 | 11 | -886 | -1.39 |
| 2019 | 90 | 82 | -239 | -1.13 |
| 2020 | 272 | 188 | +736 | +0.57 |
| 2021 | 376 | 230 | -532 | -0.87 |
| 2022 | 352 | 211 | -43 | +0.24 |
| half1 | 226 | 180 | +10 | -0.73 |
| half2 | 876 | 542 | -56 | -0.27 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 1117 | +31 | -0.52 | -29 |
| next_open | 1102 | +18 | -0.31 | -42 |
| next_close | 1102 | +35 | -0.32 | -25 |

Controls: placebo (lag 20) z @0 +0.28, @base +0.07 on 991 trades; planted +50 bps z -0.17 vs actual -0.31 (shift +0.14).

**a2r-up-close / crypto / dev — direction long, decision horizon 63 sessions, next-open fill**

Autopsy rule on `close` (bottom quintile, selection lift 1.74): match rate 19.0% of the universe per day; 18 of 547 trades made the original 63-session move (3.29%) against a universe base rate of 1.21% (realized lift 2.73).

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @alt80 | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 25249 | 23232 | 547 | 454 | +1901 | +1861 | +1841 | +1801 | +1821 | +1096 | 0.356 | +1183 | +806 | +1.47 | 41.8% | -2.45 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 547 | +19 | +0.45 | -41 | -0.73 |
| 5 | 547 | +41 | +0.05 | -19 | -0.63 |
| 21 | 547 | +220 | +0.56 | +160 | +0.35 |
| 63 * | 547 | +1901 | +1.54 | +1841 | +1.47 |
| 126 | 509 | +5671 | +2.46 | +5611 | +2.43 |
| 252 | 431 | +13601 | +2.92 | +13541 | +2.91 |
| i04 | 542 | +23 | +1.15 | -37 | -2.26 |
| i12 | 547 | +50 | +1.54 | -10 | -0.20 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2018 | 14 | 14 | +646 | +0.96 |
| 2019 | 58 | 51 | -1060 | -3.14 |
| 2020 | 147 | 124 | +1178 | +0.48 |
| 2021 | 174 | 135 | +5279 | +2.16 |
| 2022 | 154 | 130 | -209 | -1.76 |
| half1 | 131 | 112 | +341 | +0.05 |
| half2 | 416 | 342 | +2314 | +1.48 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 553 | +1509 | +1.90 | +1449 |
| next_open | 547 | +1901 | +1.54 | +1841 |
| next_close | 547 | +1932 | +1.66 | +1872 |

Controls: placebo (lag 20) z @0 +1.03, @base +0.95 on 472 trades; planted +50 bps z +1.60 vs actual +1.54 (shift +0.06).

**a2r-up-close / smallcap / dev — direction long, decision horizon 63 sessions, next-open fill**

Autopsy rule on `close` (bottom quintile, selection lift 2.82): match rate 19.8% of the universe per day; 4 of 4000 trades made the original 63-session move (0.10%) against a universe base rate of 0.03% (realized lift 3.78).

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 137772 | 125072 | 4000 | 1915 | +494 | +467 | +440 | +385 | -9 | 0.485 | +368 | +70 | +5.28 | 7.5% | +4.75 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 4000 | +12 | +0.81 | -43 | -5.20 |
| 5 | 4000 | +69 | +2.21 | +14 | -0.41 |
| 21 | 4000 | +176 | +3.93 | +121 | +2.40 |
| 63 * | 4000 | +494 | +6.08 | +440 | +5.28 |
| 126 | 3803 | +941 | +6.75 | +886 | +6.28 |
| 252 | 3267 | +1414 | +7.45 | +1359 | +7.16 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2010 | 307 | 152 | +366 | +2.16 |
| 2011 | 327 | 168 | +188 | +1.71 |
| 2012 | 223 | 144 | +115 | +0.17 |
| 2013 | 219 | 149 | +402 | +1.38 |
| 2014 | 283 | 167 | +345 | +2.20 |
| 2015 | 335 | 183 | +55 | -0.32 |
| 2016 | 344 | 186 | +716 | +3.39 |
| 2017 | 339 | 179 | +281 | +0.64 |
| 2018 | 434 | 204 | +307 | +1.62 |
| 2019 | 456 | 207 | +209 | +0.77 |
| 2020 | 733 | 176 | +1072 | +2.98 |
| half1 | 1516 | 870 | +253 | +3.11 |
| half2 | 2484 | 1045 | +554 | +4.30 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 4047 | +504 | +6.30 | +449 |
| next_open | 4000 | +494 | +6.08 | +440 |
| next_close | 4000 | +501 | +6.22 | +446 |

Controls: placebo (lag 20) z @0 +6.10, @base +5.42 on 2922 trades; planted +50 bps z +6.80 vs actual +6.08 (shift +0.72).

**a2r-up-close_to_high_250 / smallcap / dev — direction long, decision horizon 63 sessions, next-open fill**

Autopsy rule on `close_to_high_250` (bottom quintile, selection lift 3.46): match rate 19.8% of the universe per day; 6 of 4287 trades made the original 63-session move (0.14%) against a universe base rate of 0.03% (realized lift 5.29).

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 137805 | 124816 | 4287 | 1919 | +22 | -3 | -29 | -80 | -626 | 0.426 | -114 | +82 | -1.39 | 7.9% | -3.17 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 4287 | +1 | -0.52 | -50 | -5.05 |
| 5 | 4287 | -5 | +0.44 | -56 | -1.65 |
| 21 | 4287 | -65 | -1.23 | -116 | -2.39 |
| 63 * | 4287 | +22 | -0.75 | -29 | -1.39 |
| 126 | 4074 | -30 | -1.14 | -81 | -1.59 |
| 252 | 3477 | -243 | -0.73 | -295 | -0.98 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2010 | 345 | 165 | -115 | -0.28 |
| 2011 | 355 | 172 | -62 | -0.07 |
| 2012 | 228 | 148 | -50 | -0.14 |
| 2013 | 226 | 142 | +21 | -0.08 |
| 2014 | 295 | 167 | -180 | -0.13 |
| 2015 | 323 | 175 | -195 | -1.76 |
| 2016 | 354 | 176 | +421 | +1.63 |
| 2017 | 370 | 180 | -477 | -3.09 |
| 2018 | 511 | 208 | -380 | -2.08 |
| 2019 | 470 | 209 | -295 | -1.90 |
| 2020 | 810 | 177 | +520 | +0.91 |
| half1 | 1585 | 877 | -86 | -0.71 |
| half2 | 2702 | 1042 | +5 | -1.19 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 4335 | +42 | -0.75 | -9 |
| next_open | 4287 | +22 | -0.75 | -29 |
| next_close | 4287 | +21 | -0.68 | -30 |

Controls: placebo (lag 20) z @0 -0.80, @base -1.45 on 3386 trades; planted +50 bps z -0.14 vs actual -0.75 (shift +0.61).

**a2r-up-close_to_high_250 / uncapped / dev — direction long, decision horizon 63 sessions, next-open fill**

Autopsy rule on `close_to_high_250` (bottom quintile, selection lift 3.46): match rate 19.9% of the universe per day; 7 of 8517 trades made the original 63-session move (0.08%) against a universe base rate of 0.01% (realized lift 5.58).

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 275053 | 250491 | 8517 | 2308 | +7 | -14 | -36 | -80 | -541 | 0.439 | -178 | +65 | -2.74 | 7.8% | -4.60 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 8517 | -10 | -1.07 | -54 | -6.42 |
| 5 | 8517 | -17 | -2.07 | -61 | -4.78 |
| 21 | 8517 | -59 | -2.48 | -102 | -3.90 |
| 63 * | 8517 | +7 | -2.02 | -36 | -2.74 |
| 126 | 8162 | -22 | -3.06 | -66 | -3.57 |
| 252 | 6796 | -306 | -3.07 | -350 | -3.39 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2010 | 814 | 207 | -39 | +0.40 |
| 2011 | 944 | 232 | -67 | -0.67 |
| 2012 | 466 | 191 | -81 | -1.95 |
| 2013 | 398 | 197 | -120 | -1.36 |
| 2014 | 509 | 199 | -255 | -0.89 |
| 2015 | 599 | 211 | -299 | -2.09 |
| 2016 | 748 | 219 | +344 | +1.06 |
| 2017 | 595 | 205 | -401 | -2.79 |
| 2018 | 913 | 236 | -307 | -2.73 |
| 2019 | 810 | 226 | -277 | -1.62 |
| 2020 | 1721 | 185 | +387 | +0.67 |
| half1 | 3366 | 1123 | -116 | -2.42 |
| half2 | 5151 | 1185 | +16 | -1.69 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 8613 | +42 | -1.64 | -2 |
| next_open | 8517 | +7 | -2.02 | -36 |
| next_close | 8517 | +28 | -1.84 | -16 |

Controls: placebo (lag 20) z @0 -0.97, @base -1.67 on 6906 trades; planted +50 bps z -1.25 vs actual -2.02 (shift +0.77).

**a2r-up-close / uncapped / dev — direction long, decision horizon 63 sessions, next-open fill**

Autopsy rule on `close` (bottom quintile, selection lift 2.82): match rate 19.9% of the universe per day; 4 of 7776 trades made the original 63-session move (0.05%) against a universe base rate of 0.01% (realized lift 3.50).

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 275007 | 251181 | 7776 | 2273 | +392 | +369 | +346 | +299 | -62 | 0.478 | +329 | +64 | +5.10 | 7.2% | +5.11 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 7776 | +6 | +0.72 | -41 | -5.55 |
| 5 | 7776 | +41 | +2.08 | -6 | -0.47 |
| 21 | 7776 | +127 | +4.52 | +80 | +3.04 |
| 63 * | 7776 | +392 | +5.86 | +346 | +5.10 |
| 126 | 7457 | +797 | +8.38 | +751 | +7.82 |
| 252 | 6304 | +1299 | +9.33 | +1252 | +8.99 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2010 | 685 | 189 | +425 | +3.37 |
| 2011 | 796 | 222 | +109 | +0.78 |
| 2012 | 462 | 192 | +74 | +0.12 |
| 2013 | 396 | 192 | +421 | +2.52 |
| 2014 | 481 | 199 | +305 | +2.39 |
| 2015 | 625 | 217 | +153 | +0.29 |
| 2016 | 713 | 219 | +669 | +3.34 |
| 2017 | 556 | 210 | +242 | +1.73 |
| 2018 | 800 | 223 | +215 | +0.77 |
| 2019 | 790 | 232 | +170 | +0.85 |
| 2020 | 1472 | 178 | +645 | +1.97 |
| half1 | 3082 | 1097 | +218 | +3.65 |
| half2 | 4694 | 1176 | +430 | +3.75 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 7856 | +382 | +6.16 | +335 |
| next_open | 7776 | +392 | +5.86 | +346 |
| next_close | 7776 | +415 | +6.10 | +368 |

Controls: placebo (lag 20) z @0 +6.51, @base +5.78 on 5792 trades; planted +50 bps z +6.64 vs actual +5.86 (shift +0.78).

**a2r-up-med_dv_20_prev / crypto / dev — direction long, decision horizon 63 sessions, next-open fill**

Autopsy rule on `med_dv_20_prev` (bottom quintile, selection lift 1.56): match rate 19.0% of the universe per day; 28 of 1013 trades made the original 63-session move (2.76%) against a universe base rate of 1.21% (realized lift 2.29).

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @alt80 | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 25248 | 22740 | 1013 | 698 | +479 | +439 | +419 | +379 | +399 | -369 | 0.305 | +397 | +437 | +0.91 | 23.8% | -2.24 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 1013 | +30 | +1.17 | -30 | +0.11 |
| 5 | 1013 | -60 | +0.32 | -120 | -0.62 |
| 21 | 1013 | +4 | +0.34 | -56 | -0.06 |
| 63 * | 1013 | +479 | +1.04 | +419 | +0.91 |
| 126 | 929 | +516 | +0.81 | +456 | +0.75 |
| 252 | 772 | +681 | -0.34 | +621 | -0.38 |
| i04 | 1008 | +28 | +1.53 | -32 | -2.81 |
| i12 | 1012 | +44 | +2.06 | -16 | -0.16 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2018 | 21 | 21 | -388 | -0.92 |
| 2019 | 80 | 66 | -374 | -1.92 |
| 2020 | 212 | 164 | -540 | -0.85 |
| 2021 | 368 | 239 | +1704 | +1.71 |
| 2022 | 332 | 208 | -151 | -0.75 |
| half1 | 178 | 148 | +193 | -0.10 |
| half2 | 835 | 550 | +467 | +0.97 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 1021 | +396 | +1.30 | +336 |
| next_open | 1013 | +479 | +1.04 | +419 |
| next_close | 1013 | +556 | +1.14 | +496 |

Controls: placebo (lag 20) z @0 +0.52, @base +0.39 on 752 trades; planted +50 bps z +1.16 vs actual +1.04 (shift +0.11).

**a2r-up-rvol_20 / crypto / dev — direction long, decision horizon 63 sessions, next-open fill**

Autopsy rule on `rvol_20` (top quintile, selection lift 1.56): match rate 22.0% of the universe per day; 26 of 1149 trades made the original 63-session move (2.26%) against a universe base rate of 1.21% (realized lift 1.87).

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @alt80 | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 27044 | 24187 | 1149 | 821 | -142 | -182 | -202 | -242 | -222 | -1089 | 0.290 | +67 | +381 | +0.18 | 18.1% | -2.35 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 1148 | +17 | +0.64 | -43 | -0.56 |
| 5 | 1149 | +4 | +0.78 | -56 | +0.07 |
| 21 | 1149 | -131 | -0.08 | -191 | -0.46 |
| 63 * | 1149 | -142 | +0.33 | -202 | +0.18 |
| 126 | 1088 | +364 | +1.24 | +304 | +1.19 |
| 252 | 945 | -2136 | -0.78 | -2196 | -0.81 |
| i04 | 1144 | +16 | +1.04 | -44 | -3.02 |
| i12 | 1148 | +31 | +1.45 | -29 | -0.84 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2018 | 45 | 42 | -513 | -1.89 |
| 2019 | 153 | 124 | -655 | -1.91 |
| 2020 | 299 | 210 | -173 | +0.21 |
| 2021 | 363 | 246 | +133 | +0.74 |
| 2022 | 289 | 199 | -364 | -0.80 |
| half1 | 344 | 273 | -56 | -0.12 |
| half2 | 805 | 548 | -264 | +0.23 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 1157 | -158 | -0.05 | -218 |
| next_open | 1149 | -142 | +0.33 | -202 |
| next_close | 1149 | -45 | +0.58 | -105 |

Controls: placebo (lag 20) z @0 +0.97, @base +0.83 on 1050 trades; planted +50 bps z +0.46 vs actual +0.33 (shift +0.13).

**a2r-up-rvol_20 / smallcap / dev — direction long, decision horizon 63 sessions, next-open fill**

Autopsy rule on `rvol_20` (top quintile, selection lift 3.59): match rate 20.3% of the universe per day; 7 of 6021 trades made the original 63-session move (0.12%) against a universe base rate of 0.03% (realized lift 4.39).

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 140574 | 125787 | 6021 | 2261 | -18 | -44 | -70 | -121 | -689 | 0.415 | -149 | +67 | -2.23 | 7.0% | -4.25 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 6021 | -28 | -2.64 | -79 | -7.73 |
| 5 | 6021 | -43 | -2.98 | -95 | -5.70 |
| 21 | 6021 | -63 | -2.06 | -114 | -3.47 |
| 63 * | 6021 | -18 | -1.44 | -70 | -2.23 |
| 126 | 5704 | -37 | -1.16 | -88 | -1.74 |
| 252 | 4901 | -279 | -0.55 | -330 | -0.87 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2010 | 435 | 192 | -35 | +0.97 |
| 2011 | 489 | 206 | -143 | -1.59 |
| 2012 | 315 | 178 | -118 | -1.09 |
| 2013 | 304 | 182 | -258 | -1.03 |
| 2014 | 407 | 198 | -106 | -0.98 |
| 2015 | 482 | 214 | -335 | -2.35 |
| 2016 | 522 | 220 | +39 | -0.23 |
| 2017 | 529 | 213 | -311 | -1.71 |
| 2018 | 695 | 232 | -323 | -2.99 |
| 2019 | 723 | 240 | -231 | -1.28 |
| 2020 | 1120 | 186 | +466 | +1.18 |
| half1 | 2152 | 1059 | -165 | -2.26 |
| half2 | 3869 | 1202 | -17 | -1.20 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 6066 | +20 | -1.44 | -31 |
| next_open | 6021 | -18 | -1.44 | -70 |
| next_close | 6021 | +24 | -0.99 | -28 |

Controls: placebo (lag 20) z @0 -0.28, @base -0.92 on 4669 trades; planted +50 bps z -0.69 vs actual -1.44 (shift +0.75).

**a2r-up-rvol_20 / uncapped / dev — direction long, decision horizon 63 sessions, next-open fill**

Autopsy rule on `rvol_20` (top quintile, selection lift 3.59): match rate 20.2% of the universe per day; 9 of 11430 trades made the original 63-session move (0.08%) against a universe base rate of 0.01% (realized lift 5.35).

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 277822 | 250283 | 11430 | 2543 | +28 | +6 | -16 | -60 | -534 | 0.434 | -101 | +46 | -2.21 | 6.6% | -3.11 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 11430 | -19 | -2.25 | -63 | -8.90 |
| 5 | 11430 | -38 | -2.15 | -82 | -5.22 |
| 21 | 11430 | -46 | -2.02 | -90 | -3.84 |
| 63 * | 11430 | +28 | -1.20 | -16 | -2.21 |
| 126 | 10908 | +85 | -0.69 | +41 | -1.35 |
| 252 | 9213 | -67 | -0.88 | -112 | -1.29 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2010 | 962 | 228 | -117 | -0.95 |
| 2011 | 1206 | 239 | -89 | -1.92 |
| 2012 | 661 | 228 | -90 | -0.66 |
| 2013 | 540 | 215 | -56 | -0.22 |
| 2014 | 661 | 219 | -114 | -0.58 |
| 2015 | 854 | 242 | -171 | -2.61 |
| 2016 | 1028 | 244 | +73 | -0.01 |
| 2017 | 830 | 244 | -165 | -0.75 |
| 2018 | 1242 | 245 | -112 | -1.51 |
| 2019 | 1229 | 250 | -130 | -0.71 |
| 2020 | 2217 | 189 | +319 | +1.42 |
| half1 | 4378 | 1248 | -111 | -2.06 |
| half2 | 7052 | 1295 | +43 | -1.12 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 11535 | +46 | -0.77 | +2 |
| next_open | 11430 | +28 | -1.20 | -16 |
| next_close | 11430 | +52 | -0.71 | +8 |

Controls: placebo (lag 20) z @0 -0.47, @base -1.29 on 8938 trades; planted +50 bps z -0.10 vs actual -1.20 (shift +1.10).

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
# Intraday wave tables — dev era

**i1 / smallcap / dev — long, entry 10:00, decision exit `close`, floored universe**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 251 | 0.0% | 0 | 251 | 156 | +20 | +10 | +0 | -20 | -437 | 0.482 | -9 | +22 | -0.41 | 30.0% | -0.52 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1030 | 251 | +18 | +1.29 | -2 | -0.32 |
| 1200 | 250 | +18 | +0.89 | -2 | -0.17 |
| close * | 251 | +20 | +0.49 | +0 | -0.41 |
| nopen | 251 | +76 | +1.28 | +56 | +0.60 |
| 1 | 251 | +82 | +1.21 | +62 | +0.75 |
| 5 | 251 | +29 | +0.26 | +9 | -0.02 |
| 21 | 239 | -129 | -0.91 | -149 | -1.06 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 28 | 23 | +81 | +0.70 |
| 2021 | 127 | 81 | +43 | +0.11 |
| 2022 | 96 | 52 | -81 | -1.40 |
| half1 | 110 | 75 | +45 | -0.09 |
| half2 | 141 | 81 | -35 | -0.50 |

Controls: placebo (lag 20) z @0 -0.96, @base -1.85 on 383 trades; planted +50 bps z +2.73 vs actual +0.49 (shift +2.24). Power: 156 days, day-mean SE 22 bps, z = 3 needs 67 bps net per trade. Fills: mean lateness 0.0 min, 0.0% of fills late, 0.0% unfilled.

**i1 / uncapped / dev — long, entry 10:00, decision exit `close`, floored universe**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1368 | 0.0% | 0 | 1367 | 339 | +21 | +11 | +1 | -19 | -366 | 0.475 | -4 | +11 | -0.37 | 19.0% | -0.65 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1030 | 1367 | +10 | +0.41 | -10 | -3.10 |
| 1200 | 1365 | +3 | +0.13 | -17 | -2.32 |
| close * | 1367 | +21 | +1.38 | +1 | -0.37 |
| nopen | 1366 | +38 | +2.11 | +18 | +0.79 |
| 1 | 1366 | +29 | +1.13 | +9 | +0.12 |
| 5 | 1356 | +33 | +1.54 | +13 | +1.02 |
| 21 | 1243 | +51 | +1.20 | +31 | +1.09 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 262 | 75 | -4 | +0.76 |
| 2021 | 570 | 164 | +10 | +0.23 |
| 2022 | 535 | 100 | -6 | -1.96 |
| half1 | 617 | 171 | +4 | +0.31 |
| half2 | 750 | 168 | -1 | -0.94 |

Controls: placebo (lag 20) z @0 -1.07, @base -3.08 on 1695 trades; planted +50 bps z +5.74 vs actual +1.38 (shift +4.36). Power: 339 days, day-mean SE 11 bps, z = 3 needs 34 bps net per trade. Fills: mean lateness 0.0 min, 0.2% of fills late, 0.0% unfilled.

**i2-down / smallcap / dev — short, entry 09:35, decision exit `close`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1195 | 8.6% | 0 | 1060 | 368 | +34 | +15 | -3 | -40 | -495 | 0.504 | +17 | +44 | +0.39 | 16.4% | +1.84 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1030 | 1005 | +36 | +1.85 | -0 | +0.45 |
| 1200 | 951 | +51 | +1.81 | +16 | +0.76 |
| close * | 1060 | +34 | +1.27 | -3 | +0.39 |
| nopen | 1057 | +25 | +0.77 | -11 | -0.01 |
| 1 | 1057 | +74 | +2.12 | +37 | +1.40 |
| 5 | 1054 | +112 | +2.34 | +75 | +1.76 |
| 21 | 1024 | +144 | +2.24 | +107 | +1.83 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 202 | 79 | +0 | +0.36 |
| 2021 | 544 | 194 | +79 | +2.58 |
| 2022 | 314 | 95 | -147 | -1.52 |
| half1 | 496 | 187 | -3 | +1.47 |
| half2 | 564 | 181 | -3 | -0.41 |

Controls: placebo (lag 20) z @0 +0.48, @base -1.75 on 1231 trades; planted +50 bps z +2.40 vs actual +1.27 (shift +1.14). Power: 368 days, day-mean SE 44 bps, z = 3 needs 132 bps net per trade. Fills: mean lateness 0.9 min, 10.5% of fills late, 8.6% unfilled.

**i2-down / uncapped / dev — short, entry 09:35, decision exit `close`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1860 | 6.8% | 0 | 1699 | 414 | +33 | +17 | +1 | -31 | -439 | 0.513 | +38 | +28 | +1.38 | 15.5% | +1.80 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1030 | 1638 | +24 | +2.42 | -8 | +0.57 |
| 1200 | 1582 | +40 | +2.56 | +9 | +1.12 |
| close * | 1699 | +33 | +2.61 | +1 | +1.38 |
| nopen | 1692 | +24 | +1.58 | -8 | +0.63 |
| 1 | 1692 | +60 | +2.21 | +28 | +1.38 |
| 5 | 1687 | +79 | +2.20 | +46 | +1.54 |
| 21 | 1636 | +99 | +2.18 | +67 | +1.75 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 334 | 87 | -1 | -0.57 |
| 2021 | 803 | 219 | +86 | +3.34 |
| 2022 | 562 | 108 | -119 | -1.08 |
| half1 | 768 | 206 | +13 | +1.49 |
| half2 | 931 | 208 | -9 | +0.57 |

Controls: placebo (lag 20) z @0 +0.39, @base -2.51 on 2615 trades; planted +50 bps z +4.42 vs actual +2.61 (shift +1.81). Power: 414 days, day-mean SE 28 bps, z = 3 needs 83 bps net per trade. Fills: mean lateness 0.7 min, 8.0% of fills late, 6.8% unfilled.

**i2-up / smallcap / dev — long, entry 09:35, decision exit `close`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1845 | 8.0% | 0 | 1677 | 426 | -53 | -73 | -94 | -135 | -inf | 0.390 | -112 | +52 | -2.14 | 18.3% | -4.94 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1030 | 1580 | -72 | -2.56 | -112 | -4.05 |
| 1200 | 1522 | -57 | -1.19 | -97 | -2.07 |
| close * | 1677 | -53 | -1.32 | -94 | -2.14 |
| nopen | 1676 | -128 | -3.05 | -170 | -3.79 |
| 1 | 1676 | -199 | -3.67 | -240 | -4.34 |
| 5 | 1670 | -227 | -2.34 | -268 | -2.77 |
| 21 | 1652 | -226 | -1.10 | -268 | -1.35 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 476 | 102 | -23 | -1.17 |
| 2021 | 934 | 233 | -165 | -3.44 |
| 2022 | 267 | 91 | +27 | +0.80 |
| half1 | 1077 | 232 | -103 | -3.22 |
| half2 | 600 | 194 | -78 | -0.31 |

Controls: placebo (lag 20) z @0 +0.33, @base -2.36 on 1972 trades; planted +50 bps z -0.36 vs actual -1.32 (shift +0.96). Power: 426 days, day-mean SE 52 bps, z = 3 needs 157 bps net per trade. Fills: mean lateness 0.8 min, 10.0% of fills late, 8.0% unfilled.

**i2-up / uncapped / dev — long, entry 09:35, decision exit `close`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2856 | 6.3% | 0 | 2646 | 456 | -19 | -36 | -54 | -90 | -inf | 0.429 | -91 | +40 | -2.30 | 18.5% | -4.29 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1030 | 2528 | -59 | -2.32 | -94 | -3.90 |
| 1200 | 2470 | -47 | -1.41 | -81 | -2.43 |
| close * | 2646 | -19 | -1.33 | -54 | -2.30 |
| nopen | 2645 | -65 | -2.92 | -101 | -3.80 |
| 1 | 2645 | -112 | -3.88 | -148 | -4.71 |
| 5 | 2634 | -140 | -3.26 | -176 | -3.81 |
| 21 | 2601 | -196 | -2.04 | -232 | -2.35 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 982 | 104 | +32 | -0.73 |
| 2021 | 1224 | 247 | -151 | -3.22 |
| 2022 | 440 | 105 | +24 | +0.77 |
| half1 | 1769 | 237 | -59 | -3.34 |
| half2 | 877 | 219 | -45 | -0.30 |

Controls: placebo (lag 20) z @0 +0.16, @base -2.97 on 3707 trades; planted +50 bps z -0.07 vs actual -1.33 (shift +1.26). Power: 456 days, day-mean SE 40 bps, z = 3 needs 119 bps net per trade. Fills: mean lateness 0.8 min, 9.6% of fills late, 6.3% unfilled.

**i3-bottom / smallcap / dev — short, entry 10:00, decision exit `close`, floored universe**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1493 | 0.0% | 0 | 1493 | 464 | +12 | +2 | -8 | -28 | -566 | 0.470 | -10 | +11 | -0.88 | 13.4% | -1.82 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1030 | 1493 | -2 | +0.03 | -22 | -4.01 |
| 1200 | 1488 | +1 | +0.06 | -19 | -2.71 |
| close * | 1493 | +12 | +0.97 | -8 | -0.88 |
| nopen | 1487 | +32 | +2.72 | +12 | +1.42 |
| 1 | 1487 | +32 | +1.90 | +12 | +0.85 |
| 5 | 1463 | +40 | +0.83 | +20 | +0.27 |
| 21 | 1379 | +59 | +0.26 | +39 | -0.02 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 222 | 89 | -11 | -0.79 |
| 2021 | 789 | 251 | -1 | -0.04 |
| 2022 | 482 | 124 | -18 | -1.11 |
| half1 | 737 | 223 | -5 | -0.82 |
| half2 | 756 | 241 | -10 | -0.46 |

Controls: placebo (lag 20) z @0 -0.13, @base -1.73 on 847 trades; planted +50 bps z +5.61 vs actual +0.97 (shift +4.63). Random-slice placebo z @0 +0.07 on 1491 trades. Power: 464 days, day-mean SE 11 bps, z = 3 needs 32 bps net per trade. Fills: mean lateness 0.1 min, 1.2% of fills late, 0.0% unfilled.

**i3-bottom / uncapped / dev — short, entry 10:00, decision exit `close`, floored universe**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 7094 | 0.0% | 0 | 7094 | 464 | +11 | +1 | -9 | -29 | -482 | 0.480 | -15 | +6 | -2.38 | 11.8% | -3.05 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1030 | 7094 | +4 | +1.12 | -16 | -6.02 |
| 1200 | 7073 | +2 | -0.02 | -18 | -4.73 |
| close * | 7094 | +11 | +0.84 | -9 | -2.38 |
| nopen | 7061 | +28 | +2.37 | +8 | -0.07 |
| 1 | 7061 | +32 | +1.50 | +12 | -0.29 |
| 5 | 6927 | +22 | +1.13 | +2 | +0.11 |
| 21 | 6431 | -41 | -0.50 | -61 | -0.88 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 1520 | 89 | -24 | -2.52 |
| 2021 | 3035 | 251 | -4 | -1.17 |
| 2022 | 2539 | 124 | -6 | -1.25 |
| half1 | 3510 | 223 | -6 | -0.98 |
| half2 | 3584 | 241 | -12 | -2.30 |

Controls: placebo (lag 20) z @0 +0.25, @base -2.19 on 4108 trades; planted +50 bps z +8.89 vs actual +0.84 (shift +8.05). Random-slice placebo z @0 -0.64 on 7088 trades. Power: 464 days, day-mean SE 6 bps, z = 3 needs 19 bps net per trade. Fills: mean lateness 0.0 min, 0.8% of fills late, 0.0% unfilled.

**i3-top / smallcap / dev — long, entry 10:00, decision exit `close`, floored universe**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1493 | 0.0% | 0 | 1492 | 464 | -3 | -13 | -23 | -44 | -576 | 0.460 | -24 | +10 | -2.40 | 10.3% | -2.77 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1030 | 1491 | +2 | +0.70 | -18 | -3.23 |
| 1200 | 1487 | -1 | -0.32 | -21 | -3.09 |
| close * | 1492 | -3 | -0.41 | -23 | -2.40 |
| nopen | 1486 | +30 | +2.15 | +10 | +0.75 |
| 1 | 1486 | +38 | +1.53 | +18 | +0.49 |
| 5 | 1462 | -24 | -0.21 | -44 | -0.77 |
| 21 | 1378 | -94 | -1.45 | -114 | -1.72 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 222 | 89 | -7 | -0.31 |
| 2021 | 789 | 251 | -24 | -1.70 |
| 2022 | 481 | 124 | -31 | -2.14 |
| half1 | 737 | 223 | -13 | -0.86 |
| half2 | 755 | 241 | -34 | -2.63 |

Controls: placebo (lag 20) z @0 -0.48, @base -2.10 on 857 trades; planted +50 bps z +4.55 vs actual -0.41 (shift +4.96). Random-slice placebo z @0 -0.07 on 1491 trades. Power: 464 days, day-mean SE 10 bps, z = 3 needs 30 bps net per trade. Fills: mean lateness 0.1 min, 1.2% of fills late, 0.0% unfilled.

**i3-top / uncapped / dev — long, entry 10:00, decision exit `close`, floored universe**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 7094 | 0.0% | 0 | 7089 | 464 | +10 | -0 | -10 | -30 | -472 | 0.463 | -14 | +7 | -2.03 | 13.5% | -2.13 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1030 | 7088 | +3 | +0.74 | -17 | -5.98 |
| 1200 | 7072 | +4 | +0.63 | -16 | -3.64 |
| close * | 7089 | +10 | +0.97 | -10 | -2.03 |
| nopen | 7056 | +32 | +3.24 | +12 | +0.82 |
| 1 | 7056 | +45 | +3.00 | +25 | +1.11 |
| 5 | 6922 | +48 | +2.15 | +28 | +1.45 |
| 21 | 6426 | -0 | +0.48 | -20 | +0.05 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 1520 | 89 | -11 | -2.16 |
| 2021 | 3035 | 251 | -12 | -0.93 |
| 2022 | 2534 | 124 | -8 | -1.42 |
| half1 | 3510 | 223 | -8 | -0.96 |
| half2 | 3579 | 241 | -12 | -1.88 |

Controls: placebo (lag 20) z @0 -1.91, @base -4.87 on 4209 trades; planted +50 bps z +8.45 vs actual +0.97 (shift +7.48). Random-slice placebo z @0 +0.64 on 7088 trades. Power: 464 days, day-mean SE 7 bps, z = 3 needs 20 bps net per trade. Fills: mean lateness 0.0 min, 0.8% of fills late, 0.0% unfilled.

**i4 / smallcap / dev — long, entry 15:30, decision exit `close`, floored universe**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1481 | 0.0% | 0 | 1481 | 464 | +1 | -9 | -19 | -39 | -548 | 0.380 | -16 | +3 | -6.42 | 10.9% | -6.22 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| close * | 1481 | +1 | +1.44 | -19 | -6.42 |
| nopen | 1475 | +26 | +3.46 | +5 | +1.34 |
| 1 | 1475 | +32 | +2.53 | +12 | +1.17 |
| 5 | 1451 | -6 | +0.06 | -26 | -0.58 |
| 21 | 1366 | -27 | -0.19 | -47 | -0.47 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 217 | 89 | -13 | -2.54 |
| 2021 | 776 | 251 | -17 | -3.43 |
| 2022 | 488 | 124 | -25 | -6.39 |
| half1 | 724 | 223 | -17 | -4.55 |
| half2 | 757 | 241 | -20 | -4.55 |

Controls: placebo (lag 20) z @0 +0.21, @base -6.60 on 834 trades; planted +50 bps z +21.08 vs actual +1.44 (shift +19.63). Random-slice placebo z @0 -2.66 on 1481 trades. Power: 464 days, day-mean SE 3 bps, z = 3 needs 8 bps net per trade. Fills: mean lateness 0.0 min, 0.5% of fills late, 0.0% unfilled.

**i4 / uncapped / dev — long, entry 15:30, decision exit `close`, floored universe**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 7041 | 0.0% | 0 | 7041 | 464 | +1 | -9 | -19 | -39 | -472 | 0.358 | -18 | +1 | -12.59 | 12.1% | -13.00 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| close * | 7041 | +1 | +1.70 | -19 | -12.59 |
| nopen | 7009 | +21 | +3.92 | +1 | +0.47 |
| 1 | 7009 | +22 | +2.16 | +2 | +0.07 |
| 5 | 6873 | +37 | +2.09 | +17 | +1.28 |
| 21 | 6379 | +21 | +0.98 | +1 | +0.52 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 1508 | 89 | -17 | -6.41 |
| 2021 | 2995 | 251 | -17 | -7.38 |
| 2022 | 2538 | 124 | -21 | -10.86 |
| half1 | 3470 | 223 | -17 | -8.06 |
| half2 | 3571 | 241 | -20 | -9.76 |

Controls: placebo (lag 20) z @0 +1.63, @base -8.27 on 4166 trades; planted +50 bps z +37.42 vs actual +1.70 (shift +35.72). Random-slice placebo z @0 -0.41 on 7041 trades. Power: 464 days, day-mean SE 1 bps, z = 3 needs 4 bps net per trade. Fills: mean lateness 0.0 min, 0.3% of fills late, 0.0% unfilled.

**i5-all / smallcap / dev — long, entry 15:55, decision exit `nopen`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 285831 | 0.0% | 0 | 284996 | 478 | +14 | -4 | -23 | -60 | -inf | 0.416 | -23 | +5 | -4.77 | 11.1% | -4.11 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| nopen * | 284996 | +14 | +3.03 | -23 | -4.77 |
| 1 | 284996 | -1 | -0.05 | -38 | -3.82 |
| 5 | 281714 | -6 | -0.15 | -43 | -1.73 |
| 21 | 269384 | -64 | -0.11 | -101 | -0.83 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 51575 | 104 | -4 | -0.70 |
| 2021 | 147024 | 251 | -17 | -2.98 |
| 2022 | 86397 | 123 | -44 | -4.27 |
| half1 | 133651 | 238 | -4 | -1.02 |
| half2 | 151345 | 240 | -39 | -5.88 |

Controls: placebo (lag 20) z @0 +2.70, @base -3.91 on 196586 trades; planted +50 bps z +13.50 vs actual +3.03 (shift +10.47). Power: 478 days, day-mean SE 5 bps, z = 3 needs 14 bps net per trade. Fills: mean lateness 0.0 min, 0.0% of fills late, 0.0% unfilled.

**i5-all / uncapped / dev — long, entry 15:55, decision exit `nopen`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 514425 | 0.0% | 0 | 512725 | 478 | +13 | -2 | -18 | -49 | -inf | 0.436 | -19 | +5 | -3.95 | 11.5% | -3.58 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| nopen * | 512725 | +13 | +2.79 | -18 | -3.95 |
| 1 | 512725 | +5 | +0.30 | -26 | -3.12 |
| 5 | 505878 | +21 | +0.57 | -11 | -0.90 |
| 21 | 480691 | +36 | +1.45 | +5 | +0.75 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 105269 | 104 | +2 | -0.19 |
| 2021 | 240333 | 251 | -14 | -2.70 |
| 2022 | 167123 | 123 | -37 | -3.65 |
| half1 | 242250 | 238 | -1 | -0.72 |
| half2 | 270475 | 240 | -33 | -4.92 |

Controls: placebo (lag 20) z @0 +2.52, @base -3.29 on 337733 trades; planted +50 bps z +13.42 vs actual +2.79 (shift +10.63). Power: 478 days, day-mean SE 5 bps, z = 3 needs 14 bps net per trade. Fills: mean lateness 0.0 min, 0.0% of fills late, 0.0% unfilled.

**i5-q1 / smallcap / dev — long, entry 15:55, decision exit `nopen`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 56934 | 0.0% | 0 | 56767 | 478 | -6 | -25 | -44 | -82 | -inf | 0.336 | -44 | +2 | -21.40 | 9.0% | -25.18 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| nopen * | 56767 | -6 | -2.79 | -44 | -21.40 |
| 1 | 56767 | +1 | +0.28 | -37 | -10.61 |
| 5 | 56114 | -6 | -0.83 | -45 | -5.51 |
| 21 | 53678 | -34 | -1.74 | -72 | -4.04 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 10295 | 104 | -44 | -11.31 |
| 2021 | 29257 | 251 | -43 | -13.92 |
| 2022 | 17215 | 123 | -46 | -12.54 |
| half1 | 26639 | 238 | -44 | -13.03 |
| half2 | 30128 | 240 | -44 | -18.50 |

Controls: placebo (lag 20) z @0 -1.74, @base -19.36 on 39726 trades; planted +50 bps z +21.81 vs actual -2.79 (shift +24.60). Random-slice placebo z @0 +1.51 on 56767 trades. Power: 478 days, day-mean SE 2 bps, z = 3 needs 6 bps net per trade. Fills: mean lateness 0.0 min, 0.0% of fills late, 0.0% unfilled.

**i5-q1 / uncapped / dev — long, entry 15:55, decision exit `nopen`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 102587 | 0.0% | 0 | 102247 | 478 | -3 | -19 | -36 | -68 | -inf | 0.358 | -36 | +2 | -19.44 | 10.0% | -22.39 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| nopen * | 102247 | -3 | -1.93 | -36 | -19.44 |
| 1 | 102247 | +2 | +0.23 | -31 | -9.63 |
| 5 | 100879 | -1 | -0.41 | -33 | -4.56 |
| 21 | 95859 | -21 | -1.42 | -53 | -3.55 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 21005 | 104 | -35 | -11.00 |
| 2021 | 47912 | 251 | -36 | -13.89 |
| 2022 | 33330 | 123 | -35 | -8.86 |
| half1 | 48339 | 238 | -36 | -12.72 |
| half2 | 53908 | 240 | -35 | -15.02 |

Controls: placebo (lag 20) z @0 -1.62, @base -18.19 on 70379 trades; planted +50 bps z +24.93 vs actual -1.93 (shift +26.86). Random-slice placebo z @0 +2.00 on 102247 trades. Power: 478 days, day-mean SE 2 bps, z = 3 needs 6 bps net per trade. Fills: mean lateness 0.0 min, 0.0% of fills late, 0.0% unfilled.

**i5-q2 / smallcap / dev — long, entry 15:55, decision exit `nopen`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 57159 | 0.0% | 0 | 56992 | 478 | -3 | -21 | -40 | -76 | -inf | 0.315 | -40 | +1 | -27.86 | 7.2% | -31.44 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| nopen * | 56992 | -3 | -2.00 | -40 | -27.86 |
| 1 | 56992 | +1 | +0.89 | -35 | -14.65 |
| 5 | 56334 | -5 | -0.53 | -42 | -7.27 |
| 21 | 53844 | -3 | -0.39 | -39 | -3.08 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 10303 | 104 | -43 | -11.41 |
| 2021 | 29466 | 251 | -41 | -20.34 |
| 2022 | 17223 | 123 | -36 | -17.11 |
| half1 | 26759 | 238 | -43 | -17.41 |
| half2 | 30233 | 240 | -36 | -25.14 |

Controls: placebo (lag 20) z @0 -4.05, @base -27.56 on 38421 trades; planted +50 bps z +33.18 vs actual -2.00 (shift +35.19). Random-slice placebo z @0 -0.69 on 56992 trades. Power: 478 days, day-mean SE 1 bps, z = 3 needs 4 bps net per trade. Fills: mean lateness 0.0 min, 0.0% of fills late, 0.0% unfilled.

**i5-q2 / uncapped / dev — long, entry 15:55, decision exit `nopen`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 103052 | 0.0% | 0 | 102712 | 478 | -3 | -18 | -34 | -64 | -inf | 0.335 | -34 | +1 | -32.55 | 6.8% | -33.65 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| nopen * | 102712 | -3 | -2.59 | -34 | -32.55 |
| 1 | 102712 | -0 | +0.10 | -31 | -16.01 |
| 5 | 101342 | -6 | -1.33 | -37 | -8.52 |
| 21 | 96294 | -7 | -0.85 | -38 | -3.85 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 21076 | 104 | -36 | -16.36 |
| 2021 | 48154 | 251 | -35 | -22.87 |
| 2022 | 33482 | 123 | -30 | -16.92 |
| half1 | 48506 | 238 | -37 | -21.84 |
| half2 | 54206 | 240 | -30 | -25.76 |

Controls: placebo (lag 20) z @0 -2.96, @base -27.94 on 65346 trades; planted +50 bps z +45.43 vs actual -2.59 (shift +48.02). Random-slice placebo z @0 +0.06 on 102712 trades. Power: 478 days, day-mean SE 1 bps, z = 3 needs 3 bps net per trade. Fills: mean lateness 0.0 min, 0.0% of fills late, 0.0% unfilled.

**i5-q3 / smallcap / dev — long, entry 15:55, decision exit `nopen`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 57179 | 0.0% | 0 | 57012 | 478 | -1 | -19 | -37 | -73 | -inf | 0.316 | -37 | +1 | -29.96 | 7.3% | -35.92 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| nopen * | 57012 | -1 | -1.09 | -37 | -29.96 |
| 1 | 57012 | +1 | +0.30 | -36 | -15.58 |
| 5 | 56369 | +1 | +0.16 | -35 | -6.40 |
| 21 | 53902 | +20 | +1.23 | -16 | -1.59 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 10333 | 104 | -41 | -17.42 |
| 2021 | 29417 | 251 | -37 | -18.30 |
| 2022 | 17262 | 123 | -37 | -21.16 |
| half1 | 26732 | 238 | -40 | -21.05 |
| half2 | 30280 | 240 | -35 | -21.55 |

Controls: placebo (lag 20) z @0 -0.05, @base -26.24 on 38442 trades; planted +50 bps z +38.99 vs actual -1.09 (shift +40.08). Random-slice placebo z @0 -0.57 on 57012 trades. Power: 478 days, day-mean SE 1 bps, z = 3 needs 4 bps net per trade. Fills: mean lateness 0.0 min, 0.0% of fills late, 0.0% unfilled.

**i5-q3 / uncapped / dev — long, entry 15:55, decision exit `nopen`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 102884 | 0.0% | 0 | 102544 | 478 | -1 | -16 | -31 | -61 | -inf | 0.335 | -31 | +1 | -34.21 | 7.0% | -37.00 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| nopen * | 102544 | -1 | -0.95 | -31 | -34.21 |
| 1 | 102544 | +3 | +1.56 | -28 | -16.18 |
| 5 | 101168 | +3 | +1.08 | -27 | -6.28 |
| 21 | 96130 | +6 | +0.53 | -24 | -2.49 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 21038 | 104 | -31 | -16.72 |
| 2021 | 48068 | 251 | -32 | -23.37 |
| 2022 | 33438 | 123 | -29 | -20.28 |
| half1 | 48415 | 238 | -33 | -21.62 |
| half2 | 54129 | 240 | -30 | -28.73 |

Controls: placebo (lag 20) z @0 +0.53, @base -27.39 on 63884 trades; planted +50 bps z +53.95 vs actual -0.95 (shift +54.89). Random-slice placebo z @0 -0.57 on 102544 trades. Power: 478 days, day-mean SE 1 bps, z = 3 needs 3 bps net per trade. Fills: mean lateness 0.0 min, 0.0% of fills late, 0.0% unfilled.

**i5-q4 / smallcap / dev — long, entry 15:55, decision exit `nopen`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 57174 | 0.0% | 0 | 57007 | 478 | +1 | -18 | -36 | -72 | -inf | 0.324 | -36 | +1 | -28.81 | 6.4% | -30.62 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| nopen * | 57007 | +1 | +0.63 | -36 | -28.81 |
| 1 | 57007 | +1 | +0.40 | -35 | -14.36 |
| 5 | 56337 | +0 | +0.08 | -36 | -6.36 |
| 21 | 53872 | -7 | -0.89 | -43 | -3.97 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 10286 | 104 | -39 | -12.33 |
| 2021 | 29390 | 251 | -34 | -20.55 |
| 2022 | 17331 | 123 | -37 | -16.68 |
| half1 | 26683 | 238 | -35 | -17.37 |
| half2 | 30324 | 240 | -36 | -25.24 |

Controls: placebo (lag 20) z @0 -0.07, @base -24.45 on 39018 trades; planted +50 bps z +41.01 vs actual +0.63 (shift +40.38). Random-slice placebo z @0 +1.31 on 57007 trades. Power: 478 days, day-mean SE 1 bps, z = 3 needs 4 bps net per trade. Fills: mean lateness 0.0 min, 0.0% of fills late, 0.0% unfilled.

**i5-q4 / uncapped / dev — long, entry 15:55, decision exit `nopen`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 102833 | 0.0% | 0 | 102493 | 478 | -0 | -15 | -31 | -61 | -inf | 0.338 | -31 | +1 | -28.83 | 6.7% | -33.35 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| nopen * | 102493 | -0 | +0.19 | -31 | -28.83 |
| 1 | 102493 | -1 | -0.47 | -32 | -15.11 |
| 5 | 101131 | -6 | -0.69 | -36 | -6.98 |
| 21 | 96092 | -7 | -0.92 | -37 | -3.95 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 21047 | 104 | -33 | -14.26 |
| 2021 | 48041 | 251 | -30 | -19.75 |
| 2022 | 33405 | 123 | -30 | -15.85 |
| half1 | 48444 | 238 | -32 | -19.46 |
| half2 | 54049 | 240 | -30 | -21.63 |

Controls: placebo (lag 20) z @0 -0.18, @base -26.63 on 65542 trades; planted +50 bps z +47.13 vs actual +0.19 (shift +46.94). Random-slice placebo z @0 +0.61 on 102493 trades. Power: 478 days, day-mean SE 1 bps, z = 3 needs 3 bps net per trade. Fills: mean lateness 0.0 min, 0.0% of fills late, 0.0% unfilled.

**i5-q5 / smallcap / dev — long, entry 15:55, decision exit `nopen`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 57385 | 0.0% | 0 | 57218 | 478 | +9 | -10 | -29 | -68 | -inf | 0.358 | -30 | +2 | -13.30 | 8.8% | -15.98 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| nopen * | 57218 | +9 | +3.97 | -29 | -13.30 |
| 1 | 57218 | -4 | -1.23 | -43 | -11.40 |
| 5 | 56560 | +10 | +0.92 | -29 | -3.29 |
| 21 | 54088 | +23 | +1.41 | -16 | -0.39 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 10358 | 104 | -24 | -5.22 |
| 2021 | 29494 | 251 | -28 | -9.07 |
| 2022 | 17366 | 123 | -34 | -8.88 |
| half1 | 26838 | 238 | -21 | -6.33 |
| half2 | 30380 | 240 | -37 | -14.19 |

Controls: placebo (lag 20) z @0 +2.78, @base -14.19 on 40979 trades; planted +50 bps z +26.40 vs actual +3.97 (shift +22.43). Random-slice placebo z @0 +0.70 on 57218 trades. Power: 478 days, day-mean SE 2 bps, z = 3 needs 7 bps net per trade. Fills: mean lateness 0.0 min, 0.0% of fills late, 0.0% unfilled.

**i5-q5 / uncapped / dev — long, entry 15:55, decision exit `nopen`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 103069 | 0.0% | 0 | 102729 | 478 | +7 | -10 | -26 | -59 | -inf | 0.368 | -26 | +2 | -13.63 | 9.1% | -14.64 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| nopen * | 102729 | +7 | +3.51 | -26 | -13.63 |
| 1 | 102729 | -3 | -0.80 | -36 | -10.35 |
| 5 | 101358 | +9 | +0.96 | -24 | -3.07 |
| 21 | 96316 | +28 | +1.80 | -4 | +0.14 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 21103 | 104 | -21 | -5.71 |
| 2021 | 48158 | 251 | -25 | -9.14 |
| 2022 | 33468 | 123 | -32 | -8.87 |
| half1 | 48546 | 238 | -18 | -6.42 |
| half2 | 54183 | 240 | -33 | -14.41 |

Controls: placebo (lag 20) z @0 +3.00, @base -14.01 on 72582 trades; planted +50 bps z +29.47 vs actual +3.51 (shift +25.96). Random-slice placebo z @0 +0.03 on 102729 trades. Power: 478 days, day-mean SE 2 bps, z = 3 needs 6 bps net per trade. Fills: mean lateness 0.0 min, 0.0% of fills late, 0.0% unfilled.

**i6-1a-0935 / smallcap / dev — short, entry 09:35, decision exit `close`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 11221 | 21.5% | 0 | 8490 | 471 | +3 | -15 | -33 | -69 | -457 | 0.466 | -17 | +10 | -1.75 | 18.5% | -1.51 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1030 | 7581 | -2 | +0.71 | -36 | -4.41 |
| 1200 | 7010 | -1 | +0.45 | -34 | -2.82 |
| close * | 8490 | +3 | +2.12 | -33 | -1.75 |
| nopen | 8474 | +2 | +2.05 | -34 | -1.24 |
| 1 | 8474 | +5 | +1.74 | -30 | -0.68 |
| 5 | 8431 | -9 | +1.28 | -44 | -0.15 |
| 21 | 7885 | +22 | +0.37 | -14 | -0.32 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 1254 | 103 | +23 | +1.81 |
| 2021 | 4038 | 247 | -50 | -1.38 |
| 2022 | 3198 | 121 | -33 | -2.82 |
| half1 | 3368 | 237 | -23 | +1.41 |
| half2 | 5122 | 234 | -39 | -3.76 |

Controls: placebo (lag 20) z @0 -1.67, @base -4.07 on 7885 trades; planted +50 bps z +7.39 vs actual +2.12 (shift +5.27). Power: 471 days, day-mean SE 10 bps, z = 3 needs 29 bps net per trade. Fills: mean lateness 2.6 min, 32.0% of fills late, 21.5% unfilled.

**i6-1a-0935 / uncapped / dev — short, entry 09:35, decision exit `close`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 19256 | 16.1% | 0 | 15794 | 476 | +3 | -12 | -27 | -57 | -404 | 0.473 | -15 | +8 | -1.87 | 21.6% | -1.63 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1030 | 14671 | -1 | +1.14 | -30 | -4.35 |
| 1200 | 13943 | +1 | +0.61 | -27 | -2.60 |
| close * | 15794 | +3 | +2.12 | -27 | -1.87 |
| nopen | 15769 | +4 | +2.48 | -26 | -0.91 |
| 1 | 15769 | +7 | +1.94 | -23 | -0.60 |
| 5 | 15679 | -7 | +1.41 | -37 | -0.25 |
| 21 | 14407 | +13 | +0.75 | -17 | -0.10 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 2597 | 103 | +18 | +1.71 |
| 2021 | 6722 | 250 | -47 | -1.83 |
| 2022 | 6475 | 123 | -24 | -2.23 |
| half1 | 6248 | 237 | -19 | +1.45 |
| half2 | 9546 | 239 | -32 | -3.47 |

Controls: placebo (lag 20) z @0 -1.61, @base -3.86 on 15258 trades; planted +50 bps z +8.35 vs actual +2.12 (shift +6.23). Power: 476 days, day-mean SE 8 bps, z = 3 needs 24 bps net per trade. Fills: mean lateness 2.0 min, 25.0% of fills late, 16.1% unfilled.

**i6-1a-1030 / smallcap / dev — short, entry 10:30, decision exit `close`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 11221 | 21.8% | 0 | 8518 | 470 | +7 | -10 | -28 | -64 | -inf | 0.469 | -16 | +7 | -2.19 | 20.1% | -1.85 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1200 | 7133 | +3 | +0.89 | -31 | -5.20 |
| close * | 8518 | +7 | +2.86 | -28 | -2.19 |
| nopen | 8505 | +8 | +2.80 | -28 | -0.42 |
| 1 | 8505 | +11 | +1.89 | -25 | -0.59 |
| 5 | 8463 | -9 | +0.71 | -44 | -0.60 |
| 21 | 7899 | +17 | -0.10 | -19 | -0.88 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 1310 | 103 | +4 | +0.97 |
| 2021 | 3988 | 246 | -35 | -1.03 |
| 2022 | 3220 | 121 | -33 | -3.39 |
| half1 | 3394 | 236 | -17 | +0.72 |
| half2 | 5124 | 234 | -35 | -3.78 |

Controls: placebo (lag 20) z @0 -0.68, @base -4.68 on 7994 trades; planted +50 bps z +9.81 vs actual +2.86 (shift +6.95). Power: 470 days, day-mean SE 7 bps, z = 3 needs 22 bps net per trade. Fills: mean lateness 2.6 min, 31.6% of fills late, 21.8% unfilled.

**i6-1a-1030 / uncapped / dev — short, entry 10:30, decision exit `close`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 19256 | 15.9% | 0 | 15889 | 477 | +7 | -8 | -23 | -53 | -inf | 0.470 | -18 | +6 | -2.99 | 22.3% | -2.64 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1200 | 14140 | +3 | +1.00 | -25 | -5.87 |
| close * | 15889 | +7 | +2.39 | -23 | -2.99 |
| nopen | 15868 | +8 | +3.09 | -22 | -1.11 |
| 1 | 15868 | +11 | +1.59 | -19 | -1.22 |
| 5 | 15777 | -6 | +0.85 | -36 | -0.85 |
| 21 | 14480 | +11 | -0.04 | -19 | -0.95 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 2679 | 103 | -3 | +0.49 |
| 2021 | 6686 | 250 | -35 | -2.50 |
| 2022 | 6524 | 124 | -20 | -2.30 |
| half1 | 6307 | 237 | -21 | -0.18 |
| half2 | 9582 | 240 | -25 | -3.74 |

Controls: placebo (lag 20) z @0 -1.43, @base -5.74 on 15535 trades; planted +50 bps z +10.89 vs actual +2.39 (shift +8.50). Power: 477 days, day-mean SE 6 bps, z = 3 needs 18 bps net per trade. Fills: mean lateness 1.9 min, 23.5% of fills late, 15.9% unfilled.

**i6-1b-0935 / smallcap / dev — long, entry 09:35, decision exit `close`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 6666 | 13.5% | 0 | 5592 | 474 | -28 | -49 | -69 | -111 | -572 | 0.414 | -59 | +16 | -3.81 | 19.3% | -3.91 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1030 | 5048 | -24 | -1.63 | -63 | -5.31 |
| 1200 | 4782 | -32 | -1.08 | -72 | -3.74 |
| close * | 5592 | -28 | -1.10 | -69 | -3.81 |
| nopen | 5590 | -27 | -1.43 | -68 | -3.82 |
| 1 | 5590 | -73 | -2.36 | -114 | -4.42 |
| 5 | 5540 | -85 | -1.45 | -126 | -2.37 |
| 21 | 5442 | -169 | -2.31 | -210 | -3.10 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 1325 | 104 | -58 | -2.09 |
| 2021 | 3236 | 249 | -89 | -3.14 |
| 2022 | 1031 | 121 | -24 | -1.17 |
| half1 | 3387 | 237 | -84 | -1.99 |
| half2 | 2205 | 237 | -47 | -3.45 |

Controls: placebo (lag 20) z @0 +2.10, @base -1.45 on 5132 trades; planted +50 bps z +2.11 vs actual -1.10 (shift +3.21). Power: 474 days, day-mean SE 16 bps, z = 3 needs 47 bps net per trade. Fills: mean lateness 1.9 min, 23.1% of fills late, 13.5% unfilled.

**i6-1b-0935 / uncapped / dev — long, entry 09:35, decision exit `close`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 10234 | 10.6% | 0 | 8962 | 475 | -19 | -37 | -54 | -90 | -497 | 0.431 | -43 | +13 | -3.25 | 19.3% | -3.19 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1030 | 8330 | -12 | -1.57 | -46 | -5.52 |
| 1200 | 8009 | -19 | -0.94 | -52 | -4.05 |
| close * | 8962 | -19 | -0.47 | -54 | -3.25 |
| nopen | 8957 | -13 | -0.85 | -48 | -3.49 |
| 1 | 8957 | -53 | -1.98 | -88 | -4.31 |
| 5 | 8846 | -57 | -1.14 | -92 | -2.26 |
| 21 | 8700 | -152 | -2.37 | -187 | -3.18 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 2357 | 104 | -38 | -1.66 |
| 2021 | 4766 | 249 | -79 | -2.89 |
| 2022 | 1839 | 122 | -13 | -0.83 |
| half1 | 5284 | 237 | -66 | -1.51 |
| half2 | 3678 | 238 | -37 | -3.20 |

Controls: placebo (lag 20) z @0 +1.38, @base -2.63 on 7924 trades; planted +50 bps z +3.29 vs actual -0.47 (shift +3.77). Power: 475 days, day-mean SE 13 bps, z = 3 needs 40 bps net per trade. Fills: mean lateness 1.5 min, 19.0% of fills late, 10.6% unfilled.

**i6-1b-1030 / smallcap / dev — long, entry 10:30, decision exit `close`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 6666 | 17.7% | 0 | 5359 | 471 | +1 | -20 | -40 | -81 | -543 | 0.426 | -24 | +11 | -2.20 | 19.3% | -2.21 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1200 | 4664 | -9 | -0.10 | -47 | -5.07 |
| close * | 5359 | +1 | +1.65 | -40 | -2.20 |
| nopen | 5357 | +5 | +0.96 | -35 | -2.01 |
| 1 | 5357 | -41 | -0.54 | -82 | -2.87 |
| 5 | 5306 | -57 | -0.38 | -98 | -1.26 |
| 21 | 5212 | -123 | -1.18 | -164 | -1.93 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 1291 | 104 | -38 | -1.77 |
| 2021 | 3072 | 247 | -55 | -2.68 |
| 2022 | 996 | 120 | +2 | +0.51 |
| half1 | 3262 | 236 | -52 | -1.64 |
| half2 | 2097 | 235 | -22 | -1.48 |

Controls: placebo (lag 20) z @0 +0.18, @base -4.54 on 5034 trades; planted +50 bps z +6.27 vs actual +1.65 (shift +4.63). Power: 471 days, day-mean SE 11 bps, z = 3 needs 32 bps net per trade. Fills: mean lateness 2.2 min, 27.9% of fills late, 17.7% unfilled.

**i6-1b-1030 / uncapped / dev — long, entry 10:30, decision exit `close`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 10234 | 13.4% | 0 | 8717 | 475 | -3 | -20 | -38 | -73 | -479 | 0.424 | -19 | +9 | -2.20 | 21.0% | -2.34 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1200 | 7895 | -8 | +0.50 | -41 | -5.53 |
| close * | 8717 | -3 | +1.92 | -38 | -2.20 |
| nopen | 8712 | +5 | +1.30 | -29 | -2.10 |
| 1 | 8712 | -35 | -0.37 | -69 | -3.01 |
| 5 | 8597 | -38 | -0.32 | -73 | -1.49 |
| 21 | 8453 | -126 | -1.43 | -161 | -2.20 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 2316 | 104 | -36 | -1.02 |
| 2021 | 4591 | 249 | -48 | -2.44 |
| 2022 | 1810 | 122 | -14 | -0.02 |
| half1 | 5156 | 237 | -44 | -1.11 |
| half2 | 3561 | 238 | -28 | -2.02 |

Controls: placebo (lag 20) z @0 -0.53, @base -6.04 on 7870 trades; planted +50 bps z +7.59 vs actual +1.92 (shift +5.67). Power: 475 days, day-mean SE 9 bps, z = 3 needs 26 bps net per trade. Fills: mean lateness 1.8 min, 22.4% of fills late, 13.4% unfilled.

**i7 / smallcap / dev — short, entry 12:00, decision exit `close`, floored universe**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 282 | 0.0% | 0 | 282 | 180 | +16 | +6 | -4 | -24 | -539 | 0.507 | -17 | +23 | -0.75 | 26.2% | -1.44 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| close * | 282 | +16 | +0.14 | -4 | -0.75 |
| nopen | 281 | -54 | -1.56 | -74 | -1.98 |
| 1 | 281 | -34 | -0.70 | -54 | -1.08 |
| 5 | 281 | +21 | +0.28 | +1 | +0.07 |
| 21 | 269 | -7 | -0.43 | -27 | -0.50 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 46 | 34 | -18 | +0.47 |
| 2021 | 150 | 97 | +15 | -0.49 |
| 2022 | 86 | 49 | -30 | -1.15 |
| half1 | 138 | 92 | +41 | +0.67 |
| half2 | 144 | 88 | -47 | -1.93 |

Controls: placebo (lag 20) z @0 +0.75, @base -0.92 on 445 trades; planted +50 bps z +2.35 vs actual +0.14 (shift +2.21). Power: 180 days, day-mean SE 23 bps, z = 3 needs 68 bps net per trade. Fills: mean lateness 0.1 min, 1.1% of fills late, 0.0% unfilled.

**i7 / uncapped / dev — short, entry 12:00, decision exit `close`, floored universe**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 957 | 0.0% | 0 | 957 | 292 | +0 | -10 | -20 | -40 | -495 | 0.478 | -8 | +17 | -0.46 | 21.5% | +0.24 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| close * | 957 | +0 | +0.73 | -20 | -0.46 |
| nopen | 947 | -45 | -1.67 | -65 | -2.33 |
| 1 | 947 | -35 | -0.84 | -55 | -1.47 |
| 5 | 940 | -188 | -1.40 | -208 | -1.47 |
| 21 | 904 | -128 | -1.03 | -148 | -1.16 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 193 | 63 | +14 | +1.42 |
| 2021 | 410 | 146 | -35 | -1.31 |
| 2022 | 354 | 83 | -20 | +0.24 |
| half1 | 455 | 148 | -5 | +0.18 |
| half2 | 502 | 144 | -33 | -1.07 |

Controls: placebo (lag 20) z @0 +0.70, @base -1.36 on 1259 trades; planted +50 bps z +3.71 vs actual +0.73 (shift +2.97). Power: 292 days, day-mean SE 17 bps, z = 3 needs 50 bps net per trade. Fills: mean lateness 0.0 min, 0.6% of fills late, 0.0% unfilled.
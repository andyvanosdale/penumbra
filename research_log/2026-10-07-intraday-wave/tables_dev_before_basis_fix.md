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
| nopen | 251 | +35987 | -0.30 | +35967 | -0.30 |
| 1 | 251 | +58555 | -0.23 | +58535 | -0.23 |
| 5 | 251 | +42764 | -0.18 | +42744 | -0.18 |
| 21 | 239 | -128848 | -1.30 | -128868 | -1.30 |

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
| nopen | 1366 | +4919 | -2.08 | +4899 | -2.08 |
| 1 | 1366 | +9834 | -1.88 | +9814 | -1.88 |
| 5 | 1356 | +9687 | -1.89 | +9667 | -1.89 |
| 21 | 1243 | -25102 | -3.46 | -25122 | -3.46 |

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
| 52932 | 11.1% | 0 | 45632 | 479 | +10 | -7 | -25 | -60 | -inf | 0.506 | -24 | +4 | -6.13 | 9.8% | -5.22 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1030 | 41414 | +7 | +2.98 | -27 | -10.28 |
| 1200 | 38771 | +6 | +1.57 | -27 | -7.84 |
| close * | 45632 | +10 | +2.71 | -25 | -6.13 |
| nopen | 45545 | -178868598 | -20.74 | -178868633 | -20.74 |
| 1 | 45545 | -178017172 | -20.65 | -178017206 | -20.65 |
| 5 | 45167 | -174852262 | -20.37 | -174852297 | -20.37 |
| 21 | 43728 | -163287311 | -19.35 | -163287345 | -19.35 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 6708 | 104 | -32 | -3.39 |
| 2021 | 27525 | 251 | -18 | -3.15 |
| 2022 | 11399 | 124 | -38 | -4.36 |
| half1 | 24104 | 238 | -24 | -4.00 |
| half2 | 21528 | 241 | -26 | -4.67 |

Controls: placebo (lag 20) z @0 +0.91, @base -8.10 on 41715 trades; planted +50 bps z +15.38 vs actual +2.71 (shift +12.67). Power: 479 days, day-mean SE 4 bps, z = 3 needs 12 bps net per trade. Fills: mean lateness 2.1 min, 26.1% of fills late, 11.1% unfilled.

**i2-down / uncapped / dev — short, entry 09:35, decision exit `close`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 56032 | 10.8% | 0 | 48483 | 479 | +10 | -7 | -25 | -59 | -inf | 0.508 | -24 | +5 | -5.01 | 10.2% | -4.21 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1030 | 44130 | +7 | +2.59 | -26 | -8.19 |
| 1200 | 41418 | +5 | +1.17 | -28 | -6.73 |
| close * | 48483 | +10 | +2.22 | -25 | -5.01 |
| nopen | 48388 | -199624767 | -22.69 | -199624801 | -22.69 |
| 1 | 48388 | -198697358 | -22.58 | -198697393 | -22.58 |
| 5 | 47981 | -195200686 | -22.26 | -195200721 | -22.26 |
| 21 | 46418 | -182208200 | -21.22 | -182208234 | -21.22 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 7180 | 104 | -33 | -3.32 |
| 2021 | 28915 | 251 | -17 | -2.37 |
| 2022 | 12388 | 124 | -37 | -3.53 |
| half1 | 25262 | 238 | -25 | -3.51 |
| half2 | 23221 | 241 | -24 | -3.57 |

Controls: placebo (lag 20) z @0 +0.58, @base -6.85 on 45038 trades; planted +50 bps z +12.67 vs actual +2.22 (shift +10.45). Power: 479 days, day-mean SE 5 bps, z = 3 needs 14 bps net per trade. Fills: mean lateness 2.0 min, 25.5% of fills late, 10.8% unfilled.

**i2-up / smallcap / dev — long, entry 09:35, decision exit `close`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2922 | 11.7% | 0 | 2522 | 471 | +12 | -5 | -22 | -56 | -434 | 0.451 | -29 | +14 | -2.15 | 14.5% | -2.91 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1030 | 2282 | -9 | -0.93 | -43 | -4.32 |
| 1200 | 2186 | +13 | -0.11 | -20 | -2.42 |
| close * | 2522 | +12 | +0.34 | -22 | -2.15 |
| nopen | 2517 | -78078143 | -32.96 | -78078177 | -32.96 |
| 1 | 2517 | -77778398 | -32.84 | -77778432 | -32.84 |
| 5 | 2503 | -76795790 | -32.59 | -76795824 | -32.59 |
| 21 | 2440 | -71623925 | -32.13 | -71623959 | -32.13 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 790 | 104 | -19 | -1.41 |
| 2021 | 1259 | 247 | -13 | -1.02 |
| 2022 | 473 | 120 | -50 | -1.76 |
| half1 | 1610 | 236 | -21 | -1.70 |
| half2 | 912 | 235 | -24 | -1.35 |

Controls: placebo (lag 20) z @0 +0.54, @base -2.79 on 2598 trades; planted +50 bps z +3.98 vs actual +0.34 (shift +3.64). Power: 471 days, day-mean SE 14 bps, z = 3 needs 41 bps net per trade. Fills: mean lateness 1.9 min, 24.5% of fills late, 11.7% unfilled.

**i2-up / uncapped / dev — long, entry 09:35, decision exit `close`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 14634 | 5.3% | 0 | 13771 | 479 | +2 | -10 | -21 | -45 | -378 | 0.447 | -20 | +5 | -4.18 | 11.1% | -4.12 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1030 | 13272 | -7 | -1.24 | -30 | -9.18 |
| 1200 | 13050 | -4 | -1.00 | -27 | -6.75 |
| close * | 13771 | +2 | +0.77 | -21 | -4.18 |
| nopen | 13736 | -40630627 | -31.87 | -40630651 | -31.87 |
| 1 | 13736 | -40467943 | -31.76 | -40467967 | -31.76 |
| 5 | 13569 | -40097546 | -31.62 | -40097570 | -31.62 |
| 21 | 12920 | -37754612 | -30.96 | -37754636 | -30.96 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 3815 | 104 | -17 | -1.93 |
| 2021 | 5559 | 251 | -25 | -2.67 |
| 2022 | 4397 | 124 | -22 | -3.06 |
| half1 | 7574 | 238 | -24 | -3.88 |
| half2 | 6197 | 241 | -19 | -2.09 |

Controls: placebo (lag 20) z @0 +0.33, @base -6.07 on 14152 trades; planted +50 bps z +11.16 vs actual +0.77 (shift +10.39). Power: 479 days, day-mean SE 5 bps, z = 3 needs 14 bps net per trade. Fills: mean lateness 1.1 min, 15.0% of fills late, 5.3% unfilled.

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
| nopen | 1487 | -179312 | -1.43 | -179332 | -1.43 |
| 1 | 1487 | -182879 | -1.41 | -182899 | -1.41 |
| 5 | 1463 | -169498 | -1.36 | -169518 | -1.36 |
| 21 | 1379 | -174365 | -1.45 | -174385 | -1.45 |

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
| nopen | 7061 | -176373 | -4.74 | -176393 | -4.74 |
| 1 | 7061 | -176460 | -4.75 | -176480 | -4.75 |
| 5 | 6927 | -174995 | -4.70 | -175015 | -4.70 |
| 21 | 6431 | -180607 | -4.62 | -180627 | -4.62 |

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
| nopen | 1486 | +341636 | +2.00 | +341616 | +2.00 |
| 1 | 1486 | +351303 | +2.05 | +351283 | +2.05 |
| 5 | 1462 | +353429 | +2.01 | +353409 | +2.00 |
| 21 | 1378 | +330780 | +1.99 | +330760 | +1.99 |

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
| nopen | 7056 | +139483 | +3.30 | +139463 | +3.30 |
| 1 | 7056 | +140787 | +3.33 | +140767 | +3.33 |
| 5 | 6922 | +141813 | +3.27 | +141793 | +3.27 |
| 21 | 6426 | +131748 | +3.04 | +131728 | +3.04 |

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
| nopen | 1475 | +156937 | +0.22 | +156917 | +0.22 |
| 1 | 1475 | +152139 | +0.20 | +152119 | +0.19 |
| 5 | 1451 | +166616 | +0.19 | +166596 | +0.19 |
| 21 | 1366 | +115153 | +0.00 | +115133 | +0.00 |

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
| nopen | 7009 | +98603 | +2.32 | +98583 | +2.32 |
| 1 | 7009 | +97579 | +2.30 | +97559 | +2.30 |
| 5 | 6873 | +99520 | +2.27 | +99500 | +2.27 |
| 21 | 6379 | +81687 | +1.89 | +81667 | +1.89 |

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
| 285831 | 0.0% | 0 | 284996 | 478 | +66597437 | +66597419 | +66597400 | +66597363 | -inf | 0.578 | +63974581 | +1922844 | +33.27 | 6.4% | +33.88 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| nopen * | 284996 | +66597437 | +33.27 | +66597400 | +33.27 |
| 1 | 284996 | +66287252 | +33.02 | +66287215 | +33.02 |
| 5 | 281714 | +65375861 | +32.90 | +65375824 | +32.90 |
| 21 | 269384 | +60862926 | +31.57 | +60862889 | +31.57 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 51575 | 104 | +42950585 | +13.04 |
| 2021 | 147024 | 251 | +82690535 | +26.42 |
| 2022 | 86397 | 123 | +53327349 | +27.39 |
| half1 | 133651 | 238 | +77907033 | +20.48 |
| half2 | 151345 | 240 | +56609995 | +36.59 |

Controls: placebo (lag 20) z @0 +24.97, @base +24.97 on 196586 trades; planted +50 bps z +33.27 vs actual +33.27 (shift +0.00). Power: 478 days, day-mean SE 1922844 bps, z = 3 needs 5768532 bps net per trade. Fills: mean lateness 0.0 min, 0.0% of fills late, 0.0% unfilled.

**i5-all / uncapped / dev — long, entry 15:55, decision exit `nopen`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 514425 | 0.0% | 0 | 512725 | 478 | +37018913 | +37018897 | +37018881 | +37018850 | -inf | 0.517 | +36772114 | +1127245 | +32.62 | 6.4% | +32.87 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| nopen * | 512725 | +37018913 | +32.62 | +37018881 | +32.62 |
| 1 | 512725 | +36846489 | +32.40 | +36846458 | +32.40 |
| 5 | 505878 | +36407603 | +32.44 | +36407572 | +32.44 |
| 21 | 480691 | +34109181 | +30.93 | +34109149 | +30.93 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 105269 | 104 | +21043415 | +14.20 |
| 2021 | 240333 | 251 | +50587249 | +28.16 |
| 2022 | 167123 | 123 | +27569523 | +25.82 |
| half1 | 242250 | 238 | +42982463 | +20.13 |
| half2 | 270475 | 240 | +31677621 | +33.06 |

Controls: placebo (lag 20) z @0 +25.04, @base +25.04 on 337733 trades; planted +50 bps z +32.62 vs actual +32.62 (shift +0.00). Power: 478 days, day-mean SE 1127245 bps, z = 3 needs 3381736 bps net per trade. Fills: mean lateness 0.0 min, 0.0% of fills late, 0.0% unfilled.

**i5-q1 / smallcap / dev — long, entry 15:55, decision exit `nopen`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 31092 | 0.0% | 0 | 31013 | 478 | +304511806 | +304511788 | +304511770 | +304511734 | -inf | 0.084 | +276833482 | +13140134 | +21.07 | 9.8% | +21.08 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| nopen * | 31013 | +304511806 | +21.07 | +304511770 | +21.07 |
| 1 | 31013 | +302904365 | +20.93 | +302904329 | +20.93 |
| 5 | 30679 | +298368957 | +20.86 | +298368921 | +20.86 |
| 21 | 29432 | +277824884 | +20.39 | +277824848 | +20.39 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 5355 | 104 | +135315313 | +5.44 |
| 2021 | 16647 | 251 | +398679729 | +17.72 |
| 2022 | 9011 | 123 | +231094059 | +16.08 |
| half1 | 15345 | 238 | +366304227 | +12.86 |
| half2 | 15668 | 240 | +243993181 | +22.48 |

Controls: placebo (lag 20) z @0 +16.63, @base +16.63 on 24688 trades; planted +50 bps z +21.07 vs actual +21.07 (shift +0.00). Random-slice placebo z @0 +0.20 on 31013 trades. Power: 478 days, day-mean SE 13140134 bps, z = 3 needs 39420403 bps net per trade. Fills: mean lateness 0.0 min, 0.0% of fills late, 0.0% unfilled.

**i5-q1 / uncapped / dev — long, entry 15:55, decision exit `nopen`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 65575 | 0.0% | 0 | 65376 | 478 | +139408411 | +139408394 | +139408378 | +139408345 | -inf | 0.050 | +134136180 | +6693460 | +20.04 | 9.9% | +19.99 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| nopen * | 65376 | +139408411 | +20.04 | +139408378 | +20.04 |
| 1 | 65376 | +138667647 | +19.95 | +138667614 | +19.95 |
| 5 | 64505 | +136944409 | +19.91 | +136944376 | +19.91 |
| 21 | 61323 | +128801892 | +19.49 | +128801859 | +19.49 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 13302 | 104 | +50674500 | +5.50 |
| 2021 | 30992 | 251 | +208342677 | +17.72 |
| 2022 | 21082 | 123 | +94058138 | +15.97 |
| half1 | 31990 | 238 | +170494679 | +12.50 |
| half2 | 33386 | 240 | +109621917 | +20.18 |

Controls: placebo (lag 20) z @0 +15.98, @base +15.98 on 50566 trades; planted +50 bps z +20.04 vs actual +20.04 (shift +0.00). Random-slice placebo z @0 -0.52 on 65376 trades. Power: 478 days, day-mean SE 6693460 bps, z = 3 needs 20080379 bps net per trade. Fills: mean lateness 0.0 min, 0.0% of fills late, 0.0% unfilled.

**i5-q2 / smallcap / dev — long, entry 15:55, decision exit `nopen`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 31292 | 0.0% | 0 | 31213 | 478 | -68762957 | -68762974 | -68762991 | -68763024 | -68763511 | 0.000 | -63933084 | +1922350 | -33.26 | 7.6% | -33.67 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| nopen * | 31213 | -68762957 | -33.26 | -68762991 | -33.26 |
| 1 | 31213 | -68418674 | -33.00 | -68418707 | -33.00 |
| 5 | 30878 | -67455720 | -32.88 | -67455753 | -32.88 |
| 21 | 29626 | -63044827 | -31.55 | -63044861 | -31.55 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 5394 | 104 | -43020055 | -13.03 |
| 2021 | 16758 | 251 | -85589216 | -26.40 |
| 2022 | 9061 | 123 | -52968212 | -27.38 |
| half1 | 15442 | 238 | -81453457 | -20.48 |
| half2 | 15771 | 240 | -56337261 | -36.57 |

Controls: placebo (lag 20) z @0 -32.94, @base -32.94 on 24055 trades; planted +50 bps z -33.26 vs actual -33.26 (shift +0.00). Random-slice placebo z @0 -1.44 on 31213 trades. Power: 478 days, day-mean SE 1922350 bps, z = 3 needs 5767049 bps net per trade. Fills: mean lateness 0.0 min, 0.0% of fills late, 0.0% unfilled.

**i5-q2 / uncapped / dev — long, entry 15:55, decision exit `nopen`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 65749 | 0.0% | 0 | 65549 | 478 | -37717252 | -37717265 | -37717278 | -37717304 | -37717664 | 0.000 | -36771222 | +1127227 | -32.62 | 7.2% | -32.82 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| nopen * | 65549 | -37717252 | -32.62 | -37717278 | -32.62 |
| 1 | 65549 | -37531498 | -32.40 | -37531524 | -32.40 |
| 5 | 64676 | -37095397 | -32.44 | -37095423 | -32.44 |
| 21 | 61492 | -34848344 | -30.93 | -34848370 | -30.93 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 13337 | 104 | -21130128 | -14.20 |
| 2021 | 31089 | 251 | -51858921 | -28.16 |
| 2022 | 21123 | 123 | -27376573 | -25.82 |
| half1 | 32076 | 238 | -44346616 | -20.13 |
| half2 | 33473 | 240 | -31364616 | -33.06 |

Controls: placebo (lag 20) z @0 -32.46, @base -32.46 on 45209 trades; planted +50 bps z -32.62 vs actual -32.62 (shift +0.00). Random-slice placebo z @0 -1.73 on 65549 trades. Power: 478 days, day-mean SE 1127227 bps, z = 3 needs 3381680 bps net per trade. Fills: mean lateness 0.0 min, 0.0% of fills late, 0.0% unfilled.

**i5-q3 / smallcap / dev — long, entry 15:55, decision exit `nopen`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 31271 | 0.0% | 0 | 31192 | 478 | -68805010 | -68805024 | -68805039 | -68805069 | -68805450 | 0.000 | -63974638 | +1922844 | -33.27 | 7.6% | -33.68 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| nopen * | 31192 | -68805010 | -33.27 | -68805039 | -33.27 |
| 1 | 31192 | -68460912 | -33.02 | -68460942 | -33.02 |
| 5 | 30857 | -67502446 | -32.90 | -67502475 | -32.90 |
| 21 | 29603 | -63083746 | -31.57 | -63083776 | -31.57 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 5391 | 104 | -42979580 | -13.04 |
| 2021 | 16749 | 251 | -85669664 | -26.42 |
| 2022 | 9052 | 123 | -52980852 | -27.39 |
| half1 | 15437 | 238 | -81493001 | -20.48 |
| half2 | 15755 | 240 | -56373173 | -36.59 |

Controls: placebo (lag 20) z @0 -32.95, @base -32.95 on 22980 trades; planted +50 bps z -33.27 vs actual -33.27 (shift +0.00). Random-slice placebo z @0 -0.36 on 31192 trades. Power: 478 days, day-mean SE 1922844 bps, z = 3 needs 5768531 bps net per trade. Fills: mean lateness 0.0 min, 0.0% of fills late, 0.0% unfilled.

**i5-q3 / uncapped / dev — long, entry 15:55, decision exit `nopen`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 65748 | 0.0% | 0 | 65548 | 478 | -37717486 | -37717498 | -37717511 | -37717535 | -37717862 | 0.000 | -36772160 | +1127245 | -32.62 | 7.2% | -32.82 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| nopen * | 65548 | -37717486 | -32.62 | -37717511 | -32.62 |
| 1 | 65548 | -37531904 | -32.40 | -37531928 | -32.40 |
| 5 | 64677 | -37095828 | -32.44 | -37095853 | -32.44 |
| 21 | 61491 | -34848689 | -30.93 | -34848714 | -30.93 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 13344 | 104 | -21132461 | -14.20 |
| 2021 | 31081 | 251 | -51862646 | -28.16 |
| 2022 | 21123 | 123 | -27381193 | -25.82 |
| half1 | 32081 | 238 | -44344743 | -20.13 |
| half2 | 33467 | 240 | -31364738 | -33.06 |

Controls: placebo (lag 20) z @0 -32.47, @base -32.47 on 42070 trades; planted +50 bps z -32.62 vs actual -32.62 (shift +0.00). Random-slice placebo z @0 +0.38 on 65548 trades. Power: 478 days, day-mean SE 1127245 bps, z = 3 needs 3381736 bps net per trade. Fills: mean lateness 0.0 min, 0.0% of fills late, 0.0% unfilled.

**i5-q4 / smallcap / dev — long, entry 15:55, decision exit `nopen`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 31293 | 0.0% | 0 | 31214 | 478 | -68805408 | -68805423 | -68805437 | -68805467 | -68805834 | 0.000 | -63974634 | +1922844 | -33.27 | 7.6% | -33.68 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| nopen * | 31214 | -68805408 | -33.27 | -68805437 | -33.27 |
| 1 | 31214 | -68460813 | -33.02 | -68460842 | -33.02 |
| 5 | 30879 | -67498128 | -32.90 | -67498158 | -32.90 |
| 21 | 29627 | -63084365 | -31.57 | -63084394 | -31.57 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 5394 | 104 | -43033990 | -13.04 |
| 2021 | 16760 | 251 | -85647786 | -26.42 |
| 2022 | 9060 | 123 | -52992350 | -27.39 |
| half1 | 15442 | 238 | -81500459 | -20.48 |
| half2 | 15772 | 240 | -56376036 | -36.59 |

Controls: placebo (lag 20) z @0 -32.95, @base -32.95 on 22804 trades; planted +50 bps z -33.27 vs actual -33.27 (shift +0.00). Random-slice placebo z @0 -1.36 on 31214 trades. Power: 478 days, day-mean SE 1922844 bps, z = 3 needs 5768531 bps net per trade. Fills: mean lateness 0.0 min, 0.0% of fills late, 0.0% unfilled.

**i5-q4 / uncapped / dev — long, entry 15:55, decision exit `nopen`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 65754 | 0.0% | 0 | 65554 | 478 | -37718256 | -37718269 | -37718281 | -37718306 | -37718637 | 0.000 | -36772158 | +1127245 | -32.62 | 7.2% | -32.82 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| nopen * | 65554 | -37718256 | -32.62 | -37718281 | -32.62 |
| 1 | 65554 | -37532509 | -32.40 | -37532534 | -32.40 |
| 5 | 64681 | -37096341 | -32.44 | -37096366 | -32.44 |
| 21 | 61497 | -34849475 | -30.93 | -34849500 | -30.93 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 13339 | 104 | -21130602 | -14.20 |
| 2021 | 31092 | 251 | -51860525 | -28.16 |
| 2022 | 21123 | 123 | -27376587 | -25.82 |
| half1 | 32080 | 238 | -44347558 | -20.13 |
| half2 | 33474 | 240 | -31365076 | -33.06 |

Controls: placebo (lag 20) z @0 -32.47, @base -32.47 on 43332 trades; planted +50 bps z -32.62 vs actual -32.62 (shift +0.00). Random-slice placebo z @0 -0.68 on 65554 trades. Power: 478 days, day-mean SE 1127245 bps, z = 3 needs 3381736 bps net per trade. Fills: mean lateness 0.0 min, 0.0% of fills late, 0.0% unfilled.

**i5-q5 / smallcap / dev — long, entry 15:55, decision exit `nopen`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 31473 | 0.0% | 0 | 31393 | 478 | -68769514 | -68769530 | -68769546 | -68769579 | -68769991 | 0.000 | -63974851 | +1922843 | -33.27 | 7.6% | -33.68 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| nopen * | 31393 | -68769514 | -33.27 | -68769546 | -33.27 |
| 1 | 31393 | -68425975 | -33.02 | -68426007 | -33.02 |
| 5 | 31055 | -67465721 | -32.90 | -67465754 | -32.90 |
| 21 | 29795 | -63054240 | -31.57 | -63054273 | -31.57 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 5432 | 104 | -42962964 | -13.04 |
| 2021 | 16853 | 251 | -85611650 | -26.42 |
| 2022 | 9108 | 123 | -52996752 | -27.39 |
| half1 | 15531 | 238 | -81433999 | -20.48 |
| half2 | 15862 | 240 | -56369369 | -36.59 |

Controls: placebo (lag 20) z @0 -32.95, @base -32.95 on 23831 trades; planted +50 bps z -33.27 vs actual -33.27 (shift +0.00). Random-slice placebo z @0 +2.50 on 31393 trades. Power: 478 days, day-mean SE 1922843 bps, z = 3 needs 5768529 bps net per trade. Fills: mean lateness 0.0 min, 0.0% of fills late, 0.0% unfilled.

**i5-q5 / uncapped / dev — long, entry 15:55, decision exit `nopen`**

| candidates | unfilled | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 65945 | 0.0% | 0 | 65745 | 478 | -37718731 | -37718744 | -37718757 | -37718784 | -37719157 | 0.000 | -36773191 | +1127244 | -32.62 | 7.2% | -32.83 |

Horizon curve (mean excess per trade, bps; z):
| exit | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| nopen * | 65745 | -37718731 | -32.62 | -37718757 | -32.62 |
| 1 | 65745 | -37533150 | -32.40 | -37533177 | -32.40 |
| 5 | 64871 | -37096503 | -32.44 | -37096530 | -32.44 |
| 21 | 61679 | -34848280 | -30.93 | -34848307 | -30.93 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 13382 | 104 | -21125077 | -14.20 |
| 2021 | 31187 | 251 | -51855531 | -28.16 |
| 2022 | 21176 | 123 | -27385034 | -25.82 |
| half1 | 32171 | 238 | -44341224 | -20.13 |
| half2 | 33574 | 240 | -31373033 | -33.06 |

Controls: placebo (lag 20) z @0 -32.47, @base -32.47 on 46930 trades; planted +50 bps z -32.62 vs actual -32.62 (shift +0.00). Random-slice placebo z @0 -0.78 on 65745 trades. Power: 478 days, day-mean SE 1127244 bps, z = 3 needs 3381731 bps net per trade. Fills: mean lateness 0.0 min, 0.0% of fills late, 0.0% unfilled.

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
| nopen | 8474 | +10215993 | +2.84 | +10215957 | +2.84 |
| 1 | 8474 | +9948107 | +2.52 | +9948071 | +2.52 |
| 5 | 8431 | +8433751 | +2.60 | +8433716 | +2.60 |
| 21 | 7885 | +7769091 | +3.06 | +7769055 | +3.06 |

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
| nopen | 15769 | +5996628 | +1.17 | +5996598 | +1.17 |
| 1 | 15769 | +5828670 | +0.85 | +5828640 | +0.85 |
| 5 | 15679 | +4975277 | +0.90 | +4975247 | +0.90 |
| 21 | 14407 | +4676594 | +1.32 | +4676564 | +1.32 |

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
| nopen | 8505 | +2623418 | +0.16 | +2623383 | +0.16 |
| 1 | 8505 | +1889373 | +0.05 | +1889338 | +0.05 |
| 5 | 8463 | +211936 | +0.10 | +211900 | +0.10 |
| 21 | 7899 | -4175036 | +0.15 | -4175072 | +0.15 |

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
| nopen | 15868 | +2500716 | -0.28 | +2500686 | -0.28 |
| 1 | 15868 | +2064734 | -0.43 | +2064704 | -0.43 |
| 5 | 15777 | +1208460 | -0.37 | +1208430 | -0.37 |
| 21 | 14480 | -1405841 | -0.25 | -1405871 | -0.25 |

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
| nopen | 5590 | +8706836 | +0.47 | +8706795 | +0.47 |
| 1 | 5590 | +7794168 | +0.43 | +7794127 | +0.43 |
| 5 | 5540 | +6462998 | +0.41 | +6462956 | +0.41 |
| 21 | 5442 | +5811556 | +0.13 | +5811515 | +0.13 |

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
| nopen | 8957 | +12988690 | +1.36 | +12988655 | +1.36 |
| 1 | 8957 | +12412905 | +1.33 | +12412869 | +1.33 |
| 5 | 8846 | +11471107 | +1.26 | +11471072 | +1.26 |
| 21 | 8700 | +10170069 | +1.01 | +10170033 | +1.01 |

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
| nopen | 5357 | +13792740 | +1.00 | +13792699 | +1.00 |
| 1 | 5357 | +13429526 | +0.98 | +13429486 | +0.98 |
| 5 | 5306 | +11464580 | +0.94 | +11464540 | +0.94 |
| 21 | 5212 | +8048303 | +0.67 | +8048262 | +0.67 |

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
| nopen | 8712 | +15295528 | +1.71 | +15295493 | +1.71 |
| 1 | 8712 | +15057795 | +1.70 | +15057760 | +1.70 |
| 5 | 8597 | +13802566 | +1.64 | +13802532 | +1.64 |
| 21 | 8453 | +10920001 | +1.34 | +10919966 | +1.34 |

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
| nopen | 281 | -585776 | -1.48 | -585796 | -1.48 |
| 1 | 281 | -614391 | -1.51 | -614411 | -1.51 |
| 5 | 281 | -590637 | -1.45 | -590657 | -1.45 |
| 21 | 269 | -359336 | -1.05 | -359356 | -1.05 |

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
| nopen | 947 | -265507 | -2.00 | -265528 | -2.00 |
| 1 | 947 | -275892 | -2.01 | -275912 | -2.01 |
| 5 | 940 | -271062 | -2.00 | -271082 | -2.00 |
| 21 | 904 | -191585 | -1.79 | -191605 | -1.79 |

Per period (decision exit, base cost):
| period | trades | days | net | z |
|---|---|---|---|---|
| 2020 | 193 | 63 | +14 | +1.42 |
| 2021 | 410 | 146 | -35 | -1.31 |
| 2022 | 354 | 83 | -20 | +0.24 |
| half1 | 455 | 148 | -5 | +0.18 |
| half2 | 502 | 144 | -33 | -1.07 |

Controls: placebo (lag 20) z @0 +0.70, @base -1.36 on 1259 trades; planted +50 bps z +3.71 vs actual +0.73 (shift +2.97). Power: 292 days, day-mean SE 17 bps, z = 3 needs 50 bps net per trade. Fills: mean lateness 0.0 min, 0.6% of fills late, 0.0% unfilled.
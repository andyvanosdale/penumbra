# Wave 1 tables — confirm era

**a2r-down-close / smallcap / confirm — direction short, decision horizon 63 sessions, next-open fill**

Autopsy rule on `close` (top quintile, selection lift 2.24): match rate 20.1% of the universe per day; 39 of 2600 trades made the original 63-session move (1.50%) against a universe base rate of 0.43% (realized lift 3.48).

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 107892 | 97710 | 2600 | 618 | +959 | +937 | +915 | +871 | +339 | 0.654 | +767 | +110 | +6.96 | 20.2% | +8.88 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 2600 | +48 | +2.67 | +4 | +0.21 |
| 5 | 2600 | +104 | +2.81 | +59 | +1.69 |
| 21 | 2600 | +316 | +3.86 | +272 | +3.35 |
| 63 * | 2600 | +959 | +7.37 | +915 | +6.96 |
| 126 | 2391 | +1557 | +11.37 | +1513 | +10.99 |
| 252 | 1861 | +2393 | +18.57 | +2349 | +18.20 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2021 | 897 | 199 | +937 | +2.99 |
| 2022 | 973 | 239 | +843 | +5.85 |
| 2023 | 730 | 180 | +983 | +3.46 |
| half1 | 1409 | 319 | +864 | +4.49 |
| half2 | 1191 | 299 | +975 | +5.38 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 2637 | +962 | +8.49 | +917 |
| next_open | 2600 | +959 | +7.37 | +915 |
| next_close | 2600 | +930 | +7.17 | +886 |

Controls: placebo (lag 20) z @0 +7.78, @base +7.41 on 2048 trades; planted +50 bps z +7.82 vs actual +7.37 (shift +0.45).

**a2r-down-close / uncapped / confirm — direction short, decision horizon 63 sessions, next-open fill**

Autopsy rule on `close` (top quintile, selection lift 2.24): match rate 20.1% of the universe per day; 43 of 5139 trades made the original 63-session move (0.84%) against a universe base rate of 0.29% (realized lift 2.90).

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 181916 | 163785 | 5139 | 664 | +446 | +430 | +415 | +383 | +10 | 0.558 | +334 | +62 | +5.37 | 22.8% | +5.37 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 5139 | +23 | +2.72 | -9 | -0.65 |
| 5 | 5139 | +61 | +3.67 | +30 | +2.11 |
| 21 | 5139 | +191 | +6.85 | +159 | +5.98 |
| 63 * | 5139 | +446 | +5.87 | +415 | +5.37 |
| 126 | 4726 | +719 | +9.11 | +688 | +8.68 |
| 252 | 3699 | +1225 | +10.41 | +1193 | +10.10 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2021 | 1609 | 229 | +621 | +1.96 |
| 2022 | 2108 | 249 | +292 | +5.22 |
| 2023 | 1422 | 186 | +364 | +4.17 |
| half1 | 2671 | 351 | +464 | +3.00 |
| half2 | 2468 | 313 | +362 | +5.74 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 5198 | +455 | +5.98 | +423 |
| next_open | 5139 | +446 | +5.87 | +415 |
| next_close | 5139 | +435 | +5.68 | +403 |

Controls: placebo (lag 20) z @0 +8.06, @base +7.64 on 3496 trades; planted +50 bps z +6.67 vs actual +5.87 (shift +0.80).

**a2r-up-close / smallcap / confirm — direction long, decision horizon 63 sessions, next-open fill**

Autopsy rule on `close` (bottom quintile, selection lift 2.82): match rate 19.9% of the universe per day; 3 of 2666 trades made the original 63-session move (0.11%) against a universe base rate of 0.03% (realized lift 3.56).

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 107124 | 96939 | 2666 | 640 | +762 | +735 | +709 | +656 | +163 | 0.505 | +648 | +110 | +5.91 | 19.7% | +5.86 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 2666 | +34 | +1.02 | -18 | -2.30 |
| 5 | 2666 | +81 | +1.97 | +28 | +0.43 |
| 21 | 2666 | +333 | +5.00 | +280 | +4.04 |
| 63 * | 2666 | +762 | +6.41 | +709 | +5.91 |
| 126 | 2493 | +1179 | +9.23 | +1127 | +8.81 |
| 252 | 2013 | +1986 | +10.64 | +1934 | +10.39 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2021 | 1034 | 221 | +923 | +4.93 |
| 2022 | 988 | 244 | +732 | +4.47 |
| 2023 | 644 | 175 | +330 | +1.61 |
| half1 | 1569 | 343 | +836 | +5.92 |
| half2 | 1097 | 297 | +528 | +3.28 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 2697 | +763 | +7.14 | +710 |
| next_open | 2666 | +762 | +6.41 | +709 |
| next_close | 2666 | +743 | +6.35 | +690 |

Controls: placebo (lag 20) z @0 +5.48, @base +5.06 on 2210 trades; planted +50 bps z +6.87 vs actual +6.41 (shift +0.46).

**a2r-up-close / uncapped / confirm — direction long, decision horizon 63 sessions, next-open fill**

Autopsy rule on `close` (bottom quintile, selection lift 2.82): match rate 20.0% of the universe per day; 5 of 4416 trades made the original 63-session move (0.11%) against a universe base rate of 0.03% (realized lift 4.23).

| candidates | held | trades | days | net @0 | net @low | net @base | net @high | net @spec | hit @base | day-mean @base | SE | z @base | top-10 share | z w/o top 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 181128 | 163783 | 4416 | 664 | +492 | +468 | +445 | +397 | -53 | 0.478 | +311 | +65 | +4.80 | 19.9% | +4.19 |

Horizon curve (next-open fill; mean excess per trade, bps; z): 
| horizon | trades | gross excess | z @0 | net @base | z @base |
|---|---|---|---|---|---|
| 1 | 4416 | +24 | +1.12 | -24 | -3.34 |
| 5 | 4416 | +32 | +1.80 | -16 | -0.20 |
| 21 | 4416 | +190 | +3.22 | +143 | +2.04 |
| 63 * | 4416 | +492 | +5.58 | +445 | +4.80 |
| 126 | 4137 | +769 | +6.69 | +721 | +6.22 |
| 252 | 3342 | +1280 | +8.10 | +1233 | +7.80 |

Per period (decision horizon, base cost): 
| period | trades | days | net | z |
|---|---|---|---|---|
| 2021 | 1563 | 229 | +703 | +4.18 |
| 2022 | 1790 | 249 | +381 | +3.28 |
| 2023 | 1063 | 186 | +171 | +0.76 |
| half1 | 2524 | 351 | +617 | +4.76 |
| half2 | 1892 | 313 | +215 | +2.09 |

Fill comparison (decision horizon, zero cost / base): 
| fill | trades | gross excess | z @0 | net @base |
|---|---|---|---|---|
| close | 4454 | +515 | +6.05 | +468 |
| next_open | 4416 | +492 | +5.58 | +445 |
| next_close | 4416 | +488 | +5.86 | +440 |

Controls: placebo (lag 20) z @0 +4.03, @base +3.57 on 3732 trades; planted +50 bps z +6.36 vs actual +5.58 (shift +0.77).

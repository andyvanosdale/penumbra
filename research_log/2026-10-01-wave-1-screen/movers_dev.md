# Extreme movers (hypothesis material, not a result)

**smallcap: names per year (eligible on D−1) at each threshold; names eligible that year in the last column**

| year | x2/1d | x3/21d | x5/63d | x10/252d | -0.5/1d | -0.333/21d | -0.2/63d | -0.1/252d | eligible |
|---|---|---|---|---|---|---|---|---|---|
| 2010 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 3 | 480 |
| 2011 | 0 | 2 | 0 | 0 | 3 | 2 | 3 | 4 | 533 |
| 2012 | 1 | 1 | 0 | 1 | 4 | 4 | 3 | 2 | 433 |
| 2013 | 0 | 1 | 1 | 1 | 4 | 4 | 2 | 2 | 469 |
| 2014 | 2 | 2 | 0 | 0 | 7 | 10 | 2 | 6 | 567 |
| 2015 | 1 | 0 | 0 | 0 | 7 | 8 | 7 | 9 | 597 |
| 2016 | 1 | 2 | 0 | 0 | 10 | 9 | 6 | 10 | 671 |
| 2017 | 2 | 5 | 2 | 1 | 10 | 14 | 9 | 18 | 697 |
| 2018 | 1 | 5 | 3 | 1 | 14 | 19 | 14 | 36 | 836 |
| 2019 | 4 | 2 | 3 | 9 | 22 | 24 | 44 | 45 | 846 |
| 2020 | 35 | 43 | 19 | 3 | 24 | 105 | 27 | 0 | 1307 |
| total | 47 | 63 | 28 | 16 | 106 | 200 | 118 | 135 | |

**uncapped: names per year (eligible on D−1) at each threshold; names eligible that year in the last column**

| year | x2/1d | x3/21d | x5/63d | x10/252d | -0.5/1d | -0.333/21d | -0.2/63d | -0.1/252d | eligible |
|---|---|---|---|---|---|---|---|---|---|
| 2010 | 0 | 0 | 0 | 0 | 1 | 2 | 2 | 5 | 1305 |
| 2011 | 0 | 2 | 0 | 0 | 4 | 4 | 3 | 5 | 1550 |
| 2012 | 2 | 1 | 0 | 2 | 5 | 6 | 3 | 2 | 1041 |
| 2013 | 0 | 1 | 1 | 1 | 5 | 4 | 2 | 3 | 974 |
| 2014 | 3 | 4 | 0 | 0 | 9 | 11 | 3 | 9 | 1124 |
| 2015 | 1 | 1 | 0 | 0 | 8 | 9 | 11 | 14 | 1312 |
| 2016 | 1 | 2 | 0 | 0 | 17 | 15 | 9 | 12 | 1553 |
| 2017 | 4 | 8 | 2 | 1 | 11 | 14 | 10 | 21 | 1286 |
| 2018 | 3 | 6 | 4 | 2 | 16 | 23 | 15 | 39 | 1771 |
| 2019 | 5 | 5 | 5 | 13 | 24 | 24 | 53 | 56 | 1772 |
| 2020 | 39 | 53 | 27 | 5 | 32 | 165 | 34 | 0 | 2745 |
| total | 58 | 83 | 39 | 24 | 132 | 277 | 145 | 166 | |

**crypto: names per year (eligible on D−1) at each threshold; names eligible that year in the last column**

| year | x2/1d | x3/21d | x5/63d | x10/252d | -0.5/1d | -0.333/21d | -0.2/63d | -0.1/252d | eligible |
|---|---|---|---|---|---|---|---|---|---|
| 2018 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 21 |
| 2019 | 0 | 3 | 1 | 3 | 0 | 0 | 0 | 3 | 81 |
| 2020 | 2 | 29 | 51 | 64 | 31 | 14 | 0 | 0 | 171 |
| 2021 | 9 | 63 | 59 | 23 | 0 | 20 | 9 | 42 | 227 |
| 2022 | 5 | 7 | 1 | 0 | 6 | 31 | 22 | 21 | 256 |
| total | 16 | 102 | 112 | 90 | 37 | 65 | 31 | 68 | |

**smallcap: 5× over 63 sessions, 28 name-years; within-day percentile of the feature at D−1 among the universe on D−1**

| feature | lift top quintile | lift bottom quintile | median percentile | n |
|---|---|---|---|---|
| close | 1.61 | 1.96 | 0.36 | 28 |
| med_dv_20_prev | 0.71 | 1.96 | 0.34 | 28 |
| rvol_20 | 3.39 | 0.36 | 0.90 | 28 |
| close_to_high_250 | 0.36 | 3.21 | 0.10 | 28 |
| ret_20 | 1.79 | 1.25 | 0.43 | 28 |
| ret_60 | 1.43 | 1.61 | 0.50 | 28 |
| vol_pctl_250 | 1.43 | 0.89 | 0.69 | 28 |
| zscore_20 | 1.07 | 0.36 | 0.53 | 28 |
| shock | 0.89 | 1.25 | 0.41 | 28 |
| cap | 0.71 | 2.14 | 0.22 | 28 |

**smallcap: −80% over 63 sessions, 118 name-years; within-day percentile of the feature at D−1 among the universe on D−1**

| feature | lift top quintile | lift bottom quintile | median percentile | n |
|---|---|---|---|---|
| close | 2.54 | 0.76 | 0.81 | 118 |
| med_dv_20_prev | 0.68 | 1.61 | 0.36 | 118 |
| rvol_20 | 2.08 | 0.51 | 0.73 | 118 |
| close_to_high_250 | 0.68 | 1.78 | 0.31 | 118 |
| ret_20 | 1.99 | 0.55 | 0.69 | 118 |
| ret_60 | 1.48 | 1.19 | 0.54 | 118 |
| vol_pctl_250 | 1.91 | 0.47 | 0.71 | 118 |
| zscore_20 | 2.16 | 0.55 | 0.72 | 118 |
| shock | 2.08 | 0.51 | 0.65 | 118 |
| cap | 0.72 | 1.91 | 0.30 | 118 |

**uncapped: 5× over 63 sessions, 39 name-years; within-day percentile of the feature at D−1 among the universe on D−1**

| feature | lift top quintile | lift bottom quintile | median percentile | n |
|---|---|---|---|---|
| close | 1.28 | 2.82 | 0.17 | 39 |
| med_dv_20_prev | 0.26 | 2.31 | 0.24 | 39 |
| rvol_20 | 3.59 | 0.13 | 0.93 | 39 |
| close_to_high_250 | 0.26 | 3.46 | 0.07 | 39 |
| ret_20 | 1.28 | 2.44 | 0.25 | 39 |
| ret_60 | 1.28 | 2.18 | 0.37 | 39 |
| vol_pctl_250 | 1.67 | 0.77 | 0.69 | 39 |
| zscore_20 | 0.77 | 0.90 | 0.51 | 39 |
| shock | 0.64 | 1.79 | 0.29 | 39 |
| cap | 0.00 | 2.69 | 0.19 | 39 |

**uncapped: −80% over 63 sessions, 145 name-years; within-day percentile of the feature at D−1 among the universe on D−1**

| feature | lift top quintile | lift bottom quintile | median percentile | n |
|---|---|---|---|---|
| close | 2.24 | 0.83 | 0.75 | 145 |
| med_dv_20_prev | 0.59 | 1.79 | 0.29 | 145 |
| rvol_20 | 2.21 | 0.41 | 0.75 | 145 |
| close_to_high_250 | 0.52 | 2.00 | 0.26 | 145 |
| ret_20 | 2.14 | 0.59 | 0.73 | 145 |
| ret_60 | 1.45 | 1.14 | 0.51 | 145 |
| vol_pctl_250 | 1.76 | 0.76 | 0.65 | 145 |
| zscore_20 | 2.10 | 0.48 | 0.72 | 145 |
| shock | 1.86 | 0.52 | 0.65 | 145 |
| cap | 0.52 | 2.28 | 0.26 | 145 |

**crypto: 5× over 63 sessions, 112 name-years; within-day percentile of the feature at D−1 among the universe on D−1**

| feature | lift top quintile | lift bottom quintile | median percentile | n |
|---|---|---|---|---|
| close | 0.40 | 1.74 | 0.34 | 112 |
| med_dv_20_prev | 0.49 | 1.56 | 0.37 | 112 |
| rvol_20 | 1.56 | 0.80 | 0.58 | 112 |
| close_to_high_250 | 0.45 | 1.27 | 0.38 | 55 |
| ret_20 | 0.71 | 1.07 | 0.46 | 112 |
| ret_60 | 0.73 | 1.15 | 0.47 | 96 |
| vol_pctl_250 | 1.00 | 1.55 | 0.35 | 55 |
| zscore_20 | 0.89 | 1.12 | 0.49 | 112 |
| shock | 0.62 | 1.47 | 0.40 | 112 |

**crypto: −80% over 63 sessions, 31 name-years; within-day percentile of the feature at D−1 among the universe on D−1**

| feature | lift top quintile | lift bottom quintile | median percentile | n |
|---|---|---|---|---|
| close | 1.13 | 0.97 | 0.56 | 31 |
| med_dv_20_prev | 1.29 | 0.97 | 0.56 | 31 |
| rvol_20 | 3.23 | 0.32 | 0.90 | 31 |
| close_to_high_250 | 2.33 | 0.33 | 0.78 | 15 |
| ret_20 | 3.06 | 0.97 | 0.88 | 31 |
| ret_60 | 3.20 | 0.80 | 0.92 | 25 |
| vol_pctl_250 | 3.33 | 0.33 | 0.88 | 15 |
| zscore_20 | 3.06 | 0.81 | 0.87 | 31 |
| shock | 2.42 | 0.81 | 0.77 | 31 |
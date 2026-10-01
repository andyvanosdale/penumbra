"""Signal-screening engine (proposal 2026-09-30, section 8).

The v1 free-data screen (`experiments/screen_free_data.py`) split so that a new
signal is one file:

    data.py        pulls (Nasdaq Trader list, yfinance bars, caps, Binance klines),
                   the feature panels and a parquet cache under the data root
    engine.py      event mode (fixed horizon), rank mode (weekly), the v1 rule for the
                   regression, fills, comparator, cost schedule, statistic, controls
    signals/       one module per signal: as-of arrays in, candidate or score matrix out
    movers.py      the extreme-movers counts and lift study
    ledger.py      research_log/ledger.md rows
    __main__.py    python -m experiments.screen {pull,run,regress,movers,tables}

Standalone: pandas, numpy, yfinance, requests. Nothing here imports harness/ or legacy/.
"""

"""Universe: 50 large-cap S&P 500 tickers mapped to their SPDR sector ETF.

The ETF is the benchmark for excess-return calculation (plan §2 "Target").

NOTE ON SURVIVORSHIP BIAS (plan §7): this is a *static, present-day* membership
list, so it is contaminated by survivorship bias. It must be replaced with
point-in-time historical membership (Wikipedia revision history of the S&P 500
list, plan §5) before any result depends on universe composition over time.
"""

from __future__ import annotations

# SPDR sector ETFs (the benchmarks).
SECTOR_ETFS = {
    "XLK": "Technology",
    "XLF": "Financials",
    "XLV": "Health Care",
    "XLY": "Consumer Discretionary",
    "XLP": "Consumer Staples",
    "XLE": "Energy",
    "XLI": "Industrials",
    "XLC": "Communication Services",
}

# ticker -> sector ETF benchmark
TICKER_TO_ETF = {
    # Technology (XLK)
    "AAPL": "XLK", "MSFT": "XLK", "NVDA": "XLK", "AVGO": "XLK", "ORCL": "XLK",
    "CRM": "XLK", "ADBE": "XLK", "AMD": "XLK", "CSCO": "XLK", "ACN": "XLK",
    # Financials (XLF)
    "JPM": "XLF", "BAC": "XLF", "WFC": "XLF", "GS": "XLF", "MS": "XLF",
    "BLK": "XLF", "C": "XLF",
    # Health Care (XLV)
    "UNH": "XLV", "JNJ": "XLV", "LLY": "XLV", "MRK": "XLV", "ABBV": "XLV",
    "PFE": "XLV", "TMO": "XLV",
    # Consumer Discretionary (XLY)
    "AMZN": "XLY", "TSLA": "XLY", "HD": "XLY", "MCD": "XLY", "NKE": "XLY",
    "LOW": "XLY",
    # Consumer Staples (XLP)
    "PG": "XLP", "KO": "XLP", "PEP": "XLP", "COST": "XLP", "WMT": "XLP",
    # Energy (XLE)
    "XOM": "XLE", "CVX": "XLE", "COP": "XLE",
    # Industrials (XLI)
    "CAT": "XLI", "HON": "XLI", "UPS": "XLI", "BA": "XLI", "GE": "XLI",
    # Communication Services (XLC)
    "GOOGL": "XLC", "META": "XLC", "NFLX": "XLC", "DIS": "XLC", "T": "XLC",
    "VZ": "XLC", "CMCSA": "XLC",
}

TICKERS = sorted(TICKER_TO_ETF.keys())
ETFS = sorted(set(TICKER_TO_ETF.values()))
ALL_SYMBOLS = sorted(set(TICKERS) | set(ETFS))


def benchmark_for(ticker: str) -> str:
    """Return the sector ETF used as the excess-return benchmark for `ticker`."""
    return TICKER_TO_ETF[ticker]


assert len(TICKERS) == 50, f"expected 50 tickers, got {len(TICKERS)}"

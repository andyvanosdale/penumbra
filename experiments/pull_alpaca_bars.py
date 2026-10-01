"""Pull intraday equity bars from Alpaca's Market Data API into a local parquet cache.

Run this on your own machine; the cloud environment does not hold the key. The
output folder is what the intraday screening wave reads.

Setup (once):
    pip install requests pandas pyarrow
    export APCA_API_KEY_ID=...        # paper key from the Alpaca dashboard
    export APCA_API_SECRET_KEY=...
  or put those two lines (without `export`) in a file and pass --env-file PATH.
  Never commit that file.

Check the key works (one request):
    python experiments/pull_alpaca_bars.py --check

Pull 5-minute bars for the screen's common-stock universe, 2016 to 2023:
    python experiments/pull_alpaca_bars.py --out ~/penumbra-data/alpaca

Pull 1-minute bars for a subset or a shorter window (much larger):
    python experiments/pull_alpaca_bars.py --timeframe 1Min --start 2021-01-01 \
        --symbols-file my_symbols.csv --out ~/penumbra-data/alpaca

What it does:
  * Universe: the same Nasdaq Trader common-stock filter the free-data screen used
    (experiments/screen_free_data.py), downloaded fresh unless --symbols-file is given
    (a CSV with a `symbol` column). The list is written next to the bars.
  * Data: GET https://data.alpaca.markets/v2/stocks/bars, feed=iex, adjustment=raw,
    batches of symbols, one calendar month at a time, paginated. Timestamps are UTC.
    Extended-hours bars are kept; the screen filters by session time.
  * Layout: OUT/bars/<timeframe>/<YYYY-MM>/batch_<n>.parquet, columns
    symbol, ts, open, high, low, close, volume, trade_count, vwap; plus
    OUT/universe/common_stock_list.csv and OUT/manifest.jsonl (one line per file:
    month, batch, symbols, rows, sha256). Re-running skips files that exist, so a
    stopped pull resumes where it left off.
  * Start date: before pulling, the script asks Alpaca for the earliest SPY bar of the
    requested timeframe on the IEX feed and starts there if that is later than --start.
    `--probe` prints the earliest date and first-month bar count per timeframe for SPY
    and two common stocks, then exits; run it before a long pull.
  * Holdout: the end date is capped at 2023-12-31 (spec/03). --allow-holdout
    overrides it; do not use that for the screen.
  * Pause and resume: Ctrl-C once finishes the batch in flight, writes it, and stops
    cleanly; re-running the same command resumes at the next batch (a second Ctrl-C
    stops at once; the interrupted batch is re-pulled on resume). To hold the pull
    without stopping it, create the file OUT/PAUSE from another terminal
    (`touch ~/penumbra-data/alpaca/PAUSE`); the script waits, checking every 10 s,
    and continues when the file is removed. `--max-minutes N` stops cleanly after N
    minutes, for running in time boxes.
  * Rate limit: the free data plan allows 200 requests per minute. The script
    paces itself at 3 per second and backs off on 429.

Size and time, rough: 5Min bars for ~4,500 symbols over 8 years are about 25 million
rows a year and run 15 to 25 minutes a year. 1Min bars are 15x that; pull them for a
subset or a short window.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import signal
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

DATA_URL = "https://data.alpaca.markets/v2/stocks/bars"
NASDAQ_LISTED = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LISTED = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
HOLDOUT_START = date(2024, 1, 1)
PAGE_LIMIT = 10_000
BATCH_SYMBOLS = 50
REQUESTS_PER_SECOND = 3.0

# Same filters as experiments/screen_free_data.py, so the universes match.
COMMON_RE = re.compile(r"common stock|common shares|ordinary shares|class [a-c] (?:common|ordinary|shares)", re.I)
EXCL_RE = re.compile(
    r"warrant|\bright|\bunit|preferred|preference|depositary|\bads\b|\badr\b|\bnote|debenture|"
    r"\bbond|trust preferred|\bfund\b|\betf\b|\betn\b|closed.end|capital securities|"
    r"subordinated|senior|convertible|when.issued|contingent value|tracking stock|\bspac\b|"
    r"acquisition corp|acquisition co\b|acquisition holdings|acquisition ltd|acquisition inc|"
    r"acquisition corporation|acquisitions corp|blank check|\blp\b|limited partnership|\bl\.p\.",
    re.I,
)


LIVE = sys.stdout.isatty()
_live_open = {"on": False}


def log(msg: str) -> None:
    if _live_open["on"]:
        sys.stdout.write("\r\033[K")
        _live_open["on"] = False
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def live(msg: str) -> None:
    """Rewrite the current terminal line (progress inside a month); no-op when piped."""
    if not LIVE:
        return
    sys.stdout.write("\r\033[K" + msg)
    sys.stdout.flush()
    _live_open["on"] = True


def hms(seconds: float) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 3600}h{(seconds % 3600) // 60:02d}m"


# ---------------------------------------------------------------- credentials
def load_env_file(path: Path) -> None:
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def headers() -> dict[str, str]:
    key = os.environ.get("APCA_API_KEY_ID")
    secret = os.environ.get("APCA_API_SECRET_KEY")
    if not key or not secret:
        sys.exit("APCA_API_KEY_ID and APCA_API_SECRET_KEY are not set (export them or use --env-file)")
    return {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret, "Accept": "application/json"}


# ---------------------------------------------------------------- HTTP with pacing
class InvalidSymbol(Exception):
    """Alpaca rejected a symbol in the batch; the message carries the symbol."""


SKIPPED: set[str] = set()


class Client:
    def __init__(self) -> None:
        self.h = headers()
        self.s = requests.Session()
        self._last = 0.0
        self.requests = 0

    def get(self, url: str, params: dict) -> dict:
        for attempt in range(8):
            wait = max(0.0, self._last + 1.0 / REQUESTS_PER_SECOND - time.monotonic())
            if wait:
                time.sleep(wait)
            self._last = time.monotonic()
            self.requests += 1
            try:
                r = self.s.get(url, headers=self.h, params=params, timeout=60)
            except requests.RequestException as e:
                log(f"network error ({e}); retrying")
                time.sleep(2 ** attempt)
                continue
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                time.sleep(min(60, 5 * (attempt + 1)))
                continue
            if r.status_code in (401, 403):
                sys.exit(f"Alpaca refused the key: HTTP {r.status_code} {r.text[:200]}")
            if r.status_code >= 500:
                time.sleep(2 ** attempt)
                continue
            if r.status_code == 400 and "invalid symbol" in r.text:
                raise InvalidSymbol(r.text.split("invalid symbol:", 1)[1].strip(' "}'))
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
        raise RuntimeError("gave up after 8 attempts")


# ---------------------------------------------------------------- universe
def build_universe(out: Path) -> list[str]:
    ua = {"User-Agent": "penumbra-pull/1.0"}
    nq = pd.read_csv(io.StringIO(requests.get(NASDAQ_LISTED, headers=ua, timeout=60).text), sep="|", dtype=str, keep_default_na=False).iloc[:-1]
    ot = pd.read_csv(io.StringIO(requests.get(OTHER_LISTED, headers=ua, timeout=60).text), sep="|", dtype=str, keep_default_na=False).iloc[:-1]
    nq = nq[(nq["Test Issue"] == "N") & (nq["ETF"] == "N")]
    nq = nq[~nq["Symbol"].str.contains(r"[\$\.\^]", regex=True, na=False)]
    nq = nq.assign(exchange="NASDAQ", symbol=nq["Symbol"].str.strip(), name=nq["Security Name"].str.strip())
    ot = ot[(ot["Test Issue"] == "N") & (ot["ETF"] == "N") & ot["Exchange"].isin(["N", "A", "P", "Z"])]
    ot = ot[~ot["ACT Symbol"].str.contains(r"[\$\^]", regex=True, na=False)]
    ot = ot.assign(
        exchange=ot["Exchange"].map({"N": "NYSE", "A": "NYSEMKT", "P": "NYSEARCA", "Z": "BATS"}),
        symbol=ot["ACT Symbol"].str.strip().str.replace(".", "-", regex=False),
        name=ot["Security Name"].str.strip(),
    )
    df = pd.concat([nq[["symbol", "name", "exchange"]], ot[["symbol", "name", "exchange"]]], ignore_index=True)
    df = df[df["name"].str.contains(COMMON_RE, regex=True, na=False)]
    df = df[~df["name"].str.contains(EXCL_RE, regex=True, na=False)]
    df = df[df["symbol"].str.len() > 0].drop_duplicates("symbol").sort_values("symbol").reset_index(drop=True)
    (out / "universe").mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "universe" / "common_stock_list.csv", index=False)
    log(f"universe: {len(df)} common stocks from the Nasdaq Trader directory (current listing; survivorship-biased)")
    return [alpaca_symbol(s) for s in df["symbol"]]


def alpaca_symbol(sym: str) -> str:
    """Alpaca writes share classes with a dot (BRK.B); the screen's list uses the yfinance dash form."""
    return sym.replace("-", ".")


def read_symbols(path: Path) -> list[str]:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    col = "symbol" if "symbol" in df.columns else df.columns[0]
    syms = sorted({alpaca_symbol(s.strip()) for s in df[col].dropna() if s.strip()})
    log(f"universe: {len(syms)} symbols from {path}")
    return syms


# ---------------------------------------------------------------- pull
def months(start: date, end: date):
    d = date(start.year, start.month, 1)
    while d <= end:
        nxt = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
        yield d.strftime("%Y-%m"), max(d, start), min(nxt - timedelta(days=1), end)
        d = nxt


def pull_batch(c: Client, symbols: list[str], timeframe: str, start: date, end: date) -> pd.DataFrame:
    symbols = [s for s in symbols if s not in SKIPPED]
    while symbols:
        try:
            return _pull_batch(c, symbols, timeframe, start, end)
        except InvalidSymbol as e:
            bad = str(e)
            if bad not in symbols:
                raise
            log(f"Alpaca does not know {bad}; skipping it for the rest of the pull")
            SKIPPED.add(bad)
            symbols = [s for s in symbols if s != bad]
    return _empty()


def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=["symbol", "ts", "open", "high", "low", "close", "volume", "trade_count", "vwap"])


def _pull_batch(c: Client, symbols: list[str], timeframe: str, start: date, end: date) -> pd.DataFrame:
    params = {
        "symbols": ",".join(symbols),
        "timeframe": timeframe,
        "start": f"{start.isoformat()}T00:00:00Z",
        "end": f"{end.isoformat()}T23:59:59Z",
        "limit": PAGE_LIMIT,
        "adjustment": "raw",
        "feed": "iex",
        "sort": "asc",
    }
    frames: list[pd.DataFrame] = []
    token = None
    while True:
        if token:
            params["page_token"] = token
        js = c.get(DATA_URL, params)
        for sym, bars in (js.get("bars") or {}).items():
            if bars:
                f = pd.DataFrame(bars)
                f.insert(0, "symbol", sym)
                frames.append(f)
        token = js.get("next_page_token")
        if not token:
            break
    if not frames:
        return _empty()
    df = pd.concat(frames, ignore_index=True)
    df = df.rename(columns={"t": "ts", "o": "open", "h": "high", "l": "low", "c": "close", "v": "volume", "n": "trade_count", "vw": "vwap"})
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    for col in ("open", "high", "low", "close", "vwap"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ("volume", "trade_count"):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    return df[["symbol", "ts", "open", "high", "low", "close", "volume", "trade_count", "vwap"]].sort_values(["symbol", "ts"])


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def earliest_available(c: Client, timeframe: str, symbol: str = "SPY", first_year: int = 2010, last_year: int = 2023) -> date | None:
    """First date for which the IEX feed returns a bar of this timeframe for the symbol, one request per year."""
    for year in range(first_year, last_year + 1):
        js = c.get(DATA_URL, {"symbols": symbol, "timeframe": timeframe, "start": f"{year}-01-01T00:00:00Z",
                              "end": f"{year}-12-31T23:59:59Z", "limit": 1, "feed": "iex", "sort": "asc"})
        bars = (js.get("bars") or {}).get(symbol) or []
        if bars:
            return pd.to_datetime(bars[0]["t"]).date()
    return None


def month_bar_count(c: Client, timeframe: str, symbol: str, first_day: date) -> int:
    m_end = date(first_day.year + (first_day.month == 12), first_day.month % 12 + 1, 1) - timedelta(days=1)
    n = 0
    token = None
    while True:
        params = {"symbols": symbol, "timeframe": timeframe, "start": f"{first_day.isoformat()}T00:00:00Z",
                  "end": f"{m_end.isoformat()}T23:59:59Z", "limit": PAGE_LIMIT, "feed": "iex", "sort": "asc"}
        if token:
            params["page_token"] = token
        js = c.get(DATA_URL, params)
        n += len((js.get("bars") or {}).get(symbol) or [])
        token = js.get("next_page_token")
        if not token:
            return n


def probe() -> None:
    """Where the IEX history starts, per timeframe, for SPY and for two ordinary common stocks."""
    c = Client()
    for symbol in ("SPY", "AAPL", "PLUG"):
        for tf in ("1Day", "1Hour", "15Min", "5Min", "1Min"):
            first = earliest_available(c, tf, symbol)
            if first is None:
                log(f"{symbol:5s} {tf:6s}: no bars in any year 2010 to 2023")
                continue
            probe_month = date(first.year, first.month, 1)
            n = month_bar_count(c, tf, symbol, probe_month)
            log(f"{symbol:5s} {tf:6s}: earliest {first}; {n} bars in {probe_month.strftime('%Y-%m')}")
    log("choose --start from the row for the timeframe you will pull; a month with only a handful of bars is not usable history")


class StopRequested(Exception):
    pass


STOP = {"requested": False}


def _on_sigint(signum, frame):  # noqa: ARG001
    if STOP["requested"]:
        log("second Ctrl-C: stopping now; the batch in flight will be re-pulled on resume")
        raise KeyboardInterrupt
    STOP["requested"] = True
    log("Ctrl-C: finishing the batch in flight, then stopping; re-run the same command to resume")


def wait_if_paused(out: Path) -> None:
    pause = out / "PAUSE"
    if not pause.exists():
        return
    log(f"paused: remove {pause} to continue (checking every 10 s)")
    while pause.exists():
        time.sleep(10)
        if STOP["requested"]:
            raise StopRequested
    log("resumed")


def run(args: argparse.Namespace) -> None:
    out = Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    if end >= HOLDOUT_START and not args.allow_holdout:
        log(f"end capped at {HOLDOUT_START - timedelta(days=1)}: the holdout era is never downloaded (spec/03)")
        end = HOLDOUT_START - timedelta(days=1)
    symbols = read_symbols(Path(args.symbols_file)) if args.symbols_file else build_universe(out)
    batches = [symbols[i : i + BATCH_SYMBOLS] for i in range(0, len(symbols), BATCH_SYMBOLS)]
    c = Client()
    first = earliest_available(c, args.timeframe)
    if first is None:
        sys.exit(f"the IEX feed returned no {args.timeframe} SPY bar for any year 2010 to 2023; nothing to pull")
    if first > start:
        log(f"start moved to {first}: the earliest IEX {args.timeframe} bar Alpaca returns for SPY (months before it would be empty)")
        start = date(first.year, first.month, 1)
    if start > end:
        sys.exit(f"nothing to pull: data begins {first} and the end date is {end}")
    manifest = out / "manifest.jsonl"
    done = {json.loads(l)["file"] for l in manifest.read_text().splitlines()} if manifest.exists() else set()
    signal.signal(signal.SIGINT, _on_sigint)
    t0 = time.monotonic()
    rows_total = 0
    plan = list(months(start, end))
    log(f"{args.timeframe} bars, {len(symbols)} symbols in {len(batches)} batches, {len(plan)} months, feed=iex -> {out}")
    todo_total = sum(1 for ym, _, _ in plan for bi in range(len(batches)) if f"bars/{args.timeframe}/{ym}/batch_{bi:03d}.parquet" not in done)
    done_this_run = 0
    for mi, (ym, m_start, m_end) in enumerate(plan, 1):
        folder = out / "bars" / args.timeframe / ym
        folder.mkdir(parents=True, exist_ok=True)
        for bi, batch in enumerate(batches):
            rel = f"bars/{args.timeframe}/{ym}/batch_{bi:03d}.parquet"
            if rel in done:
                continue
            try:
                wait_if_paused(out)
            except StopRequested:
                log(f"stopped while paused after {rows_total:,} new rows; re-run the same command to resume")
                return
            if STOP["requested"] or (args.max_minutes and time.monotonic() - t0 > args.max_minutes * 60):
                log(f"stopped cleanly after {rows_total:,} new rows ({c.requests} requests); re-run the same command to resume")
                return
            df = pull_batch(c, batch, args.timeframe, m_start, m_end)
            path = out / rel
            df.to_parquet(path, index=False)
            rows_total += len(df)
            done_this_run += 1
            elapsed = time.monotonic() - t0
            eta = (todo_total - done_this_run) * elapsed / done_this_run if done_this_run else 0
            live(f"{ym} ({mi}/{len(plan)}) batch {bi + 1}/{len(batches)} · {rows_total:,} rows · {c.requests} req · "
                 f"{hms(elapsed)} elapsed · ETA {hms(eta)}")
            with manifest.open("a") as f:
                f.write(json.dumps({"file": rel, "month": ym, "batch": bi, "symbols": [s for s in batch if s not in SKIPPED], "rows": len(df),
                                    "sha256": sha256(path), "pulled_at": datetime.now(timezone.utc).isoformat()}) + "\n")
        elapsed = time.monotonic() - t0
        eta = (todo_total - done_this_run) * elapsed / done_this_run if done_this_run else 0
        log(f"{ym} done ({mi}/{len(plan)}): {rows_total:,} rows so far, {c.requests} requests, {hms(elapsed)} elapsed, ETA {hms(eta)}")
    if SKIPPED:
        (out / "universe" / "skipped_symbols.json").write_text(json.dumps(sorted(SKIPPED), indent=2))
        log(f"{len(SKIPPED)} symbols unknown to Alpaca were skipped; list in universe/skipped_symbols.json")
    log(f"finished: {rows_total:,} new rows; manifest at {manifest}")


def check() -> None:
    c = Client()
    js = c.get(DATA_URL, {"symbols": "SPY", "timeframe": "1Min", "start": "2023-12-29T14:30:00Z",
                          "end": "2023-12-29T14:35:00Z", "limit": 10, "feed": "iex"})
    n = len((js.get("bars") or {}).get("SPY", []))
    log(f"key accepted; SPY returned {n} one-minute bars for 2023-12-29 09:30-09:35 ET from the IEX feed")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--env-file", help="file with APCA_API_KEY_ID=... and APCA_API_SECRET_KEY=... lines")
    ap.add_argument("--check", action="store_true", help="one request to confirm the key works, then exit")
    ap.add_argument("--probe", action="store_true", help="find the earliest date the IEX feed has data for, then exit")
    ap.add_argument("--out", default=os.environ.get("PENUMBRA_ALPACA_OUT", "./alpaca_bars"), help="output folder")
    ap.add_argument("--timeframe", default="5Min", help="1Min, 5Min, 15Min, 30Min or 1Hour (default 5Min)")
    ap.add_argument("--start", default="2016-01-01")
    ap.add_argument("--end", default="2023-12-31")
    ap.add_argument("--symbols-file", help="CSV with a `symbol` column; default builds the screen's universe")
    ap.add_argument("--allow-holdout", action="store_true", help="permit end dates in the holdout era (not for the screen)")
    ap.add_argument("--max-minutes", type=float, default=0, help="stop cleanly after this many minutes (0 = no limit)")
    args = ap.parse_args()
    if args.env_file:
        load_env_file(Path(args.env_file).expanduser())
    if args.check:
        check()
        return
    if args.probe:
        probe()
        return
    run(args)


if __name__ == "__main__":
    main()

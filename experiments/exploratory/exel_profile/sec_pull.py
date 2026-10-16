#!/usr/bin/env python3
"""Pull point-in-time fundamentals from SEC EDGAR's XBRL "company facts" API, plus each
company's submissions file (SIC code, exchange, every filing with its date).

Standalone: requests + pandas. Resumable (skips CIKs already on disk). Rate-limited to
--rps requests per second across all workers (SEC's fair-access limit is 10/s).

    python sec_pull.py --out DATA_DIR [--tickers common_stock_list.csv] [--rps 8] [--workers 4]
                       [--keep-raw] [--user-agent "Name contact@example.com"]

Inputs
  --tickers   CSV with a `symbol` column (default: uni/common_stock_list.csv next to this
              script). Mapped to CIKs through https://www.sec.gov/include/ticker.txt.
  --ciks      alternatively, a text file of 10-digit CIKs, one per line.

Outputs under --out
  ticker_cik.csv                 the ticker -> CIK map used
  facts/CIK##########.csv.gz     one row per reported fact for the tags in TAGS:
                                 cik, taxonomy, tag, unit, start, end, val, accn, fy, fp,
                                 form, filed, frame
  subs/CIK##########.json        the submissions record (name, tickers, exchanges, sic,
                                 sicDescription, fiscalYearEnd, stateOfIncorporation)
  filings/CIK##########.csv.gz   every filing: form, filingDate, reportDate, accn, primaryDoc
  raw/ (with --keep-raw)         the untouched JSON responses, gzipped
  manifest.jsonl                 one line per file written: path, bytes, sha256, pulled_at
  pull.log

SEC asks that automated tools identify themselves with a contact address in the
User-Agent. Set SEC_USER_AGENT in the environment or pass --user-agent.
"""
from __future__ import annotations
import argparse, gzip, hashlib, io, json, logging, os, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd, requests

TAGS = {
    "us-gaap": [
        # income statement
        "Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "RevenueFromContractWithCustomerIncludingAssessedTax",
        "SalesRevenueNet", "SalesRevenueGoodsNet", "SalesRevenueServicesNet", "RevenuesNetOfInterestExpense", "TotalRevenuesAndOtherIncome",
        "GrossProfit", "CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold", "CostOfServices",
        "OperatingExpenses", "CostsAndExpenses", "ResearchAndDevelopmentExpense", "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost",
        "SellingGeneralAndAdministrativeExpense", "OperatingIncomeLoss", "InterestExpense", "IncomeTaxExpenseBenefit",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        "NetIncomeLoss", "ProfitLoss", "NetIncomeLossAvailableToCommonStockholdersBasic",
        "EarningsPerShareDiluted", "EarningsPerShareBasic",
        "WeightedAverageNumberOfDilutedSharesOutstanding", "WeightedAverageNumberOfSharesOutstandingBasic", "CommonStockSharesOutstanding",
        # balance sheet
        "CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents", "Cash",
        "ShortTermInvestments", "MarketableSecuritiesCurrent", "AvailableForSaleSecuritiesDebtSecuritiesCurrent", "AvailableForSaleSecuritiesCurrent",
        "HeldToMaturitySecuritiesCurrent", "CashCashEquivalentsAndShortTermInvestments",
        "LongTermInvestments", "MarketableSecuritiesNoncurrent", "AvailableForSaleSecuritiesDebtSecuritiesNoncurrent", "AvailableForSaleSecuritiesNoncurrent",
        "HeldToMaturitySecuritiesNoncurrent", "MarketableSecurities",
        "LongTermDebt", "LongTermDebtNoncurrent", "LongTermDebtCurrent", "DebtCurrent", "ShortTermBorrowings",
        "LongTermDebtAndCapitalLeaseObligations", "LongTermDebtAndCapitalLeaseObligationsCurrent", "ConvertibleNotesPayable",
        "ConvertibleNotesPayableCurrent", "NotesPayable", "DebtInstrumentCarryingAmount", "LineOfCredit", "SeniorNotes", "ConvertibleDebtNoncurrent",
        "Assets", "Liabilities", "StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        # cash flow
        "NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
        "PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets",
        "PaymentsForRepurchaseOfCommonStock", "ProceedsFromIssuanceOfCommonStock", "ProceedsFromIssuanceOrSaleOfEquity",
        "PaymentsOfDividendsCommonStock", "PaymentsOfDividends", "ShareBasedCompensation", "AllocatedShareBasedCompensationExpense",
    ],
    "dei": ["EntityCommonStockSharesOutstanding", "EntityPublicFloat"],
}

log = logging.getLogger("sec_pull")


class RateLimiter:
    def __init__(self, rps: float):
        self.min_interval = 1.0 / rps; self.lock = threading.Lock(); self.next_t = 0.0
    def wait(self):
        with self.lock:
            now = time.monotonic(); t = max(now, self.next_t); self.next_t = t + self.min_interval
        if t > now: time.sleep(t - now)


class Client:
    def __init__(self, ua: str, rps: float):
        self.s = requests.Session(); self.s.headers.update({"User-Agent": ua, "Accept-Encoding": "gzip, deflate"}); self.rl = RateLimiter(rps)
    def get(self, url: str, timeout: int = 60) -> requests.Response | None:
        """Returns the response, None for a 404 (no such CIK / no facts), raises after 5 failures."""
        last = None
        for attempt in range(5):
            self.rl.wait()
            try:
                r = self.s.get(url, timeout=timeout)
                if r.status_code == 404: return None
                if r.status_code in (403, 429):  # SEC throttling or an undeclared-tool block; back off, then give up
                    last = f"{r.status_code} {r.text[:80]!r}"
                    if "www.sec.gov" in url: raise RuntimeError(f"{url}: {last} (SEC wants a contact address in the User-Agent; set SEC_USER_AGENT)")
                    time.sleep(10 * (attempt + 1)); continue
                r.raise_for_status(); return r
            except requests.RequestException as e:
                last = repr(e)[:120]; time.sleep(2 ** attempt)
        raise RuntimeError(f"{url}: {last}")


def sha256(b: bytes) -> str: return hashlib.sha256(b).hexdigest()


def write_manifest(out: Path, path: Path, data: bytes, lock: threading.Lock):
    with lock, open(out / "manifest.jsonl", "a") as f:
        f.write(json.dumps({"path": str(path.relative_to(out)), "bytes": len(data), "sha256": sha256(data), "pulled_at": datetime.now(timezone.utc).isoformat()}) + "\n")


def extract_facts(cik: str, doc: dict) -> pd.DataFrame:
    rows = []
    facts = doc.get("facts", {})
    for tax, tags in TAGS.items():
        for tag in tags:
            node = facts.get(tax, {}).get(tag)
            if not node: continue
            for unit, vals in node.get("units", {}).items():
                for v in vals:
                    rows.append((cik, tax, tag, unit, v.get("start"), v.get("end"), v.get("val"), v.get("accn"), v.get("fy"), v.get("fp"), v.get("form"), v.get("filed"), v.get("frame")))
    return pd.DataFrame(rows, columns=["cik", "taxonomy", "tag", "unit", "start", "end", "val", "accn", "fy", "fp", "form", "filed", "frame"])


def filings_frame(sub: dict, client: Client, cik: str, out: Path, keep_raw: bool, mlock) -> pd.DataFrame:
    frames = []
    rec = sub.get("filings", {}).get("recent", {})
    if rec: frames.append(pd.DataFrame({k: rec[k] for k in ["form", "filingDate", "reportDate", "accessionNumber", "primaryDocument"] if k in rec}))
    for extra in sub.get("filings", {}).get("files", []):   # older filings live in sidecar files
        r = client.get(f"https://data.sec.gov/submissions/{extra['name']}")
        if r is None: continue
        if keep_raw:
            p = out / "raw" / (extra["name"] + ".gz"); p.write_bytes(gzip.compress(r.content)); write_manifest(out, p, r.content, mlock)
        d = r.json(); frames.append(pd.DataFrame({k: d[k] for k in ["form", "filingDate", "reportDate", "accessionNumber", "primaryDocument"] if k in d}))
    if not frames: return pd.DataFrame(columns=["form", "filingDate", "reportDate", "accessionNumber", "primaryDocument"])
    df = pd.concat(frames, ignore_index=True); df.insert(0, "cik", cik); return df


def pull_one(cik: str, client: Client, out: Path, keep_raw: bool, mlock) -> str:
    fpath = out / "facts" / f"CIK{cik}.csv.gz"; spath = out / "subs" / f"CIK{cik}.json"; lpath = out / "filings" / f"CIK{cik}.csv.gz"
    if fpath.exists() and spath.exists() and lpath.exists(): return "cached"
    status = []
    if not fpath.exists():
        r = client.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")
        if r is None:
            pd.DataFrame(columns=["cik", "taxonomy", "tag", "unit", "start", "end", "val", "accn", "fy", "fp", "form", "filed", "frame"]).to_csv(fpath, index=False, compression="gzip"); status.append("facts:404")
        else:
            if keep_raw:
                p = out / "raw" / f"companyfacts_CIK{cik}.json.gz"; p.write_bytes(gzip.compress(r.content)); write_manifest(out, p, r.content, mlock)
            df = extract_facts(cik, r.json()); buf = io.BytesIO(); df.to_csv(buf, index=False, compression="gzip"); fpath.write_bytes(buf.getvalue()); write_manifest(out, fpath, buf.getvalue(), mlock)
            status.append(f"facts:{len(df)}")
    if not (spath.exists() and lpath.exists()):
        r = client.get(f"https://data.sec.gov/submissions/CIK{cik}.json")
        if r is None:
            spath.write_text("{}"); pd.DataFrame().to_csv(lpath, index=False, compression="gzip"); status.append("subs:404")
        else:
            if keep_raw:
                p = out / "raw" / f"submissions_CIK{cik}.json.gz"; p.write_bytes(gzip.compress(r.content)); write_manifest(out, p, r.content, mlock)
            sub = r.json()
            keep = {k: sub.get(k) for k in ["cik", "name", "tickers", "exchanges", "sic", "sicDescription", "stateOfIncorporation", "fiscalYearEnd", "entityType", "category", "formerNames"]}
            b = json.dumps(keep).encode(); spath.write_bytes(b); write_manifest(out, spath, b, mlock)
            fl = filings_frame(sub, client, cik, out, keep_raw, mlock); buf = io.BytesIO(); fl.to_csv(buf, index=False, compression="gzip"); lpath.write_bytes(buf.getvalue()); write_manifest(out, lpath, buf.getvalue(), mlock)
            status.append(f"filings:{len(fl)}")
    return " ".join(status)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True); ap.add_argument("--tickers", default=str(Path(__file__).parent / "uni" / "common_stock_list.csv"))
    ap.add_argument("--ciks"); ap.add_argument("--ticker-map", help="local copy of https://www.sec.gov/include/ticker.txt (ticker<TAB>cik); fetched if omitted"); ap.add_argument("--rps", type=float, default=8.0); ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--keep-raw", action="store_true"); ap.add_argument("--user-agent", default=os.environ.get("SEC_USER_AGENT", "penumbra-research-screen/0.1"))
    ap.add_argument("--first", nargs="*", default=["EXEL"], help="tickers to pull first (so they can be inspected early)")
    a = ap.parse_args()
    out = Path(a.out); [ (out / d).mkdir(parents=True, exist_ok=True) for d in ["facts", "subs", "filings", "raw"] ]
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", handlers=[logging.FileHandler(out / "pull.log"), logging.StreamHandler(sys.stdout)])
    client = Client(a.user_agent, a.rps); mlock = threading.Lock()

    if a.ciks:
        ciks = [l.strip().zfill(10) for l in open(a.ciks) if l.strip()]; order = ciks
    else:
        if a.ticker_map:
            text = open(a.ticker_map).read()
        else:
            r = client.get("https://www.sec.gov/include/ticker.txt"); assert r is not None and r.text.lstrip().startswith(("a", "A")) and "<html" not in r.text[:200].lower(), "www.sec.gov refused; pass --ticker-map with a saved ticker.txt"
            text = r.text
        tmap = pd.read_csv(io.StringIO(text), sep="\t", header=None, names=["ticker", "cik"], dtype=str); tmap["ticker"] = tmap["ticker"].str.upper(); tmap["cik"] = tmap["cik"].str.zfill(10)
        lst = pd.read_csv(a.tickers, keep_default_na=False); lst["key"] = lst["symbol"].str.upper()
        m = lst.merge(tmap, left_on="key", right_on="ticker", how="left")
        m[["symbol", "name", "exchange", "cik"]].to_csv(out / "ticker_cik.csv", index=False)
        log.info("tickers %d, mapped to a CIK %d, distinct CIKs %d", len(m), m["cik"].notna().sum(), m["cik"].nunique())
        first = m[m["symbol"].isin(a.first)]["cik"].dropna().tolist()
        order = first + [c for c in m["cik"].dropna().unique().tolist() if c not in first]
    t0 = time.time(); n = 0; fails = 0
    with ThreadPoolExecutor(a.workers) as ex:
        futs = {ex.submit(pull_one, c, client, out, a.keep_raw, mlock): c for c in order}
        for f in as_completed(futs):
            n += 1
            try: msg = f.result()
            except Exception as e: msg = f"FAIL {e}"; fails += 1
            if n <= 3 or n % 100 == 0 or msg.startswith("FAIL"): log.info("%d/%d CIK%s %s (%.0fs, fails %d)", n, len(order), futs[f], msg, time.time() - t0, fails)
    log.info("DONE %d ciks, %d fails, %.0fs", n, fails, time.time() - t0)


if __name__ == "__main__":
    main()

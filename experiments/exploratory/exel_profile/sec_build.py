#!/usr/bin/env python3
"""Build a point-in-time annual fundamentals table from the files sec_pull.py wrote.

One row per 10-K filing: the fiscal year it reports, the date it was filed (the first day
the numbers were public), the current-year values and the prior-year comparatives *as
printed in that same filing*, plus sector (SIC) and the count of 13D filings against the
company in the year before. Nothing from a later filing leaks into a row.

    python sec_build.py --data DATA_DIR --out annual.csv.gz
"""
from __future__ import annotations
import argparse, glob, json, os, sys
import numpy as np, pandas as pd

ANNUAL_FORMS = {"10-K", "10-K405", "10-KT"}
# concept -> ordered tag fallbacks. D = duration (flow), I = instant (stock).
CONCEPTS = {
    "rev":    ("D", ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet",
                     "RevenuesNetOfInterestExpense", "TotalRevenuesAndOtherIncome", "SalesRevenueGoodsNet", "SalesRevenueServicesNet"]),
    "gp":     ("D", ["GrossProfit"]),
    "cogs":   ("D", ["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold", "CostOfServices"]),
    "opex":   ("D", ["OperatingExpenses", "CostsAndExpenses"]),
    "rd":     ("D", ["ResearchAndDevelopmentExpense", "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost"]),
    "sga":    ("D", ["SellingGeneralAndAdministrativeExpense"]),
    "oi":     ("D", ["OperatingIncomeLoss"]),
    "intexp": ("D", ["InterestExpense"]),
    "pretax": ("D", ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest"]),
    "ni":     ("D", ["NetIncomeLoss", "ProfitLoss", "NetIncomeLossAvailableToCommonStockholdersBasic"]),
    "eps_d":  ("D", ["EarningsPerShareDiluted", "EarningsPerShareBasic"]),
    "sh_dil": ("D", ["WeightedAverageNumberOfDilutedSharesOutstanding", "WeightedAverageNumberOfSharesOutstandingBasic"]),
    "sh_bs":  ("I", ["CommonStockSharesOutstanding"]),
    "cash":   ("I", ["CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents", "Cash"]),
    "csti":   ("I", ["CashCashEquivalentsAndShortTermInvestments"]),
    "sti":    ("I", ["ShortTermInvestments", "MarketableSecuritiesCurrent", "AvailableForSaleSecuritiesDebtSecuritiesCurrent", "AvailableForSaleSecuritiesCurrent", "HeldToMaturitySecuritiesCurrent"]),
    "lti":    ("I", ["LongTermInvestments", "MarketableSecuritiesNoncurrent", "AvailableForSaleSecuritiesDebtSecuritiesNoncurrent", "AvailableForSaleSecuritiesNoncurrent", "HeldToMaturitySecuritiesNoncurrent"]),
    "ltd":    ("I", ["LongTermDebtNoncurrent", "LongTermDebt", "LongTermDebtAndCapitalLeaseObligations", "SeniorNotes", "ConvertibleDebtNoncurrent", "ConvertibleNotesPayable"]),
    "std":    ("I", ["LongTermDebtCurrent", "DebtCurrent", "ShortTermBorrowings", "LongTermDebtAndCapitalLeaseObligationsCurrent", "ConvertibleNotesPayableCurrent", "NotesPayable"]),
    "assets": ("I", ["Assets"]),
    "equity": ("I", ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"]),
    "ocf":    ("D", ["NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"]),
    "capex":  ("D", ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"]),
    "bb":     ("D", ["PaymentsForRepurchaseOfCommonStock"]),
    "iss":    ("D", ["ProceedsFromIssuanceOfCommonStock", "ProceedsFromIssuanceOrSaleOfEquity"]),
    "div":    ("D", ["PaymentsOfDividendsCommonStock", "PaymentsOfDividends"]),
    "sbc":    ("D", ["ShareBasedCompensation", "AllocatedShareBasedCompensationExpense"]),
    "sh_out": ("I", ["EntityCommonStockSharesOutstanding"]),     # dei, as of the cover date (after FYE)
    "pfloat": ("I", ["EntityPublicFloat"]),                       # dei, as of the last Q2
}
UNIT_OK = {"USD", "shares", "USD/shares", "pure"}


def _near(entries, target, tol=15):
    """entries: list of (end, val) ; return the val whose end is within tol days of target, latest end wins."""
    best = None
    for end, val in entries:
        if abs((end - target).days) <= tol and (best is None or end > best[0]): best = (end, val)
    return None if best is None else best[1]


def pick(by_tag: dict, kind: str, tags: list[str], fye: pd.Timestamp, prior: bool):
    """Value for the current fiscal year (prior=False) or the prior-year comparative (prior=True), as reported in this filing."""
    target = fye - pd.DateOffset(years=1) if prior else fye
    for tag in tags:
        ent = by_tag.get((kind, tag))
        if not ent: continue
        if tag == "EntityCommonStockSharesOutstanding":
            if prior: return np.nan, None
            c = [(e, v) for e, v in ent if fye <= e <= fye + pd.DateOffset(months=4)]
            if c: return float(max(c)[1]), tag
            continue
        if tag == "EntityPublicFloat":
            if prior: return np.nan, None
            c = [(e, v) for e, v in ent if fye - pd.DateOffset(months=8) <= e <= fye]
            if c: return float(max(c)[1]), tag
            continue
        v = _near(ent, target)
        if v is not None: return float(v), tag
    return np.nan, None


def build_cik(path: str, subs_dir: str, fil_dir: str) -> list[dict]:
    cik = os.path.basename(path)[3:13]
    try: f = pd.read_csv(path, dtype={"cik": str, "accn": str, "fy": "float"})
    except Exception: return []
    if f.empty or "form" not in f: return []
    f = f[f["form"].isin(ANNUAL_FORMS) & f["unit"].isin(UNIT_OK)].copy()
    if f.empty: return []
    for c in ("start", "end", "filed"): f[c] = pd.to_datetime(f[c], errors="coerce")
    f = f.dropna(subset=["end", "filed", "val"]).drop_duplicates(["accn", "tag", "unit", "start", "end"])
    f["dur"] = (f["end"] - f["start"]).dt.days
    f = f[f["start"].isna() | ((f["dur"] >= 340) & (f["dur"] <= 390))]          # annual flows and instants only
    try: sub = json.load(open(os.path.join(subs_dir, f"CIK{cik}.json")))
    except Exception: sub = {}
    try:
        fl = pd.read_csv(os.path.join(fil_dir, f"CIK{cik}.csv.gz")); fl["filingDate"] = pd.to_datetime(fl["filingDate"], errors="coerce")
        d13 = fl[fl["form"].astype(str).str.startswith("SC 13D")]["filingDate"].dropna().tolist()
    except Exception: d13 = []
    rows = []
    for accn, acc in f.groupby("accn", sort=False):
        filed = acc["filed"].iloc[0]
        ann = acc[acc["start"].notna()]
        if ann.empty: continue
        fye = ann["end"].max()
        if (filed - fye).days < 0 or (filed - fye).days > 200: continue
        by_tag = {}
        for tag, st, en, val in zip(acc["tag"].values, acc["start"].values, acc["end"].values, acc["val"].values):
            kind = "I" if pd.isna(st) else "D"
            by_tag.setdefault((kind, tag), []).append((pd.Timestamp(en), val))
        row = {"cik": cik, "accn": accn, "form": acc["form"].iloc[0], "filed": filed, "fye": fye, "fy": acc["fy"].iloc[0]}
        for name, (kind, tags) in CONCEPTS.items():
            v, tag = pick(by_tag, kind, tags, fye, prior=False); row[name] = v; row[name + "_tag"] = tag
            if name not in ("sh_out", "pfloat", "sh_bs"):
                order = ([tag] + [t for t in tags if t != tag]) if tag else tags
                row[name + "_prev"] = pick(by_tag, kind, order, fye, prior=True)[0]
        lo = filed - pd.Timedelta(days=365)
        row["n_13d_12m"] = sum(1 for d in d13 if lo < d <= filed); row["n_13d_ever_before"] = sum(1 for d in d13 if d <= filed)
        row.update({"name": sub.get("name"), "tickers": "|".join(sub.get("tickers") or []), "exchanges": "|".join(sub.get("exchanges") or []),
                    "sic": sub.get("sic"), "sic_desc": sub.get("sicDescription"), "state_inc": sub.get("stateOfIncorporation"), "filer_category": sub.get("category")})
        rows.append(row)
    return rows


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--out", required=True); ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    paths = sorted(glob.glob(os.path.join(a.data, "facts", "CIK*.csv.gz")))
    if a.limit: paths = paths[: a.limit]
    rows = []
    for i, p in enumerate(paths):
        rows.extend(build_cik(p, os.path.join(a.data, "subs"), os.path.join(a.data, "filings")))
        if (i + 1) % 250 == 0: print(f"{i+1}/{len(paths)} files, {len(rows)} filings", flush=True)
    A = pd.DataFrame(rows)
    if A.empty: print("no rows"); return
    A = A.sort_values(["cik", "fye", "filed"]).drop_duplicates(["cik", "fye"], keep="first")   # one 10-K per fiscal year: the first filed
    A["sic2"] = A["sic"].astype(str).str.zfill(4).str[:2]
    A.to_csv(a.out, index=False, compression="gzip" if a.out.endswith(".gz") else None)
    print(f"wrote {len(A)} filings for {A['cik'].nunique()} companies, fiscal years {A['fye'].min().date()} to {A['fye'].max().date()}")
    print("coverage of key concepts (share of filings with a value):")
    print((A[["rev", "gp", "oi", "ni", "sh_dil", "sh_out", "cash", "ocf", "bb", "opex", "rd"]].notna().mean()).round(3).to_string())


if __name__ == "__main__":
    main()

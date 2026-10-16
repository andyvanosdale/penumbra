import pandas as pd, yfinance as yf, logging, time, json, os, warnings; warnings.filterwarnings("ignore")
from concurrent.futures import ThreadPoolExecutor, as_completed
logging.getLogger("yfinance").setLevel(logging.CRITICAL)
KEYS = ["TotalRevenue","GrossProfit","ResearchAndDevelopment","OperatingIncome","NetIncome","NetIncomeCommonStockholders","DilutedAverageShares","DilutedEPS",
        "OperatingExpense","SellingGeneralAndAdministration","EBITDA","CostOfRevenue","InterestExpense","PretaxIncome",
        "CashCashEquivalentsAndShortTermInvestments","CashAndCashEquivalents","OtherShortTermInvestments","InvestmentsAndAdvances","TotalDebt","LongTermDebt","CurrentDebt",
        "OrdinarySharesNumber","ShareIssued","StockholdersEquity","TotalAssets","TotalLiabilitiesNetMinorityInterest",
        "OperatingCashFlow","FreeCashFlow","CapitalExpenditure","RepurchaseOfCapitalStock","IssuanceOfCapitalStock","CommonStockDividendPaid","CashDividendsPaid","StockBasedCompensation","NetIncomeFromContinuingOperations"]
lst = pd.read_csv("uni/common_stock_list.csv", keep_default_na=False); tickers = lst["symbol"].tolist()
def work(t):
    out = f"fund/{t}.json"
    if os.path.exists(out): return t, "cached"
    for attempt in range(4):
        try:
            df = yf.Ticker(t)._fundamentals.financials._get_financials_time_series("yearly", KEYS)
            rec = {str(c.date()): {k: (None if pd.isna(v) else float(v)) for k, v in df[c].items()} for c in df.columns}
            json.dump(rec, open(out, "w")); return t, f"ok {len(rec)}"
        except Exception as e:
            err = repr(e)[:100]
            if "404" in err or "Empty" in err or "No fundamentals" in err: json.dump({}, open(out, "w")); return t, "none"
            time.sleep(2*2**attempt)
    json.dump({"_error": err}, open(out, "w")); return t, f"FAIL {err}"
t0=time.time(); n=0; fails=0
with ThreadPoolExecutor(3) as ex:
    futs=[ex.submit(work,t) for t in tickers]
    for f in as_completed(futs):
        t,msg=f.result(); n+=1; fails += msg.startswith("FAIL")
        if n%200==0: print(f"{n}/{len(tickers)} last={t} {msg} fails={fails} {time.time()-t0:.0f}s", flush=True)
print("DONE fund", n, "fails", fails, time.time()-t0)

import pandas as pd, re, json
COMMON_RE = re.compile(r"common stock|common shares|ordinary shares|class [a-c] (common|ordinary|shares)", re.I)
EXCL_RE = re.compile(
    r"warrant|\bright|\bunit|preferred|preference|depositary|\bads\b|\badr\b|\bnote|debenture|"
    r"\bbond|trust preferred|\bfund\b|\betf\b|\betn\b|closed.end|capital securities|"
    r"subordinated|senior|convertible|when.issued|contingent value|tracking stock|\bspac\b|"
    r"acquisition corp|acquisition co\b|acquisition holdings|acquisition ltd|acquisition inc|"
    r"acquisition corporation|acquisitions corp|blank check|\blp\b|limited partnership|\bl\.p\.", re.I)
nq = pd.read_csv("uni/nasdaqlisted.txt", sep="|", dtype=str, keep_default_na=False).iloc[:-1]
ot = pd.read_csv("uni/otherlisted.txt", sep="|", dtype=str, keep_default_na=False).iloc[:-1]
steps = {"nasdaqlisted_rows": len(nq), "otherlisted_rows": len(ot)}
nq = nq[(nq["Test Issue"] == "N") & (nq["ETF"] == "N")]
nq = nq[~nq["Symbol"].str.contains(r"[\$\.\^]", regex=True, na=False)]
nq = nq.assign(exchange="NASDAQ", symbol=nq["Symbol"].str.strip(), name=nq["Security Name"].str.strip())
ot = ot[(ot["Test Issue"] == "N") & (ot["ETF"] == "N") & ot["Exchange"].isin(["N", "A", "P", "Z"])]
ot = ot[~ot["ACT Symbol"].str.contains(r"[\$\^]", regex=True, na=False)]
ot = ot.assign(exchange=ot["Exchange"].map({"N": "NYSE", "A": "NYSEMKT", "P": "NYSEARCA", "Z": "BATS"}),
               symbol=ot["ACT Symbol"].str.strip().str.replace(".", "-", regex=False), name=ot["Security Name"].str.strip())
df = pd.concat([nq[["symbol","name","exchange"]], ot[["symbol","name","exchange"]]], ignore_index=True)
steps["after_exchange_etf_test"] = len(df)
df = df[df["name"].str.contains(COMMON_RE, regex=True, na=False)]; steps["after_common_match"] = len(df)
df = df[~df["name"].str.contains(EXCL_RE, regex=True, na=False)]; steps["after_exclusions"] = len(df)
df = df.drop_duplicates("symbol").sort_values("symbol").reset_index(drop=True); steps["unique"] = len(df)
df.to_csv("uni/common_stock_list.csv", index=False); print(json.dumps(steps, indent=1)); print(df["exchange"].value_counts().to_dict())

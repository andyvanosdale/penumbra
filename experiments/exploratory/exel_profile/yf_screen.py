"""Coiled-spring screen: a fixed six-condition profile taken from EXEL's FY2022 state, run on
every other US common stock with yfinance annual statements, by formation vintage.

Nothing here is fitted to the universe. The thresholds were written down from EXEL's own
FY2022 ratios and the literature before any other name's outcome was read.
"""
import glob, json, os, sys
import numpy as np, pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 400)

FILING_LAG_DAYS = 75          # FY end -> statement assumed public (10-K deadline is 60-90 days)
DV_FLOOR = 2_000_000          # median dollar volume over the 20 sessions before entry
PRICE_FLOOR = 2.0
EXCLUDE = {"EXEL"}            # the name the profile was written from is never scored as evidence

# ---------------------------------------------------------------- load prices
px = pd.concat([pd.read_pickle(f) for f in sorted(glob.glob("px/batch_*.pkl")) if os.path.getsize(f) > 0], ignore_index=True)
px = px.dropna(subset=["close"]).sort_values(["ticker", "date"])
px["date"] = pd.to_datetime(px["date"])
px["dv"] = px["close"] * px["volume"]
P = {t: g.set_index("date") for t, g in px.groupby("ticker")}
sessions = np.array(sorted(px["date"].unique()))
last_session = sessions[-1]
print(f"prices: {len(P)} tickers, {len(sessions)} sessions, last {pd.Timestamp(last_session).date()}")

def g(rec, k):
    v = rec.get(k); return np.nan if v is None else float(v)

# ---------------------------------------------------------------- build one row per (ticker, fiscal year)
rows = []
for f in glob.glob("fund/*.json"):
    t = os.path.basename(f)[:-5]
    if t not in P: continue
    try: rec = json.load(open(f))
    except Exception: continue
    if not rec or "_error" in rec: continue
    fys = sorted(rec.keys())
    for i, fy in enumerate(fys):
        r = rec[fy]; prev = rec[fys[i-1]] if i > 0 else {}
        rev = g(r, "TotalRevenue")
        if np.isnan(rev) or rev <= 0: continue
        fy_end = pd.Timestamp(fy); state = fy_end + pd.Timedelta(days=FILING_LAG_DAYS)
        pos = np.searchsorted(sessions, np.datetime64(state))
        if pos >= len(sessions): continue
        entry = pd.Timestamp(sessions[pos]); pxt = P[t]
        if entry not in pxt.index: continue
        hist = pxt.loc[:entry].iloc[:-1]
        if len(hist) < 20: continue
        dv20 = hist["dv"].iloc[-20:].median(); price = pxt.loc[entry, "close"]; ac = pxt["adj_close"]
        a0 = ac.loc[entry]
        def fwd(n):
            j = pos + n
            if j >= len(sessions): return np.nan
            d = pd.Timestamp(sessions[j]); s = ac.loc[:d]
            return np.nan if s.empty else s.iloc[-1] / a0 - 1
        shares = g(r, "OrdinarySharesNumber");
        if np.isnan(shares): shares = g(r, "ShareIssued")
        if np.isnan(shares) or shares <= 0: continue
        mcap = price * shares
        gp = g(r, "GrossProfit"); oi = g(r, "OperatingIncome"); ocf = g(r, "OperatingCashFlow"); fcf = g(r, "FreeCashFlow")
        rd = g(r, "ResearchAndDevelopment"); cash = g(r, "CashCashEquivalentsAndShortTermInvestments")
        if np.isnan(cash): cash = g(r, "CashAndCashEquivalents")
        lti = g(r, "InvestmentsAndAdvances"); debt = g(r, "TotalDebt")
        if np.isnan(debt): debt = np.nansum([g(r, "LongTermDebt"), g(r, "CurrentDebt")])
        bb = -g(r, "RepurchaseOfCapitalStock"); iss = g(r, "IssuanceOfCapitalStock")
        prev_rev = g(prev, "TotalRevenue"); prev_sh = g(prev, "OrdinarySharesNumber"); prev_oi = g(prev, "OperatingIncome"); prev_opex = g(prev, "OperatingExpense"); prev_rd = g(prev, "ResearchAndDevelopment"); opex = g(r, "OperatingExpense")
        netcash = np.nansum([cash, lti]) - (0 if np.isnan(debt) else debt)
        rows.append(dict(ticker=t, fy=fy, entry=entry, vintage=entry.year, price=price, dv20=dv20, mcap=mcap, rev=rev,
            gm=gp / rev if not np.isnan(gp) else np.nan, opm=oi / rev if not np.isnan(oi) else np.nan,
            profitable=(oi > 0) and (ocf > 0) if not (np.isnan(oi) or np.isnan(ocf)) else False,
            rd_mv=(0 if np.isnan(rd) else rd) / mcap, netcash_mv=netcash / mcap, ev_sales=(mcap - netcash) / rev,
            fcf_yield=fcf / mcap if not np.isnan(fcf) else np.nan,
            rev_g=rev / prev_rev - 1 if prev_rev and not np.isnan(prev_rev) and prev_rev > 0 else np.nan,
            dshares=shares / prev_sh - 1 if prev_sh and not np.isnan(prev_sh) and prev_sh > 0 else np.nan,
            opm_chg=(oi / rev - prev_oi / prev_rev) if not (np.isnan(oi) or np.isnan(prev_oi) or np.isnan(prev_rev) or prev_rev <= 0) else np.nan,
            bb_yield=(0 if np.isnan(bb) else bb) / mcap, opex_rev_chg=(opex / rev - prev_opex / prev_rev) if not (np.isnan(opex) or np.isnan(prev_opex) or np.isnan(prev_rev) or prev_rev <= 0) else np.nan, rd_rev_chg=(rd / rev - prev_rd / prev_rev) if not (np.isnan(rd) or np.isnan(prev_rd) or np.isnan(prev_rev) or prev_rev <= 0) else np.nan, iss_yield=(0 if np.isnan(iss) else iss) / mcap,
            fcf_neg=(fcf < 0) if not np.isnan(fcf) else np.nan, oi_neg=(oi < 0) if not np.isnan(oi) else np.nan,
            r6=fwd(126), r12=fwd(252), r_now=ac.iloc[-1] / a0 - 1, complete12=(pos + 252) < len(sessions)))
D = pd.DataFrame(rows)
D["opm_gap"] = D["gm"] - D["opm"]
D = D[(D["dv20"] >= DV_FLOOR) & (D["price"] >= PRICE_FLOOR)].copy()
print(f"rows after liquidity/price floors: {len(D)} ({D['ticker'].nunique()} tickers); by vintage:", D.groupby("vintage").size().to_dict())

# ---------------------------------------------------------------- the profile (fixed from EXEL FY2022: gm .96, opm .13, netcash/mcap .36, EV/S 2.1, rev_g +.14, rd/mv .17)
C = pd.DataFrame(index=D.index)
C["c1_gm60"] = D["gm"] >= 0.60
C["c2_profitable"] = D["profitable"].astype(bool)
C["c3_opm_gap40"] = D["opm_gap"] >= 0.40
C["c4_netcash10"] = D["netcash_mv"] >= 0.10
C["c5_evs4"] = D["ev_sales"] <= 4.0
C["c6_revg5"] = D["rev_g"] >= 0.05
known6 = D["rev_g"].notna()
D["score"] = C.sum(axis=1)
D["evaluable"] = 5 + known6.astype(int)
D["full"] = (D["score"] == D["evaluable"])            # every evaluable condition met
D["full_rd"] = D["full"] & (D["rd_mv"] >= 0.05)        # the R&D-heavy sub-profile
# deterioration mirror
M = pd.DataFrame(index=D.index)
M["d1_dilution10"] = D["dshares"] >= 0.10
M["d2_fcf_neg"] = D["fcf_neg"] == True
M["d3_oi_neg"] = D["oi_neg"] == True
M["d4_opm_falling"] = D["opm_chg"] < -0.02
D["dscore"] = M.sum(axis=1)
E = D[~D["ticker"].isin(EXCLUDE)].copy()

def summarize(df, col, label, ret="r12"):
    u = df[df[ret].notna()]
    out = []
    for v, grp in u.groupby("vintage"):
        um = grp[ret].median(); ua = grp[ret].mean()
        for key, sub in grp.groupby(col):
            if len(sub) == 0: continue
            out.append(dict(vintage=v, **{label: key}, n=len(sub), mean=sub[ret].mean(), median=sub[ret].median(),
                            excess_mean=sub[ret].mean() - ua, excess_median=sub[ret].median() - um, hit_vs_univ_median=(sub[ret] > um).mean(),
                            univ_n=len(grp), univ_mean=ua, univ_median=um))
    return pd.DataFrame(out)

pd.set_option("display.float_format", lambda x: f"{x:,.3f}")
print("\n================ 12-month forward return by SCORE (number of EXEL-profile conditions met), per vintage; EXEL excluded")
S = summarize(E, "score", "score"); print(S.to_string(index=False))
print("\n================ FULL profile (all evaluable conditions met) vs rest, 12-month forward")
F = summarize(E, "full", "full"); print(F.to_string(index=False))
print("\n================ FULL profile, 6-month forward")
print(summarize(E, "full", "full", ret="r6").to_string(index=False))
print("\n================ FULL + R&D/MV >= 5% sub-profile, 12-month forward")
print(summarize(E, "full_rd", "full_rd").to_string(index=False))
print("\n================ each condition alone (met vs not), 12-month excess over universe mean, pooled across complete vintages")
rows = []
Ec = E[E["r12"].notna()]
for c in C.columns:
    for v, grp in Ec.groupby("vintage"):
        m = C.loc[grp.index, c]
        rows.append(dict(cond=c, vintage=v, n_met=int(m.sum()), met_mean=grp.loc[m, "r12"].mean(), notmet_mean=grp.loc[~m, "r12"].mean(), spread=grp.loc[m, "r12"].mean() - grp.loc[~m, "r12"].mean(),
                         met_median=grp.loc[m, "r12"].median(), notmet_median=grp.loc[~m, "r12"].median()))
print(pd.DataFrame(rows).to_string(index=False))
print("\n================ DETERIORATION mirror score (dilution >=10%, FCF<0, OI<0, op margin falling), 12-month forward, per vintage")
print(summarize(E[E["dshares"].notna()], "dscore", "dscore").to_string(index=False))


# ---------------------------------------------------------------- normalized score (share of evaluable conditions met)
E["score_norm"] = E["score"] / E["evaluable"]
E["bucket"] = pd.cut(E["score_norm"], bins=[-0.01, 0.41, 0.61, 0.81, 0.99, 1.01], labels=["<=2of5", "3of5", "4of5", "all-but-1 (6)", "all"])
print("\n================ 12-month forward return by share of evaluable conditions met, per vintage")
print(summarize(E, "bucket", "bucket").to_string(index=False))

# ---------------------------------------------------------------- rank composite: direction of the profile without hard thresholds
def pct(s): return s.rank(pct=True)
comp_parts = []
for v, grp in E.groupby("vintage"):
    parts = pd.concat([pct(grp["gm"]), pct(grp["opm_gap"]), pct(grp["netcash_mv"]), 1 - pct(grp["ev_sales"]), pct(grp["rd_mv"])], axis=1)
    if grp["rev_g"].notna().sum() > 50: parts = pd.concat([parts, pct(grp["rev_g"])], axis=1)
    comp_parts.append(parts.mean(axis=1, skipna=True))
E["composite"] = pd.concat(comp_parts)
def deciles(df, label, ret="r12"):
    u = df[df[ret].notna()].copy(); out = []
    for v, grp in u.groupby("vintage"):
        if len(grp) < 100: continue
        grp = grp.copy(); grp["dec"] = pd.qcut(grp["composite"].rank(method="first"), 10, labels=False) + 1
        um = grp[ret].median()
        for d, sub in grp.groupby("dec"):
            out.append(dict(vintage=v, decile=d, n=len(sub), mean=sub[ret].mean(), median=sub[ret].median(), excess_median=sub[ret].median() - um,
                            hit=(sub[ret] > um).mean(), doubled_to_date=(sub["r_now"] >= 1.0).mean(), univ_doubled=(grp["r_now"] >= 1.0).mean()))
    R = pd.DataFrame(out)
    print(f"\n================ {label}: composite-rank deciles (10 = most EXEL-like), 12-month forward; 'doubled_to_date' = share with r_now >= +100%")
    print(R.to_string(index=False))
    sp = R.pivot(index="vintage", columns="decile", values="median")
    print("top-minus-bottom decile median 12m return, by vintage:", (sp[10] - sp[1]).round(3).to_dict())
deciles(E, "ALL liquid names")
deciles(E[E["profitable"].astype(bool)], "PROFITABLE names only (OI>0 and OCF>0)")
deciles(E[E["mcap"] >= 3e8], "names with market cap >= USD 300m")
deciles(E[(E["mcap"] >= 3e8) & E["profitable"].astype(bool)], "market cap >= USD 300m AND profitable")


# ---------------------------------------------------------------- INFLECTION profile: what EXEL looked like at its FY2024 filing (opm +23pp, R&D/rev -15pp, shares -7%, rev +18%, buyback 7% of mcap)
I = pd.DataFrame(index=E.index)
I["i1_opm_up5"] = E["opm_chg"] >= 0.05
I["i2_opex_ratio_down"] = E["opex_rev_chg"] <= -0.03
I["i3_shares_down"] = E["dshares"] <= -0.02
I["i4_revg5"] = E["rev_g"] >= 0.05
I["i5_profitable"] = E["profitable"].astype(bool)
known = E["opm_chg"].notna() & E["dshares"].notna() & E["opex_rev_chg"].notna()
E["iscore"] = I.sum(axis=1).where(known)
E["ifull"] = (E["iscore"] == 5)
print("\n================ INFLECTION score (margin up >=5pp, opex/rev down >=3pp, shares down >=2%, revenue +5%, profitable), 12-month forward, per vintage")
print(summarize(E[known], "iscore", "iscore").to_string(index=False))
print("\n================ INFLECTION full (5 of 5) vs rest, 12-month forward")
print(summarize(E[known], "ifull", "ifull").to_string(index=False))
print("\n================ INFLECTION full, 6-month forward (includes the partial 2026 vintage)")
print(summarize(E[known], "ifull", "ifull", ret="r6").to_string(index=False))
# inflection composite deciles: direction without thresholds
E2 = E[known].copy()
parts = []
for v, grp in E2.groupby("vintage"):
    parts.append(pd.concat([pct(grp["opm_chg"]), 1 - pct(grp["opex_rev_chg"]), 1 - pct(grp["dshares"]), pct(grp["rev_g"]), pct(grp["bb_yield"])], axis=1).mean(axis=1))
E2["composite"] = pd.concat(parts)
deciles(E2, "INFLECTION composite (margin change, opex-ratio change, share-count change, revenue growth, buyback yield)")
deciles(E2[E2["profitable"].astype(bool)], "INFLECTION composite, PROFITABLE names only")
print("\n================ EXEL under the inflection profile")
X = D[D["ticker"] == "EXEL"].copy()
print(X[["fy", "entry", "price", "opm_chg", "opex_rev_chg", "dshares", "rev_g", "bb_yield", "r12", "r_now"]].to_string(index=False))
for v in sorted(E2["vintage"].unique()):
    sub = E2[(E2["vintage"] == v) & E2["ifull"]].sort_values("r12", ascending=False)
    print(f"\n================ vintage {v}: inflection-full names ({len(sub)})")
    print(sub[["ticker", "fy", "entry", "price", "mcap", "opm", "opm_chg", "opex_rev_chg", "dshares", "rev_g", "bb_yield", "r12", "r_now"]].to_string(index=False))
# summary tables to CSV for charting
summarize(E, "bucket", "bucket").to_csv("sum_level_bucket.csv", index=False)
summarize(E[E["dshares"].notna()], "dscore", "dscore").to_csv("sum_deterioration.csv", index=False)
summarize(E[known], "iscore", "iscore").to_csv("sum_inflection.csv", index=False)
E.to_csv("model_rows_scored.csv", index=False)

# EXEL sanity
print("\n================ EXEL's own rows (sanity: does the profile flag it?)")
print(D[D["ticker"] == "EXEL"][["fy", "entry", "price", "gm", "opm", "opm_gap", "netcash_mv", "ev_sales", "rev_g", "rd_mv", "score", "evaluable", "full", "r12", "r_now"]].to_string(index=False))

# names
cols = ["ticker", "fy", "entry", "price", "mcap", "gm", "opm", "netcash_mv", "ev_sales", "rev_g", "rd_mv", "bb_yield", "score", "r12", "r_now"]
for v in sorted(E["vintage"].unique()):
    sub = E[(E["vintage"] == v) & E["full"]].sort_values("r12", ascending=False)
    print(f"\n================ vintage {v}: full-profile names ({len(sub)}), with 12-month and to-date returns")
    print(sub[cols].to_string(index=False))
D.to_csv("model_rows.csv", index=False); C.to_csv("model_conditions.csv"); M.to_csv("model_mirror.csv")

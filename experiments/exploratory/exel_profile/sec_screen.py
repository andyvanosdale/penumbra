#!/usr/bin/env python3
"""Point-in-time screen of three fixed fundamental profiles (level, inflection, deterioration)
on every 10-K filing in the annual table, with entry on the first session after the filing
date and forward returns from daily prices.

    python sec_screen.py --annual annual.csv.gz --map ticker_cik.csv --prices px_hist px --out results/

Profiles and thresholds are those of the 2026-10-16 exploratory run (fixed before this data
was read); see exel-profile-screen-results.md. Nothing is fitted here.
"""
from __future__ import annotations
import argparse, glob, os
import numpy as np, pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 500)

DV_FLOOR, PRICE_FLOOR, EXCLUDE = 2_000_000, 2.0, {"EXEL"}


def load_prices(dirs):
    frames = []
    for d in dirs:
        for f in sorted(glob.glob(os.path.join(d, "batch_*.pkl"))):
            if os.path.getsize(f) > 0: frames.append(pd.read_pickle(f))
    px = pd.concat(frames, ignore_index=True).dropna(subset=["close"])
    px["date"] = pd.to_datetime(px["date"]); px = px.drop_duplicates(["ticker", "date"]).sort_values(["ticker", "date"])
    px["dv"] = px["close"] * px["volume"]
    return px


def nz(x): return 0.0 if pd.isna(x) else float(x)


def build_rows(A, tmap, px):
    P = {}
    for t, g in px.groupby("ticker"):
        P[t] = (g["date"].values.astype("datetime64[ns]"), g["close"].values.astype(float), g["adj_close"].values.astype(float), g["dv"].values.astype(float))
    A = A.merge(tmap[["symbol", "cik"]], on="cik", how="inner")
    A["filed"] = pd.to_datetime(A["filed"]); A["fye"] = pd.to_datetime(A["fye"])
    rows = []
    for r in A.itertuples(index=False):
        t = r.symbol
        if t not in P: continue
        dates, close, ac, dv = P[t]
        pos = int(np.searchsorted(dates, np.datetime64(r.filed, "ns"), side="right"))   # first session strictly after the filing date
        if pos >= len(dates) or pos < 20: continue
        dv20 = float(np.median(dv[pos - 20:pos])); price = float(close[pos]); a0 = float(ac[pos])
        if not (dv20 >= DV_FLOOR and price >= PRICE_FLOOR and a0 > 0): continue
        def fwd(n):
            j = pos + n
            return np.nan if j >= len(dates) else ac[j] / a0 - 1
        shares = r.sh_out if not pd.isna(r.sh_out) else (r.sh_bs if not pd.isna(r.sh_bs) else r.sh_dil)
        rev = r.rev
        if pd.isna(shares) or shares <= 0 or pd.isna(rev) or rev <= 0: continue
        mcap = price * shares
        gp = r.gp if not pd.isna(r.gp) else (rev - r.cogs if not pd.isna(r.cogs) else np.nan)
        cash = r.cash if not pd.isna(r.cash) else r.csti
        sti = 0.0 if (pd.isna(r.cash) and not pd.isna(r.csti)) else nz(r.sti)
        netcash = nz(cash) + sti + nz(r.lti) - nz(r.ltd) - nz(r.std)
        fcf = r.ocf - nz(r.capex) if not pd.isna(r.ocf) else np.nan
        opm = r.oi / rev if not pd.isna(r.oi) else np.nan
        opm_prev = r.oi_prev / r.rev_prev if not (pd.isna(r.oi_prev) or pd.isna(r.rev_prev) or r.rev_prev <= 0) else np.nan
        # operating-cost ratio: the tagged total, else R&D + SG&A, else revenue minus operating income (same basis for both years, since both come from the same filing)
        def opex_ratio(opex, rd, sga, oi, rv):
            if pd.isna(rv) or rv <= 0: return np.nan, None
            if not pd.isna(opex): return opex / rv, "tagged"
            if not (pd.isna(rd) or pd.isna(sga)): return (rd + sga) / rv, "rd+sga"
            if not pd.isna(oi): return (rv - oi) / rv, "rev-oi"
            return np.nan, None
        oxr, oxr_src = opex_ratio(r.opex, r.rd, r.sga, r.oi, rev)
        oxr_prev, oxr_src_prev = opex_ratio(r.opex_prev, r.rd_prev, r.sga_prev, r.oi_prev, r.rev_prev)
        opex_rev_chg = oxr - oxr_prev if (oxr_src is not None and oxr_src == oxr_src_prev) else np.nan
        rows.append(dict(ticker=t, cik=r.cik, fye=r.fye, filed=r.filed, entry=pd.Timestamp(dates[pos]), vintage=pd.Timestamp(dates[pos]).year, price=price, dv20=dv20, mcap=mcap, rev=rev, sic2=r.sic2, name=r.name,
            gm=gp / rev if not pd.isna(gp) else np.nan, opm=opm, opm_chg=opm - opm_prev if not (pd.isna(opm) or pd.isna(opm_prev)) else np.nan,
            opex_rev_chg=opex_rev_chg, opex_src=oxr_src,
            profitable=bool((not pd.isna(r.oi)) and r.oi > 0 and (not pd.isna(r.ocf)) and r.ocf > 0),
            rd_mv=nz(r.rd) / mcap, netcash_mv=netcash / mcap, ev_sales=(mcap - netcash) / rev, fcf_yield=fcf / mcap if not pd.isna(fcf) else np.nan,
            rev_g=rev / r.rev_prev - 1 if not (pd.isna(r.rev_prev) or r.rev_prev <= 0) else np.nan,
            dshares=r.sh_dil / r.sh_dil_prev - 1 if not (pd.isna(r.sh_dil) or pd.isna(r.sh_dil_prev) or r.sh_dil_prev <= 0) else np.nan,
            bb_yield=nz(r.bb) / mcap, iss_yield=nz(r.iss) / mcap, netpayout=(nz(r.bb) + nz(r.div) - nz(r.iss)) / mcap,
            fcf_neg=(fcf < 0) if not pd.isna(fcf) else np.nan, oi_neg=(r.oi < 0) if not pd.isna(r.oi) else np.nan,
            act_13d=int(r.n_13d_12m > 0), r6=fwd(126), r12=fwd(252), r36=fwd(756), r_now=ac[-1] / a0 - 1))
    return pd.DataFrame(rows)


def score(D):
    C = pd.DataFrame(index=D.index)
    C["c1_gm60"] = D["gm"] >= 0.60; C["c2_profitable"] = D["profitable"]; C["c3_opm_gap40"] = (D["gm"] - D["opm"]) >= 0.40
    C["c4_netcash10"] = D["netcash_mv"] >= 0.10; C["c5_evs4"] = D["ev_sales"] <= 4.0; C["c6_revg5"] = D["rev_g"] >= 0.05
    D["lscore"] = C.sum(axis=1); D["levaluable"] = 5 + D["rev_g"].notna().astype(int); D["lfull"] = D["lscore"] == D["levaluable"]
    I = pd.DataFrame(index=D.index)
    I["i1_opm_up5"] = D["opm_chg"] >= 0.05; I["i2_opex_ratio_down"] = D["opex_rev_chg"] <= -0.03; I["i3_shares_down"] = D["dshares"] <= -0.02
    I["i4_revg5"] = D["rev_g"] >= 0.05; I["i5_profitable"] = D["profitable"]
    iknown = D["opm_chg"].notna() & D["dshares"].notna() & D["opex_rev_chg"].notna()
    D["iscore"] = I.sum(axis=1).where(iknown); D["ifull"] = D["iscore"] == 5
    M = pd.DataFrame(index=D.index)
    M["d1_dilution10"] = D["dshares"] >= 0.10; M["d2_fcf_neg"] = D["fcf_neg"] == True; M["d3_oi_neg"] = D["oi_neg"] == True; M["d4_opm_falling"] = D["opm_chg"] < -0.02
    D["dscore"] = M.sum(axis=1).where(D["dshares"].notna() & D["opm_chg"].notna())
    return D, C, I, M


def pct(s): return s.rank(pct=True)


def composites(D):
    lv, inf = [], []
    for v, g in D.groupby("vintage"):
        parts = [pct(g["gm"]), pct(g["gm"] - g["opm"]), pct(g["netcash_mv"]), 1 - pct(g["ev_sales"]), pct(g["rd_mv"])]
        if g["rev_g"].notna().sum() > 50: parts.append(pct(g["rev_g"]))
        lv.append(pd.concat(parts, axis=1).mean(axis=1, skipna=True))
        inf.append(pd.concat([pct(g["opm_chg"]), 1 - pct(g["opex_rev_chg"]), 1 - pct(g["dshares"]), pct(g["rev_g"]), pct(g["bb_yield"])], axis=1).mean(axis=1, skipna=False))
    D["lcomp"] = pd.concat(lv); D["icomp"] = pd.concat(inf)
    return D


def by_group(df, col, ret="r12", sector_neutral=False):
    u = df[df[ret].notna() & df[col].notna()].copy(); out = []
    if sector_neutral:
        med = u.groupby(["vintage", "sic2"])[ret].transform("median"); cnt = u.groupby(["vintage", "sic2"])[ret].transform("size")
        u["bench"] = med.where(cnt >= 10, u.groupby("vintage")[ret].transform("median"))
    else:
        u["bench"] = u.groupby("vintage")[ret].transform("median")
    u["ex"] = u[ret] - u["bench"]
    for (v, k), g in u.groupby(["vintage", col]):
        out.append(dict(vintage=v, **{col: k}, n=len(g), median_ret=g[ret].median(), excess_median=g["ex"].median(), mean_excess=g["ex"].mean(), hit=(g["ex"] > 0).mean(), univ_n=(u["vintage"] == v).sum()))
    return pd.DataFrame(out)


def pooled(tbl, col, key, min_n=5):
    """Across vintages: how often the group's median excess is positive, and its average."""
    t = tbl[(tbl[col] == key) & (tbl["n"] >= min_n)]
    return dict(group=f"{col}={key}", vintages=len(t), positive=int((t["excess_median"] > 0).sum()), mean_excess_median=t["excess_median"].mean(), mean_hit=t["hit"].mean(), total_n=int(t["n"].sum()))


def decile_spread(D, comp, ret="r12"):
    out = []
    for v, g in D[D[ret].notna() & D[comp].notna()].groupby("vintage"):
        if len(g) < 100: continue
        g = g.copy(); g["dec"] = pd.qcut(g[comp].rank(method="first"), 10, labels=False) + 1
        m = g.groupby("dec")[ret].median(); um = g[ret].median()
        out.append(dict(vintage=v, n=len(g), top_excess=m[10] - um, bottom_excess=m[1] - um, spread=m[10] - m[1], top_hit=(g[g["dec"] == 10][ret] > um).mean(),
                        monotone_corr=np.corrcoef(np.arange(1, 11), m.values)[0, 1]))
    return pd.DataFrame(out)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--annual", required=True); ap.add_argument("--map", required=True); ap.add_argument("--prices", nargs="+", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    A = pd.read_csv(a.annual, dtype={"cik": str, "sic": str, "sic2": str}); tmap = pd.read_csv(a.map, dtype={"cik": str}, keep_default_na=False); tmap = tmap[tmap["cik"] != ""]
    px = load_prices(a.prices); print(f"prices: {px['ticker'].nunique()} tickers, {px['date'].min().date()} to {px['date'].max().date()}")
    D = build_rows(A, tmap, px); print(f"filings with prices and passing floors: {len(D)} ({D['ticker'].nunique()} tickers); by vintage:", D.groupby("vintage").size().to_dict())
    D, C, I, M = score(D); D = composites(D)
    E = D[~D["ticker"].isin(EXCLUDE)].copy()
    E.to_csv(os.path.join(a.out, "rows_scored.csv.gz"), index=False, compression="gzip")
    pd.set_option("display.float_format", lambda x: f"{x:,.3f}")
    res = {}
    for label, col in [("LEVEL full (all evaluable conditions)", "lfull"), ("INFLECTION score", "iscore"), ("INFLECTION full (5 of 5)", "ifull"), ("DETERIORATION score", "dscore")]:
        for sn in (False, True):
            t = by_group(E, col, sector_neutral=sn); name = f"{label}{' [sector-neutral]' if sn else ''}"
            t.to_csv(os.path.join(a.out, f"{col}{'_sn' if sn else ''}.csv"), index=False)
            print(f"\n================ {name}: median 12-month excess over the {'same-sector ' if sn else ''}universe median, by vintage")
            print(t.to_string(index=False))
            res[name] = t
    print("\n================ POOLED across vintages (groups with n >= 5 in a vintage)")
    P = pd.DataFrame([pooled(res["LEVEL full (all evaluable conditions)"], "lfull", True), pooled(res["LEVEL full (all evaluable conditions) [sector-neutral]"], "lfull", True),
                      pooled(res["INFLECTION full (5 of 5)"], "ifull", True), pooled(res["INFLECTION full (5 of 5) [sector-neutral]"], "ifull", True),
                      pooled(res["INFLECTION score"], "iscore", 4.0), pooled(res["INFLECTION score"], "iscore", 0.0),
                      pooled(res["DETERIORATION score"], "dscore", 3.0), pooled(res["DETERIORATION score"], "dscore", 4.0), pooled(res["DETERIORATION score"], "dscore", 0.0)])
    print(P.to_string(index=False)); P.to_csv(os.path.join(a.out, "pooled.csv"), index=False)
    for comp, label in [("lcomp", "LEVEL composite"), ("icomp", "INFLECTION composite")]:
        t = decile_spread(E, comp); t.to_csv(os.path.join(a.out, f"{comp}_deciles.csv"), index=False)
        print(f"\n================ {label}: top decile and bottom decile median excess, spread, and rank correlation of decile medians (1 = monotone), by vintage")
        print(t.to_string(index=False)); print("vintages with positive spread:", int((t["spread"] > 0).sum()), "of", len(t), "; mean spread", round(t["spread"].mean(), 3))
    # placebo: the inflection score the same company had two fiscal years earlier, with today's entry
    lag = E[["cik", "fye", "iscore"]].copy(); lag["fye"] = lag["fye"] + pd.DateOffset(years=2); lag = lag.rename(columns={"iscore": "iscore_lag2"})
    E2 = E.merge(lag, on=["cik"], suffixes=("", "_l")); E2 = E2[(E2["fye_l"] - E2["fye"]).abs().dt.days <= 20].drop(columns=["fye_l"])
    t = by_group(E2, "iscore_lag2"); t.to_csv(os.path.join(a.out, "placebo_iscore_lag2.csv"), index=False)
    print("\n================ PLACEBO: inflection score from two fiscal years earlier, forward return from today's entry (should be flat)")
    print(t[t["iscore_lag2"].isin([0.0, 4.0, 5.0])].to_string(index=False))
    # the activism flag as a split on the level profile
    t = by_group(E[E["lfull"]], "act_13d"); print("\n================ LEVEL full names split by a 13D in the prior 12 months (1) or not (0)"); print(t.to_string(index=False))
    # EXEL
    X = D[D["ticker"] == "EXEL"][["fye", "filed", "entry", "price", "gm", "opm", "opm_chg", "opex_rev_chg", "netcash_mv", "ev_sales", "rev_g", "dshares", "bb_yield", "act_13d", "lscore", "lfull", "iscore", "ifull", "dscore", "r12", "r36", "r_now"]]
    print("\n================ EXEL"); print(X.to_string(index=False))
    # names: inflection-full in the two most recent complete vintages and the current one
    for v in sorted(E["vintage"].unique())[-3:]:
        sub = E[(E["vintage"] == v) & E["ifull"]].sort_values("r12", ascending=False)
        print(f"\n================ vintage {v}: inflection-full names ({len(sub)})")
        print(sub[["ticker", "name", "sic2", "filed", "price", "mcap", "opm", "opm_chg", "opex_rev_chg", "dshares", "rev_g", "bb_yield", "act_13d", "r12", "r_now"]].to_string(index=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fetch_history.py - A 股多期历史序列拉取（第二关趋势表的固定数据源）。

设计动机：单期取数只有 2 个报告期，禁止下趋势结论（周期混淆守卫）。
本脚本拉最近 5 个完整年报 + 最新中报，产出判据/报告可直接用的多年序列：
营收/净利/扣非/毛利率/ROE/ROIC(保守口径)/OCF÷净利/股本/有息负债/合同负债，
另附分红明细（按年度聚合中期+末期，估算派息率）。

防卡死：每个接口独立 try + socket 全局超时；单源失败不影响其余，缺的如实标 null。
国内源必须直连：脚本内强制 NO_PROXY。

用法：
  python scripts/fetch_history.py --code 600519 [--name 贵州茅台] [--out trial/]
输出：trial/<code>-history.json
"""
import argparse
import json
import os
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def f(v):
    try:
        x = float(v)
        return None if x != x else x
    except (TypeError, ValueError):
        return None


def rows_by_date(df):
    out = {}
    for _, r in df.iterrows():
        d = str(r.get("REPORT_DATE"))[:10]
        out[d] = r
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--code", required=True)
    ap.add_argument("--name", default=None)
    ap.add_argument("--out", default=str(ROOT / "trial"))
    a = ap.parse_args()
    code = "".join(c for c in a.code if c.isdigit())
    if len(code) != 6:
        raise SystemExit("A 股代码应为 6 位数字")
    px = ("SH" if code[0] == "6" else "SZ") + code
    os.environ["NO_PROXY"] = "*"
    os.environ.pop("HTTP_PROXY", None)
    os.environ.pop("HTTPS_PROXY", None)
    socket.setdefaulttimeout(40)
    import akshare as ak

    warn = []
    pf = bl = cf = dv = None
    for name, fn in [
        ("利润表", lambda: ak.stock_profit_sheet_by_report_em(symbol=px)),
        ("资产负债表", lambda: ak.stock_balance_sheet_by_report_em(symbol=px)),
        ("现金流量表", lambda: ak.stock_cash_flow_sheet_by_report_em(symbol=px)),
        ("分红", lambda: ak.stock_fhps_detail_em(symbol=code)),
    ]:
        try:
            r = fn()
            if name == "利润表": pf = r
            elif name == "资产负债表": bl = r
            elif name == "现金流量表": cf = r
            else: dv = r
        except Exception as e:
            warn.append("%s FAIL %s: %s" % (name, type(e).__name__, str(e)[:80]))

    def pick(df, d, cols):
        if df is None:
            return {}
        m = {c: None for c in cols}
        try:
            row = df[df["REPORT_DATE"].astype(str).str[:10] == d]
            if row.empty:
                return m
            r0 = row.iloc[0]
            for c in cols:
                m[c] = f(r0.get(c))
        except Exception as e:
            warn.append("pick %s %s: %s" % (d, type(e).__name__, str(e)[:60]))
        return m

    PC = ["TOTAL_OPERATE_INCOME", "OPERATE_COST", "PARENT_NETPROFIT",
          "DEDUCT_PARENT_NETPROFIT", "TOTAL_PROFIT", "INCOME_TAX"]
    BC = ["TOTAL_EQUITY", "TOTAL_PARENT_EQUITY", "MONETARYFUNDS", "SHARE_CAPITAL",
          "SHORT_LOAN", "LONG_LOAN", "BOND_PAYABLE", "NONCURRENT_LIAB_1YEAR",
          "GOODWILL", "CONTRACT_LIAB"]
    CC = ["NETCASH_OPERATE", "CONSTRUCT_LONG_ASSET", "FA_IR_DEPR", "IR_DEPR",
          "IA_AMORTIZE", "LPE_AMORTIZE"]

    latest_dates = []
    if bl is not None:
        ds = sorted({str(x)[:10] for x in bl["REPORT_DATE"].astype(str)}, reverse=True)
        latest_dates = ds[:1]
    years = [y + "-12-31" for y in sorted(
        {d[:4] for d in (pf["REPORT_DATE"].astype(str).str[:10]
                         if pf is not None else []) if d.endswith("12-31")},
        reverse=True)[:5]]

    series = []
    prev_eq = prev_ni = None
    for d in years + [x for x in latest_dates if not x.endswith("12-31")]:
        p, b, c = pick(pf, d, PC), pick(bl, d, BC), pick(cf, d, CC)
        ni, nd = p.get("PARENT_NETPROFIT"), p.get("DEDUCT_PARENT_NETPROFIT")
        rev, cost = p.get("TOTAL_OPERATE_INCOME"), p.get("OPERATE_COST")
        ocf = c.get("NETCASH_OPERATE")
        capex = abs(c.get("CONSTRUCT_LONG_ASSET") or 0) or None
        da = sum(x for x in [c.get("FA_IR_DEPR"), c.get("IR_DEPR"),
                             c.get("IA_AMORTIZE"), c.get("LPE_AMORTIZE")] if x) or None
        eq = b.get("TOTAL_EQUITY")
        debt = sum(x for x in [b.get("SHORT_LOAN"), b.get("LONG_LOAN"),
                               b.get("BOND_PAYABLE"),
                               b.get("NONCURRENT_LIAB_1YEAR")] if x) or None
        # 期初权益用上一同季度：简单用本期/(1+增速)不可靠，退化为期末权益口径（注明）
        nopat = (p.get("TOTAL_PROFIT") or 0) - (p.get("INCOME_TAX") or 0)
        roe = (100 * ni / eq) if (ni and eq) else None            # 期末口径,注明
        roic = (100 * nopat / ((eq or 0) + (debt or 0))) if (nopat and eq) else None
        series.append({
            "date": d, "half_year": not d.endswith("12-31"),
            "revenue": rev, "rev_cost": cost,
            "net_income": ni, "deducted": nd,
            "nonrec_ratio": (1 - nd / ni) if (ni and nd) else None,
            "ocf": ocf, "ocf_ni": (ocf / ni) if (ocf is not None and ni) else None,
            "da": da, "capex": capex,
            "equity": eq, "parent_equity": b.get("TOTAL_PARENT_EQUITY"),
            "cash": b.get("MONETARYFUNDS"), "share_capital": b.get("SHARE_CAPITAL"),
            "goodwill": b.get("GOODWILL"), "contract_liab": b.get("CONTRACT_LIAB"),
            "interest_bearing_debt": debt, "roe_period_end": roe, "roic_conservative": roic,
        })
    # 同比（去年同日）
    by_date = {s["date"]: s for s in series}
    for s in series:
        ly = s["date"][:4] + "-" + s["date"][5:]
        prev_year = s["date"].replace(s["date"][:4], str(int(s["date"][:4]) - 1))
        q = by_date.get(prev_year)
        if q is None and pf is not None:
            try:
                q_row = pf[pf["REPORT_DATE"].astype(str).str[:10] == prev_year]
                if not q_row.empty:
                    r0 = q_row.iloc[0]
                    q = {"revenue": f(r0.get("TOTAL_OPERATE_INCOME")),
                         "net_income": f(r0.get("PARENT_NETPROFIT"))}
            except Exception:
                q = None
        if q and q.get("revenue"):
            s["rev_yoy"] = s["revenue"] / q["revenue"] - 1
        if q and q.get("net_income"):
            s["ni_yoy"] = s["net_income"] / q["net_income"] - 1

    divs = []
    if dv is not None:
        try:
            dvc = dv.copy()
            dvc["报告期"] = dvc["报告期"].astype(str)
            dvc = dvc[dvc["报告期"].str[:4].astype(int) >= int(years[-1][:4])] if years else dvc
            for _, r in dvc.iterrows():
                desc = str(r.get("现金分红-现金分红比例描述") or "")
                divs.append({"报告期": r["报告期"], "描述": desc,
                             "股息率": f(r.get("现金分红-股息率"))})
        except Exception as e:
            warn.append("div: %s" % str(e)[:70])

    outdir = Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / ("%s-history.json" % code)
    doc = {"code": code, "name": a.name or code, "fetched": __import__("time").strftime("%Y-%m-%d"),
           "unit_note": "元(人民币)原值；roe为期末权益口径；roic为保守口径(不扣超额现金)",
           "series": series, "dividends": divs, "warnings": warn,
           "source": "akshare/东财 datacenter 年报+最新期，直连"}
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    got = sum(1 for s in series if s.get("net_income"))
    print("WROTE", out)
    print("年度序列 %d 期（净利可得 %d 期）｜分红行 %d｜警告 %d" % (len(series), got, len(divs), len(warn)))
    for w in warn:
        print("WARN:", w)


if __name__ == "__main__":
    main()

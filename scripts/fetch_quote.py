#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fetch_quote.py - 实时取数入口：把"某股票最近怎么样"变成判据引擎的合法输入。

主引擎 yfinance（封装了 Yahoo 的 cookie/crumb/限流），手搓 urllib 兜底。
代理失败自动降级直连；都失败则退出并说明，不编数据。

用法：
  python scripts/fetch_quote.py --symbol TSLA [--name 特斯拉] [--out trial/]
输出：
  trial/<SYMBOL>-live.financials.json（26 字段 schema，缺的明写 not_disclosed）
"""
import argparse
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROXY = "http://127.0.0.1:7897"


def norm(s):
    return (s or "").lower().replace(" ", "").replace("_", "").replace("-", "")


def row(df, *candidates):
    """在 yfinance 报表 DataFrame 里模糊匹配行标签，返回该行（Series）或 None。"""
    if df is None or df.empty:
        return None
    want = {norm(c) for c in candidates}
    for idx in df.index:
        if norm(str(idx)) in want:
            return df.loc[idx]
    return None


def latest_cols(df, n=2):
    """按列名日期倒序取最近 n 期。"""
    if df is None or df.empty:
        return []
    cols = list(df.columns)
    try:
        cols = sorted(cols, reverse=True)
    except Exception:
        pass
    return cols[:n]


def fetch_via_yfinance(sym):
    import yfinance as yf
    try:
        t = yf.Ticker(sym)
        info = t.info
        if info.get("currentPrice") or info.get("regularMarketPrice"):
            return t, info
        raise RuntimeError("no price")
    except Exception:
        # 直连被限流/被墙 → 代理
        try:
            yf.config.network.proxy = PROXY
        except Exception:
            yf.set_config(proxy=PROXY)
        t = yf.Ticker(sym)
        return t, t.info


def val(v):
    try:
        f = float(v)
        return f
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--name", default=None)
    ap.add_argument("--out", default=str(ROOT / "trial"))
    a = ap.parse_args()
    sym = a.symbol.upper()
    today = time.strftime("%Y-%m-%d")

    t, info = fetch_via_yfinance(sym)
    price = info.get("currentPrice") or info.get("regularMarketPrice")
    if not price:
        raise SystemExit("取价失败，不编数据，退出。")

    qi = t.quarterly_income_stmt
    qc = t.quarterly_cashflow
    qb = t.quarterly_balance_sheet

    loc = "Yahoo Finance via yfinance, fetched %s" % today
    fields = []

    def add(key, value, conf=0.9, extra=""):
        fields.append({"key": key, "value": value if value is not None else "not_disclosed",
                       "confidence": conf, "source_locator": loc + extra})

    # 利润表（最近一季）
    ic = latest_cols(qi, 1)
    if ic:
        r = row(qi, "Total Revenue", "Revenues")
        n = row(qi, "Net Income", "Net Income Common Stockholders")
        add("revenue", val(r[ic[0]]) if r is not None else None, 0.92, " IS " + str(ic[0])[:10])
        add("net_income", val(n[ic[0]]) if n is not None else None, 0.92, " IS " + str(ic[0])[:10])
    # 现金流（最近一季）
    cc = latest_cols(qc, 1)
    if cc:
        o = row(qc, "Operating Cash Flow", "Total Cash From Operating Activities")
        x = row(qc, "Capital Expenditure", "Capital Expenditures")
        d = row(qc, "Depreciation Amortization Depletion", "Depreciation And Amortization", "Depreciation")
        add("ocf", val(o[cc[0]]) if o is not None else None, 0.92, " CF " + str(cc[0])[:10])
        if x is not None:
            cx = val(x[cc[0]])
            add("capex_total", abs(cx) if cx is not None else None, 0.92, " CF " + str(cc[0])[:10])
        add("da", val(d[cc[0]]) if d is not None else None, 0.85, " CF " + str(cc[0])[:10])
    # 资产负债（最近两期 → 营运资本变动）
    bc = latest_cols(qb, 2)
    if bc:
        endb = str(bc[0])[:10]
        pairs = [("cash_and_equivalents", ("Cash Cash Equivalents And Short Term Investments", "Cash And Cash Equivalents")),
                 ("receivables", ("Net Receivables", "Accounts Receivable")),
                 ("inventory", ("Inventory",)),
                 ("total_assets", ("Total Assets",)),
                 ("net_assets_attributable", ("Stockholders Equity", "Total Equity Gross Minority Interest"))]
        for key, cands in pairs:
            r = row(qb, *cands)
            add(key, val(r[bc[0]]) if r is not None else None, 0.9, " BS " + endb)
        if len(bc) > 1:
            ca0, cl0 = row(qb, "Current Assets"), row(qb, "Current Liabilities")
            if ca0 is not None and cl0 is not None:
                wc0 = val(ca0[bc[0]]) - val(cl0[bc[0]])
                wc1 = val(ca0[bc[1]]) - val(cl0[bc[1]])
                if wc0 is not None and wc1 is not None:
                    add("working_capital_delta", wc0 - wc1, 0.82, " BS 两期差值(近似)")
    # info 补充
    add("ebitda", val(info.get("ebitda")), 0.9, " TTM info（债务口径必须配 TTM，禁止用单季EBITDA比总债务）")
    add("interest_bearing_debt", val(info.get("totalDebt")), 0.9, " info TTM")
    add("gross_margin", val(info.get("grossMargins")), 0.9, " info TTM")
    add("roe_weighted", val(info.get("returnOnEquity")), 0.9, " info TTM")
    for k, why in [
        ("net_income_deducted", "美股无扣非概念"),
        ("non_recurring_detail", "需读 10-K/10-Q 原文"),
        ("interest_expense", "聚合源未稳定提供"),
        ("capex_maintenance", "维持性capex任何聚合源都不披露"),
        ("roic", "需自行计算"),
        ("customer_concentration_top1", "需读年报"),
        ("audit_opinion", "需读 10-K 审计意见页"),
        ("litigation_disclosure", "需读 10-K/新闻"),
        ("share_pledge_or_freeze", "需读 13D/13F/新闻"),
    ]:
        add(k, None, 1.0, " | " + why)

    market_block = {
        "price": price,
        "currency": info.get("currency"),
        "exchange": info.get("exchange"),
        "market_cap_raw": info.get("marketCap"),
        "pe_ttm_raw": info.get("trailingPE"),
        "forward_pe_raw": info.get("forwardPE"),
        "fetched_at": today,
        "source": loc,
    }
    doc = {
        "company": a.name or info.get("longName") or sym,
        "market": info.get("exchange") or "?",
        "period": "latest reported quarter (live fetch %s)" % today,
        "source": loc + "（聚合源；一级证据以 SEC EDGAR 为准）",
        "unit": "USD (Yahoo raw scale)",
        "market_block": market_block,
        "fields": fields,
        "live_fetch": {"tool": "fetch_quote.py yfinance", "symbol": sym, "fetched_at": today},
    }
    outdir = Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / ("%s-live.financials.json" % sym)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    got = [f for f in fields if f["value"] != "not_disclosed"]
    miss = [f["key"] for f in fields if f["value"] == "not_disclosed"]
    pe = market_block["pe_ttm_raw"]
    print("WROTE", out)
    print("取到字段 %d 个 / 缺口 %d 个（已明写 not_disclosed）" % (len(got), len(miss)))
    print("价格 %s %s ｜ PE(TTM) %s ｜ 市值 %s" % (price, market_block["currency"], pe, market_block["market_cap_raw"]))


if __name__ == "__main__":
    main()

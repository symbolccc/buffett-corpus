#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fetch_ashare.py - A 股实时取数入口（akshare 免费源，无 key）。

数据源：东方财富 datacenter 三大报表（报告期）+ 东财估值接口（PE-TTM/市值/收盘价）。
注意：必须直连国内源——脚本内部已强制 NO_PROXY，避免被系统代理截胡。
输出：trial/<code>-live.financials.json（26 字段 schema，缺的明写 not_disclosed）

用法：
  python scripts/fetch_ashare.py --code 600519 --name 贵州茅台 --out trial/
"""
import argparse
import json
import os
import re
import socket
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def num(v):
    try:
        f = float(v)
        return None if f != f else f  # NaN 防污染：任何一个 NaN 都不能混进合计
    except (TypeError, ValueError):
        return None


def pick_col(df, *patterns):
    """按正则在列名里找第一个匹配。"""
    for p in patterns:
        for c in df.columns:
            if re.search(p, str(c), re.I):
                return c
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--code", required=True, help="6 位 A 股代码，如 600519")
    ap.add_argument("--name", default=None)
    ap.add_argument("--out", default=str(ROOT / "trial"))
    a = ap.parse_args()
    code = re.sub(r"\D", "", a.code)
    if len(code) != 6:
        raise SystemExit("A 股代码应为 6 位数字")
    prefix = "SH" if code[0] == "6" else "SZ"
    today = time.strftime("%Y-%m-%d")

    # 国内源必须直连：压掉系统代理
    os.environ["NO_PROXY"] = "*"
    os.environ.pop("HTTP_PROXY", None)
    os.environ.pop("HTTPS_PROXY", None)
    socket.setdefaulttimeout(40)  # 全局保险：任何取数调用最多挂 40 秒，防单接口卡死整个流程
    import akshare as ak

    loc = "akshare/东方财富 datacenter 报告期三表, fetched %s" % today
    pf = ak.stock_profit_sheet_by_report_em(symbol=prefix + code)
    cf = ak.stock_cash_flow_sheet_by_report_em(symbol=prefix + code)
    balance_source = "EM"
    try:
        bl = ak.stock_balance_sheet_by_report_em(symbol=prefix + code)
    except Exception:
        bl = None
    if bl is None or bl.empty:
        # EM 卡死/失败 → 新浪备用（列名为中文，7 秒左右返回）
        bl = ak.stock_financial_report_sina(stock=(prefix + code).lower(), symbol="资产负债表")
        balance_source = "sina"
    val = ak.stock_value_em(symbol=code)
    if pf.empty or bl.empty:
        raise SystemExit("报表取数失败，不编数据，退出。")

    p0, p1 = pf.iloc[0], pf.iloc[1] if len(pf) > 1 else None
    c0, c1 = cf.iloc[0], cf.iloc[1] if len(cf) > 1 else None
    b0, b1 = bl.iloc[0], bl.iloc[1] if len(bl) > 1 else None
    report_date = str(p0.get("REPORT_DATE", ""))[:10]

    fields = []

    def add(key, value, conf=0.92, extra=""):
        fields.append({"key": key, "value": value if value is not None else "not_disclosed",
                       "confidence": conf, "source_locator": loc + extra})

    # 利润表
    rev = num(p0.get("TOTAL_OPERATE_INCOME"))
    ni = num(p0.get("PARENT_NETPROFIT"))
    cost = num(p0.get("OPERATE_COST"))
    add("revenue", rev, 0.93, " 利润表 " + report_date)
    add("net_income", ni, 0.93, " 利润表 " + report_date)
    add("net_income_deducted", num(p0.get("DEDUCT_PARENT_NETPROFIT")), 0.93, " 利润表 " + report_date + "（A 股原生扣非口径）")
    op = num(p0.get("OPERATE_PROFIT"))
    # 现金流量表
    ocf = num(c0.get("NETCASH_OPERATE")) if c0 is not None else None
    add("ocf", ocf, 0.93, " 现金流量表 " + report_date)
    cap_col = pick_col(cf, "CONSTRUCT_LONG_ASSET", "BUILD_FIXED")
    add("capex_total", abs(num(c0.get(cap_col))) if (c0 is not None and cap_col) else None, 0.9, " 购建长期资产现金")
    # 东财现金流量表折旧摊销为多列拆分；_YOY 列是百分比不是金额（曾误取致 da=8.39），
    # OILGAS_BIOLOGY_DEPR 与 FA_IR_DEPR 同值（数据源重复列）不计，只取四项金额列求和
    da = None
    if c0 is not None:
        parts = [num(c0.get(x)) for x in
                 ("FA_IR_DEPR", "IR_DEPR", "IA_AMORTIZE", "LPE_AMORTIZE")]
        got = [p for p in parts if p]
        da = sum(got) if got else None
    add("da", da, 0.9, " 折旧摊销=FA_IR_DEPR+IR_DEPR+IA_AMORTIZE+LPE_AMORTIZE(排除YOY%列与重复列)")
    # 资产负债表
    BAL = {
        "cash": ("MONETARYFUNDS", "货币资金"),
        "receivables": ("ACCOUNTS_RECE", "应收账款"),
        "inventory": ("INVENTORIES", "存货"),
        "total_assets": ("TOTAL_ASSETS", "资产总计"),
        "equity": ("TOTAL_PARENT_EQUITY", "归属于母公司股东权益合计", "所有者权益(或股东权益)合计"),
        "current_assets": ("TOTAL_CURRENT_ASSETS", "流动资产合计"),
        "current_liab": ("TOTAL_CURRENT_LIABILITIES", "流动负债合计"),
    }
    DEBT_PARTS = (("SHORT_LOAN", "短期借款"), ("LONG_LOAN", "长期借款"),
                  ("BOND_PAYABLE", "应付债券"), ("NONCURRENT_LIAB_1YEAR", "一年内到期的非流动负债"))

    def g(d, *names):
        for n in names:
            if d.get(n) is not None:
                return num(d.get(n))
        return None

    if b0 is not None:
        def bg(key, d):
            return g(d, *BAL[key])

        src_note = " 资产负债表(%s) " % balance_source + report_date
        add("cash_and_equivalents", bg("cash", b0), 0.92, src_note)
        add("receivables", bg("receivables", b0), 0.92, src_note)
        add("inventory", bg("inventory", b0), 0.92, src_note)
        add("total_assets", bg("total_assets", b0), 0.92, src_note)
        equity = bg("equity", b0)
        add("net_assets_attributable", equity, 0.92, src_note)
        debt = sum(x for x in [g(b0, *part) for part in DEBT_PARTS] if x)
        add("interest_bearing_debt", debt or None, 0.9, " 短借+长借+应付债券+一年内到期")
        if b1 is not None:
            wc = lambda d: (bg("current_assets", d) or 0) - (bg("current_liab", d) or 0)
            add("working_capital_delta", wc(b0) - wc(b1), 0.85, " 两期报告差值(近似)")
            eq1 = bg("equity", b1)
            if equity and eq1 and ni is not None:
                add("roe_weighted", ni / ((equity + eq1) / 2), 0.82, " 期初期末平均净资产近似(单期净利口径)")
    # 计算类
    if rev and cost:
        add("gross_margin", (rev - cost) / rev, 0.9, " (营收-营业成本)/营收 " + report_date)
    if op and da:
        add("ebitda", op + da, 0.82, " 营业利润+折旧摊销(近似)")
    fin_exp = num(p0.get("FINANCE_EXPENSE"))
    add("interest_expense", fin_exp, 0.8, " 财务费用口径近似" if fin_exp is not None else None)
    # 聚合源不提供的，明写
    for k, why in [
        ("non_recurring_detail", "需读年报附注"),
        ("capex_maintenance", "维持性capex任何聚合源都不披露"),
        ("roic", "需自行计算"),
        ("customer_concentration_top1", "需读年报前五大客户"),
        ("audit_opinion", "需读年报审计页"),
        ("litigation_disclosure", "需读公告/新闻"),
        ("share_pledge_or_freeze", "需读股权质押公告"),
    ]:
        add(k, None, 1.0, " | " + why)

    v = val.iloc[-1] if not val.empty else {}
    market_block = {
        "price": num(v.get("当日收盘价")),
        "as_of": str(v.get("数据日期", today)),
        "currency": "CNY",
        "market_cap_raw": num(v.get("总市值")),
        "pe_ttm_raw": num(v.get("PE(TTM)")),
        "pb_raw": num(v.get("市净率")),
        "fetched_at": today,
        "source": "akshare/东财估值 stock_value_em",
    }
    doc = {
        "company": a.name or code,
        "market": "A股 " + prefix + code,
        "period": "报告期 " + report_date + "（live fetch %s）" % today,
        "source": loc + "（聚合源；正式决策以交易所公告原文为准）",
        "unit": "CNY",
        "market_block": market_block,
        "fields": fields,
        "live_fetch": {"tool": "fetch_ashare.py akshare", "symbol": prefix + code, "fetched_at": today},
    }
    outdir = Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / ("%s-live.financials.json" % code)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    got = [f for f in fields if f["value"] != "not_disclosed"]
    print("WROTE", out)
    print("取到字段 %d 个 / 缺口 %d 个（已明写 not_disclosed）" % (len(got), len(fields) - len(got)))
    print("收盘 %s ｜ PE(TTM) %s ｜ 总市值 %s" % (market_block["price"], market_block["pe_ttm_raw"], market_block["market_cap_raw"]))


if __name__ == "__main__":
    sys.exit(main() or 0)

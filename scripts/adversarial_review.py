#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""adversarial_review.py - 对抗评审循环：吃 verdict.json，吐结构化红队质询。

原理：判据引擎输出的是"支持买入/观察的证据组织"，对抗层强制寻找反面证据，
防止确认偏误。借鉴 mimeo 的阶段化 + 自己的反例库交叉引用。

用法：
  python scripts/adversarial_review.py --verdict trial/verdicts/xxx.verdict.json
输出：
  adversarial/REVIEW-<case>-<时间戳>.md 和 .json

协议（adversarial/protocol.md）：判决 → 红队质询 → 分析者逐条回答 →
重跑引擎 → 只有回答完所有 MANDATORY 项才能出最终结论。
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 每条判据的定制质询模板（找什么反面证据）
CHALLENGES = {
    "C-circle-competence": "写一段'这不是能力圈'的最强论证：用最外行的话解释这门生意，检查哪一句说不下去。",
    "C-earnings-quality": "OCF/NI 偏高是否来自营运资本一次性释放或折旧政策异常？调出前两个完整周期年份对比数据。",
    "C-owner-earnings": "维持性 capex 是否估低了？行业再投资强度上四分位是多少？用同行的重置成本核一遍。",
    "C-debt-survival": "净现金里有没有受限资金/质押？最低运营现金需求是多少？极端月现金流下能撑几个月？",
    "C-inversion": "列出 kill 条件：每条给出证伪指标、监测频率、触发后动作。没有 kill 条件 = 没想清楚。",
    "C-durability": "找出最可能让需求消失的一个技术或行为变化，给发生概率区间（不是'不可能'）。",
    "C-moat-replicability": "复制者需要多少钱、多少年、什么准入条件？找一个最接近的成功复制案例。",
    "C-moat-trend": "价格周期还是结构性改善？调出上一个完整周期的毛利率/市占率对比，两条线必须分开画。",
    "C-pricing-power": "上次提价是什么时候？流失了多少客户/份额？涨价幅度与通胀累积幅度比是多少？",
    "C-mgmt-integrity": "四项必查：关联交易、股东减持、股权质押、审计意见。逐项给证据原文。",
    "C-alignment": "管理层过去三年的资本配置决策清单：回购/分红/收购/薪酬，逐项和股东利益对表。",
    "C-time-horizon": "写 10 年终局：这家公司 10 年后最可能的样子和最不可能的样子。写不出 10 年 = 降低仓位等级。",
}
DEFAULT_CHALLENGE = "给出两个最可能推翻本判据结论的反面数据点；给不出来就是搜索不足，不是结论可靠。"

CONFIRMATION_BIAS = [
    "强制换边：如果被迫写做空报告，你最强的三个论点是什么？（写出来，不许空）",
    "扰动测试：把关键输入（利润率/增长率/折现率）各调 ±20%，结论翻转吗？翻转点在哪里？",
    "历史对照：本案例与反例库（counter-examples.json）里哪个已验证失败案例最像？逐条对比信号。",
]


def load(p):
    with open(p, encoding="utf-8-sig") as f:
        return json.load(f)


def cross_refs(crid):
    """从反例库找与该判据相关的历史失败案例。"""
    ce = load(ROOT / "criteria" / "counter-examples" / "counter-examples.json")
    hits = []
    for c in ce["counter_examples"]:
        links = c.get("links") or []
        if any(crid in l or l in crid for l in links):
            hits.append("%s（%s，status=%s）" % (c["id"], c["case"], c["status"]))
    return hits


def review(verdict_path):
    v = load(verdict_path)
    case = v.get("cases") or v.get("case") or Path(verdict_path).stem
    crit = v.get("criteria", {})
    lines = ["# 对抗评审 · %s" % case, "",
             "- 判决源：%s" % verdict_path,
             "- 引擎结论：%s" % v.get("overall"), "",
             "> 规则：MANDATORY 项未逐条回答前，禁止把引擎结论当最终结论。",
             "> 引擎只组织支持证据；反面证据由本层强制搜索。", ""]
    js = {"case": case, "verdict_overall": v.get("overall"), "generated": time.strftime("%Y-%m-%d %H:%M"),
          "mandatory": [], "advisory": []}
    n_m = n_a = 0
    for crid, c in crit.items():
        status = c.get("auto_status") or c.get("status")
        lines.append("## %s（引擎判定：%s）" % (crid, status))
        q = CHALLENGES.get(crid, DEFAULT_CHALLENGE)
        lines.append("- 质询：%s" % q)
        mandatory = status in ("pass", "flag") or c.get("decision_weight") == "veto"
        lines.append("- 强制级别：%s" % ("MANDATORY" if mandatory else "ADVISORY"))
        refs = cross_refs(crid)
        if refs:
            lines.append("- 历史失败对照：%s" % "；".join(refs))
        lines.append("- 回答：（待分析者填写）")
        lines.append("")
        item = {"criterion": crid, "challenge": q, "status": status, "cross_refs": refs}
        (js["mandatory"] if mandatory else js["advisory"]).append(item)
        n_m += mandatory
        n_a += (not mandatory)
    lines += ["## 确认偏误三问（全部 MANDATORY）", ""]
    for i, q in enumerate(CONFIRMATION_BIAS, 1):
        lines.append("%d. %s" % (i, q))
        js["mandatory"].append({"criterion": "confirmation-bias-%d" % i, "challenge": q})
        n_m += 1
    lines += ["", "## 通过标准", "",
              "- 所有 MANDATORY 项有具体回答（不接受'已考虑'）",
              "- 至少一个 MANDATORY 项的回答改变了引擎结论的表述（否则说明红队没用力）",
              "- 三问中第 2 问必须给出具体翻转点数字", ""]
    js["counts"] = {"mandatory": n_m, "advisory": n_a}
    return "\n".join(lines), js


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verdict", required=True)
    ap.add_argument("--out", default=None, help="输出目录，默认 adversarial/")
    a = ap.parse_args()
    md, js = review(a.verdict)
    outdir = Path(a.out) if a.out else ROOT / "adversarial"
    outdir.mkdir(parents=True, exist_ok=True)
    case = re.sub(r"[^\w\-]", "", js["case"])[:40] or "case"
    ts = time.strftime("%Y%m%d-%H%M%S")
    mdp = outdir / ("REVIEW-%s-%s.md" % (case, ts))
    jsp = outdir / ("REVIEW-%s-%s.json" % (case, ts))
    mdp.write_text(md, encoding="utf-8")
    jsp.write_text(json.dumps(js, ensure_ascii=False, indent=1), encoding="utf-8")
    print("WROTE", mdp)
    print("WROTE", jsp)
    print("MANDATORY 项:", js["counts"]["mandatory"], "| ADVISORY 项:", js["counts"]["advisory"])
    if js["counts"]["mandatory"] == 0:
        print("警告：无质询项，检查判决文件结构")
        sys.exit(2)


if __name__ == "__main__":
    main()

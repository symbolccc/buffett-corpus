#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""free_search.py - 零密钥搜索插件：问股票时的免费新闻/网页情报源。

三个免费源（全部无需 API key）：
  1. Yahoo Finance RSS   按代码拉个股新闻   feeds.finance.yahoo.com
  2. Google News RSS     按关键词拉全网新闻  news.google.com/rss/search
  3. DuckDuckGo (ddgs)   通用网页/新闻搜索   pip install ddgs

与 deepseek_search.py 的关系：本插件是默认（免费），DeepSeek 是可选付费升级。
网络不通就明说，不编造结果。

用法：
  python scripts/free_search.py --ticker TSLA [--limit 6]      # 个股新闻三源聚合
  python scripts/free_search.py --query "特斯拉 财报" [--limit 6]
"""
import argparse
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET

PROXY = "http://127.0.0.1:7897"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def get(url, timeout=20):
    """直连失败自动走代理。返回文本或 None（不抛异常）。"""
    for opener in (
        urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})),
        urllib.request.build_opener(urllib.request.ProxyHandler({})),
    ):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            return opener.open(req, timeout=timeout).read().decode("utf-8", "replace")
        except Exception:
            continue
    return None


def rss_items(xml_text, limit):
    """解析 RSS -> [(title, link, date)]，容忍不规整 feed。"""
    out = []
    if not xml_text:
        return out
    try:
        root = ET.fromstring(re.sub(r'&(?!(amp|lt|gt|quot|apos|#\d+);)', '&amp;', xml_text))
        for it in root.iter("item"):
            t = (it.findtext("title") or "").strip()
            l = (it.findtext("link") or "").strip()
            d = (it.findtext("pubDate") or "").strip()
            if t:
                out.append((t, l, d))
            if len(out) >= limit:
                break
    except ET.ParseError:
        pass
    return out


def ddg(query, limit, kind="news"):
    try:
        from ddgs import DDGS
    except ImportError:
        return []
    try:
        fn = DDGS().news if kind == "news" else DDGS().text
        rows = fn(query, max_results=limit) or []
        return [(r.get("title", ""), r.get("url") or r.get("href", ""),
                 str(r.get("date", ""))[:19]) for r in rows]
    except Exception:
        return []


def dedupe(items, limit):
    seen, out = set(), []
    for t, l, d in items:
        key = re.sub(r"\W", "", t.lower())[:40]
        if key and key not in seen:
            seen.add(key)
            out.append((t, l, d))
        if len(out) >= limit:
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", help="股票代码，如 TSLA（走财经新闻源）")
    ap.add_argument("--query", help="自由关键词（走通用新闻+网页）")
    ap.add_argument("--limit", type=int, default=6)
    a = ap.parse_args()
    if not a.ticker and not a.query:
        ap.error("--ticker 与 --query 至少给一个")

    tag = time.strftime("%Y-%m-%d %H:%M")
    pools, sources_ok = [], []

    if a.ticker:
        sym = a.ticker.upper()
        y = rss_items(get("https://feeds.finance.yahoo.com/rss/2.0/headline?s=%s&region=US&lang=en-US" % sym), a.limit)
        if y:
            sources_ok.append("Yahoo财经RSS")
            pools.append([("Y] " + t, l, d) for t, l, d in y])
        g = rss_items(get("https://news.google.com/rss/search?q=%s&hl=zh-CN&gl=CN&ceid=CN:zh-Hans" % sym), a.limit)
        if g:
            sources_ok.append("Google新闻RSS")
            pools.append([("G] " + t, l, d) for t, l, d in g])
        d = ddg("%s stock news" % sym, a.limit, "news")
        if d:
            sources_ok.append("DuckDuckGo")
            pools.append([("D] " + t, l, d) for t, l, d in d])
    if a.query:
        g = rss_items(get("https://news.google.com/rss/search?q=%s&hl=zh-CN&gl=CN&ceid=CN:zh-Hans" % urllib.parse.quote(a.query)), a.limit)
        if g:
            sources_ok.append("Google新闻RSS")
            pools.append([("G] " + t, l, d) for t, l, d in g])
        d = ddg(a.query, a.limit, "news")
        if d:
            sources_ok.append("DuckDuckGo")
            pools.append([("D] " + t, l, d) for t, l, d in d])

    # 三源轮插：保证来源多样性，不让单源霸榜
    collected = []
    for round_idx in range(a.limit):
        for pool in pools:
            if round_idx < len(pool):
                collected.append(pool[round_idx])

    items = dedupe(collected, a.limit)
    print("免费搜索 · %s ｜ 通达源：%s" % (tag, "、".join(sources_ok) if sources_ok else "无（网络不通，宁缺勿编）"))
    if not items:
        print("（无结果——本次分析不得引用任何'新闻面'）")
        return 1
    for i, (t, l, d) in enumerate(items, 1):
        print("%d. %s（%s）" % (i, t, d))
        if l:
            print("   %s" % l)
    return 0


if __name__ == "__main__":
    import urllib.parse
    sys.exit(main() or 0)

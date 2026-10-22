#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""deepseek_search.py - 网页搜索插件（DeepSeek Search API，2026-10-17 上线）。

用户问"某股票最近怎么样"时的第 2 数据源：新闻/公告/行业动态。
API: POST https://api.deepseek.com/v1/tools/search（Bearer 鉴权）
计费: 5 元/1000 次成功请求（2026-11-01 前免费期）
密钥: 只从环境变量 DEEPSEEK_API_KEY 读取，严禁写进任何文件或仓库。

用法：
  set DEEPSEEK_API_KEY=sk-xxx（或 $env:DEEPSEEK_API_KEY='sk-xxx'）
  python scripts/deepseek_search.py --query "特斯拉 最近 财报" [--count 5] [--content]
没有密钥时退出并提示，不做任何降级编造。
"""
import argparse
import json
import os
import sys
import urllib.request

API = "https://api.deepseek.com/v1/tools/search"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--count", type=int, default=5)
    ap.add_argument("--content", action="store_true", help="返回网页正文（更贵更慢，默认只返回标题+摘要）")
    a = ap.parse_args()
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        print("缺 DEEPSEEK_API_KEY 环境变量——该插件需要 DeepSeek 密钥，未配置就不搜索，不编造。", file=sys.stderr)
        sys.exit(2)
    body = {"query": a.query[:128], "count": max(1, min(a.count, 50)), "need_content": bool(a.content)}
    req = urllib.request.Request(
        API,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key, "User-Agent": "buffett-corpus/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print("搜索失败: %s（不编造结果）" % str(e)[:160], file=sys.stderr)
        sys.exit(3)
    results = data.get("results") or []
    for i, it in enumerate(results, 1):
        print("%d. %s" % (i, it.get("title", "")))
        print("   %s" % it.get("url", ""))
        s = it.get("summary") or it.get("content") or ""
        if s:
            print("   %s" % s[:220].replace("\n", " "))
    if not results:
        print("无结果。")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)

# 夜间工作报告 · 2026-10-21 凌晨

> 你的指令：把"问股票→实时数据→巴菲特研判"干通，优先用现成轮子，干到早上。
> 本文就是早检材料。所有结论带文件路径，可逐条复核。

## 一句话状态

**主流程已跑通**：`fetch_quote.py`（实时取数）→ `run-criteria.py`（判据引擎）→
`adversarial_review.py`（对抗评审），三只美股实跑成功；DeepSeek 搜索插件写好等你的 key。

## 三只票实跑结果（2026-10-21 实时数据）

| 标的 | 实时价 | PE(TTM) | 市值 | 引擎判决 | 关键信号 |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 特斯拉 TSLA | $373.85 | 346 | $1.48T | 需人工核验 | 净现金 +$274亿；盈利质量 OCF/NI=4.2 触发复查；10年趋势数据不足自动 uncertain |
| 可口可乐 KO | $92.81 | 27.9 | $399B | **建议打回** | 债务/EBITDA=2.6 超编辑者阈值；净现金 -$279亿；利息保障因缺披露跳过（已标注） |
| 英伟达 NVDA | $217.14 | 27.4 | $5.24T | 需人工核验 | 现金转化率 0.40 触发警报 + 应收/净资产 0.275——利润没变成现金，巴菲特最在意的事 |

文件：
- trial/TSLA-live.financials.json + verdicts/TSLA-live.verdict.json + notes（AI 草稿，标了"需本人复核"）
- trial/KO-live.*、trial/NVDA-live.* 同上
- adversarial/REVIEW-TeslaInc-*.md（5 项强制质询）

对照实验说明：KO 被打回**不是引擎错**，是阈值 2.5 为编辑者设定（skill 规定必须声明"非巴菲特原话"）。
对抗层的作用就是让人质疑这类判定——这正是"引擎给证据、人做决定"的设计。

## 你说得对的部分（认错记录）

1. **不该手搓轮子**：Yahoo 的 cookie/crumb 流程 yfinance（v1.7.0，25k+ stars）早封装完了。
   我重写了 fetch_quote.py，yfinance 为主引擎，原手搓逻辑已删除。
2. **DeepSeek 搜索可以直接接**：2026-10-17 上线 Search/Fetch API（POST api.deepseek.com/v1/tools/search，
   Bearer 鉴权，5元/1000次，2026-11-01 前免费）。已写 `scripts/deepseek_search.py`：
   key 只从环境变量 DEEPSEEK_API_KEY 读取（安全规则：密钥不进任何文件/仓库）。
3. **没人问"巴菲特的事"**：SKILL.md 已把"问股票"立为最高频主流程（六步工作流），
   时代分期降为辅助守卫。分期做减法（E1 学徒期降级）等你拍板，没动。

## 夜里修掉的 bug（都有据）

| bug | 现象 | 修复 |
| :-- | :-- | :-- |
| jget 不认列表下标 | result[0] 断链 → 取价失败 | dict/list 双类型处理 |
| 缺 cookie 预热 | quoteSummary 401 Invalid Crumb | 先访问 fc.yahoo.com 种 cookie 再取 crumb |
| **EBITDA 口径错配** | TSLA 债务/EBITDA=5.3 误触发 FAIL | 单季 EBITDA 比总债务是错的；改 TTM 对 TTM → 1.5 恢复正常 |
| notes 格式错 | 引擎要求 JSON 数组带 criterion 键 | 改为数组格式，模板已留档 |
| 现金口径 | 现金等价物漏掉短投（TSLA 持有巨额 T-bills） | 优先取"现金+短投"合并行 |

## 调研：现成方案清单（按你"不自己造"的指令）

| 方案 | 状态 | 结论 |
| :-- | :-- | :-- |
| yfinance | **已接入** | 主取数引擎，免费无需 key |
| DeepSeek Search/Fetch API | 插件已写，**等你的 key** | 官方文档 api-docs.deepseek.com/zh-cn/api/search/；11-01 起收费 |
| yahoo-finance-mcp（GitHub 多个） | 未接入 | 适合以后挂到 Claude Desktop/Claude Code，备注在案 |
| akshare（A股数据） | **未接入** | 下一步候选：A 股字段映射（扣非/质押/审计意见都是现成的） |
| OpenBB / financial-datasets-mcp | 未采用 | 前者太重，后者要 API key |

## 已知问题与改进清单（诚实申报）

1. **判决文件不带市价/PE**：market_block 在 financials 文件里，verdict 里没有——
   下一步把估值上下文（价格/PE/市值）注入判决头部
2. **估值判据（C-valuation-margin）未参与**：26 字段 schema 里没有价格字段，
   PE 346 的特斯拉在判决里看不到"太贵"的定量表达——需给 schema 加 market 价格字段
3. **notes 是 AI 草稿**：TSLA/KO/NVDA 的 gate 判定都标了"需本人复核"，你确认后才算数
4. **A 股未通**：你说过的 A 股数据（东方财富/akshare）还没接
5. **直连 Yahoo 被限流**：走代理正常；代理挂了脚本会自动降级，但降级也可能失败
6. **GitHub 推送**：仍积压（3 个旧提交 + 这两轮全部改动），等你说推
7. 直连被墙页问题：Yahoo 国内 IP 返回拦截页，已用代理解决，无残留

## 早上验收命令（复制即用）

    # 1. 看特斯拉完整判决
    code "03_投资与命理\buffett-corpus\trial\verdicts\TSLA-live.verdict.json"（位于本机 OneDrive 桌面）
    # 2. 自己取一只票跑全流程
    cd 03_投资与命理\buffett-corpus（位于本机 OneDrive 桌面）
    python scripts\fetch_quote.py --symbol AAPL --name Apple
    # 3. 配好 DeepSeek key 后试搜索
    $env:DEEPSEEK_API_KEY='你的key'; python scripts\deepseek_search.py --query "特斯拉 最新新闻"

## 体检状态

- 判据引擎三连跑：TSLA/KO/NVDA 全部正常退出，输出合法 JSON
- 对抗评审：TSLA 生成 5 项 MANDATORY 质询
- 数据诚实性：每只票 9 个字段明写 not_disclosed，零编造
- person-forge 四模式体检：上一轮全 PASS；本轮新增文件未破坏结构（json 均合法）

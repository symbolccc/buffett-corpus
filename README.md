# buffett-corpus

机器可读的巴菲特全集元数据与判据仓库。索引与判据公开，受版权全文只存本地 `corpus/`（已 gitignore）。

## 30 秒看效果（三星电子 2026Q2 实跑）

把三星财务数据喂给确定性判据引擎（`scripts/run-criteria.py`），产出
[trial/verdicts/samsung-2Q26.verdict.json](trial/verdicts/samsung-2Q26.verdict.json)：

| 判据 | 结论 | 引擎自动证据 |
| :-- | :-- | :-- |
| C-circle-competence（gate） | pass | DS 占收入 74%，生意可一段话解释 |
| C-earnings-quality | pass | OCF/NI = 1.47，非经常损益占比 6.8% |
| C-owner-earnings | pass | 股东盈余 = 净利+折旧−资本开支−营运资本增加 = 43.8 |
| C-debt-survival | pass | 债务/EBITDA = 0.22，净现金充裕 |
| **C-moat-trend** | uncertain | **周期混淆守卫触发**：毛利率 6.3%→52.2% 属价格周期，非护城河变宽 |
| C-moat-replicability | flag | HBM4 领先真实，但对手以同等量级 capex 跟进：能复制、代价极高 |

整体结论：`需人工核验`（分析者注记外的判据自动标 uncertain，不替人拍板）。
**同样输入必得同样输出；数据缺披露就明说缺，绝不编造。**

每条判据带出处与成熟度，例：

> C-wonderful-at-fair · `buffett_verbatim` · maturity=validated
> "It's far better to buy a wonderful company at a fair price than a fair company
> at a wonderful price." — letter:1989（48 封信逐字核验 EXACT 1.0）

装上即用：把本仓库挂到任意支持 [Agent Skills](https://agentskills.io/) 的客户端
（根目录 `SKILL.md` 已按标准写好）。

## 结构总览（六层 + 两个跨切层）

| 层 | 位置 | 一句话 |
| :-- | :-- | :-- |
| 判据层 | `criteria/criteria.json` | 20 条判据，provenance/权重/成熟度三标注 |
| 时代层 | `corpus-index/eras.json` | 分四期，Abel 期（2026-02+）禁用巴菲特判据解读 |
| 归属层 | `criteria/attribution.json` | 每个概念标发明人（安全边际=Graham 等） |
| 反例层 | `criteria/counter-examples/` | 认错原话逐字核验，6 验 + 1 待 |
| 画像层 | `persona/buffett.persona.json` | 身份/世界观/决策/语言/演变/边界六层 |
| 对抗层 | `adversarial/` + `scripts/adversarial_review.py` | 判决强制过红队质询才生效 |

通用内核见 `../person-forge/spec/SPEC.md`（炼化任何其他人物的六层契约）。

## 版权边界（硬约束）
- 官网信件全文（1977–2024）：**不入库**。只存元数据 + 官方直链；`scripts/fetch-official.ps1` 拉全文到本地 `corpus/`
- SEC 10-K / 13F / SC 13D/13G / Form 4：**可入库**（法定披露）
- 自写笔记、判据、阈值、摘要：**可入库**（原创）
- 短引用（单条 ≤50 词）+ 出处：可入库（合理引用），必须标来源与年份
- 年会文字稿、书籍章节、报纸专栏全文、视频：**绝对不放**，只放链接
- LICENSE（MIT）**只覆盖本仓库原创代码与文档，不覆盖任何语料**
- 有些历史文件没有权威 URL：**不要编一个**（source_refs 留空 + status=missing）

## provenance 硬规则（scripts/validate.py 强制）
1. `decision_weight == veto` 的条目，`provenance` 必须为 `buffett_verbatim`
2. `provenance == buffett_verbatim` 的条目，`source_refs` 必须非空
3. `decision_weight == gate` 的条目，`provenance` 必须为 `buffett_verbatim` 或 `buffett_implied`，且必须有 `gate_rule` 与 `fallback`

provenance 枚举：buffett_verbatim | buffett_implied | skill_author | industry_convention | practice_derived
decision_weight 枚举：gate | veto | core | signal_only | context

## 主战场
美股为主（大部分用例）；A股/港股为少数用例，层0 输入解析为半人工（见 ingest/schema）。

## 目录
- criteria/criteria.json      判据（20 条）
- criteria/thresholds.json    数字阈值（9 条，全部标 provenance）
- criteria/counter-examples/  他判错的 / 赢了但不可复制的案例
- ingest/schema/              跨市场统一财务字段
- scripts/validate.py         provenance 硬校验
- scripts/fetch-edgar.ps1     EDGAR 索引拉取（已实测）
- track-record/               持仓与举牌索引（fetch 产物）
- corpus/                     .gitignore，受版权全文只存本地

## 已知缺口（不假装完整）
- EDGAR submissions recent 窗口只回溯到 2017-02-09（实测）
- 官网无 1965–1976 信件；1971 年信任何已知公开档案都没有
- A股/港股无 EDGAR 等价物，层0 输入解析为半人工

## 通用化与工具
- person-agent-template/  通用"炼化人"模板：换一个人照五步填数据，即得专属 Agent（SKILL.md 可直接挂载）
- TOOLS.md  仓库体检与导出工具链：repomix 打包、gitingest 速览、lychee 死链检查、CI 激活步骤

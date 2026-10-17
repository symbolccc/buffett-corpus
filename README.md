# buffett-corpus

机器可读的巴菲特全集元数据与判据仓库。索引与判据公开，受版权全文只存本地 `corpus/`（已 gitignore）。

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
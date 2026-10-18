# person-agent-template · 通用"炼化人"模板

把任意博主、企业家、作者的全部公开资料，炼成一个可对话、可溯源的专属 Agent。
本模板从 buffett-corpus（巴菲特版）抽出方法论骨架——换一个人，只需换数据，不换结构。

## 产物形态

```text
<person>-corpus/
├── corpus-index/          # ① 索引层：sources/works/speeches/interviews 元数据+官方直链
├── person/
│   └── profile.json       #     人格档案：含语言指纹、稳定模式、矛盾与修订日志（字段按 schema/person.schema.json）
├── criteria/              # ② 判据层：TA 的判断框架（每条带 provenance）
├── track-record/          # ③ 言行对照层：TA 说的 vs TA 做的
├── SKILL.md               # ④ Agent 定义：任何支持技能的 AI 直接挂载
└── SOURCES.md             # ⑤ 数据处置三级规则（照抄改人名）
```

## 五步流程

1. **采集 + 三级处置**：🟢 官方发布可全文入库；🟡 有版权只存链接+≤50 词短引；🔴 第三方转录只作本地检索语料，引用前必须回官方源逐字核对。
2. **建索引**：每条素材 = 元数据 + 官方直链 + 验证日期。不编 URL，验证不过不入库。
3. **炼判据**：从语料提炼 TA 的判断框架，每条标 provenance（person_verbatim / person_implied / editor_analyst / practice_derived），不得把编辑者的总结说成 TA 的原话。
4. **登记反例与矛盾**：TA 判断错的、自相矛盾的单独建档；矛盾并列呈现，禁止抹平。
5. **生成 Agent**：复制本目录 SKILL.md，填入人名挂到任意 AI 客户端；输出必须带出处，无出处即拒答。

## 硬规则（违者整个体系作废）

- 未经回源核对的引语一律标 unverified，不得作为 TA 的观点输出。
- 证据不足的结论输出 uncertain，禁止用常识脑补 TA 的立场。
- 一切模仿语气生成的内容，必须声明"模拟风格，非本人言论"。
- 在世人物注意诽谤与隐私风险；默认私有使用，不对外分发。

## 有界代表集（先定边界再采集）

采集前先拍板代表集，避免无底洞：如"最近 30 项公开内容"、"2024-2025 全部长文"、"5 个代表作案例"（借鉴 personal-distillation-skill）。

## 采集适配器（借鉴 WeClone 端到端思路）

| 来源 | 进 indexes 的方式 |
| :-- | :-- |
| 官网文集/专栏 | URL 逐条 HTTP 验证后入 letters/writings 索引 |
| 视频（B站/YouTube） | 播放页实测 200 → 入 speeches/interviews 索引；官方优先，第三方上传标 🔴 |
| 聊天记录（微信等） | 私人语料只进本地检索层，永不进公开仓库 |
| 播客/访谈 | 音轨→文字稿后按 🔴 处理，引用回原音频核对 |

## 验收测试（借鉴 personal-distillation acceptance test）

蒸馏完成后出 10 道验收题（人物事迹/观点/判断风格各若干），每道题的答案必须能指回具体 source id；指不回的条目回炉或标 unverified。

## 借鉴登记（谁的结构进了本模板）

| 本模板的部分 | 借鉴对象 | 借鉴内容 |
| :-- | :-- | :-- |
| 记忆分层协议（SKILL.md §8） | Second-Me | L0-L2 分层记忆思想（证据适配版：跨会话记忆必须先入库） |
| 写入即提案（SKILL.md §9） | Personal-Ontology | 提案门禁式修订 + maturity 三级（seed/corroborated/validated） |
| 有界代表集 + 验收测试 | personal-distillation-skill / EnterBoom | 先定边界再采集；testable hypotheses；10 题验收 |
| negative_constraints / knowledge_boundaries 字段 | yorishiro | SOUL.md 的负面约束与信息边界 |
| 采集适配器表 | WeClone | 端到端管线思想（仅结构，不搬其微调路线） |
| provenance 四值 + 言行对照 + 反例库 | 自创 | 竞品均无 |

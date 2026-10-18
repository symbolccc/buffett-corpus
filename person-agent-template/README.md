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

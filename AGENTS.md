# AGENTS.md — 给 AI 的导航与上下文预算规则

这是判据与索引仓库，不是可执行应用。

1. 查判据先读 criteria/criteria.json 的对应 id，**不要整包吞**。按 id 或 layer 过滤后再读。
2. 每条判据看三个字段：provenance（谁的判据）、decision_weight（能不能否决）、source_refs_status（出处核实了没有）。
3. source_refs_status == to_verify 或 missing 的引用，**不得在输出中当作已核实出处引用**。
4. 分析任何公司前，先过 C-circle-competence（gate）。不通过则输出 not_scorable，**其余判据不得继续打分**。
5. 任何财务字段若无 source_locator 或 extraction_confidence 低于 0.9，该字段进 uncertain，不进判据。
6. 校验器 scripts/validate.py 只校验本地 schema 与 provenance 规则，**不校验外部链接活性、不校验文本准确性、不校验年份真实性**。
7. 不得在无法解释生意如何赚钱时输出任何买卖结论。
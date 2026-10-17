# Trial Run · 2Q26 · Samsung Electronics vs SK hynix

> 2026-10-17 · 目的：验证「26 字段抽取 → 20 判据 → 结论」通路是否真的会拒绝凑结论。
> 输入：samsung.com IR 2Q26 conference PDF（p12–15）；SK hynix 2Q26 newsroom release + SEC 6-K 存在性确认（CIK 0002120882）。
> 字段明细见 samsung-2Q26.financials.json / skhynix-2Q26.financials.json（每字段带 confidence + source_locator）。

## 0. 通则执行记录（规则是否真的 firing）

| 规则 | 触发情况 |
| :-- | :-- |
| confidence < 0.9 → uncertain | Samsung 3 个字段触发：non_recurring_detail(0.8)、working_capital_delta(0.85 推导)、roic(0.7)。**推导值也被降级**，不只抽取值 |
| 年报不披露 → not_disclosed，禁止猜 | Samsung 6 项、SK hynix 12 项。维持性 capex 两家都 not_disclosed |
| 非经常性损益占比 >30% → 盈利质量复核 | **SK hynix 触发**：净利 93.92 > 营业利润 60.54 ⇒ 非经营收益 +33.38 = 净利的 36% ⇒ C-earnings-quality 判 uncertain，不得 pass |
| gate 不通过则停止打分 | 两家 gate 均通过，未触发 |
| 无估值输入 → 不得给买卖结论 | 两家 C-margin-of-safety / C-price-vs-value 均 uncertain ⇒ **总体结论只能是「需人工核验/观察」** |

## 1. Samsung Electronics 2Q26（KRW 万亿）

收入 171.5（+130% YoY）· 营业利润 89.5（margin 52.2%）· 净利 71.6 · OCF 105.08 · D&A 12.11 · capex 14.11 · 有息负债 22.41 · 现金* 190.0 · 净资产 579.3 · 净现金 167.6

| 判据 | 结果 | 依据/注 |
| :-- | :-- | :-- |
| C-circle-competence (gate) | pass | DS 半导体占收入 74%（127.5/171.5），生意可一段话解释 |
| C-moat-replicability | **flag** | 按 Q3 原问「竞争者认真投入能否复制」：HBM4 领先真实，但 SK hynix/美光以同等量级 capex 在做 ⇒ 答「能，代价极高」⇒ 不构成否决但记 flag |
| C-moat-trend | **uncertain** | margin 6.3%→52.2% 是**价格周期**不是护城河变宽。周期混淆必须标出，否则会把周期当 moat |
| C-pricing-power | pass | 售罄+提价，DRAM/NAND bit sales 历史新高 |
| C-institutional-imperative | **signal** | 全行业 capex 竞赛 = 教科书级机构惯性；DX 分部亏损（-0.8）仍保留 |
| C-mgmt-integrity (veto) | 未触发 | 季报为 review 非审计，无掩盖证据 |
| C-earnings-quality | pass | OCF/净利 = 147% |
| C-owner-earnings | pass | 71.6+12.1−14.1−25.8(WC,uncertain) ≈ +44，即使按全 capex 计仍强正 |
| C-debt-survival | pass | 净现金 167.6；debt/equity 4%；收入−30% 压力测试轻松存活 |
| T-cash-conversion 147% / T-leverage 0.22 / T-receivables 0.17 | pass | 均 signal_only，不计否决 |
| C-margin-of-safety / C-price-vs-value | uncertain | 无估值输入 |
| 卖出标准 1–4 | not_applicable | 买方分析 |

**总体：需人工核验（观察）。** 不是「买」。理由：估值缺失 + margin 扩张为周期混淆 + moat 可复制性 flag + capex 竞赛 signal。

## 2. SK hynix 2Q26（KRW 万亿）

收入 79.3187（+257% YoY）· 营业利润 60.5426（margin 76%）· 净利 93.9226（margin 118%）· 现金 88.0 · H1 收入 131.895

| 判据 | 结果 | 依据/注 |
| :-- | :-- | :-- |
| C-circle-competence (gate) | pass | 存储纯-play，可解释 |
| C-earnings-quality | **uncertain（复核触发）** | 净利>营业利润 ⇒ 非经营 +33.38 = 净利 36% > 30% 阈值；构成未披露 ⇒ 不得 pass |
| C-pricing-power | pass | HBM/DRAM 提价+售罄，约 10 家核心客户多年长协 |
| C-moat-replicability | flag | HBM4 良率+能效领先真实；同可复制性 caveat |
| C-moat-trend | uncertain | 同上周期混淆 |
| C-debt-survival | pass-with-note | 现金 88T、债务下降（方向披露、数字 not_disclosed） |
| 12/26 字段 not_disclosed | → 相关判据 uncertain | 新闻稿无 BS/CF 明细；6-K exhibit 路径已记录未取 |
| C-margin-of-safety / C-price-vs-value | uncertain | 无估值输入 |

**总体：需人工核验。** 比三星更强一档的「核验」，因为盈利质量复核触发 + 数据缺口更大。

## 3. 这次试跑证明了什么

1. **系统会拒绝有说服力**：两家都是史上最强季度，打分卡若机械运行会给出漂亮高分；本通路因估值缺失+周期混淆+非经常触发，输出「需人工核验」。这是设计目标达成，不是失败。
2. **周期混淆被显式标出**（C-moat-trend uncertain）——这是把「margin 变宽」误当「moat 变宽」的常见错误，schema 层挡住了它。
3. **not_disclosed 与 derived<0.9 都正确传播到 uncertain**，没有一个字段被猜。
4. **缺口即证据**：SK hynix 的 12 个 not_disclosed 直接告诉你下一步该取 6-K exhibit，而不是让模型补数。

## 4. 未做（诚实清单）

- 估值层（内在价值区间）未输入 ⇒ 买卖结论不可能产生。P6 之前这是常态。
- SK hynix 完整 BS/CF 未取（6-K 壳无 exhibit 链接；路径 CIK 0002120882 / 2026-07-29 6-K 已记录）。
- 两家均为季报 review 非审计 ⇒ audit_opinion 字段值为 review，C-mgmt-integrity 的证据强度受限。
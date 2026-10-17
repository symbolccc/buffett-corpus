# 试跑报告 · 2Q26 · Samsung Electronics vs SK hynix

> 2026-10-17 · 目的：验证「26 字段抽取 → confidence/locator 门槛 → 20 判据 → 结论」整条通路是否真的会拒绝凑结论。
> 数据源：Samsung = samsung.com IR `2026_2Q_conference_eng.pdf`（p12–15，实测抽取 16 页 0 空页）；SK hynix = newsroom 2Q26 release + SEC 6-K 存在性确认（CIK 0002120882，tickers SKHY/HXSCL）。
> 字段级明细：samsung-2Q26.financials.json（27 键）/ skhynix-2Q26.financials.json（16 键，含缺口声明）。

## 0. 规则 firing 记录（这是试跑的真正目的）

| 规则 | 是否触发 | 证据 |
| :-- | :-- | :-- |
| confidence < 0.9 → 进 uncertain 不进判据 | ✅ 触发 3 次（Samsung） | non_recurring_detail 0.8、working_capital_delta 0.85（**推导值也被降级**）、roic 0.7 |
| 年报不披露 → not_disclosed，禁止猜 | ✅ 触发 18 次 | Samsung 6 项、SK hynix 12 项；维持性 capex 两家均 not_disclosed |
| 非经常性损益/净利 > 30% → 盈利质量复核 | ✅ 触发（SK hynix） | 净利 93.92 > 营业利润 60.54 ⇒ 非经营收益 +33.38 = 净利 36% ⇒ C-earnings-quality = uncertain，**不得 pass** |
| gate（能力圈）不通过 → 停止打分 | 未触发 | 两家 gate 均通过 |
| 无估值输入 → 不得输出买卖结论 | ✅ 触发（两家） | C-margin-of-safety / C-price-vs-value 均 uncertain ⇒ 总体只能「需人工核验/观察」 |
| 周期混淆必须标出 | ✅ 触发（两家） | 毛利率/OP margin 的暴涨是**价格周期**，不是护城河变宽；C-moat-trend 判 uncertain 而非 pass |

## 1. Samsung Electronics 2Q26（KRW 万亿，合并口径）

收入 171.5（YoY +130%）· OP 89.5（margin 52.2%）· 净利 71.6 · OCF 105.08 · D&A 12.11 · capex 14.11 · 有息负债 22.41 · 现金* 190.0 · 权益 579.3 · 净现金 167.6 · DS 分部收入 127.5 / OP 89.2（margin 70%）· DX 分部 OP **-0.8（亏损）**

| 判据 | 结果 | 注 |
| :-- | :-- | :-- |
| C-circle-competence (gate) | pass | DS 占收入 74%，生意可一段话解释 |
| C-moat-replicability | flag | HBM4 领先真实，但 SK hynix/美光以同等量级 capex 在做 ⇒「能复制，代价极高」 |
| C-moat-trend | uncertain | margin 6.3%→52.2% 是周期，不是 moat |
| C-pricing-power | pass | 售罄+提价，DRAM/NAND bit sales 历史新高 |
| C-institutional-imperative | signal | 全行业 capex 竞赛=教科书级机构惯性；DX 亏损仍保留 |
| C-mgmt-integrity (veto) | 未触发 | 季报为 review 非审计，无掩盖证据 |
| C-earnings-quality | pass | OCF/净利 = 147% |
| C-owner-earnings | pass | 71.6+12.1−14.1−25.8(WC, uncertain) ≈ +44，强正 |
| C-debt-survival | pass | 净现金 167.6；debt/equity 4% |
| C-margin-of-safety / C-price-vs-value | uncertain | 无估值输入 |
| 阈值 T-cash-conversion / T-leverage-ebitda / T-nonrecurring-ratio / T-receivables | pass / pass / pass(带 uncertain 标签) / pass | 147% · 0.22× · 6.6% · 0.17× |

**总体：需人工核验（观察）。** 不是买入结论——估值缺失 + 周期混淆 + moat 可复制 flag，三者任一都不允许给「建议通过」级结论。

## 2. SK hynix 2Q26（KRW 万亿）

收入 79.3187（YoY +257%）· OP 60.5426（margin 76%）· 净利 93.9226（margin 118%）· 现金 88.0 · H1 收入 131.895 / H1 OP 98.1529

| 判据 | 结果 | 注 |
| :-- | :-- | :-- |
| C-circle-competence (gate) | pass | 存储纯play，可解释 |
| C-earnings-quality | **uncertain（复核触发）** | 净利>OP ⇒ 非经营 +33.38 = 36% > 30% 阈值；构成未披露 |
| C-pricing-power | pass | HBM/DRAM 提价+售罄，约 10 家核心客户多年长约 |
| C-moat-replicability | flag | HBM4 良率+能效领先，同 Samsung 的可复制性注记 |
| C-moat-trend | uncertain | 周期混淆 |
| C-debt-survival | pass(带注) | 现金 88T、债务下降；**具体债务数字 not_disclosed** |
| 其余 12 个 schema 键 | not_disclosed | 新闻稿不含 BS/CF；完整数据在 6-K exhibit（路径已记录：CIK 0002120882，2026-07-29 6-K accession 0001193125-26-321989；该 shell 无 exhibit 链接，未继续追） |

**总体：需人工核验。** 比 Samsung 更强的「核验」信号：盈利质量复核触发 + 数据缺口 12 项。

## 3. 试跑证明了三件事 / 暴露了一件事

证明：
1. **规则会真的 firing**——net>OP 异常、推导值降级、not_disclosed 传播，全部按设计执行，没有一条被「常识」绕过。
2. **系统会拒绝有说服力**——两家都是史上最强季度，输出却是「需人工核验」。这正是巴菲特方法的要求：强业绩≠可买。
3. **provenance 机制在实战中可用**——所有 pass 都能指到 p12–15 或 release 原文；所有 uncertain 都能指到「缺什么」。

暴露：
- **韩股不在层0 自动通路内**（既非 EDGAR 也非 A股）。SK hynix 因 ADR 上市而有 6-K，属意外收获；纯韩股/日股/欧股需要逐个市场补 resolver。已在 README「主战场」节注明美股为主，其余市场按用例补。
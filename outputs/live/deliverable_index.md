# 衍生品偏斜情绪盯盘 Agent 阅读指南

这份文件帮助你快速找到本 Agent 的关键材料。它面向研究员、交易者和使用智能体的用户，不要求你理解内部实现。

## 建议阅读顺序

1. 先打开 `report.html`，看当前判断、证据图和反证条件。
2. 再看 `decision_matrix.csv`，把当前情景、升级情景、降级情景分开。
3. 用 `monitoring_checklist.csv` 建立下一轮观察清单。
4. 如果要写复盘，直接从 `research_journal_template.md` 开始。
5. 如果要交给另一个研究员或 AI Agent，使用 `handoff_card.md` 和 `agent_snapshot.json`。

## 你会用到的材料

- `agent_snapshot.json`
- `alert_rules.json`
- `data_dictionary.csv`
- `decision_matrix.csv`
- `deliverable_index.md`
- `derivatives_sentiment_memo.md`
- `handoff_card.md`
- `iv_snapshot.csv`
- `monitoring_checklist.csv`
- `monitoring_rules.md`
- `operator_runbook.md`
- `research_journal_template.md`
- `scorecard_metrics.csv`
- `skew_sentiment_scorecard.json`

## 质量检查摘要

- 总体状态：`通过`
- 数据已成功读取：`通过`
- 关键证据足够形成本轮判断：`通过`
- 已经形成状态、证据和反证边界：`通过`
- 报告和配套材料已经生成：`通过`
- 没有自动下单或无条件买卖指令：`通过`
- 研究日志、观察清单和交接材料已经准备好：`通过`

## 本次使用的数据

- `fina_reports`: 4 rows
- `future_dominant_corr`: 9 rows
- `index_weights`: 600 rows
- `industry_constituents`: 1 rows
- `lhb_list`: 550 rows
- `margin`: 7 rows
- `option_implied_volatility`: 5404 rows
- `option_underlying_volatility`: 1 rows
- `charts/`

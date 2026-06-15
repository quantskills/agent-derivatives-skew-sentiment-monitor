# 衍生品偏斜情绪盯盘 Agent 使用指南

## 1. 先看它回答什么问题

打开 `report.html`，先读 `Executive Summary / 核心结论` 和 `适合回答的问题`。如果这个问题不是你关心的场景，就不用继续深挖。

## 2. 再看证据是否支持

检查 `charts/`、`scorecard_metrics.csv` 和 `data_dictionary.csv`，确认核心判断来自真实 Pandadata 表。

## 3. 决定下一步观察动作

读取 `decision_matrix.csv` 和 `monitoring_checklist.csv`，把需要跟踪的触发条件写入自己的研究流程。

## 4. 复盘

用 `research_journal_template.md` 记录支持证据、反证证据和下次重跑条件。

## 5. 停止条件

如果质量检查不是通过状态，或 `data_dictionary.csv` 里的关键表行数不足，本轮结果只能作为数据缺口记录。

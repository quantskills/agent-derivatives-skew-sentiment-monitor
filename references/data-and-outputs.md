# Data And Outputs / 数据与产物

本仓库已经附带一份 Pandadata live 示例输出，位于 `outputs/live/`。

## 主要阅读入口

- `outputs/live/report.html`：面向人的图文报告。
- `outputs/live/deliverable_index.md`：当前产物阅读指南。
- `outputs/live/handoff_card.md`：交给研究员或 AI Agent 的简短交接卡。

## 核心数据文件

- `outputs/live/iv_snapshot.csv`：期权隐含波动率截面。
- `outputs/live/skew_sentiment_scorecard.json`：衍生品情绪 scorecard。
- `outputs/live/scorecard_metrics.csv`：报告中展示的核心指标。
- `outputs/live/data_dictionary.csv`：使用的数据表、字段和行数。

## 研究辅助文件

- `outputs/live/decision_matrix.csv`：当前、升级、降级和证据不足情景。
- `outputs/live/monitoring_checklist.csv`：下一轮观察清单。
- `outputs/live/research_journal_template.md`：复盘记录模板。
- `outputs/live/monitoring_rules.md`：衍生品情绪观察规则。
- `outputs/live/derivatives_sentiment_memo.md`：情绪解释备忘。
- `outputs/live/alert_rules.json`：可供其他 Agent 读取的观察规则。

## 图表文件

- `outputs/live/charts/iv_distribution.png`
- `outputs/live/charts/iv_top_contracts.png`
- `outputs/live/charts/scorecard_metrics.png`

## 未公开的内部文件

公开仓库不包含内部验收文件和原始运行证据文件。用户应以 `report.html`、CSV、Markdown 和图表作为阅读与复盘入口。

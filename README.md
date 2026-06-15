# 衍生品偏斜情绪盯盘 Agent

这是 QuantSkills 组织的 Pandadata 研究/盯盘 Agent：`agent-derivatives-skew-sentiment-monitor`。

它面向研究员、交易者和使用 AI Agent 做市场复盘的用户。它不会自动下单，也不会输出无条件买卖指令；它的作用是把真实市场数据整理成你可以阅读、复盘和继续跟踪的研究材料。

## 它帮你回答什么

期权市场是否正在为风险或事件预期支付明显溢价？

## 你什么时候会用它

- 你想先判断一个市场状态、风险状态或研究线索是否值得继续看。
- 你需要把 Pandadata 数据转成图文报告，而不是只看原始表格。
- 你需要给自己或团队留下一份可复盘的观察清单。
- 你希望把结果交给另一个研究员或 AI Agent 继续分析。

## 本 Agent 的核心观察焦点

隐含波动率、历史波动率、IV-HV 差和高隐波合约。

## 如何阅读输出

本仓库已经附带一份 Pandadata live 示例输出，位于 `outputs/live/`。

1. 先打开 `outputs/live/report.html`，读核心结论和适合回答的问题。
2. 再看三张证据图，确认主判断、辅助证据和 scorecard 指标是否一致。
3. 用 `outputs/live/decision_matrix.csv` 判断当前是延续、升级、降级还是证据不足。
4. 用 `outputs/live/monitoring_checklist.csv` 建立下一轮盯盘清单。
5. 用 `outputs/live/research_journal_template.md` 写复盘，用 `outputs/live/handoff_card.md` 做交接。

## 你会得到的材料

| 材料 | 怎么用 |
| --- | --- |
| `outputs/live/report.html` | 先看结论、证据图、情景推演和反证条件。 |
| `outputs/live/decision_matrix.csv` | 把当前、升级、降级、证据不足四类情景转成后续动作。 |
| `outputs/live/monitoring_checklist.csv` | 下一轮盯盘的优先级清单。 |
| `outputs/live/research_journal_template.md` | 记录支持证据、反证证据和下次重跑条件。 |
| `outputs/live/handoff_card.md` | 把本次判断交给另一个研究员或 AI Agent。 |
| `outputs/live/data_dictionary.csv` | 查看使用的数据表、字段和行数。 |

## 参考文档

- `references/methodology.md`：解释本 Agent 的判断逻辑、指标含义和适用场景。
- `references/data-and-outputs.md`：说明 `outputs/live/` 下每个公开产物的用途。
- `references/agent-boundary.md`：说明 Agent 能做什么、不能做什么，以及交易边界。

## Python 脚本

本仓库附带一个无第三方依赖的 Python 工具脚本：

```powershell
py -3.10 scripts/agent_package.py validate
py -3.10 scripts/agent_package.py summarize
py -3.10 scripts/agent_package.py summarize --brief outputs/live/generated_brief.md
```

- `validate`：检查 `AGENT.md`、README、references、公开产物和图表是否完整。
- `summarize`：读取 `outputs/live/`，输出适合其他 AI Agent 使用的 JSON 摘要。
- `--brief`：额外生成一份 Markdown 简报，方便复制进研究日志。

## 使用的数据

- `get_option_implied_volatility`
- `get_option_underlying_volatility`

## 升级与降级线索

- 升级观察：IV-HV 差继续扩大，且高隐波集中在有解释力的到期或行权结构。
- 降级观察：隐波快速回落，或历史波动率上升解释了大部分溢价。

## 边界

这是研究和盯盘 Agent，不是自动交易系统。它不接券商接口，不执行订单，不替用户做最终交易决定。用户需要结合自己的策略、风险预算和执行系统使用这些材料。

## License

GNU General Public License v3.0。详见 [LICENSE](LICENSE)。

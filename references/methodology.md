# Methodology / 方法说明

本 Agent 用 Pandadata 的期权隐含波动率和标的历史波动率，观察衍生品市场是否正在为风险或事件预期支付溢价。它适合用于情绪监控、波动率复盘和事件预期观察。

## 核心问题

期权市场是否正在为风险或事件预期支付明显溢价？

## 使用的数据

- Pandadata methods: `get_option_implied_volatility`, `get_option_underlying_volatility`
- 主要产物：`outputs/live/iv_snapshot.csv`
- 关键图表：
  - `outputs/live/charts/iv_distribution.png`
  - `outputs/live/charts/iv_top_contracts.png`
  - `outputs/live/charts/scorecard_metrics.png`

## 判断逻辑

1. 读取期权隐含波动率截面。
2. 读取标的历史波动率。
3. 计算或比较 IV 与 HV 的差异。
4. 当 IV 明显高于 HV，说明市场正在为未来不确定性支付溢价。
5. 观察高隐波合约是否集中在少数合约、到期日或行权价附近。

## 输出解释

- `隐波溢价观察`：期权市场风险溢价明显，需要关注事件预期或避险需求。
- `衍生品情绪平稳观察`：当前隐含波动率相对历史波动率没有明显溢价。
- `IV-HV 差`：隐含波动率与历史波动率之间的差值。
- `高隐波合约`：截面里隐含波动率较高、值得继续拆解的合约。

## 适合继续追问的问题

- 溢价来自整个期权截面，还是少数合约？
- IV-HV 差是否在后续交易日收敛？
- 高隐波合约是否对应事件日、到期日或行权价结构？
- 这只是波动率定价，还是也伴随方向性资金行为？

## 使用边界

隐含波动率不等于方向判断。本 Agent 只做衍生品情绪和风险溢价观察，不替代完整期权定价、希腊字母风险和组合保证金管理。

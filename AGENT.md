---
name: agent-derivatives-skew-sentiment-monitor
description: "Monitor derivatives sentiment from option implied volatility and underlying historical volatility. Use when a research or trading AI agent needs Pandadata-backed monitoring, evidence-backed interpretation, user-readable reports, watchlists, and review materials without automated order placement."
metadata:
  organization: QuantSkills
  organization_url: https://github.com/quantskills
  repository: quantskills/agent-derivatives-skew-sentiment-monitor
  repository_url: https://github.com/quantskills/agent-derivatives-skew-sentiment-monitor
  project_type: agent
  collection: pandadata-research-monitor-agents-8
  license: GPL-3.0
  category: monitor-agent
  tags: [derivatives, options, sentiment, pandadata]
  platforms: [claude-code, codex, openclaw, cursor]
  language: zh-en
  status: active
  validation_level: verified
  maintainer_type: official
  requires: [skill-pandadata-api]
  pandadata_methods: [get_option_implied_volatility, get_option_underlying_volatility]
  summary_zh: 用期权隐含波动率和标的历史波动率观察衍生品市场风险偏好，不重复已有期权波动率分析 Skill。
  summary_en: Monitor derivatives sentiment from option implied volatility and underlying historical volatility.
quantSkills:
  organization: QuantSkills
  organization_url: https://github.com/quantskills
  repository: quantskills/agent-derivatives-skew-sentiment-monitor
  repository_url: https://github.com/quantskills/agent-derivatives-skew-sentiment-monitor
  project_type: agent
  collection: pandadata-research-monitor-agents-8
  license: GPL-3.0
  category: monitor-agent
  tags: [derivatives, options, sentiment, pandadata]
  platforms: [claude-code, codex, openclaw, cursor]
  language: zh-en
  status: active
  validation_level: verified
  maintainer_type: official
  requires: [skill-pandadata-api]
  pandadata_methods: [get_option_implied_volatility, get_option_underlying_volatility]
  summary_zh: 用期权隐含波动率和标的历史波动率观察衍生品市场风险偏好，不重复已有期权波动率分析 Skill。
  summary_en: Monitor derivatives sentiment from option implied volatility and underlying historical volatility.
---

# Derivatives Skew Sentiment Monitor

Use this Agent when a user needs a Pandadata-backed research or monitoring answer for:

> Is the options market paying a meaningful premium for risk or event uncertainty?

The Agent should produce user-readable research materials, not only raw tables. Keep the answer evidence-backed, cautious, and clear about what would invalidate the current view.

## User-Facing Workflow

1. State the current answer in plain language.
2. Show the key evidence and explain why it matters.
3. Separate current, upgrade, downgrade, and insufficient-evidence scenarios.
4. Produce a watch checklist and review template the user can continue using.
5. Keep order execution outside the Agent boundary.

## Primary Watch Focus

隐含波动率、历史波动率、IV-HV 差和高隐波合约。

## Materials To Produce

| Material | Use |
| --- | --- |
| `outputs/live/report.html` | Start with the conclusion, evidence charts, scenarios, and invalidation conditions. |
| `outputs/live/decision_matrix.csv` | Turns base, upgrade, downgrade, and insufficient-evidence cases into next actions. |
| `outputs/live/monitoring_checklist.csv` | Prioritized watch items for the next review window. |
| `outputs/live/research_journal_template.md` | Template for evidence, counter-evidence, and rerun conditions. |
| `outputs/live/handoff_card.md` | Short handoff for another researcher or AI agent. |
| `outputs/live/data_dictionary.csv` | Tables, fields, and row counts used in the run. |

## Pandadata Methods

- `get_option_implied_volatility`
- `get_option_underlying_volatility`

## Boundary

- Use Pandadata or user-provided data only.
- Mark missing data as inconclusive instead of filling gaps with assumptions.
- Do not produce unconditional buy/sell commands.
- Do not connect to broker order execution.

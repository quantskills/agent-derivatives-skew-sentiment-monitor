# Derivatives Skew Sentiment Monitor

This is a QuantSkills Pandadata research and monitoring agent: `agent-derivatives-skew-sentiment-monitor`.

It is built for researchers, traders, and AI-agent-assisted market review workflows. It does not place orders and does not issue unconditional buy/sell instructions. Its job is to turn real market evidence into readable, reviewable, and reusable research materials.

## What It Helps You Answer

Is the options market paying a meaningful premium for risk or event uncertainty?

## When To Use It

- You want to decide whether a market state, risk state, or research lead deserves more attention.
- You want Pandadata evidence turned into a report instead of raw tables only.
- You need a watchlist and review checklist for the next observation window.
- You want to hand the result to another researcher or AI agent.

## Primary Watch Focus

隐含波动率、历史波动率、IV-HV 差和高隐波合约。

## How To Read The Output

This repository includes a packaged Pandadata live sample output under `outputs/live/`.

1. Open `outputs/live/report.html` and read the conclusion plus the questions this agent is suited for.
2. Check the three evidence charts: main evidence, supporting evidence, and scorecard metrics.
3. Use `outputs/live/decision_matrix.csv` to separate base, upgrade, downgrade, and insufficient-evidence cases.
4. Use `outputs/live/monitoring_checklist.csv` for the next review window.
5. Use `outputs/live/research_journal_template.md` for review notes and `outputs/live/handoff_card.md` for handoff.

## Materials You Get

| Material | Use |
| --- | --- |
| `outputs/live/report.html` | Start with the conclusion, evidence charts, scenarios, and invalidation conditions. |
| `outputs/live/decision_matrix.csv` | Turns base, upgrade, downgrade, and insufficient-evidence cases into next actions. |
| `outputs/live/monitoring_checklist.csv` | Prioritized watch items for the next review window. |
| `outputs/live/research_journal_template.md` | Template for evidence, counter-evidence, and rerun conditions. |
| `outputs/live/handoff_card.md` | Short handoff for another researcher or AI agent. |
| `outputs/live/data_dictionary.csv` | Tables, fields, and row counts used in the run. |

## References

- `references/methodology.md`: Agent logic, metric interpretation, and intended use.
- `references/data-and-outputs.md`: Public output files under `outputs/live/` and how to use them.
- `references/agent-boundary.md`: What the Agent can do, what it cannot do, and trading boundaries.

## Python Script

This repository includes a dependency-free Python utility script:

```powershell
py -3.10 scripts/agent_package.py validate
py -3.10 scripts/agent_package.py summarize
py -3.10 scripts/agent_package.py summarize --brief outputs/live/generated_brief.md
```

- `validate`: Checks `AGENT.md`, READMEs, references, public outputs, and chart files.
- `summarize`: Reads `outputs/live/` and prints a JSON summary for other AI agents.
- `--brief`: Writes a Markdown brief for research notes or handoff.

## Pandadata Methods

- `get_option_implied_volatility`
- `get_option_underlying_volatility`

## Upgrade And Downgrade Clues

- Upgrade watch: IV-HV 差继续扩大，且高隐波集中在有解释力的到期或行权结构。
- Downgrade watch: 隐波快速回落，或历史波动率上升解释了大部分溢价。

## Boundary

This is a research and monitoring agent, not an automated trading system. It does not connect to brokers, execute orders, or replace the user's own strategy, risk budget, and execution process.

## License

GNU General Public License v3.0. See [LICENSE](LICENSE).

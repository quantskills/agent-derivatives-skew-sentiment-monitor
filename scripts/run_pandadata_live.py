from __future__ import annotations

import argparse
import csv
import html
import json
import math
import os
import shutil
import statistics
import time
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "http://pandadata.pandaaiquant.com"
DEFAULT_START_DATE = "20250102"
DEFAULT_END_DATE = "20250110"
DEFAULT_OPTION_DATE = "20260310"
DEFAULT_SYMBOL = "000001.SZ"


AGENT_CONFIGS: dict[str, dict[str, Any]] = {
    "agent-market-regime-monitor": {
        "title_zh": "市场状态盯盘 Agent",
        "title_en": "Market Regime Monitor",
        "category": "monitor-agent",
        "state_label": "热度扩张观察",
        "question": "当前市场环境是热度扩张、风险扩张，还是需要先观望？",
        "watch_focus": "融资余额、龙虎榜事件原因分布、历史波动率。",
        "required_tables": ["margin", "lhb_list", "option_underlying_volatility"],
        "scorecard_file": "regime_scorecard.json",
        "memo_file": "market_regime_brief.md",
        "extra_files": ["breadth_table.csv", "watch_triggers.md"],
        "chart_builders": ["funding_balance", "event_reason_distribution", "scorecard_metrics"],
    },
    "agent-crowding-risk-monitor": {
        "title_zh": "拥挤交易风险盯盘 Agent",
        "title_en": "Crowding Risk Monitor",
        "category": "risk-agent",
        "state_label": "拥挤观察",
        "question": "当前交易热度是否已经进入拥挤区，后续应观察哪些去拥挤风险？",
        "watch_focus": "融资余额、龙虎榜成交额、换手率和做空余额变化。",
        "required_tables": ["margin", "lhb_list"],
        "scorecard_file": "crowding_scorecard.json",
        "memo_file": "crowding_risk_memo.md",
        "extra_files": ["de_risk_triggers.md", "counter_evidence.md"],
        "chart_builders": ["funding_balance_crowding", "lhb_amount_top", "scorecard_metrics"],
    },
    "agent-correlation-break-research": {
        "title_zh": "相关性断裂研究 Agent",
        "title_en": "Correlation Break Research Agent",
        "category": "research-agent",
        "state_label": "相关性断裂观察",
        "question": "资产相关性是否出现结构变化，组合分散是否可能失效？",
        "watch_focus": "期货主力合约相关矩阵、最大/最小相关差、跨品种相关扩散。",
        "required_tables": ["future_dominant_corr"],
        "scorecard_file": "break_scorecard.json",
        "memo_file": "correlation_break_memo.md",
        "extra_files": ["correlation_matrix.csv", "risk_questions.md"],
        "chart_builders": ["correlation_heatmap", "cross_correlation_bars", "scorecard_metrics"],
    },
    "agent-derivatives-skew-sentiment-monitor": {
        "title_zh": "衍生品偏斜情绪盯盘 Agent",
        "title_en": "Derivatives Skew Sentiment Monitor",
        "category": "monitor-agent",
        "state_label": "隐波溢价观察",
        "question": "期权隐含波动率相对标的历史波动率是否显示风险偏好变化？",
        "watch_focus": "期权隐含波动率分布、隐波最高合约、标的历史波动率。",
        "required_tables": ["option_implied_volatility", "option_underlying_volatility"],
        "scorecard_file": "skew_sentiment_scorecard.json",
        "memo_file": "derivatives_sentiment_memo.md",
        "extra_files": ["iv_snapshot.csv", "monitoring_rules.md"],
        "chart_builders": ["iv_distribution", "iv_top_contracts", "scorecard_metrics"],
    },
}


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def init_pandadata(base_url: str) -> tuple[Any, dict[str, Any]]:
    load_env_file(ROOT / ".env")
    load_env_file(Path.home() / ".pandadata" / "pandadata.env")
    username = os.getenv("PANDADATA_USERNAME") or os.getenv("DEFAULT" + "_" + "USERNAME")
    password = os.getenv("PANDADATA_PASSWORD") or os.getenv("DEFAULT" + "_" + "PASSWORD")
    base = os.getenv("PANDADATA_BASE_URL") or os.getenv("JAVA_SERVICE_BASE_URL") or base_url
    if not username or not password:
        raise RuntimeError(
            "Missing Pandadata credentials. Set PANDADATA_USERNAME and "
            "PANDADATA_PASSWORD in the environment or in a local .env file."
        )
    try:
        import panda_data
    except ImportError as exc:
        raise RuntimeError("Missing package panda-data. Run: py -3.10 -m pip install -r requirements.txt") from exc

    started = time.time()
    panda_data.init_token(username=username, password=password, base_url=base)
    return panda_data, {"base_url": base, "login_seconds": round(time.time() - started, 2)}


def df_to_records(frame: Any) -> list[dict[str, Any]]:
    if frame is None:
        return []
    if hasattr(frame, "to_dict"):
        records = frame.to_dict(orient="records")
    elif isinstance(frame, list):
        records = frame
    elif isinstance(frame, dict):
        records = [{"pair": key, "correlation": value} for key, value in frame.items()]
    else:
        records = list(frame)
    return [json_safe(row) for row in records if isinstance(row, dict)]


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    if hasattr(value, "item"):
        try:
            return json_safe(value.item())
        except Exception:
            pass
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def pct_change(first: Any, last: Any) -> float | None:
    a = as_float(first)
    b = as_float(last)
    if a is None or b is None or abs(a) < 1e-12:
        return None
    return (b - a) / abs(a)


def mean(values: list[Any]) -> float | None:
    nums = [x for x in (as_float(v) for v in values) if x is not None]
    return sum(nums) / len(nums) if nums else None


def median(values: list[Any]) -> float | None:
    nums = [x for x in (as_float(v) for v in values) if x is not None]
    return statistics.median(nums) if nums else None


def fmt(value: Any, digits: int = 4) -> str:
    number = as_float(value)
    if number is None:
        return str(value)
    return f"{number:.{digits}f}"


def fetch_data(agent_name: str, args: argparse.Namespace) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    panda_data, runtime = init_pandadata(args.base_url)
    calls: dict[str, Callable[[], Any]] = {
        "margin": lambda: panda_data.get_margin(
            symbol=args.symbol,
            start_date=args.start_date,
            end_date=args.end_date,
            margin_type="stock",
            fields=["symbol", "date", "margin_balance", "short_balance", "total_balance", "buy_on_margin_value"],
        ),
        "lhb_list": lambda: panda_data.get_lhb_list(
            start_date=args.start_date,
            end_date=args.end_date,
            type="",
            symbol="",
            fields=["symbol", "date", "type", "amount", "change_rate", "deviation", "reason", "turnover", "volume"],
        ),
        "future_dominant_corr": lambda: panda_data.get_future_dominant_corr(
            symbol=args.future_symbols.split(","),
            start_date=args.future_start_date,
            end_date=args.future_end_date,
        ),
        "option_implied_volatility": lambda: panda_data.get_option_implied_volatility(
            start_date=args.option_date,
            end_date=args.option_date,
            symbol="",
            fields=["date", "symbol", "implied_volatility"],
        ),
        "option_underlying_volatility": lambda: panda_data.get_option_underlying_volatility(
            start_date=args.option_date,
            end_date=args.option_date,
            symbol=args.option_underlying,
            period=args.option_period,
            fields=["date", "symbol", "close", "period", "historical_volatility"],
        ),
    }
    data: dict[str, list[dict[str, Any]]] = {}
    call_meta: list[dict[str, Any]] = []
    for table in AGENT_CONFIGS[agent_name]["required_tables"]:
        started = time.time()
        print(json.dumps({"event": "pandadata_call_start", "table": table}, ensure_ascii=False), flush=True)
        rows = df_to_records(calls[table]())
        data[table] = rows
        meta = {
            "table": table,
            "seconds": round(time.time() - started, 2),
            "rows": len(rows),
            "columns": list(rows[0].keys()) if rows else [],
        }
        call_meta.append(meta)
        print(json.dumps({"event": "pandadata_call_done", **meta}, ensure_ascii=False), flush=True)
    runtime["calls"] = call_meta
    runtime["date_windows"] = {
        "market": [args.start_date, args.end_date],
        "options": [args.option_date, args.option_date],
        "futures": [args.future_start_date, args.future_end_date],
    }
    return data, runtime


def table_profile(data: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    return {
        table: {"rows": len(rows), "columns": sorted(rows[0].keys()) if rows else []}
        for table, rows in sorted(data.items())
    }


def build_scorecard(agent_name: str, data: dict[str, list[dict[str, Any]]]) -> tuple[dict[str, Any], str, str]:
    if agent_name == "agent-market-regime-monitor":
        margin = sorted(data.get("margin", []), key=lambda row: str(row.get("date", "")))
        lhb = data.get("lhb_list", [])
        hv_rows = data.get("option_underlying_volatility", [])
        margin_change = pct_change(margin[0].get("total_balance"), margin[-1].get("total_balance")) if len(margin) >= 2 else None
        lhb_mean_change = mean([row.get("change_rate") for row in lhb])
        hv = as_float(hv_rows[0].get("historical_volatility")) if hv_rows else None
        state = "heat-expansion-watch" if (lhb_mean_change or 0) >= 0 and (margin_change or 0) >= 0 else "mixed-regime-watch"
        scorecard = {
            "regime": state,
            "lhb_rows": len(lhb),
            "lhb_mean_change_rate": lhb_mean_change,
            "margin_total_balance_change": margin_change,
            "underlying_hv": hv,
            "confidence": "medium" if lhb and margin else "low",
        }
        return scorecard, state, "中高关注"
    if agent_name == "agent-crowding-risk-monitor":
        margin = sorted(data.get("margin", []), key=lambda row: str(row.get("date", "")))
        lhb = data.get("lhb_list", [])
        state = "crowding-watch"
        scorecard = {
            "state": state,
            "lhb_heat_rows": len(lhb),
            "symbol": DEFAULT_SYMBOL,
            "lhb_mean_change_rate": mean([row.get("change_rate") for row in lhb]),
            "lhb_avg_amount": mean([row.get("amount") for row in lhb]),
            "lhb_avg_turnover": mean([row.get("turnover") for row in lhb]),
            "margin_total_balance_change": pct_change(margin[0].get("total_balance"), margin[-1].get("total_balance")) if len(margin) >= 2 else None,
            "short_balance_change": pct_change(margin[0].get("short_balance"), margin[-1].get("short_balance")) if len(margin) >= 2 else None,
            "confidence": "medium" if lhb and margin else "low",
        }
        return scorecard, state, "高关注"
    if agent_name == "agent-correlation-break-research":
        rows = data.get("future_dominant_corr", [])
        abs_corr = [abs(v) for v in (as_float(row.get("correlation")) for row in rows) if v is not None]
        max_abs = max(abs_corr) if abs_corr else None
        min_abs = min(abs_corr) if abs_corr else None
        spread = max_abs - min_abs if max_abs is not None and min_abs is not None else None
        state = "correlation-break-watch" if (spread or 0) >= 0.3 else "correlation-stable-watch"
        scorecard = {
            "state": state,
            "max_abs_cross_corr": max_abs,
            "min_abs_cross_corr": min_abs,
            "corr_spread": spread,
            "pair_count": len(rows),
            "confidence": "medium" if rows else "low",
        }
        return scorecard, state, "高关注"
    rows = data.get("option_implied_volatility", [])
    hv_rows = data.get("option_underlying_volatility", [])
    iv = median([row.get("implied_volatility") for row in rows])
    hv = as_float(hv_rows[0].get("historical_volatility")) if hv_rows else None
    hv_pct = hv * 100 if hv is not None and hv < 1 else hv
    premium = iv - hv_pct if iv is not None and hv_pct is not None else None
    state = "iv-premium-watch" if (premium or 0) > 0 else "iv-neutral-watch"
    scorecard = {
        "state": state,
        "median_implied_volatility": iv,
        "underlying_historical_volatility_pct": hv_pct,
        "iv_minus_hv": premium,
        "iv_rows": len(rows),
        "confidence": "medium" if rows and hv_rows else "low",
    }
    return scorecard, state, "中高关注"


def scorecard_rows(scorecard: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "metric": key,
            "value": "" if value is None else fmt(value) if isinstance(value, float) else str(value),
            "type": type(value).__name__,
            "reader_note": "用于复核本次判断的核心字段",
        }
        for key, value in scorecard.items()
    ]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_safe(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


def make_decision_rows(state: str, risk_level: str) -> list[dict[str, str]]:
    return [
        {
            "scenario": "当前基准判断",
            "trigger": state,
            "research_action": "先把本轮证据写入研究日志，再观察下一次数据是否延续。",
            "risk_action": f"按{risk_level}处理，只作为研究和盯盘输入。",
            "invalidation": "核心证据在下一次重跑中明显反向。",
        },
        {
            "scenario": "升级观察",
            "trigger": "核心指标继续同向强化，且没有明显反证。",
            "research_action": "提高复盘频率，补充更长窗口和更多交叉证据。",
            "risk_action": "先更新观察等级，再由用户自己的风险系统决定是否调整暴露。",
            "invalidation": "升级触发后没有得到后续数据确认。",
        },
        {
            "scenario": "降级观察",
            "trigger": "核心指标转弱，或新增证据与当前解释冲突。",
            "research_action": "降低当前解释权重，回到样本复核和反证检查。",
            "risk_action": "减少对当前结论的依赖，避免用旧标签解释新数据。",
            "invalidation": "降级信号被后续强证据快速修复。",
        },
        {
            "scenario": "证据不足",
            "trigger": "关键表、关键字段或时间窗口不足。",
            "research_action": "记录缺口，等待数据补齐后重跑。",
            "risk_action": "不把本轮结果作为交易依据。",
            "invalidation": "缺失数据补齐且质量检查重新通过。",
        },
    ]


def make_monitoring_rows(config: dict[str, Any], scorecard: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "priority": 1,
            "item": "核心状态是否延续",
            "why_it_matters": config["question"],
            "current_value": scorecard.get("state") or scorecard.get("regime"),
            "next_check": "下一次 Pandadata 数据刷新后重跑本脚本。",
        },
        {
            "priority": 2,
            "item": "反证条件是否出现",
            "why_it_matters": "防止把短期噪声误读成稳定结构。",
            "current_value": "见 decision_matrix.csv",
            "next_check": "对照升级/降级观察条件。",
        },
        {
            "priority": 3,
            "item": "数据覆盖是否足够",
            "why_it_matters": "样本行数和字段完整度会影响解释强度。",
            "current_value": scorecard.get("confidence", "unknown"),
            "next_check": "查看 data_dictionary.csv。",
        },
    ]


def make_alert_rules(state: str) -> dict[str, Any]:
    return {
        "agent_state": state,
        "rules": [
            {"level": "watch", "condition": "核心状态延续", "action": "更新研究日志并保留观察"},
            {"level": "upgrade", "condition": "核心指标继续同向强化", "action": "提高复盘频率"},
            {"level": "downgrade", "condition": "核心指标反向或数据不足", "action": "降级当前解释权重"},
        ],
        "trading_boundary": "Research and monitoring only. No automatic order placement.",
    }


def configure_plotting() -> Any:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["axes.unicode_minus"] = False
    return plt


def save_scorecard_chart(path: Path, scorecard: dict[str, Any]) -> None:
    plt = configure_plotting()
    values = []
    labels = []
    for key, value in scorecard.items():
        number = as_float(value)
        if number is not None:
            labels.append(key)
            values.append(number)
    labels = labels[:8] or ["score"]
    values = values[:8] or [0]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.barh(labels, values, color="#4477aa")
    ax.set_title("Scorecard Metrics")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def save_agent_charts(agent_name: str, data: dict[str, list[dict[str, Any]]], scorecard: dict[str, Any], charts_dir: Path) -> list[str]:
    plt = configure_plotting()
    charts_dir.mkdir(parents=True, exist_ok=True)
    chart_files: list[str] = []

    def save_current(name: str) -> None:
        chart_files.append(f"charts/{name}")
        plt.tight_layout()
        plt.savefig(charts_dir / name, dpi=150)
        plt.close()

    if agent_name == "agent-market-regime-monitor":
        margin = sorted(data.get("margin", []), key=lambda row: str(row.get("date", "")))
        plt.figure(figsize=(9, 4.5))
        plt.plot([row.get("date") for row in margin], [as_float(row.get("total_balance")) or 0 for row in margin], marker="o")
        plt.title("Margin Total Balance")
        plt.grid(alpha=0.25)
        save_current("funding_balance.png")

        reasons: dict[str, int] = {}
        for row in data.get("lhb_list", []):
            reason = str(row.get("reason") or row.get("type") or "unknown")[:28]
            reasons[reason] = reasons.get(reason, 0) + 1
        top = sorted(reasons.items(), key=lambda item: item[1], reverse=True)[:10]
        plt.figure(figsize=(9, 4.5))
        plt.barh([x[0] for x in top], [x[1] for x in top], color="#66aa77")
        plt.title("Event Reason Distribution")
        save_current("event_reason_distribution.png")
    elif agent_name == "agent-crowding-risk-monitor":
        margin = sorted(data.get("margin", []), key=lambda row: str(row.get("date", "")))
        plt.figure(figsize=(9, 4.5))
        plt.plot([row.get("date") for row in margin], [as_float(row.get("total_balance")) or 0 for row in margin], marker="o")
        plt.title("Funding Balance")
        plt.grid(alpha=0.25)
        save_current("funding_balance_crowding.png")

        lhb = sorted(data.get("lhb_list", []), key=lambda row: as_float(row.get("amount")) or 0, reverse=True)[:12]
        plt.figure(figsize=(9, 4.5))
        plt.barh([str(row.get("symbol")) for row in lhb], [as_float(row.get("amount")) or 0 for row in lhb], color="#cc6677")
        plt.title("Top LHB Amount")
        save_current("lhb_amount_top.png")
    elif agent_name == "agent-correlation-break-research":
        rows = data.get("future_dominant_corr", [])
        pairs = [str(row.get("pair", f"pair_{i}")) for i, row in enumerate(rows)]
        vals = [as_float(row.get("correlation")) or 0 for row in rows]
        size = max(1, int(math.ceil(math.sqrt(len(vals) or 1))))
        matrix = [[0.0 for _ in range(size)] for _ in range(size)]
        for i, val in enumerate(vals):
            matrix[i // size][i % size] = val
        fig, ax = plt.subplots(figsize=(6, 5))
        im = ax.imshow(matrix, cmap="coolwarm", vmin=-1, vmax=1)
        ax.set_title("Correlation Heatmap")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        fig.tight_layout()
        fig.savefig(charts_dir / "correlation_heatmap.png", dpi=150)
        plt.close(fig)
        chart_files.append("charts/correlation_heatmap.png")

        plt.figure(figsize=(9, 4.5))
        plt.barh(pairs, vals, color="#aa7744")
        plt.title("Cross Correlation Bars")
        save_current("cross_correlation_bars.png")
    else:
        iv_values = [as_float(row.get("implied_volatility")) for row in data.get("option_implied_volatility", [])]
        iv_values = [v for v in iv_values if v is not None]
        plt.figure(figsize=(9, 4.5))
        plt.hist(iv_values, bins=30, color="#7788cc")
        plt.title("Implied Volatility Distribution")
        save_current("iv_distribution.png")

        rows = sorted(data.get("option_implied_volatility", []), key=lambda row: as_float(row.get("implied_volatility")) or 0, reverse=True)[:12]
        plt.figure(figsize=(9, 4.5))
        plt.barh([str(row.get("symbol")) for row in rows], [as_float(row.get("implied_volatility")) or 0 for row in rows], color="#aa66aa")
        plt.title("Top IV Contracts")
        save_current("iv_top_contracts.png")

    save_scorecard_chart(charts_dir / "scorecard_metrics.png", scorecard)
    chart_files.append("charts/scorecard_metrics.png")
    return chart_files


def write_extra_files(agent_name: str, output_dir: Path, data: dict[str, list[dict[str, Any]]], scorecard: dict[str, Any]) -> None:
    if agent_name == "agent-market-regime-monitor":
        write_csv(output_dir / "breadth_table.csv", data.get("lhb_list", [])[:50])
        write_text(output_dir / "watch_triggers.md", "- 观察融资余额是否继续上行\n- 观察龙虎榜事件热度是否降温\n- 观察历史波动率是否抬升")
    elif agent_name == "agent-crowding-risk-monitor":
        write_text(output_dir / "de_risk_triggers.md", "- 融资余额回落\n- 龙虎榜成交额快速下降\n- 换手率和价格背离")
        write_text(output_dir / "counter_evidence.md", "- 热度下降但价格稳定\n- 融资余额下降但承接改善\n- 龙虎榜集中度下降")
    elif agent_name == "agent-correlation-break-research":
        write_csv(output_dir / "correlation_matrix.csv", data.get("future_dominant_corr", []))
        write_text(output_dir / "risk_questions.md", "- 当前组合分散是否仍然有效？\n- 哪些品种对整体相关性变化贡献最大？\n- 相关性变化是否只来自短窗口噪声？")
    else:
        write_csv(output_dir / "iv_snapshot.csv", data.get("option_implied_volatility", [])[:200])
        write_text(output_dir / "monitoring_rules.md", "- 观察隐波中位数是否继续高于历史波动率\n- 观察高隐波合约是否集中\n- 观察标的波动率是否追上隐波")


def write_report(
    output_dir: Path,
    config: dict[str, Any],
    scorecard: dict[str, Any],
    state: str,
    risk_level: str,
    charts: list[str],
    runtime: dict[str, Any],
    profile: dict[str, Any],
) -> None:
    chart_html = "\n".join(
        f'<figure class="chart"><figcaption>{html.escape(Path(src).stem.replace("_", " ").title())}</figcaption><img src="{html.escape(src)}" alt="{html.escape(src)}"></figure>'
        for src in charts
    )
    score_rows = "\n".join(
        f"<tr><td>{html.escape(row['metric'])}</td><td>{html.escape(row['value'])}</td><td>{html.escape(row['reader_note'])}</td></tr>"
        for row in scorecard_rows(scorecard)
    )
    data_rows = "\n".join(
        f"<tr><td>{html.escape(table)}</td><td>{info.get('rows', 0)}</td><td>{html.escape(', '.join(info.get('columns', [])))}</td></tr>"
        for table, info in profile.items()
    )
    calls = runtime.get("calls", [])
    call_rows = "".join(f"<li>{html.escape(c['table'])}: {c['rows']} rows, {c['seconds']}s</li>" for c in calls)
    generated_at = time.strftime("%Y-%m-%d %H:%M:%S")
    html_text = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(config['title_zh'])}</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #18212f; background: #f6f8fb; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 28px 18px 48px; }}
    header {{ padding: 26px 0 18px; border-bottom: 1px solid #d9e0ea; }}
    h1 {{ margin: 0 0 10px; font-size: 32px; letter-spacing: 0; }}
    h2 {{ margin-top: 30px; font-size: 21px; }}
    p, li {{ line-height: 1.75; }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 14px; }}
    .pill {{ border: 1px solid #cbd5e1; background: #fff; padding: 6px 10px; border-radius: 6px; font-size: 14px; }}
    .panel {{ background: #fff; border: 1px solid #d9e0ea; border-radius: 6px; padding: 18px; margin-top: 16px; }}
    .chart-stack {{ display: grid; grid-template-columns: 1fr; gap: 14px; }}
    .chart {{ margin: 0; padding: 14px; background: #fff; border: 1px solid #d9e0ea; border-radius: 6px; }}
    .chart img {{ display: block; width: 100%; height: auto; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; }}
    th, td {{ border: 1px solid #d9e0ea; padding: 9px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #edf2f7; }}
    .table-wrap {{ overflow-x: auto; }}
    details {{ background: #fff; border: 1px solid #d9e0ea; border-radius: 6px; padding: 12px 14px; }}
    summary {{ cursor: pointer; font-weight: 700; }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>{html.escape(config['title_zh'])}</h1>
    <p>{html.escape(config['title_en'])}</p>
    <div class="meta">
      <span class="pill">状态：{html.escape(config['state_label'])}</span>
      <span class="pill">风险关注：{html.escape(risk_level)}</span>
      <span class="pill">数据源：Pandadata</span>
      <span class="pill">用途：研究和盯盘</span>
    </div>
  </header>

  <section class="panel">
    <h2>核心结论</h2>
    <p>本次运行给出的状态是 <b>{html.escape(state)}</b>。这不是自动买卖建议，而是帮助研究者判断是否需要继续观察、升级复盘或寻找反证。</p>
  </section>

  <section class="panel">
    <h2>这个 Agent 适合你解决什么问题</h2>
    <p>{html.escape(config['question'])}</p>
    <p><b>核心观察焦点：</b>{html.escape(config['watch_focus'])}</p>
  </section>

  <section>
    <h2>关键证据图</h2>
    <div class="chart-stack">{chart_html}</div>
  </section>

  <section>
    <h2>证据拆解</h2>
    <div class="table-wrap"><table><thead><tr><th>指标</th><th>值</th><th>说明</th></tr></thead><tbody>{score_rows}</tbody></table></div>
  </section>

  <section class="panel">
    <h2>情景推演</h2>
    <p>当前状态可以作为基准观察；如果核心指标继续同向强化，进入升级观察；如果核心证据反向，降级当前解释权重；如果数据覆盖不足，先停止解释并等待补数。</p>
  </section>

  <section class="panel">
    <h2>观察清单</h2>
    <ul>
      <li>先看核心状态是否延续。</li>
      <li>再看是否出现反证条件。</li>
      <li>最后确认数据覆盖和字段完整性。</li>
    </ul>
  </section>

  <section class="panel">
    <h2>下一步观察</h2>
    <p>下一次 Pandadata 数据刷新后重新运行脚本，重点比较 scorecard、decision matrix 和 monitoring checklist 的变化。</p>
  </section>

  <section>
    <h2>数据来源与可信度</h2>
    <div class="table-wrap"><table><thead><tr><th>表</th><th>行数</th><th>字段</th></tr></thead><tbody>{data_rows}</tbody></table></div>
    <details>
      <summary>查看运行信息</summary>
      <p>生成时间：{html.escape(generated_at)}。登录耗时：{runtime.get('login_seconds')}s。</p>
      <ul>{call_rows}</ul>
      <p>限制与假设：样本窗口较短，适合盯盘和研究复盘，不适合单独形成交易结论。</p>
    </details>
  </section>
</main>
</body>
</html>"""
    write_text(output_dir / "report.html", html_text)


def public_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.name


def generate(agent_name: str, args: argparse.Namespace) -> dict[str, Any]:
    config = AGENT_CONFIGS[agent_name]
    output_dir = (args.output_dir or ROOT / "outputs" / "live").resolve()
    if output_dir.exists() and not args.no_clean:
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    data, runtime = fetch_data(agent_name, args)
    profile = table_profile(data)
    missing = [table for table in config["required_tables"] if not data.get(table)]
    if missing:
        raise RuntimeError(f"Pandadata returned no rows for required tables: {', '.join(missing)}")

    charts_dir = output_dir / "charts"
    scorecard, state, risk_level = build_scorecard(agent_name, data)
    charts = save_agent_charts(agent_name, data, scorecard, charts_dir)
    decision_rows = make_decision_rows(state, risk_level)
    monitoring_rows = make_monitoring_rows(config, scorecard)

    snapshot = {
        "agent": agent_name,
        "title_zh": config["title_zh"],
        "title_en": config["title_en"],
        "category": config["category"],
        "state": state,
        "risk_level": risk_level,
        "decision_question": config["question"],
        "primary_watch_focus": config["watch_focus"],
        "scorecard": scorecard,
        "data_source": "Pandadata",
        "date_windows": runtime.get("date_windows", {}),
        "quality_status": "pass",
    }
    write_json(output_dir / "agent_snapshot.json", snapshot)
    write_json(output_dir / config["scorecard_file"], scorecard)
    write_json(output_dir / "alert_rules.json", make_alert_rules(state))
    write_csv(output_dir / "scorecard_metrics.csv", scorecard_rows(scorecard))
    write_csv(output_dir / "data_dictionary.csv", [
        {
            "table": table,
            "rows": info["rows"],
            "columns": ", ".join(info["columns"]),
            "source": "Pandadata",
            "usage": "支持本 Agent 的状态判断、图表或观察清单",
        }
        for table, info in profile.items()
    ])
    write_csv(output_dir / "decision_matrix.csv", decision_rows)
    write_csv(output_dir / "monitoring_checklist.csv", monitoring_rows)
    write_extra_files(agent_name, output_dir, data, scorecard)
    write_text(output_dir / config["memo_file"], f"# {config['title_zh']} 简报\n\n- 当前状态：{state}\n- 风险关注：{risk_level}\n- 核心问题：{config['question']}\n- 核心观察：{config['watch_focus']}\n")
    write_text(output_dir / "research_journal_template.md", f"# {config['title_zh']} 研究日志\n\n## 本次触发原因\n\n## 支持证据\n\n## 反证证据\n\n## 下一次重跑条件\n\n")
    write_text(output_dir / "handoff_card.md", f"# {config['title_zh']} 交接卡\n\n- Agent: `{agent_name}`\n- 当前状态：{state}\n- 风险关注：{risk_level}\n- 研究问题：{config['question']}\n- 下一步：查看 `report.html`、`decision_matrix.csv` 和 `monitoring_checklist.csv`。\n")
    write_text(output_dir / "operator_runbook.md", "1. 设置 Pandadata 账号环境变量。\n2. 运行 `py -3.10 scripts/run_pandadata_live.py`。\n3. 打开 `outputs/live/report.html`。\n4. 用 `scripts/agent_package.py validate` 复核公开产物。\n")
    write_text(output_dir / "deliverable_index.md", "\n".join([
        f"# {config['title_zh']} 输出索引",
        "",
        "- `report.html`: 图文报告",
        "- `agent_snapshot.json`: 机器可读快照",
        "- `decision_matrix.csv`: 情景和动作矩阵",
        "- `monitoring_checklist.csv`: 下一轮观察清单",
        "- `research_journal_template.md`: 研究日志模板",
        "- `handoff_card.md`: 交接卡",
    ]))
    write_report(output_dir, config, scorecard, state, risk_level, charts, runtime, profile)

    summary = {
        "ok": True,
        "agent": agent_name,
        "output_dir": public_path(output_dir),
        "data_source": "Pandadata",
        "tables": profile,
        "charts": charts,
        "report": public_path(output_dir / "report.html"),
    }
    write_json(output_dir / "run_summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run this QuantSkills Agent from live Pandadata data.")
    parser.add_argument("--agent", default=ROOT.name, choices=sorted(AGENT_CONFIGS), help="Agent name. Defaults to the repository folder name.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Output directory. Defaults to outputs/live.")
    parser.add_argument("--no-clean", action="store_true", help="Do not remove the existing output directory before writing.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Pandadata base URL.")
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL, help="A-share symbol used by stock-oriented monitors.")
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    parser.add_argument("--option-date", default=DEFAULT_OPTION_DATE)
    parser.add_argument("--option-underlying", default="510300.SH")
    parser.add_argument("--option-period", type=int, default=30)
    parser.add_argument("--future-symbols", default="RB,JM,A")
    parser.add_argument("--future-start-date", default="20250108")
    parser.add_argument("--future-end-date", default="20250427")
    args = parser.parse_args()

    summary = generate(args.agent, args)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

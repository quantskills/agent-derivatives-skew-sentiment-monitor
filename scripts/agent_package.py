from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_TERMS = [
    "DEFAULT" + "_" + "PASSWORD",
    "DEFAULT" + "_" + "USERNAME",
    "gate" + "_" + "report",
    "gate" + "_" + "status",
    "Gate " + "Status",
    "gated " + "deliverables",
    "declared " + "deliverables",
    "Generated from live " + "Pandadata calls",
    "SS" + "Quant",
    "Q" + "lib",
]
REQUIRED_ROOT_FILES = ["AGENTS.md", "README.md", "README.en.md", "LICENSE"]
REQUIRED_REFERENCES = [
    "references/methodology.md",
    "references/data-and-outputs.md",
    "references/agent-boundary.md",
]
REQUIRED_OUTPUTS = [
    "report.html",
    "agent_snapshot.json",
    "alert_rules.json",
    "decision_matrix.csv",
    "monitoring_checklist.csv",
    "research_journal_template.md",
    "handoff_card.md",
    "data_dictionary.csv",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


def read_csv(path: Path, limit: int | None = None) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return rows[:limit] if limit else rows


def public_files(root: Path) -> list[Path]:
    ignored_parts = {".git", "__pycache__"}
    suffixes = {".md", ".yaml", ".yml", ".json", ".csv", ".html", ".txt", ".gitignore", ".gitattributes"}
    out: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in ignored_parts for part in path.parts):
            continue
        if path.name == "LICENSE" or path.suffix in suffixes or path.name in {"AGENTS.md", "README.md", "README.en.md"}:
            out.append(path)
    return out


def validate(root: Path, output_dir: Path) -> dict[str, Any]:
    errors: list[str] = []
    for rel in REQUIRED_ROOT_FILES:
        if not (root / rel).exists():
            errors.append(f"missing {rel}")
    for rel in REQUIRED_REFERENCES:
        if not (root / rel).exists():
            errors.append(f"missing {rel}")
    for rel in REQUIRED_OUTPUTS:
        if not (output_dir / rel).exists():
            errors.append(f"missing outputs/live/{rel}")
    internal_validation_name = "gate" + "_" + "report" + ".json"
    if (output_dir / internal_validation_name).exists():
        errors.append(f"internal file must not be public: outputs/live/{internal_validation_name}")
    if (output_dir / "evidence.json").exists():
        errors.append("internal file must not be public: outputs/live/evidence.json")
    charts = sorted((output_dir / "charts").glob("*.png")) if (output_dir / "charts").exists() else []
    if len(charts) < 3:
        errors.append(f"expected at least 3 chart png files, found {len(charts)}")

    agent_md = read_text(root / "AGENTS.md") if (root / "AGENTS.md").exists() else ""
    for fragment in [
        "organization: QuantSkills",
        "organization_url: https://github.com/quantskills",
        "project_type: agent",
        "status: active",
        "validation_level: verified",
        "Reference Documents",
        "Pandadata Methods",
        "Boundary",
    ]:
        if fragment not in agent_md:
            errors.append(f"AGENTS.md missing fragment: {fragment}")
    if not re.search(r"description:\s*[\"'].*Use when", agent_md, flags=re.IGNORECASE | re.DOTALL):
        errors.append("AGENTS.md description should contain a clear Use when trigger")

    for path in public_files(root):
        if path.name == "LICENSE":
            continue
        text = read_text(path)
        for term in FORBIDDEN_TERMS:
            if term in text:
                errors.append(f"forbidden term {term!r} in {path.relative_to(root).as_posix()}")

    return {
        "status": "pass" if not errors else "fail",
        "repo": root.name,
        "output_dir": output_dir.relative_to(root).as_posix() if output_dir.is_relative_to(root) else str(output_dir),
        "chart_count": len(charts),
        "errors": errors,
    }


def summarize(root: Path, output_dir: Path, brief_path: Path | None) -> dict[str, Any]:
    snapshot = read_json(output_dir / "agent_snapshot.json")
    scorecard_paths = sorted(output_dir.glob("*scorecard.json"))
    scorecard = read_json(scorecard_paths[0]) if scorecard_paths else {}
    decision_rows = read_csv(output_dir / "decision_matrix.csv", limit=8)
    watch_rows = read_csv(output_dir / "monitoring_checklist.csv", limit=8)
    data_rows = read_csv(output_dir / "data_dictionary.csv")
    charts = sorted(path.relative_to(root).as_posix() for path in (output_dir / "charts").glob("*.png"))
    result = {
        "agent": snapshot.get("agent", root.name),
        "title": snapshot.get("title_zh") or snapshot.get("title_en") or root.name,
        "state": snapshot.get("state"),
        "risk_level": snapshot.get("risk_level"),
        "decision_question": snapshot.get("decision_question"),
        "watch_focus": snapshot.get("primary_watch_focus"),
        "pandadata_methods": re.findall(r"`([^`]+)`", read_text(root / "AGENTS.md").split("## Pandadata Methods", 1)[-1]),
        "scorecard": scorecard,
        "charts": charts,
        "decision_rows": decision_rows,
        "watch_rows": watch_rows,
        "data_tables": data_rows,
        "report": (output_dir / "report.html").relative_to(root).as_posix() if (output_dir / "report.html").exists() else None,
    }
    if brief_path:
        lines = [
            f"# {result['title']} Brief",
            "",
            f"- Agent: `{result['agent']}`",
            f"- State: `{result.get('state')}`",
            f"- Risk level: `{result.get('risk_level')}`",
            f"- Question: {result.get('decision_question')}",
            f"- Watch focus: {result.get('watch_focus')}",
            f"- Report: `{result.get('report')}`",
            "",
            "## Charts",
            "",
        ]
        lines.extend(f"- `{chart}`" for chart in charts)
        lines.extend(["", "## Next Decision Rows", ""])
        for row in decision_rows[:4]:
            lines.append("- " + " | ".join(f"{key}: {value}" for key, value in row.items() if value))
        brief_path.parent.mkdir(parents=True, exist_ok=True)
        brief_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        result["brief_written"] = str(brief_path)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and summarize this QuantSkills Agent package.")
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root. Defaults to this script's parent repo.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Agent output directory. Defaults to <root>/outputs/live.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="Validate public package structure and content.")
    summarize_parser = sub.add_parser("summarize", help="Summarize outputs/live as JSON and optionally write a Markdown brief.")
    summarize_parser.add_argument("--brief", type=Path, default=None, help="Optional Markdown brief path to write.")
    args = parser.parse_args()

    root = args.root.resolve()
    output_dir = (args.output_dir or root / "outputs" / "live").resolve()
    if args.command == "validate":
        result = validate(root, output_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "pass" else 1
    result = summarize(root, output_dir, args.brief)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

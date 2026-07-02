from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schemas import AgentCallRecord, Artifact, Task


def write_outputs(task: Task, modeling_result: dict[str, Any], mesa_result: dict[str, Any], agent_results: dict[str, Any], calls: list[AgentCallRecord], error: str | None = None) -> tuple[str, str]:
    status = "failed" if error else "completed"
    report_path = Path("reports/archive") / f"{task.task_id}.md"
    latest_report = Path("reports/latest_report.md")
    artifact_path = Path("artifacts/archive") / f"{task.task_id}.json"
    latest_artifact = Path("artifacts/latest_result.json")
    for p in [report_path.parent, artifact_path.parent, latest_report.parent, latest_artifact.parent]:
        p.mkdir(parents=True, exist_ok=True)
    cost_usd = round(sum(call.cost_usd for call in calls), 8)
    artifact = Artifact(task_id=task.task_id, status=status, modeling_result=modeling_result, mesa_result=mesa_result, agent_results=agent_results, calls=calls, cost_usd=cost_usd, error=error)
    artifact_json = artifact.model_dump_json(indent=2)
    artifact_path.write_text(artifact_json, encoding="utf-8")
    latest_artifact.write_text(artifact_json, encoding="utf-8")
    report = render_report(task, modeling_result, mesa_result, agent_results, calls, cost_usd, error)
    report_path.write_text(report, encoding="utf-8")
    latest_report.write_text(report, encoding="utf-8")
    return str(report_path), str(artifact_path)


def render_report(task: Task, modeling_result: dict[str, Any], mesa_result: dict[str, Any], agent_results: dict[str, Any], calls: list[AgentCallRecord], cost_usd: float, error: str | None = None) -> str:
    judge = agent_results.get("judge", {})
    parts = [
        "# Core conclusion", judge.get("summary", "Use reversible, low-cost options first."), "",
        "# Task summary", f"- task_id: `{task.task_id}`", f"- task_type: `{task.task_type}`", f"- question: {task.question}", "",
        "# GPT modeling result", _json_block(modeling_result), "",
        "# Key variables", _bullets(modeling_result.get("variables", [])), "",
        "# Key assumptions", _bullets(modeling_result.get("assumptions", [])), "",
        "# Causal chain", _bullets(modeling_result.get("causal_chain", [])), "",
        "# Scenario tree", _json_block(modeling_result.get("scenario_tree", {})), "",
        "# Mesa enabled", _json_block(modeling_result.get("mesa_recommendation", {})), "",
        "# Mesa result", _json_block(mesa_result), "",
        "# Red-team review", _json_block(agent_results.get("red_team", {})), "",
        "# Stop conditions", "- Stop when trial evidence is below the baseline.", "- Stop when cost, fatigue, or operational risk rises above tolerance.", "",
        "# Uncertainty", _bullets(modeling_result.get("uncertainties", [])), "",
        "# Cost and call records", f"- total_cost_usd: `{cost_usd}`", _json_block([call.model_dump() for call in calls]), "",
        "# Final judgment", _json_block(judge),
    ]
    if error:
        parts.extend(["", "# Failure reason", error])
    return "\n".join(parts) + "\n"


def _json_block(value: Any) -> str:
    return "```json\n" + json.dumps(value, ensure_ascii=False, indent=2) + "\n```"


def _bullets(value: Any) -> str:
    if not value:
        return "- None"
    lines = []
    for item in value:
        if isinstance(item, dict):
            label = item.get("name") or item.get("risk") or item.get("option") or "item"
            desc = item.get("description") or item.get("control") or ""
            lines.append(f"- **{label}**: {desc}" if desc else f"- {json.dumps(item, ensure_ascii=False)}")
        else:
            lines.append(f"- {item}")
    return "\n".join(lines)

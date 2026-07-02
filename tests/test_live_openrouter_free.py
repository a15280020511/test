import json
import os
from pathlib import Path

from hebc_lite.agents import run_expert_panel
from hebc_lite.gpt_modeling import build_modeling_result
from hebc_lite.mesa_runner import run_mesa
from hebc_lite.report_writer import write_outputs
from hebc_lite.schemas import Task


def test_fullflow():
    assert os.getenv("OPENROUTER_API_KEY")
    task = Task.model_validate({
        "task_id": "fullflow_20260702",
        "task_type": "simulation",
        "question": "Full-flow test: choose a low-cost local side-income trial among delivery options and baseline under competition, fatigue, risk, and exit cost.",
        "background": {"city": "Fuzhou", "options": ["food", "grocery", "parcel", "baseline"], "simulation": "workers compete for limited orders"},
        "constraints": {"avoid": ["high deposit", "sleep damage", "high risk"], "must_have": ["ranking", "red_team", "mesa", "trial_plan"]},
        "modeling": {"use_gpt_modeling": True, "use_mesa": True, "mesa_reason": "workers compete for limited local orders"},
    })
    model_cfg = {
        "budget": {"test_mode": False, "allow_paid_models": True, "allow_expensive_models": False, "max_cost_usd_per_task": 0.05, "max_calls_per_task": 3},
        "model_pool": {"strong_reasoning": ["deepseek/deepseek-v4-flash"], "low_cost": ["deepseek/deepseek-v4-flash"], "red_team": ["deepseek/deepseek-v4-flash"]},
        "fallback": {"on_model_unavailable": "continue"}
    }
    mesa_cfg = {"mesa": {"require_explicit_reason": True, "timeout_seconds": 60, "default_steps": 40, "default_agents": 30, "random_seed": 42}}
    roles = ["planner", "red_team", "judge"]
    agent_results, calls = run_expert_panel(task, roles, model_cfg)
    modeling_result = build_modeling_result(task, mesa_needed=True, mesa_reason=task.modeling.mesa_reason)
    mesa_result = run_mesa(task, modeling_result, mesa_cfg, mesa_needed=True, mesa_reason=task.modeling.mesa_reason)
    report_path, artifact_path = write_outputs(task, modeling_result, mesa_result, agent_results, calls)
    Path("reports/fullflow_report.md").write_text(Path(report_path).read_text(encoding="utf-8"), encoding="utf-8")
    Path("artifacts/fullflow_result.json").write_text(Path(artifact_path).read_text(encoding="utf-8"), encoding="utf-8")
    Path("artifacts/fullflow_summary.json").write_text(json.dumps({"calls": [c.model_dump() for c in calls], "mesa": mesa_result}, ensure_ascii=False, indent=2), encoding="utf-8")
    assert len(calls) == 3
    assert all(c.model == "deepseek/deepseek-v4-flash" for c in calls)
    assert any(c.status == "ok" for c in calls)
    assert mesa_result.get("status") == "completed"

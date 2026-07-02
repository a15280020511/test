import json
import os
from pathlib import Path

from hebc_lite.agents import run_expert_panel
from hebc_lite.gpt_modeling import build_modeling_result
from hebc_lite.mesa_runner import run_mesa_if_needed
from hebc_lite.report_writer import write_outputs
from hebc_lite.schemas import Task


def test_live_fuzhou_work_options_report():
    assert os.getenv("OPENROUTER_API_KEY"), "OPENROUTER_API_KEY is missing in GitHub Actions secrets"
    task = Task.model_validate({
        "task_id": "fuzhou_work_options_20260702",
        "task_type": "decision_modeling",
        "question": "In Fuzhou, compare four practical income options: ride hailing driver, parcel courier, Pupu grocery delivery, and food delivery. Give a practical recommendation for a low-cost, low-maintenance, reversible trial.",
        "background": {
            "city": "Fuzhou",
            "current_context": "night shift security work; wants better income without high sunk cost",
            "options": ["ride_hailing", "parcel_courier", "pupu_delivery", "food_delivery"],
            "hard_preferences": ["low upfront cost", "low maintenance", "stable", "reversible", "avoid severe physical damage", "avoid high compliance or vehicle risk"],
            "local_notes": [
                "Ride hailing requires vehicle and driver compliance; vehicle depreciation and charging or fuel downtime matter.",
                "Pupu originated in Fuzhou and uses front-warehouse grocery delivery model.",
                "Food delivery has flexible entry but high traffic and weather risk.",
                "Parcel courier may be steadier but route/station dependency and parcel volume matter."
            ]
        },
        "constraints": {
            "avoid": ["high deposit", "large vehicle investment", "unclear platform penalties", "sleep damage", "high accident exposure"],
            "must_have": ["net income after costs", "entry cost", "stability", "physical load", "compliance risk", "exit cost", "one-week trial plan"]
        },
        "modeling": {"use_gpt_modeling": True, "use_mesa": False, "mesa_reason": None},
        "outputs": ["core_conclusion", "ranking", "risk_analysis", "red_team", "trial_plan", "stop_conditions"]
    })
    cfg = {
        "budget": {
            "test_mode": False,
            "allow_paid_models": False,
            "allow_expensive_models": False,
            "max_cost_usd_per_task": 0.0,
            "max_calls_per_task": 5,
        },
        "model_pool": {
            "strong_reasoning": ["cohere/north-mini-code:free"],
            "low_cost": ["cohere/north-mini-code:free"],
            "red_team": ["cohere/north-mini-code:free"],
            "free_test": ["cohere/north-mini-code:free"]
        },
        "fallback": {"on_model_unavailable": "stop_and_report"},
    }
    modeling_result = build_modeling_result(task, {"force_mesa": False})
    mesa_result = run_mesa_if_needed(task, {}, modeling_result)
    roles = ["planner", "modeler", "red_team", "judge", "reporter"]
    agent_results, calls = run_expert_panel(task, roles, cfg, context={"modeling_result": modeling_result, "mesa_result": mesa_result})
    assert calls, "no model calls were made"
    assert all(call.provider == "openrouter" for call in calls)
    assert all(call.model.endswith(":free") for call in calls)
    assert all(call.cost_usd == 0.0 for call in calls)
    assert any(call.status == "ok" for call in calls), [call.model_dump() for call in calls]
    error = None if all(call.status == "ok" for call in calls) else "partial free-model result; inspect call records"
    report_path, artifact_path = write_outputs(task, modeling_result, mesa_result, agent_results, calls, error=error)
    Path("reports/fuzhou_work_options_summary.md").write_text(Path(report_path).read_text(encoding="utf-8"), encoding="utf-8")
    Path("artifacts/fuzhou_work_options_result.json").write_text(Path(artifact_path).read_text(encoding="utf-8"), encoding="utf-8")
    artifact = json.loads(Path(artifact_path).read_text(encoding="utf-8"))
    assert artifact["cost_usd"] == 0.0
    assert Path("reports/fuzhou_work_options_summary.md").exists()
    assert Path("artifacts/fuzhou_work_options_result.json").exists()

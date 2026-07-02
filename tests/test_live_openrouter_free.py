import json
import os
from pathlib import Path

from hebc_lite.agents import run_role
from hebc_lite.schemas import Task


def test_deepseek_local_work_options():
    assert os.getenv("OPENROUTER_API_KEY"), "OPENROUTER_API_KEY is missing"
    task = Task.model_validate({
        "task_id": "deepseek_work_options_20260702",
        "task_type": "decision_modeling",
        "question": "Analyze a Fuzhou side-income choice: ride-hailing driver, parcel courier, Pupu grocery delivery, or food delivery. Give a practical ranking and a one-week low-cost trial plan. Focus on net income after costs, entry cost, stability, physical load, compliance risk, accident exposure, exit cost, and fit for someone already working night security shifts.",
        "background": {
            "city": "Fuzhou",
            "current_context": "night security shift; wants higher income but low sunk cost and low maintenance",
            "options": ["ride_hailing", "parcel_courier", "pupu_grocery_delivery", "food_delivery"],
            "preferences": ["low upfront cost", "stable", "reversible", "avoid high accident exposure", "avoid severe fatigue", "avoid high vehicle cost"]
        },
        "constraints": {"avoid": ["large vehicle investment", "high deposit", "unclear penalties", "sleep damage"], "must_have": ["ranking", "trial plan", "stop conditions"]},
        "modeling": {"use_gpt_modeling": True, "use_mesa": False, "mesa_reason": None},
    })
    cfg = {
        "budget": {"test_mode": False, "allow_paid_models": True, "allow_expensive_models": False, "max_cost_usd_per_task": 0.02, "max_calls_per_task": 1},
        "model_pool": {"strong_reasoning": ["deepseek/deepseek-v4-flash"], "low_cost": ["deepseek/deepseek-v4-flash"], "red_team": ["deepseek/deepseek-v4-flash"]},
        "fallback": {"on_model_unavailable": "stop_and_report"},
    }
    result, record = run_role("judge", task, cfg)
    Path("reports").mkdir(exist_ok=True)
    Path("artifacts").mkdir(exist_ok=True)
    payload = {"task_id": task.task_id, "model_result": result, "call_record": record.model_dump(), "note": "DeepSeek live run through OpenRouter. Paid models allowed with cap 0.02 USD."}
    Path("artifacts/deepseek_work_options_result.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    Path("reports/deepseek_work_options_summary.md").write_text("# DeepSeek Work Options Result\n\n```json\n" + json.dumps(payload, ensure_ascii=False, indent=2) + "\n```\n", encoding="utf-8")
    assert record.provider == "openrouter"
    assert record.model == "deepseek/deepseek-v4-flash"
    assert record.status == "ok", payload

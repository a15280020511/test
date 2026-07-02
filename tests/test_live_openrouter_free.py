import os

from hebc_lite.agents import run_role
from hebc_lite.schemas import Task


def test_live_openrouter_free_model_smoke():
    assert os.getenv("OPENROUTER_API_KEY"), "OPENROUTER_API_KEY is missing in GitHub Actions secrets"
    task = Task.model_validate({
        "task_id": "live_free_smoke",
        "task_type": "decision_modeling",
        "question": "Return one concise JSON recommendation for a low-cost maintenance test.",
        "modeling": {"use_gpt_modeling": True, "use_mesa": False},
    })
    cfg = {
        "budget": {
            "test_mode": False,
            "allow_paid_models": False,
            "allow_expensive_models": False,
            "max_cost_usd_per_task": 0.0,
            "max_calls_per_task": 1,
        },
        "model_pool": {
            "strong_reasoning": ["cohere/north-mini-code:free"],
            "low_cost": ["cohere/north-mini-code:free"],
            "red_team": ["cohere/north-mini-code:free"],
        },
        "fallback": {"on_model_unavailable": "stop_and_report"},
    }
    result, record = run_role("planner", task, cfg)
    assert record.provider == "openrouter"
    assert record.model.endswith(":free")
    assert record.cost_usd == 0.0
    assert record.status == "ok", result
    assert result.get("mode") == "openrouter_free_model"
    assert result.get("cost_usd") == 0.0
    assert "summary" in result or "recommendation" in result


def test_live_openrouter_free_model_marker():
    assert "live-free-smoke".replace("-", "_") == "live_free_smoke"

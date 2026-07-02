from hebc_lite.agents import is_free_openrouter_model, run_role
from hebc_lite.health_check import validate_free_model_policy
from hebc_lite.schemas import Task


def test_free_model_suffix_required():
    assert is_free_openrouter_model("cohere/north-mini-code:free")
    assert not is_free_openrouter_model("openrouter:auto")


def test_live_free_policy_accepts_only_free_models():
    models = {
        "budget": {"test_mode": False, "allow_paid_models": False, "max_cost_usd_per_task": 0.0},
        "model_pool": {"strong_reasoning": ["cohere/north-mini-code:free"], "red_team": ["nvidia/nemotron-3-ultra-550b-a55b:free"]},
    }
    policy = {"require_free_suffix_for_live_tests": True, "blocked_defaults": ["openrouter:auto"]}
    result = validate_free_model_policy(models, policy)
    assert result["ok"] is True
    assert result["non_free_model_ids"] == []


def test_live_free_policy_rejects_openrouter_auto():
    models = {
        "budget": {"test_mode": False, "allow_paid_models": False, "max_cost_usd_per_task": 0.0},
        "model_pool": {"strong_reasoning": ["openrouter:auto"]},
    }
    policy = {"require_free_suffix_for_live_tests": True, "blocked_defaults": ["openrouter:auto"]}
    result = validate_free_model_policy(models, policy)
    assert result["ok"] is False
    assert "openrouter:auto" in result["blocked_defaults_present"]


def test_paid_model_blocked_before_network(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy")
    task = Task.model_validate({"task_id": "policy", "question": "test"})
    cfg = {
        "budget": {"test_mode": False, "allow_paid_models": False, "max_cost_usd_per_task": 0.0, "max_calls_per_task": 1},
        "model_pool": {"strong_reasoning": ["openrouter:auto"]},
    }
    result, record = run_role("planner", task, cfg)
    assert record.status == "failed"
    assert "Paid model blocked" in result["error"]

import pytest

from hebc_lite.orchestration import OrchestrationError, apply_webgpt_orchestration, model_for_role, validate_webgpt_orchestration
from hebc_lite.schemas import Task


def make_task(extra=None):
    payload = {
        "task_id": "orch_test",
        "task_type": "analysis",
        "question": "test",
    }
    if extra:
        payload.update(extra)
    return Task.model_validate(payload)


def test_webgpt_orchestration_supplies_roles_and_models():
    task = make_task({
        "orchestration": {
            "strict": True,
            "roles": ["planner", "red_team", "judge"],
            "models": {
                "planner": "deepseek/deepseek-v4-flash",
                "red_team": "anthropic/claude-sonnet-4.5",
                "judge": "openai/gpt-5.5-thinking"
            },
            "budget": {"test_mode": True, "max_calls_per_task": 3},
            "tool_plan": {"gpt_modeling": True, "mesa": False}
        }
    })
    merged, roles, validation = apply_webgpt_orchestration(task, {"budget": {}, "model_pool": {}})
    assert validation["mode"] == "webgpt_orchestrated"
    assert roles == ["planner", "red_team", "judge"]
    assert model_for_role("planner", merged) == "deepseek/deepseek-v4-flash"
    assert model_for_role("red_team", merged) == "anthropic/claude-sonnet-4.5"
    assert merged["budget"]["max_calls_per_task"] == 3


def test_webgpt_orchestration_rejects_missing_role_model():
    task = make_task({"orchestration": {"roles": ["planner", "judge"], "models": {"planner": "m1"}}})
    with pytest.raises(OrchestrationError):
        validate_webgpt_orchestration(task)


def test_orchestration_fallback_when_absent():
    task = make_task()
    merged, roles, validation = apply_webgpt_orchestration(task, {"roles": {"planner": {}, "judge": {}}, "budget": {}, "model_pool": {}})
    assert validation["mode"] == "config_fallback"
    assert roles
    assert merged["model_pool"] == {}

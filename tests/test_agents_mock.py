from hebc_lite.agents import run_expert_panel
from hebc_lite.schemas import Task


def test_agents_mock_zero_cost(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    task = Task.model_validate({"task_id": "t1", "question": "how to choose?"})
    cfg = {"budget": {"test_mode": True, "allow_paid_models": False, "max_cost_usd_per_task": 0.0, "max_calls_per_task": 5}}
    results, calls = run_expert_panel(task, ["planner", "red_team", "judge", "reporter"], cfg)
    assert set(results) == {"planner", "red_team", "judge", "reporter"}
    assert all(call.cost_usd == 0.0 for call in calls)
    assert all(call.provider == "mock" for call in calls)

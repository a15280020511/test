from hebc_lite.mesa_runner import run_mesa
from hebc_lite.schemas import Task


def test_mesa_default_not_run():
    task = Task.model_validate({"task_id": "t1", "question": "ordinary case"})
    result = run_mesa(task, {}, {"mesa": {"enabled": False}}, mesa_needed=False)
    assert result["enabled"] is False


def test_mesa_missing_package_is_explicit_failure(monkeypatch):
    import importlib.util

    original = importlib.util.find_spec

    def fake_find_spec(name):
        if name == "mesa":
            return None
        return original(name)

    monkeypatch.setattr(importlib.util, "find_spec", fake_find_spec)
    task = Task.model_validate({"task_id": "t2", "question": "ordinary case", "modeling": {"use_mesa": True, "mesa_reason": "explicit reason"}})
    result = run_mesa(task, {}, {"mesa": {"timeout_seconds": 1, "default_steps": 1, "default_agents": 2, "require_explicit_reason": True}}, mesa_needed=True, mesa_reason="explicit reason")
    assert result["enabled"] is True
    assert result["status"] == "failed"
    assert "not importable" in result["error"]

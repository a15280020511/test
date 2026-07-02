from hebc_lite.router import decide_need_mesa
from hebc_lite.schemas import Task


def test_mesa_default_closed():
    task = Task.model_validate({"task_id": "t1", "question": "ordinary job choice"})
    enabled, reason = decide_need_mesa(task, {"routing": {"mesa": {"enabled": False}}})
    assert enabled is False
    assert reason is None


def test_mesa_requires_explicit_reason_when_requested():
    task = Task.model_validate({"task_id": "t2", "question": "platform allocation case", "modeling": {"use_mesa": True}})
    enabled, reason = decide_need_mesa(task, {"routing": {"mesa": {"enabled": False}}})
    assert enabled is False
    assert "missing" in reason


def test_mesa_explicit_reason_enabled():
    task = Task.model_validate({"task_id": "t3", "question": "platform allocation case", "modeling": {"use_mesa": True, "mesa_reason": "many agents share limited requests"}})
    enabled, reason = decide_need_mesa(task, {"routing": {"mesa": {"enabled": False}}})
    assert enabled is True
    assert reason == "many agents share limited requests"

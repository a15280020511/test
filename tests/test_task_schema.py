import pytest
from pydantic import ValidationError

from hebc_lite.schemas import Task


def test_task_schema_accepts_valid_task():
    task = Task.model_validate({"task_id": "abc_123-x", "task_type": "decision_modeling", "question": "test question"})
    assert task.task_id == "abc_123-x"
    assert task.modeling.use_gpt_modeling is True


def test_task_schema_rejects_bad_task_id():
    with pytest.raises(ValidationError):
        Task.model_validate({"task_id": "bad/id", "task_type": "decision_modeling", "question": "x"})


def test_task_schema_rejects_empty_question():
    with pytest.raises(ValidationError):
        Task.model_validate({"task_id": "ok", "task_type": "decision_modeling", "question": "  "})

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

_TASK_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


class TaskModelingConfig(BaseModel):
    use_gpt_modeling: bool = True
    use_mesa: bool = False
    mesa_reason: str | None = None

    @field_validator("mesa_reason")
    @classmethod
    def clean_mesa_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class TaskConstraints(BaseModel):
    avoid: list[str] = Field(default_factory=list)
    must_have: list[str] = Field(default_factory=list)


class Task(BaseModel):
    model_config = ConfigDict(extra="allow")

    task_id: str
    task_type: str = "decision_modeling"
    question: str
    background: dict[str, Any] = Field(default_factory=dict)
    constraints: TaskConstraints = Field(default_factory=TaskConstraints)
    modeling: TaskModelingConfig = Field(default_factory=TaskModelingConfig)
    outputs: list[str] = Field(default_factory=list)

    @field_validator("task_id")
    @classmethod
    def validate_task_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("task_id must not be empty")
        if not _TASK_ID_RE.fullmatch(value):
            raise ValueError("task_id may only contain letters, numbers, underscore, and hyphen")
        return value

    @field_validator("task_type")
    @classmethod
    def validate_task_type(cls, value: str) -> str:
        value = value.strip()
        allowed = {"decision_modeling", "simulation", "analysis", "red_team", "health_check"}
        if value not in allowed:
            raise ValueError(f"unsupported task_type: {value}")
        return value

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("question must not be empty")
        return value


JobStatusValue = Literal["queued", "running", "waiting", "failed", "completed", "cancelled", "stuck"]


class JobStatus(BaseModel):
    job_id: str
    task_id: str | None = None
    status: JobStatusValue
    stage: str
    progress: float = Field(ge=0.0, le=1.0)
    task_file: str | None = None
    report_path: str | None = None
    artifact_path: str | None = None
    started_at: str | None = None
    updated_at: str
    error: str | None = None


class AgentCallRecord(BaseModel):
    role: str
    provider: str = "mock"
    model: str = "mock"
    status: Literal["ok", "failed", "skipped"] = "ok"
    cost_usd: float = 0.0
    error: str | None = None


class Artifact(BaseModel):
    task_id: str
    status: Literal["completed", "failed", "partial"]
    modeling_result: dict[str, Any] = Field(default_factory=dict)
    mesa_result: dict[str, Any] = Field(default_factory=dict)
    agent_results: dict[str, Any] = Field(default_factory=dict)
    calls: list[AgentCallRecord] = Field(default_factory=list)
    cost_usd: float = 0.0
    error: str | None = None

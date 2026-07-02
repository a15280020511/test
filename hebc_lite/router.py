from __future__ import annotations

from typing import Any

from .schemas import Task

MESA_KEYWORDS = {
    "multi-agent", "multi agent", "competition", "dispatch", "platform", "market",
    "spatial", "congestion", "ecosystem", "driver", "rider", "order allocation",
}


def _task_text(task: Task) -> str:
    parts = [task.question, task.task_type]
    parts.extend(map(str, task.background.values()))
    parts.extend(task.constraints.avoid)
    parts.extend(task.constraints.must_have)
    return "\n".join(parts).lower()


def decide_need_gpt_modeling(task: Task, routing_config: dict[str, Any]) -> bool:
    defaults = routing_config.get("defaults", {})
    routing = routing_config.get("routing", {})
    gpt = routing.get("gpt_modeling", {})
    return bool(task.modeling.use_gpt_modeling and gpt.get("enabled", defaults.get("enable_gpt_modeling", True)))


def decide_need_mesa(task: Task, routing_config: dict[str, Any]) -> tuple[bool, str | None]:
    explicit_reason = task.modeling.mesa_reason
    if task.modeling.use_mesa:
        if not explicit_reason:
            return False, "Mesa requested but mesa_reason is missing."
        return True, explicit_reason

    routing = routing_config.get("routing", {})
    mesa_cfg = routing.get("mesa", {})
    if not mesa_cfg.get("enabled", False):
        return False, None

    text = _task_text(task)
    matched = sorted(k for k in MESA_KEYWORDS if k in text)
    if not matched:
        return False, None

    if mesa_cfg.get("requires_explicit_reason", True):
        return True, f"Route matched Mesa keywords: {', '.join(matched[:5])}."
    return True, None


def decide_model_roles(task: Task, models_config: dict[str, Any]) -> list[str]:
    roles = models_config.get("roles", {})
    default = ["planner", "red_team", "judge", "reporter"]
    selected = [role for role in default if role in roles]
    if task.task_type in {"simulation", "decision_modeling"} and "modeler" in roles:
        selected.insert(1, "modeler")
    return selected or default

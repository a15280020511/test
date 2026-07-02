from __future__ import annotations

from copy import deepcopy
from typing import Any

from .schemas import Task


class OrchestrationError(ValueError):
    pass


def get_webgpt_orchestration(task: Task) -> dict[str, Any]:
    extra = getattr(task, "model_extra", {}) or {}
    value = extra.get("orchestration") or {}
    if not isinstance(value, dict):
        raise OrchestrationError("orchestration must be an object supplied by WebGPT")
    return value


def validate_webgpt_orchestration(task: Task) -> dict[str, Any]:
    orch = get_webgpt_orchestration(task)
    strict = bool(orch.get("strict", False))
    if not orch and strict:
        raise OrchestrationError("strict orchestration requested but orchestration is empty")
    if not orch:
        return {"ok": True, "mode": "config_fallback", "warnings": ["No WebGPT orchestration supplied; using config fallback."]}

    roles = orch.get("roles")
    models = orch.get("models")
    tool_plan = orch.get("tool_plan", {})
    budget = orch.get("budget", {})
    errors: list[str] = []
    if not isinstance(roles, list) or not roles:
        errors.append("orchestration.roles must be a non-empty list")
    if not isinstance(models, dict) or not models:
        errors.append("orchestration.models must map role names to model ids")
    if roles and models:
        missing = [role for role in roles if role not in models]
        if missing:
            errors.append("orchestration.models is missing roles: " + ", ".join(missing))
    if not isinstance(tool_plan, dict):
        errors.append("orchestration.tool_plan must be an object")
    if not isinstance(budget, dict):
        errors.append("orchestration.budget must be an object")
    if errors:
        raise OrchestrationError("; ".join(errors))
    return {"ok": True, "mode": "webgpt_orchestrated", "roles": roles, "tool_plan": tool_plan, "budget": budget}


def apply_webgpt_orchestration(task: Task, models_config: dict[str, Any]) -> tuple[dict[str, Any], list[str], dict[str, Any]]:
    orch = get_webgpt_orchestration(task)
    validation = validate_webgpt_orchestration(task)
    merged = deepcopy(models_config)
    if not orch:
        roles = _fallback_roles(merged)
        return merged, roles, validation

    roles = list(orch.get("roles", []))
    role_models = orch.get("models", {})
    pool: dict[str, list[str]] = {}
    for role in roles:
        model_id = role_models[role]
        pool[role] = [model_id]
    # keep legacy pools for old picker compatibility
    if "planner" in pool:
        pool["strong_reasoning"] = pool["planner"]
    if "red_team" in pool:
        pool["red_team"] = pool["red_team"]
    if "reporter" in pool:
        pool["low_cost"] = pool["reporter"]
    if "judge" in pool:
        pool["judge"] = pool["judge"]
    merged["model_pool"] = {**merged.get("model_pool", {}), **pool}
    merged["budget"] = {**merged.get("budget", {}), **orch.get("budget", {})}
    merged["fallback"] = {**merged.get("fallback", {}), **orch.get("fallback", {})}
    merged["webgpt_orchestration"] = orch
    return merged, roles, validation


def model_for_role(role: str, models_config: dict[str, Any]) -> str | None:
    orch = models_config.get("webgpt_orchestration") or {}
    models = orch.get("models") or {}
    if role in models:
        return str(models[role])
    return None


def tool_plan_for(task: Task) -> dict[str, Any]:
    orch = get_webgpt_orchestration(task)
    plan = orch.get("tool_plan") or {}
    return plan if isinstance(plan, dict) else {}


def _fallback_roles(models_config: dict[str, Any]) -> list[str]:
    roles = models_config.get("roles", {})
    default = ["planner", "red_team", "judge", "reporter"]
    selected = [role for role in default if role in roles]
    if "modeler" in roles:
        selected.insert(1, "modeler")
    return selected or default

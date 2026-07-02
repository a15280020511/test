from __future__ import annotations

import os
from typing import Any

from .schemas import AgentCallRecord, Task

_SAFE_MOCK_OUTPUTS = {
    "planner": {"summary": "Task decomposed into variables, constraints, risks, and stop-loss rules.", "next_stage": "gpt_modeling"},
    "modeler": {"summary": "Use structural variables and scenario trees before any numerical simulation.", "next_stage": "router"},
    "red_team": {"summary": "Key objections: missing real costs, unstable demand, compliance limits, and physical load.", "objections": ["Return may be overestimated", "Hidden cost may be underestimated", "Sleep loss may change the conclusion"]},
    "judge": {"summary": "Default to low-sunk-cost, reversible, stop-loss-first options.", "confidence": "medium"},
    "reporter": {"summary": "Report should keep conclusion, variables, assumptions, red-team objections, stop-loss, and call records.", "format": "markdown"},
}


def has_openrouter_key() -> bool:
    return bool(os.getenv("OPENROUTER_API_KEY"))


def is_zero_spend_mode(models_config: dict[str, Any]) -> bool:
    budget = models_config.get("budget", {})
    return bool(
        budget.get("test_mode", True)
        or not budget.get("allow_paid_models", False)
        or float(budget.get("max_cost_usd_per_task", 0.0)) <= 0.0
    )


def run_role(role: str, task: Task, models_config: dict[str, Any], context: dict[str, Any] | None = None) -> tuple[dict[str, Any], AgentCallRecord]:
    context = context or {}
    budget = models_config.get("budget", {})
    if is_zero_spend_mode(models_config):
        output = dict(_SAFE_MOCK_OUTPUTS.get(role, {"summary": f"mock result for {role}"}))
        output.update({"role": role, "mode": "test_mode_mock", "cost_usd": 0.0})
        return output, AgentCallRecord(role=role, provider="mock", model="mock", status="ok", cost_usd=0.0)

    if not has_openrouter_key():
        err = "OPENROUTER_API_KEY missing; real OpenRouter call skipped."
        return {"role": role, "status": "failed", "error": err}, AgentCallRecord(role=role, provider="openrouter", model="openrouter:auto", status="failed", error=err)

    if float(budget.get("max_cost_usd_per_task", 0.0)) <= 0.0:
        err = "max_cost_usd_per_task is zero; real call blocked."
        return {"role": role, "status": "failed", "error": err}, AgentCallRecord(role=role, provider="openrouter", model="openrouter:auto", status="failed", error=err)

    return _run_pydantic_ai_role(role, task, models_config, context)


def run_expert_panel(task: Task, roles: list[str], models_config: dict[str, Any], context: dict[str, Any] | None = None) -> tuple[dict[str, Any], list[AgentCallRecord]]:
    results: dict[str, Any] = {}
    calls: list[AgentCallRecord] = []
    max_calls = int(models_config.get("budget", {}).get("max_calls_per_task", 5))
    for role in roles[:max_calls]:
        result, record = run_role(role, task, models_config, context={**(context or {}), "previous_results": results})
        results[role] = result
        calls.append(record)
        if record.status == "failed" and models_config.get("fallback", {}).get("on_model_unavailable") == "stop_and_report":
            break
    return results, calls


def _run_pydantic_ai_role(role: str, task: Task, models_config: dict[str, Any], context: dict[str, Any]) -> tuple[dict[str, Any], AgentCallRecord]:
    """OpenRouter adapter through Pydantic AI.

    This path is isolated from tests and zero-spend mode. It never prints the API key and reports failures explicitly.
    """
    model_name = _pick_model(role, models_config)
    try:
        from pydantic_ai import Agent
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.openai import OpenAIProvider
    except Exception as exc:  # pragma: no cover
        err = f"pydantic_ai import failed: {type(exc).__name__}: {exc}"
        return {"role": role, "status": "failed", "error": err}, AgentCallRecord(role=role, provider="openrouter", model=model_name, status="failed", error=err)

    try:  # pragma: no cover
        provider = OpenAIProvider(base_url="https://openrouter.ai/api/v1", api_key=os.environ["OPENROUTER_API_KEY"])
        model = OpenAIChatModel(model_name.replace("openrouter:", ""), provider=provider)
        agent = Agent(model, system_prompt=_system_prompt_for(role), output_type=dict)
        prompt = {
            "task": task.model_dump(),
            "role": role,
            "context": context,
            "required": "Return strict structured JSON with summary, reasoning_basis, risks, and decision fields.",
        }
        result = agent.run_sync(str(prompt))
        output = result.output if hasattr(result, "output") else result.data
        if not isinstance(output, dict):
            output = {"summary": str(output)}
        output["role"] = role
        output["mode"] = "pydantic_ai_openrouter"
        return output, AgentCallRecord(role=role, provider="openrouter", model=model_name, status="ok", cost_usd=0.0)
    except Exception as exc:
        err = f"OpenRouter role call failed: {type(exc).__name__}: {exc}"
        return {"role": role, "status": "failed", "error": err}, AgentCallRecord(role=role, provider="openrouter", model=model_name, status="failed", error=err)


def _pick_model(role: str, models_config: dict[str, Any]) -> str:
    pool = models_config.get("model_pool", {})
    if role == "red_team":
        choices = pool.get("red_team") or pool.get("strong_reasoning") or ["openrouter:auto"]
    elif role in {"planner", "judge", "modeler"}:
        choices = pool.get("strong_reasoning") or pool.get("low_cost") or ["openrouter:auto"]
    else:
        choices = pool.get("low_cost") or pool.get("free_test") or ["openrouter:auto"]
    return choices[0]


def _system_prompt_for(role: str) -> str:
    prompts = {
        "planner": "You are the HEBC-Lite planning analyst. Decompose variables, constraints, and decision path.",
        "modeler": "You are the HEBC-Lite modeling officer. Build assumptions, causal chains, and scenario trees.",
        "red_team": "You are the HEBC-Lite red-team analyst. Attack assumptions and identify disconfirming evidence.",
        "judge": "You are the HEBC-Lite final judge. Weigh evidence, risks, uncertainty, and stop-loss conditions.",
        "reporter": "You are the HEBC-Lite reporter. Produce concise structured markdown-ready findings.",
    }
    return prompts.get(role, "You are a structured HEBC-Lite analyst.")

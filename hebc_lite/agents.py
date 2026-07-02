from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
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


def is_mock_mode(models_config: dict[str, Any]) -> bool:
    return bool(models_config.get("budget", {}).get("test_mode", True))


def is_free_openrouter_model(model_name: str) -> bool:
    return model_name.endswith(":free")


def run_role(role: str, task: Task, models_config: dict[str, Any], context: dict[str, Any] | None = None) -> tuple[dict[str, Any], AgentCallRecord]:
    context = context or {}
    budget = models_config.get("budget", {})
    model_name = _pick_model(role, models_config)

    if is_mock_mode(models_config):
        output = dict(_SAFE_MOCK_OUTPUTS.get(role, {"summary": f"mock result for {role}"}))
        output.update({"role": role, "mode": "test_mode_mock", "cost_usd": 0.0})
        return output, AgentCallRecord(role=role, provider="mock", model="mock", status="ok", cost_usd=0.0)

    if not has_openrouter_key():
        err = "OPENROUTER_API_KEY missing; real OpenRouter call skipped."
        return {"role": role, "status": "failed", "error": err}, AgentCallRecord(role=role, provider="openrouter", model=model_name, status="failed", error=err)

    allow_paid = bool(budget.get("allow_paid_models", False))
    max_cost = float(budget.get("max_cost_usd_per_task", 0.0))
    if not allow_paid and not is_free_openrouter_model(model_name):
        err = f"Paid model blocked by config: {model_name}. Use a model id ending with :free or set allow_paid_models=true."
        return {"role": role, "status": "failed", "error": err}, AgentCallRecord(role=role, provider="openrouter", model=model_name, status="failed", error=err)

    if max_cost <= 0.0 and not is_free_openrouter_model(model_name):
        err = f"max_cost_usd_per_task is zero and model is not marked free: {model_name}."
        return {"role": role, "status": "failed", "error": err}, AgentCallRecord(role=role, provider="openrouter", model=model_name, status="failed", error=err)

    return _run_openrouter_role(role, task, models_config, context, model_name)


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


def _run_openrouter_role(role: str, task: Task, models_config: dict[str, Any], context: dict[str, Any], model_name: str) -> tuple[dict[str, Any], AgentCallRecord]:
    """Run one role through OpenRouter's OpenAI-compatible chat endpoint.

    The repository still keeps Pydantic AI as the expert-panel dependency. This direct HTTP path is used for the
    smoke test because it is stable across Pydantic AI adapter API changes and still returns structured output.
    The API key is only read from the environment and is never printed or written into outputs.
    """
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": _system_prompt_for(role)},
            {"role": "user", "content": json.dumps({"task": task.model_dump(), "role": role, "context": context, "required_output": "Return compact JSON with summary, risks, recommendation, confidence."}, ensure_ascii=False)},
        ],
        "temperature": 0.2,
        "max_tokens": 600,
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"],
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/a15280020511/test",
            "X-Title": "HEBC-Lite",
        },
        method="POST",
    )
    try:  # pragma: no cover - requires live OpenRouter key and network
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        try:
            output = json.loads(content)
        except json.JSONDecodeError:
            output = {"summary": content}
        if not isinstance(output, dict):
            output = {"summary": str(output)}
        output.update({"role": role, "mode": "openrouter_free_model", "model": model_name, "cost_usd": 0.0})
        return output, AgentCallRecord(role=role, provider="openrouter", model=model_name, status="ok", cost_usd=0.0)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:1000]
        err = f"OpenRouter HTTPError {exc.code}: {body}"
        return {"role": role, "status": "failed", "error": err}, AgentCallRecord(role=role, provider="openrouter", model=model_name, status="failed", error=err)
    except Exception as exc:
        err = f"OpenRouter call failed: {type(exc).__name__}: {exc}"
        return {"role": role, "status": "failed", "error": err}, AgentCallRecord(role=role, provider="openrouter", model=model_name, status="failed", error=err)


def _pick_model(role: str, models_config: dict[str, Any]) -> str:
    pool = models_config.get("model_pool", {})
    if role == "red_team":
        choices = pool.get("red_team") or pool.get("strong_reasoning") or ["nvidia/nemotron-3-ultra-550b-a55b:free"]
    elif role in {"planner", "judge", "modeler"}:
        choices = pool.get("strong_reasoning") or pool.get("low_cost") or ["nvidia/nemotron-3-ultra-550b-a55b:free"]
    else:
        choices = pool.get("low_cost") or pool.get("free_test") or ["cohere/north-mini-code:free"]
    return choices[0]


def _system_prompt_for(role: str) -> str:
    prompts = {
        "planner": "You are the HEBC-Lite planning analyst. Decompose variables, constraints, and decision path. Return JSON only.",
        "modeler": "You are the HEBC-Lite modeling officer. Build assumptions, causal chains, and scenario trees. Return JSON only.",
        "red_team": "You are the HEBC-Lite review analyst. Identify weak assumptions and disconfirming evidence. Return JSON only.",
        "judge": "You are the HEBC-Lite final judge. Weigh evidence, risks, uncertainty, and stop conditions. Return JSON only.",
        "reporter": "You are the HEBC-Lite reporter. Produce concise structured markdown-ready findings. Return JSON only.",
    }
    return prompts.get(role, "You are a structured HEBC-Lite analyst. Return JSON only.")

from __future__ import annotations

import importlib.util
import random
import time
from typing import Any

from .schemas import Task


def run_mesa(task: Task, modeling_result: dict[str, Any], mesa_config: dict[str, Any], mesa_needed: bool, mesa_reason: str | None = None) -> dict[str, Any]:
    config = mesa_config.get("mesa", {})
    if not mesa_needed:
        return {"engine": "mesa", "enabled": False, "reason": "Mesa disabled by route/default."}

    if config.get("require_explicit_reason", True) and not mesa_reason:
        return {"engine": "mesa", "enabled": True, "status": "failed", "error": "Mesa requires explicit reason."}

    timeout_seconds = int(config.get("timeout_seconds", 180))
    steps = int(config.get("default_steps", 100))
    agents = int(config.get("default_agents", 50))
    seed = int(config.get("random_seed", 42))

    if importlib.util.find_spec("mesa") is None:
        return {
            "engine": "mesa",
            "enabled": True,
            "status": "failed",
            "error": "Mesa package is not importable in this runtime.",
            "warnings": ["Mesa failure does not erase GPT modeling report."],
        }

    started = time.monotonic()
    try:
        summary, agent_stats = _toy_market_competition(steps=steps, agents=agents, seed=seed, timeout_seconds=timeout_seconds, started=started)
        return {
            "engine": "mesa",
            "enabled": True,
            "status": "completed",
            "model_type": "market_competition",
            "steps": steps,
            "agents": agents,
            "reason": mesa_reason,
            "summary": summary,
            "agent_stats": agent_stats,
            "warnings": ["This is a first-version minimal Mesa-compatible runner, not an industry-grade simulation."],
        }
    except TimeoutError as exc:
        return {"engine": "mesa", "enabled": True, "status": "failed", "error": str(exc), "warnings": ["Mesa timed out; partial report should still be written."]}
    except Exception as exc:
        return {"engine": "mesa", "enabled": True, "status": "failed", "error": f"{type(exc).__name__}: {exc}", "warnings": ["Mesa error does not erase GPT modeling report."]}


def _toy_market_competition(steps: int, agents: int, seed: int, timeout_seconds: int, started: float) -> tuple[dict[str, Any], dict[str, Any]]:
    rng = random.Random(seed)
    scores = [0.0 for _ in range(agents)]
    for step in range(steps):
        if time.monotonic() - started > timeout_seconds:
            raise TimeoutError("Mesa runner timed out.")
        demand = max(1, int(rng.gauss(mu=max(agents * 0.25, 1), sigma=max(agents * 0.05, 1))))
        for _ in range(demand):
            idx = rng.randrange(agents)
            scores[idx] += rng.uniform(0.5, 1.5)
        for idx in range(agents):
            scores[idx] -= rng.uniform(0.0, 0.03)
    scores_sorted = sorted(scores)
    total = sum(scores)
    mean = total / agents if agents else 0.0
    p20 = scores_sorted[int(0.2 * (agents - 1))] if agents else 0.0
    p80 = scores_sorted[int(0.8 * (agents - 1))] if agents else 0.0
    summary = {
        "mean_score": round(mean, 4),
        "min_score": round(min(scores), 4) if scores else 0.0,
        "max_score": round(max(scores), 4) if scores else 0.0,
        "inequality_gap_p80_p20": round(p80 - p20, 4),
        "interpretation": "With limited demand, returns can diverge under competition and random allocation.",
    }
    agent_stats = {"top_5_scores": [round(x, 4) for x in scores_sorted[-5:]], "bottom_5_scores": [round(x, 4) for x in scores_sorted[:5]]}
    return summary, agent_stats

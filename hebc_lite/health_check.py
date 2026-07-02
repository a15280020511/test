from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any

REQUIRED_DIRS = ["tasks/inbox", "tasks/processed", "jobs/status", "reports/archive", "artifacts/archive", "configs"]
REQUIRED_CONFIGS = ["models.json", "routing.json", "mesa.json", "cleanup.json", "safety.json", "free_model_policy.json"]
REQUIRED_IMPORTS = ["pydantic", "pydantic_ai", "mesa"]
REQUIRED_WORKFLOWS = ["run_task.yml", "test.yml", "health_check.yml", "cleanup.yml", "check_status.yml", "maintenance.yml"]


def check_health() -> dict[str, Any]:
    dirs = {path: Path(path).exists() for path in REQUIRED_DIRS}
    configs: dict[str, Any] = {}
    loaded_configs: dict[str, Any] = {}
    for name in REQUIRED_CONFIGS:
        path = Path("configs") / name
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            loaded_configs[name] = data
            configs[name] = {"exists": True, "json_readable": True}
        except Exception as exc:
            configs[name] = {"exists": path.exists(), "json_readable": False, "error": f"{type(exc).__name__}: {exc}"}

    imports = {name: importlib.util.find_spec(name) is not None for name in REQUIRED_IMPORTS}
    writable = {}
    for folder in ["reports", "artifacts", "jobs/status"]:
        path = Path(folder)
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_probe"
        try:
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            writable[folder] = True
        except Exception:
            writable[folder] = False

    workflows = {name: (Path(".github/workflows") / name).exists() for name in REQUIRED_WORKFLOWS}
    free_model_policy = validate_free_model_policy(loaded_configs.get("models.json", {}), loaded_configs.get("free_model_policy.json", {}))
    maintenance = {
        "dependabot_config_exists": Path(".github/dependabot.yml").exists(),
        "scheduled_health_check": workflows.get("health_check.yml", False),
        "scheduled_cleanup": workflows.get("cleanup.yml", False),
        "scheduled_maintenance": workflows.get("maintenance.yml", False),
    }

    result = {
        "directories": dirs,
        "configs": configs,
        "secrets": {"OPENROUTER_API_KEY": "exists" if os.getenv("OPENROUTER_API_KEY") else "missing"},
        "writable": writable,
        "imports": imports,
        "workflows": workflows,
        "free_model_policy": free_model_policy,
        "maintenance": maintenance,
    }
    result["ok"] = (
        all(dirs.values())
        and all(item.get("json_readable") for item in configs.values())
        and all(writable.values())
        and imports.get("pydantic", False)
        and free_model_policy.get("ok", False)
        and all(maintenance.values())
    )
    return result


def validate_free_model_policy(models_config: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    budget = models_config.get("budget", {})
    pool = models_config.get("model_pool", {})
    require_free_suffix = bool(policy.get("require_free_suffix_for_live_tests", True))
    allow_paid = bool(budget.get("allow_paid_models", False))
    test_mode = bool(budget.get("test_mode", True))
    model_ids = [model for values in pool.values() for model in values]
    non_free = [model for model in model_ids if require_free_suffix and not model.endswith(":free")]
    blocked_defaults = [model for model in model_ids if model in set(policy.get("blocked_defaults", []))]
    ok = True
    problems: list[str] = []
    if not test_mode and not allow_paid and non_free:
        ok = False
        problems.append("live tests forbid paid models, but non-free model ids are configured")
    if blocked_defaults:
        ok = False
        problems.append("blocked default model ids are configured")
    if budget.get("max_cost_usd_per_task", 0.0) != 0.0 and not allow_paid:
        ok = False
        problems.append("max_cost_usd_per_task should stay 0.0 when paid models are not allowed")
    return {
        "ok": ok,
        "test_mode": test_mode,
        "allow_paid_models": allow_paid,
        "max_cost_usd_per_task": budget.get("max_cost_usd_per_task"),
        "model_ids": model_ids,
        "non_free_model_ids": non_free,
        "blocked_defaults_present": blocked_defaults,
        "problems": problems,
    }


def write_health_report(result: dict[str, Any]) -> None:
    Path("reports").mkdir(exist_ok=True)
    Path("artifacts").mkdir(exist_ok=True)
    md = ["# HEBC-Lite Health Check", "", "```json", json.dumps(result, ensure_ascii=False, indent=2), "```", ""]
    Path("reports/health_check.md").write_text("\n".join(md), encoding="utf-8")
    Path("artifacts/health_check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    result = check_health()
    write_health_report(result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

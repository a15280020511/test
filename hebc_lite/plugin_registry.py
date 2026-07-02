from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any


def load_plugin_registry(path: str | Path = "configs/plugins.json") -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def check_plugins(registry: dict[str, Any] | None = None, *, full_ci: bool = False) -> dict[str, Any]:
    registry = registry or load_plugin_registry()
    plugins = registry.get("plugins", {})
    results: dict[str, Any] = {}
    for name, spec in plugins.items():
        enabled = bool(spec.get("enabled", False))
        import_name = spec.get("import_name")
        required = bool(spec.get("required_in_full_ci", False)) if full_ci else False
        result = {
            "enabled": enabled,
            "kind": spec.get("kind"),
            "role": spec.get("role"),
            "required": required,
            "status": "skipped",
            "details": [],
        }
        if not enabled:
            result["status"] = "disabled"
            results[name] = result
            continue
        if import_name:
            available = importlib.util.find_spec(import_name) is not None
            result["import_name"] = import_name
            result["importable"] = available
            if not available:
                result["status"] = "failed" if required else "missing_optional"
                result["details"].append(f"{import_name} is not importable")
                results[name] = result
                continue
        if name == "mesa":
            result.update(_check_mesa_minimal())
        elif name == "openrouter":
            secret_name = spec.get("secret_name", "OPENROUTER_API_KEY")
            result["secret_name"] = secret_name
            result["secret_exists"] = bool(os.getenv(secret_name))
            result["status"] = "ok" if result["secret_exists"] else "missing_secret"
        elif name == "webgpt_orchestrator":
            contract = registry.get("execution_contract", {})
            result["contract_present"] = bool(contract)
            result["status"] = "ok" if contract else "failed"
        else:
            result["status"] = "ok"
        results[name] = result
    return {
        "version": registry.get("version"),
        "principle": registry.get("principle"),
        "execution_contract": registry.get("execution_contract", {}),
        "plugins": results,
        "ok": all(item.get("status") in {"ok", "disabled", "missing_optional", "missing_secret"} for item in results.values()),
    }


def _check_mesa_minimal() -> dict[str, Any]:
    try:
        import mesa  # type: ignore
        return {"status": "ok", "mesa_version": getattr(mesa, "__version__", "unknown"), "minimal_run": "import_ok"}
    except Exception as exc:  # pragma: no cover
        return {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}


def write_plugin_report(path: str | Path = "reports/plugin_report.md", *, full_ci: bool = False) -> dict[str, Any]:
    result = check_plugins(full_ci=full_ci)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path("artifacts").mkdir(exist_ok=True)
    Path(path).write_text("# HEBC-Lite Plugin Report\n\n```json\n" + json.dumps(result, ensure_ascii=False, indent=2) + "\n```\n", encoding="utf-8")
    Path("artifacts/plugin_report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> int:
    result = write_plugin_report(full_ci=os.getenv("HEBC_FULL_CI") == "1")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    hard_fail = any(item.get("required") and item.get("status") == "failed" for item in result.get("plugins", {}).values())
    return 1 if hard_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())

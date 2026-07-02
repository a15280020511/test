from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any

REQUIRED_DIRS = ["tasks/inbox", "tasks/processed", "jobs/status", "reports/archive", "artifacts/archive", "configs"]
REQUIRED_CONFIGS = ["models.json", "routing.json", "mesa.json", "cleanup.json", "safety.json"]
REQUIRED_IMPORTS = ["pydantic", "pydantic_ai", "mesa"]


def check_health() -> dict[str, Any]:
    dirs = {path: Path(path).exists() for path in REQUIRED_DIRS}
    configs: dict[str, Any] = {}
    for name in REQUIRED_CONFIGS:
        path = Path("configs") / name
        try:
            json.loads(path.read_text(encoding="utf-8"))
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

    result = {
        "directories": dirs,
        "configs": configs,
        "secrets": {"OPENROUTER_API_KEY": "exists" if os.getenv("OPENROUTER_API_KEY") else "missing"},
        "writable": writable,
        "imports": imports,
    }
    result["ok"] = all(dirs.values()) and all(item.get("json_readable") for item in configs.values()) and all(writable.values()) and imports.get("pydantic", False)
    return result


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

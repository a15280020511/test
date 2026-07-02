from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .health_check import check_health
from .plugin_registry import check_plugins
from .upstream_monitor import check_upstream_sources


def build_maintenance_report() -> dict[str, Any]:
    required_files = [
        "configs/plugins.json",
        "configs/upstream_sources.json",
        "pyproject.toml",
        ".github/dependabot.yml",
        ".github/workflows/full_system_check.yml",
        ".github/workflows/cleanup.yml",
        ".github/workflows/health_check.yml",
        "docs/WEBGPT_ORCHESTRATION_CONTRACT.md",
        "docs/WEBGPT_TASK_TEMPLATE.json",
    ]
    files = {path: Path(path).exists() for path in required_files}
    health = check_health()
    plugins = check_plugins(full_ci=True)
    upstream = check_upstream_sources()
    result = {
        "files": files,
        "health_ok": health.get("ok", False),
        "plugins_ok": plugins.get("ok", False),
        "upstream_ok": upstream.get("ok", False),
        "health": health,
        "plugins": plugins,
        "upstream_sources": upstream,
        "daily_ops_ready": all(files.values()) and health.get("ok", False) and plugins.get("ok", False) and upstream.get("ok", False),
        "notes": [
            "Routine checks are automated through workflows and dependency update PRs.",
            "Upstream repositories are declared in configs/upstream_sources.json.",
            "Breaking upstream public interface changes are detected by CI and reported.",
            "WebGPT owns task information, model choices, role order, and tool plan.",
        ],
    }
    return result


def write_maintenance_report() -> dict[str, Any]:
    result = build_maintenance_report()
    Path("reports").mkdir(exist_ok=True)
    Path("artifacts").mkdir(exist_ok=True)
    Path("reports/maintenance_report.md").write_text("# HEBC-Lite Maintenance Report\n\n```json\n" + json.dumps(result, ensure_ascii=False, indent=2) + "\n```\n", encoding="utf-8")
    Path("artifacts/maintenance_report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> int:
    result = write_maintenance_report()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("daily_ops_ready") else 1


if __name__ == "__main__":
    raise SystemExit(main())

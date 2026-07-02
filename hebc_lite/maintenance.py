from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .health_check import check_health
from .cleanup import cleanup


def run_maintenance() -> dict[str, Any]:
    """Run routine zero-cost maintenance checks.

    This command does not call OpenRouter. It verifies repository health, free-model policy,
    scheduled maintenance configuration, and safe cleanup behavior, then writes reports.
    """
    health = check_health()
    cleanup_result = cleanup()
    result = {
        "status": "ok" if health.get("ok") else "failed",
        "health_ok": health.get("ok", False),
        "free_model_policy_ok": health.get("free_model_policy", {}).get("ok", False),
        "maintenance": health.get("maintenance", {}),
        "secret_state": health.get("secrets", {}).get("OPENROUTER_API_KEY", "missing"),
        "cleanup_removed_count": len(cleanup_result.get("removed", [])),
        "cleanup_skipped_count": len(cleanup_result.get("skipped", [])),
        "warnings": _warnings(health),
    }
    write_maintenance_report(result, health, cleanup_result)
    return result


def _warnings(health: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if health.get("secrets", {}).get("OPENROUTER_API_KEY") != "exists":
        warnings.append("OPENROUTER_API_KEY is missing; live free-model OpenRouter tests cannot run, but mock and policy tests can still run.")
    if not health.get("free_model_policy", {}).get("ok", False):
        warnings.append("Free model policy failed; inspect configs/models.json and configs/free_model_policy.json.")
    if not all(health.get("maintenance", {}).values()):
        warnings.append("One or more maintenance hooks are missing.")
    return warnings


def write_maintenance_report(result: dict[str, Any], health: dict[str, Any], cleanup_result: dict[str, Any]) -> None:
    Path("reports").mkdir(exist_ok=True)
    Path("artifacts").mkdir(exist_ok=True)
    artifact = {"result": result, "health": health, "cleanup": cleanup_result}
    Path("artifacts/maintenance_report.json").write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    md = [
        "# HEBC-Lite Maintenance Report",
        "",
        f"- status: `{result['status']}`",
        f"- health_ok: `{result['health_ok']}`",
        f"- free_model_policy_ok: `{result['free_model_policy_ok']}`",
        f"- secret_state: `{result['secret_state']}`",
        f"- cleanup_removed_count: `{result['cleanup_removed_count']}`",
        f"- cleanup_skipped_count: `{result['cleanup_skipped_count']}`",
        "",
        "## Warnings",
    ]
    if result["warnings"]:
        md.extend(f"- {item}" for item in result["warnings"])
    else:
        md.append("- None")
    md.extend(["", "## Raw summary", "", "```json", json.dumps(result, ensure_ascii=False, indent=2), "```", ""])
    Path("reports/maintenance_report.md").write_text("\n".join(md), encoding="utf-8")


def main() -> int:
    result = run_maintenance()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())

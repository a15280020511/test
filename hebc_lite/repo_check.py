from __future__ import annotations

import json
from pathlib import Path


def check_repo_outputs(task_id: str = "example_decision_task") -> dict:
    workflows = {name: (Path(".github/workflows") / name).exists() for name in ["run_task.yml", "test.yml", "health_check.yml", "cleanup.yml", "check_status.yml", "maintenance.yml"]}
    result = {
        "task_id": task_id,
        "workflows": workflows,
        "example_task_exists": Path("tasks/inbox/example_task.json").exists(),
        "status_file_exists": Path("jobs/status") .joinpath(f"{task_id}.status.json").exists(),
        "latest_report_exists": Path("reports/latest_report.md").exists(),
        "latest_result_exists": Path("artifacts/latest_result.json").exists(),
        "health_report_exists": Path("reports/health_check.md").exists(),
        "cleanup_report_exists": Path("reports/cleanup_report.json").exists(),
    }
    result["ok"] = all(workflows.values()) and result["status_file_exists"] and result["latest_report_exists"] and result["latest_result_exists"]
    return result


def write_repo_check(task_id: str = "example_decision_task") -> dict:
    result = check_repo_outputs(task_id)
    Path("reports").mkdir(exist_ok=True)
    Path("artifacts").mkdir(exist_ok=True)
    Path("reports/repo_check.md").write_text("# HEBC-Lite Repo Check\n\n```json\n" + json.dumps(result, ensure_ascii=False, indent=2) + "\n```\n", encoding="utf-8")
    Path("artifacts/repo_check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> int:
    result = write_repo_check()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

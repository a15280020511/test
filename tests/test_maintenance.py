import json
from pathlib import Path

from hebc_lite.maintenance import run_maintenance


def test_maintenance_runner_writes_reports(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for folder in ["tasks/inbox", "tasks/processed", "jobs/status", "reports/archive", "artifacts/archive", "configs"]:
        Path(folder).mkdir(parents=True, exist_ok=True)
    Path(".github/workflows").mkdir(parents=True, exist_ok=True)
    for name in ["run_task.yml", "test.yml", "health_check.yml", "cleanup.yml", "check_status.yml", "maintenance.yml"]:
        Path(".github/workflows", name).write_text("name: test\n", encoding="utf-8")
    Path(".github/dependabot.yml").parent.mkdir(parents=True, exist_ok=True)
    Path(".github/dependabot.yml").write_text("version: 2\n", encoding="utf-8")
    Path("configs/models.json").write_text(json.dumps({"budget": {"test_mode": False, "allow_paid_models": False, "max_cost_usd_per_task": 0.0}, "model_pool": {"strong_reasoning": ["cohere/north-mini-code:free"], "red_team": ["nvidia/nemotron-3-ultra-550b-a55b:free"]}}), encoding="utf-8")
    Path("configs/free_model_policy.json").write_text(json.dumps({"require_free_suffix_for_live_tests": True, "blocked_defaults": ["openrouter:auto"]}), encoding="utf-8")
    for name in ["routing.json", "mesa.json", "cleanup.json", "safety.json"]:
        Path("configs", name).write_text(json.dumps({"ok": True}), encoding="utf-8")

    result = run_maintenance()
    assert result["free_model_policy_ok"] is True
    assert Path("reports/maintenance_report.md").exists()
    assert Path("artifacts/maintenance_report.json").exists()

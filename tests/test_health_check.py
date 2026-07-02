import json
from pathlib import Path

from hebc_lite.health_check import check_health

REQUIRED_DIRS = ["tasks/inbox", "tasks/processed", "jobs/status", "reports/archive", "artifacts/archive", "configs"]
REQUIRED_CONFIGS = ["models.json", "routing.json", "mesa.json", "cleanup.json", "safety.json", "free_model_policy.json"]
REQUIRED_WORKFLOWS = ["run_task.yml", "test.yml", "health_check.yml", "cleanup.yml", "check_status.yml", "maintenance.yml"]


def _write_minimal_repo_layout():
    for folder in REQUIRED_DIRS:
        Path(folder).mkdir(parents=True, exist_ok=True)
    Path(".github/workflows").mkdir(parents=True, exist_ok=True)
    for name in REQUIRED_WORKFLOWS:
        Path(".github/workflows", name).write_text("name: test\n", encoding="utf-8")
    Path(".github/dependabot.yml").parent.mkdir(parents=True, exist_ok=True)
    Path(".github/dependabot.yml").write_text("version: 2\n", encoding="utf-8")
    Path("configs/models.json").write_text(json.dumps({"budget": {"test_mode": False, "allow_paid_models": False, "max_cost_usd_per_task": 0.0}, "model_pool": {"strong_reasoning": ["cohere/north-mini-code:free"], "red_team": ["nvidia/nemotron-3-ultra-550b-a55b:free"]}}), encoding="utf-8")
    Path("configs/free_model_policy.json").write_text(json.dumps({"require_free_suffix_for_live_tests": True, "blocked_defaults": ["openrouter:auto"]}), encoding="utf-8")
    for name in ["routing.json", "mesa.json", "cleanup.json", "safety.json"]:
        Path("configs", name).write_text(json.dumps({"ok": True}), encoding="utf-8")


def test_health_check_does_not_print_secret_value(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_minimal_repo_layout()
    monkeypatch.setenv("OPENROUTER_API_KEY", "secret_should_not_appear")
    result = check_health()
    serialized = json.dumps(result, ensure_ascii=False)
    assert "secret_should_not_appear" not in serialized
    assert result["secrets"]["OPENROUTER_API_KEY"] == "exists"


def test_health_check_reports_missing_secret(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_minimal_repo_layout()
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    result = check_health()
    assert result["secrets"]["OPENROUTER_API_KEY"] == "missing"


def test_health_check_validates_maintenance_and_free_policy(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_minimal_repo_layout()
    result = check_health()
    assert result["free_model_policy"]["ok"] is True
    assert result["maintenance"]["dependabot_config_exists"] is True
    assert result["maintenance"]["scheduled_health_check"] is True
    assert result["maintenance"]["scheduled_cleanup"] is True
    assert result["maintenance"]["scheduled_maintenance"] is True

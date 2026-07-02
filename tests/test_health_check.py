import json
from pathlib import Path

from hebc_lite.health_check import check_health


def test_health_check_does_not_print_secret_value(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for folder in ["tasks/inbox", "tasks/processed", "jobs/status", "reports/archive", "artifacts/archive", "configs"]:
        Path(folder).mkdir(parents=True, exist_ok=True)
    for name in ["models.json", "routing.json", "mesa.json", "cleanup.json", "safety.json"]:
        Path("configs", name).write_text(json.dumps({"ok": True}), encoding="utf-8")
    monkeypatch.setenv("OPENROUTER_API_KEY", "secret_should_not_appear")
    result = check_health()
    serialized = json.dumps(result, ensure_ascii=False)
    assert "secret_should_not_appear" not in serialized
    assert result["secrets"]["OPENROUTER_API_KEY"] == "exists"


def test_health_check_reports_missing_secret(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for folder in ["tasks/inbox", "tasks/processed", "jobs/status", "reports/archive", "artifacts/archive", "configs"]:
        Path(folder).mkdir(parents=True, exist_ok=True)
    for name in ["models.json", "routing.json", "mesa.json", "cleanup.json", "safety.json"]:
        Path("configs", name).write_text(json.dumps({"ok": True}), encoding="utf-8")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    result = check_health()
    assert result["secrets"]["OPENROUTER_API_KEY"] == "missing"

from pathlib import Path

from hebc_lite.repo_check import check_repo_outputs, write_repo_check


def test_repo_check_detects_missing_outputs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path(".github/workflows").mkdir(parents=True)
    for name in ["run_task.yml", "test.yml", "health_check.yml", "cleanup.yml", "check_status.yml", "maintenance.yml"]:
        Path(".github/workflows", name).write_text("name: test\n", encoding="utf-8")
    Path("tasks/inbox").mkdir(parents=True)
    Path("tasks/inbox/example_task.json").write_text("{}\n", encoding="utf-8")
    result = check_repo_outputs()
    assert result["example_task_exists"] is True
    assert result["status_file_exists"] is False
    assert result["ok"] is False


def test_repo_check_writes_reports(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = write_repo_check()
    assert Path("reports/repo_check.md").exists()
    assert Path("artifacts/repo_check.json").exists()
    assert result["ok"] is False

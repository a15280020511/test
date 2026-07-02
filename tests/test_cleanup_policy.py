from pathlib import Path

from hebc_lite.cleanup import is_protected


def test_cleanup_never_delete_prefixes():
    protected = ["reports/final/", "artifacts/decision_records/", "configs/", "tasks/processed/index.json"]
    assert is_protected(Path("reports/final/keep.md"), protected)
    assert is_protected(Path("configs/models.json"), protected)
    assert is_protected(Path("tasks/processed/index.json"), protected)
    assert not is_protected(Path("artifacts/archive/old.json"), protected)

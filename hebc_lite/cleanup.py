from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def load_cleanup_config(path: str | Path = "configs/cleanup.json") -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def is_protected(path: Path, never_delete: list[str]) -> bool:
    posix = path.as_posix().rstrip("/")
    for raw in never_delete:
        protected = raw.rstrip("/")
        if posix == protected or posix.startswith(protected + "/"):
            return True
    return False


def cleanup(config_path: str | Path = "configs/cleanup.json") -> dict[str, Any]:
    config = load_cleanup_config(config_path)
    retention = config.get("retention", {})
    never_delete = config.get("never_delete", [])
    now = time.time()
    removed: list[str] = []
    skipped: list[str] = []

    policies = [
        (Path("jobs/status"), int(retention.get("status_keep_days", 30))),
        (Path("artifacts/archive"), int(retention.get("ordinary_artifacts_keep_days", 30))),
    ]
    for folder, keep_days in policies:
        if not folder.exists():
            continue
        cutoff = now - keep_days * 86400
        for path in folder.rglob("*"):
            if path.is_dir():
                continue
            if is_protected(path, never_delete):
                skipped.append(path.as_posix())
                continue
            if path.stat().st_mtime < cutoff:
                path.unlink()
                removed.append(path.as_posix())

    report = {"removed": removed, "skipped": skipped, "protected": never_delete}
    Path("reports").mkdir(exist_ok=True)
    Path("artifacts").mkdir(exist_ok=True)
    Path("reports/cleanup_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

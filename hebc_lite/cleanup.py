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
    never_delete = config.get("never_delete", [])
    dry_run = bool(config.get("auto_actions", {}).get("dry_run", False))
    now = time.time()
    removed: list[str] = []
    skipped: list[str] = []
    candidates: list[str] = []

    policies = config.get("policies") or _legacy_policies(config)
    for policy in policies:
        folder = Path(policy.get("folder", "."))
        if not folder.exists():
            skipped.append(f"missing_folder:{folder.as_posix()}")
            continue
        patterns = policy.get("patterns") or ["*"]
        max_age_days = int(policy.get("max_age_days", 30))
        keep_latest = int(policy.get("keep_latest", 0))
        files = _matching_files(folder, patterns)
        protected_files = [path for path in files if is_protected(path, never_delete)]
        for path in protected_files:
            skipped.append(path.as_posix())
        files = [path for path in files if path not in protected_files]
        files.sort(key=lambda item: item.stat().st_mtime, reverse=True)
        keep_set = set(files[:keep_latest]) if keep_latest > 0 else set()
        cutoff = now - max_age_days * 86400
        for path in files:
            if path in keep_set:
                skipped.append(path.as_posix())
                continue
            if path.stat().st_mtime >= cutoff:
                continue
            candidates.append(path.as_posix())
            if not dry_run:
                path.unlink(missing_ok=True)
            removed.append(path.as_posix())

    report = {
        "mode": config.get("mode", "scheduled_safe_cleanup"),
        "dry_run": dry_run,
        "removed": removed,
        "candidates": candidates,
        "skipped": skipped,
        "protected": never_delete,
        "policies": policies,
        "summary": {"removed_count": len(removed), "candidate_count": len(candidates), "skipped_count": len(skipped)},
    }
    Path("reports").mkdir(exist_ok=True)
    Path("artifacts").mkdir(exist_ok=True)
    Path("reports/cleanup_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    Path("artifacts/cleanup_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def _matching_files(folder: Path, patterns: list[str]) -> list[Path]:
    result: list[Path] = []
    for pattern in patterns:
        for path in folder.rglob(pattern):
            if path.is_file():
                result.append(path)
    return sorted(set(result))


def _legacy_policies(config: dict[str, Any]) -> list[dict[str, Any]]:
    retention = config.get("retention", {})
    return [
        {"name": "status_files", "folder": "jobs/status", "patterns": ["*.json"], "max_age_days": int(retention.get("status_keep_days", 30)), "keep_latest": int(retention.get("status_keep_latest", 100))},
        {"name": "archived_artifacts", "folder": "artifacts/archive", "patterns": ["*.json", "*.md", "*.txt", "*.zip"], "max_age_days": int(retention.get("ordinary_artifacts_keep_days", 30)), "keep_latest": int(retention.get("artifacts_keep_latest", 50))},
    ]


def main() -> int:
    cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

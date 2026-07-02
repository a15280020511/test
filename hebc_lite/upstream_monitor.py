from __future__ import annotations

import importlib.metadata
import importlib.util
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def load_sources(path: str | Path = "configs/upstream_sources.json") -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def check_upstream_sources(config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or load_sources()
    sources = config.get("sources", {})
    results: dict[str, Any] = {}
    for name, spec in sources.items():
        if not spec.get("enabled", False):
            results[name] = {"enabled": False, "status": "disabled"}
            continue
        import_name = spec.get("import_name")
        package_name = spec.get("package_name")
        repo_full_name = spec.get("repo_full_name")
        result = {
            "enabled": True,
            "upstream_repo": spec.get("upstream_repo"),
            "repo_full_name": repo_full_name,
            "package_manager": spec.get("package_manager"),
            "package_name": package_name,
            "import_name": import_name,
            "track": spec.get("track"),
            "required": bool(spec.get("required", False)),
            "importable": False,
            "installed_version": None,
            "repo_check": "not_checked",
            "status": "unknown",
            "warnings": [],
        }
        if import_name:
            result["importable"] = importlib.util.find_spec(import_name) is not None
        if package_name:
            try:
                result["installed_version"] = importlib.metadata.version(package_name)
            except importlib.metadata.PackageNotFoundError:
                result["warnings"].append("package_not_installed")
        if repo_full_name:
            result["repo_check"] = _check_github_repo(repo_full_name)
        ok = bool(result["importable"]) and bool(result["installed_version"])
        if result["repo_check"] not in {"ok", "not_checked", "network_unavailable"}:
            ok = False
        result["status"] = "ok" if ok else "failed"
        results[name] = result
    return {
        "version": config.get("version"),
        "principle": config.get("principle"),
        "tracking_policy": config.get("tracking_policy", {}),
        "zero_daily_maintenance_mode": config.get("zero_daily_maintenance_mode", {}),
        "sources": results,
        "ok": all(not item.get("required") or item.get("status") == "ok" for item in results.values()),
    }


def _check_github_repo(repo_full_name: str) -> str:
    url = f"https://api.github.com/repos/{repo_full_name}"
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "HEBC-Lite-Upstream-Monitor"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return "ok" if response.status == 200 else f"http_{response.status}"
    except urllib.error.URLError:
        return "network_unavailable"
    except Exception as exc:  # pragma: no cover
        return f"error:{type(exc).__name__}"


def write_upstream_report() -> dict[str, Any]:
    result = check_upstream_sources()
    Path("reports").mkdir(exist_ok=True)
    Path("artifacts").mkdir(exist_ok=True)
    Path("reports/upstream_sources_report.md").write_text("# HEBC-Lite Upstream Sources Report\n\n```json\n" + json.dumps(result, ensure_ascii=False, indent=2) + "\n```\n", encoding="utf-8")
    Path("artifacts/upstream_sources_report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> int:
    result = write_upstream_report()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

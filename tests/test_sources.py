from hebc_lite.upstream_monitor import check_upstream_sources


def test_source_monitor_ok_package():
    config = {"version": "test", "sources": {"pydantic": {"enabled": True, "package_name": "pydantic", "import_name": "pydantic", "repo_full_name": "", "required": True}}}
    result = check_upstream_sources(config)
    assert result["sources"]["pydantic"]["importable"] is True
    assert result["sources"]["pydantic"]["installed_version"]
    assert result["ok"] is True


def test_source_monitor_missing_package():
    config = {"version": "test", "sources": {"missing": {"enabled": True, "package_name": "missing-package-xyz-hebc", "import_name": "missing_package_xyz_hebc", "repo_full_name": "", "required": True}}}
    result = check_upstream_sources(config)
    assert result["sources"]["missing"]["status"] == "failed"
    assert result["ok"] is False

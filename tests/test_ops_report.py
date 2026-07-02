from hebc_lite.maintenance_report import build_maintenance_report


def test_ops_report_has_required_sections():
    result = build_maintenance_report()
    assert "files" in result
    assert "health" in result
    assert "plugins" in result
    assert "daily_ops_ready" in result

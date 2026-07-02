from hebc_lite.plugin_registry import check_plugins


def test_plugin_registry_reports_contract():
    registry = {
        "version": "test",
        "principle": "test principle",
        "execution_contract": {"model_selection_owner": "webgpt_task_input"},
        "plugins": {
            "webgpt_orchestrator": {"enabled": True, "kind": "control", "role": "owner"},
            "openrouter": {"enabled": True, "kind": "gateway", "role": "model", "secret_name": "OPENROUTER_API_KEY"},
        },
    }
    result = check_plugins(registry)
    assert result["execution_contract"]["model_selection_owner"] == "webgpt_task_input"
    assert result["plugins"]["webgpt_orchestrator"]["status"] == "ok"
    assert result["plugins"]["openrouter"]["status"] in {"ok", "missing_secret"}


def test_plugin_registry_missing_optional_import_does_not_break_light_ci():
    registry = {
        "version": "test",
        "plugins": {
            "optional_missing": {"enabled": True, "kind": "test", "role": "test", "import_name": "definitely_missing_package_xyz", "required_in_full_ci": True}
        },
    }
    light = check_plugins(registry, full_ci=False)
    assert light["plugins"]["optional_missing"]["status"] == "missing_optional"
    full = check_plugins(registry, full_ci=True)
    assert full["plugins"]["optional_missing"]["status"] == "failed"

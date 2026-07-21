import json

from tstack.automation import get_capability, list_capabilities, registry_json, validate_automation
from tstack.cli import main


def test_automation_registry_contains_safe_boundaries() -> None:
    capabilities = {item.id: item for item in list_capabilities()}
    assert "ssh-plan" in capabilities
    assert "auto-plugin-install" in capabilities
    assert capabilities["ssh-plan"].mode == "plan-only"
    assert capabilities["ssh-plan"].execution_allowed is False
    assert capabilities["auto-plugin-install"].status == "blocked"
    assert capabilities["auto-plugin-install"].execution_allowed is False


def test_automation_registry_json_is_machine_readable() -> None:
    payload = json.loads(registry_json())
    assert payload["schema"] == "tstack-automation-registry/v1"
    assert any(item["id"] == "python-rule-plugins" for item in payload["capabilities"])


def test_automation_registry_validation_passes() -> None:
    result = validate_automation()
    assert result.valid is True
    assert result.capabilities_checked >= 5
    assert result.errors == ()


def test_get_unknown_automation_capability_fails() -> None:
    try:
        get_capability("missing")
    except KeyError as exc:
        assert "unknown automation capability" in str(exc)
    else:
        raise AssertionError("unknown automation capability should fail")


def test_automation_cli_list_json(capsys) -> None:
    assert main(["automation", "list", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-automation-registry/v1"
    assert any(item["id"] == "ssh-plan" for item in payload["capabilities"])


def test_automation_cli_show_markdown(capsys) -> None:
    assert main(["automation", "show", "ssh-plan"]) == 0
    output = capsys.readouterr().out
    assert "SSH automation planner" in output
    assert "Execution allowed: `false`" in output


def test_automation_cli_validate_json(capsys) -> None:
    assert main(["automation", "validate", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-automation-validation/v1"
    assert payload["valid"] is True

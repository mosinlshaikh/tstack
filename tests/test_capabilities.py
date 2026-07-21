import json

from tstack.capabilities import get_capability_definition, list_capability_definitions, validate_capability_registry
from tstack.cli import main


def test_capability_registry_has_honest_statuses() -> None:
    errors = validate_capability_registry()
    assert errors == ()
    statuses = {item.status for item in list_capability_definitions()}
    assert {"WORKING", "EXPERIMENTAL", "PLAN-ONLY", "UNSUPPORTED"}.issubset(statuses)
    assert get_capability_definition("filesystem.write").status == "EXPERIMENTAL"
    assert get_capability_definition("browser.open").status == "UNSUPPORTED"


def test_capability_cli_list_json(capsys) -> None:
    assert main(["capability", "list", "--status", "EXPERIMENTAL", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-capability-registry/v1"
    assert payload["capabilities"]
    assert all(item["status"] == "EXPERIMENTAL" for item in payload["capabilities"])


def test_capability_cli_validate_json(capsys) -> None:
    assert main(["capability", "validate"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-capability-validation/v1"
    assert payload["valid"] is True
    assert payload["capabilities_checked"] >= 10

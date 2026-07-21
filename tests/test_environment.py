import json

from tstack.cli import main
from tstack.environment import inspect_environment


def test_environment_inspect_core_profile() -> None:
    report = inspect_environment(profile="core")
    assert report.schema == "tstack-environment-report/v1"
    assert report.tools_checked >= 2
    ids = {tool.id for tool in report.tools}
    assert {"python", "git"}.issubset(ids)
    assert report.execution_allowed is False


def test_environment_inspect_cli_json(capsys) -> None:
    assert main(["environment", "inspect", "--profile", "3d", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-environment-report/v1"
    assert payload["profile"] == "3d"
    assert any(tool["id"] == "blender" for tool in payload["tools"])
    assert payload["approval_required_for_install"] is True

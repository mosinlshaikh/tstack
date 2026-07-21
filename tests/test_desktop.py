import json

from tstack.cli import main
from tstack.desktop import desktop_blueprint


def test_desktop_blueprint_is_local_first() -> None:
    payload = desktop_blueprint()
    assert payload["schema"] == "tstack-desktop-blueprint/v1"
    assert payload["default_mode"] == "local-first-api-free"
    ids = {item["id"] for item in payload["capabilities"]}
    assert {"file-agent", "browser-agent", "permission-controller", "audit-rollback", "local-llm"}.issubset(ids)
    assert "unrestricted total PC control" in payload["blocked"]


def test_desktop_blueprint_cli_json(capsys) -> None:
    assert main(["desktop", "blueprint", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-desktop-blueprint/v1"
    assert payload["recommended_stack"]["browser"] == "Local Chromium + Playwright"
    assert any(item["id"] == "external-api-plugin" and item["external_api_required"] for item in payload["capabilities"])

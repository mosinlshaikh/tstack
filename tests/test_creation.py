import json

from tstack.cli import main
from tstack.creation import creation_blueprint


def test_creation_blueprint_contains_required_pipelines() -> None:
    payload = creation_blueprint()
    assert payload["schema"] == "tstack-creation-blueprint/v1"
    pipeline_ids = {item["id"] for item in payload["pipelines"]}
    assert {"image-to-glb", "blender-bridge", "game-builder", "android-builder", "ios-builder"}.issubset(pipeline_ids)
    plugin_ids = {item["id"] for item in payload["plugins"]}
    assert {"blender-bridge", "godot-bridge", "android-bridge", "xcode-mac-bridge", "docker-bridge"}.issubset(plugin_ids)
    assert "final iOS build requires Mac + Xcode or approved Mac build node" in payload["hard_rules"]


def test_creation_blueprint_cli_json(capsys) -> None:
    assert main(["creation", "blueprint", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-creation-blueprint/v1"
    assert "image-to-glb" in {item["id"] for item in payload["pipelines"]}
    assert "deployment-bridge" in {item["id"] for item in payload["plugins"]}

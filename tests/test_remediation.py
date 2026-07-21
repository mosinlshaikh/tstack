"""Safety and behavior tests for TStack remediation."""

from __future__ import annotations

import json

from tstack.cli import main
from tstack.remediation import apply_remediation, plan_remediation


def test_fix_defaults_to_dry_run(tmp_path, capsys) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname="demo"\nversion="1.0.0"\nrequires-python=">=3.10"\n', encoding="utf-8")
    assert main(["fix", str(tmp_path), "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["dry_run"] is True
    assert not (tmp_path / ".gitignore").exists()
    assert {item["path"] for item in payload["actions"]} == {".gitignore", "SECURITY.md", ".github/workflows/ci.yml"}


def test_fix_apply_creates_only_missing_controls(tmp_path) -> None:
    (tmp_path / "package.json").write_text('{"name":"demo","version":"1.0.0","scripts":{"test":"node --test"},"engines":{"node":">=20"}}', encoding="utf-8")
    (tmp_path / "package-lock.json").write_text("{}\n", encoding="utf-8")
    result = apply_remediation(tmp_path, dry_run=False)
    assert set(result.created) == {".gitignore", "SECURITY.md", ".github/workflows/ci.yml"}
    assert "node_modules/" in (tmp_path / ".gitignore").read_text(encoding="utf-8")
    ci = (tmp_path / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "npm ci" in ci
    assert "permissions:" in ci


def test_fix_does_not_replace_existing_file_without_force(tmp_path) -> None:
    original = "custom rules\n"
    (tmp_path / ".gitignore").write_text(original, encoding="utf-8")
    _, actions = plan_remediation(tmp_path)
    assert ".gitignore" not in {action.path for action in actions}
    result = apply_remediation(tmp_path, dry_run=False)
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == original
    assert ".gitignore" not in result.created


def test_fix_is_idempotent(tmp_path) -> None:
    first = apply_remediation(tmp_path, dry_run=False)
    second = apply_remediation(tmp_path, dry_run=False)
    assert first.created
    assert second.actions == ()
    assert second.created == ()

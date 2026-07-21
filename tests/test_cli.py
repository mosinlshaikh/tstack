"""Regression tests for the TStack CLI."""

from __future__ import annotations

import json

from tstack.cli import WORKFLOWS, main
from tstack.scanner import scan_project


def test_list_command(capsys) -> None:
    assert main(["list"]) == 0
    assert capsys.readouterr().out.splitlines() == list(WORKFLOWS)


def test_architect_command_prints_packaged_workflow(capsys) -> None:
    assert main(["architect"]) == 0
    output = capsys.readouterr().out.lower()
    assert "tstack architect" in output
    assert "evidence" in output
    assert "## guardrails" in output


def test_validate_command_passes(capsys) -> None:
    assert main(["validate"]) == 0
    output = capsys.readouterr().out
    assert "Verdict: PASS" in output
    assert output.count("PASS") >= len(WORKFLOWS)


def test_validate_json_is_machine_readable(capsys) -> None:
    assert main(["validate", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is True
    assert len(payload["results"]) == len(WORKFLOWS)


def test_init_creates_project_contract(tmp_path, capsys) -> None:
    assert main(["init", str(tmp_path)]) == 0
    assert (tmp_path / ".tstack" / "config.json").is_file()
    assert (tmp_path / ".tstack" / "workflows" / "ship.md").is_file()
    assert "Initialized TStack" in capsys.readouterr().out


def test_init_refuses_overwrite_without_force(tmp_path, capsys) -> None:
    assert main(["init", str(tmp_path)]) == 0
    capsys.readouterr()
    assert main(["init", str(tmp_path)]) == 1
    assert "already initialized" in capsys.readouterr().err


def _create_healthy_project(root) -> None:
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / "tests").mkdir()
    files = {
        "README.md": "# Demo\n",
        "LICENSE": "MIT\n",
        ".gitignore": ".env\n__pycache__/\n",
        "pyproject.toml": '[project]\nname = "demo"\nversion = "1.0.0"\nrequires-python = ">=3.10"\n',
        "requirements.txt": "pytest==8.0.0\n",
        "Pipfile.lock": "{}\n",
        "SECURITY.md": "# Security\n",
        ".github/workflows/ci.yml": "name: CI\n",
        "app.py": "def add(a, b): return a + b\n",
        "tests/test_app.py": "def test_ok(): assert True\n",
    }
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def test_scan_healthy_project_passes_and_is_deterministic(tmp_path) -> None:
    _create_healthy_project(tmp_path)
    first = scan_project(tmp_path)
    second = scan_project(tmp_path)
    assert first.verdict == "PASS"
    assert first.risk_score == 0
    assert first.fingerprint == second.fingerprint
    assert first.languages["Python"] == 2
    assert [profile.name for profile in first.frameworks] == ["Python"]


def test_scan_json_report_and_output_file(tmp_path, capsys) -> None:
    _create_healthy_project(tmp_path)
    output = tmp_path / "audit.json"
    assert main(["scan", str(tmp_path), "--format", "json", "--output", str(output)]) == 0
    assert "Written:" in capsys.readouterr().out
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["verdict"] == "PASS"
    assert payload["files_scanned"] >= 10
    assert payload["frameworks"][0]["name"] == "Python"


def test_node_profile_detects_missing_quality_gates(tmp_path) -> None:
    (tmp_path / "package.json").write_text('{"name":"demo","version":"1.0.0"}', encoding="utf-8")
    report = scan_project(tmp_path)
    rules = {item.rule_id for item in report.findings}
    assert "Node.js" in {profile.name for profile in report.frameworks}
    assert {"NODE002", "NODE003", "NODE004", "NODE005"}.issubset(rules)


def test_android_profile_detects_manifest_and_test_gaps(tmp_path) -> None:
    (tmp_path / "app" / "src" / "main" / "java").mkdir(parents=True)
    (tmp_path / "settings.gradle.kts").write_text('rootProject.name = "Demo"\n', encoding="utf-8")
    (tmp_path / "gradlew").write_text("#!/bin/sh\n", encoding="utf-8")
    (tmp_path / "app" / "src" / "main" / "java" / "MainActivity.kt").write_text("class MainActivity\n", encoding="utf-8")
    report = scan_project(tmp_path)
    rules = {item.rule_id for item in report.findings}
    assert "Android" in {profile.name for profile in report.frameworks}
    assert "AND002" in rules
    assert "AND003" in rules


def test_go_and_rust_profiles_are_detected(tmp_path) -> None:
    (tmp_path / "go.mod").write_text("module example.com/demo\n", encoding="utf-8")
    (tmp_path / "main.go").write_text("package main\n", encoding="utf-8")
    (tmp_path / "Cargo.toml").write_text('[package]\nname = "demo"\nversion = "0.1.0"\n', encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "lib.rs").write_text("pub fn demo() {}\n", encoding="utf-8")
    report = scan_project(tmp_path)
    profiles = {profile.name for profile in report.frameworks}
    rules = {item.rule_id for item in report.findings}
    assert {"Go", "Rust"}.issubset(profiles)
    assert {"GO002", "GO003", "GO004", "RS002", "RS003", "RS004"}.issubset(rules)


def test_scan_holds_on_embedded_secret_without_printing_secret(tmp_path, capsys) -> None:
    (tmp_path / "app.py").write_text('token = "ghp_abcdefghijklmnopqrstuvwxyz1234567890"\n', encoding="utf-8")
    assert main(["scan", str(tmp_path), "--format", "json"]) == 3
    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload["verdict"] == "HOLD"
    assert "ghp_abcdefghijklmnopqrstuvwxyz1234567890" not in output
    assert any(item["rule_id"] == "SEC002" for item in payload["findings"])


def test_scan_fail_on_never_allows_ci_to_continue(tmp_path, capsys) -> None:
    (tmp_path / ".env").write_text("PASSWORD=unsafe-example\n", encoding="utf-8")
    assert main(["scan", str(tmp_path), "--fail-on", "never"]) == 0
    assert "TStack Project Audit" in capsys.readouterr().out


def test_unknown_command_fails() -> None:
    try:
        main(["unknown"])
    except SystemExit as exc:
        assert exc.code != 0
    else:
        raise AssertionError("Unknown command should fail")

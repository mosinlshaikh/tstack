"""Regression tests for the TStack CLI."""

from __future__ import annotations

import json

from tstack.cli import WORKFLOWS, main


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


def test_unknown_command_fails() -> None:
    try:
        main(["unknown"])
    except SystemExit as exc:
        assert exc.code != 0
    else:
        raise AssertionError("Unknown command should fail")

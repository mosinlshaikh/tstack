"""Basic regression tests for the TStack CLI."""

from __future__ import annotations

from tstack.cli import WORKFLOWS, main


def test_list_command(capsys) -> None:
    exit_code = main(["list"])
    output = capsys.readouterr().out.splitlines()

    assert exit_code == 0
    assert output == list(WORKFLOWS)


def test_architect_command_prints_workflow(capsys) -> None:
    exit_code = main(["architect"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "architect" in output.lower()
    assert "evidence" in output.lower()


def test_unknown_command_fails() -> None:
    try:
        main(["unknown"])
    except SystemExit as exc:
        assert exc.code != 0
    else:
        raise AssertionError("Unknown command should fail")

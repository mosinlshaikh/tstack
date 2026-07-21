import json

import pytest

from tstack.cli import main
from tstack.runtime import approve_runtime_request, create_audit_event, create_process_run_request, create_runtime_request, runtime_json


def test_runtime_request_is_hash_bound_and_execution_blocked() -> None:
    request = create_runtime_request("filesystem.move", "Organize Downloads folder", target="Downloads")
    assert request.schema == "tstack-runtime-request/v1"
    assert request.risk == "medium"
    assert request.approval_required is True
    assert request.execution_allowed is False
    assert len(request.request_hash) == 64


def test_process_run_request_binds_exact_action_payload() -> None:
    request = create_process_run_request("Run tests", ("python", "-m", "pytest"), request_id="RUNTIME-PROCESS-1", timeout_seconds=60)
    assert request.schema == "tstack-runtime-request/v2"
    assert request.capability == "process.run"
    assert request.action == {
        "type": "process.run",
        "command": ["python", "-m", "pytest"],
        "cwd": None,
        "write": False,
        "network": False,
        "timeout_seconds": 60,
    }
    assert request.action_hash


def test_runtime_decision_rejects_tampered_request(tmp_path) -> None:
    request = create_runtime_request("filesystem.read", "Inspect project")
    path = tmp_path / "request.json"
    payload = json.loads(runtime_json(request))
    payload["intent"] = "tampered"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        approve_runtime_request(path, approved=True, approver="Mosin", reason="Reviewed.")


def test_runtime_audit_binds_decision_to_request(tmp_path) -> None:
    request = create_runtime_request("project.scan", "Scan repository")
    request_path = tmp_path / "request.json"
    decision_path = tmp_path / "decision.json"
    request_path.write_text(runtime_json(request), encoding="utf-8")
    decision = approve_runtime_request(request_path, approved=True, approver="Mosin", reason="Reviewed.")
    decision_path.write_text(runtime_json(decision), encoding="utf-8")
    event = create_audit_event(request_path, decision_path, outcome="approved")
    assert event.schema == "tstack-runtime-audit/v1"
    assert event.request_hash == request.request_hash
    assert event.decision_hash
    assert "no OS action was executed" in event.notes


def test_runtime_cli_request_json(capsys) -> None:
    assert main(["runtime", "request", "browser.control", "Open local preview", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-runtime-request/v1"
    assert payload["capability"] == "browser.control"
    assert payload["execution_allowed"] is False


def test_runtime_cli_process_request_requires_command(capsys) -> None:
    assert main(["runtime", "request", "process.run", "Run tests", "--format", "json", "--cmd", "python", "-m", "pytest"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-runtime-request/v2"
    assert payload["action"]["command"] == ["python", "-m", "pytest"]
    assert payload["action_hash"]

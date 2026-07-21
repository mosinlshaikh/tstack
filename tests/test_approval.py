import json

from tstack.approval import create_approval_request, decide_approval
from tstack.cli import main


def test_approval_request_classifies_high_risk_action() -> None:
    request = create_approval_request("Deploy to production over SSH")
    assert request.schema == "tstack-approval-request/v1"
    assert request.risk == "high"
    assert request.approval_required is True
    assert request.execution_allowed is False


def test_approval_decision_records_approval_without_execution(tmp_path) -> None:
    request_path = tmp_path / "approval.json"
    assert main(["approval", "request", "Update README", "--format", "json", "--output", str(request_path)]) == 0
    decision = decide_approval(request_path, approved=True, approver="Mosin", reason="Low-risk documentation change.")
    assert decision.approved is True
    assert decision.execution_allowed is False


def test_approval_cli_decide_json(tmp_path, capsys) -> None:
    request_path = tmp_path / "approval.json"
    assert main(["approval", "request", "Change auth config", "--format", "json", "--output", str(request_path)]) == 0
    capsys.readouterr()
    assert main(["approval", "decide", str(request_path), "--approved", "--approver", "Mosin", "--reason", "Reviewed plan.", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-approval-decision/v1"
    assert payload["approved"] is True
    assert payload["execution_allowed"] is False

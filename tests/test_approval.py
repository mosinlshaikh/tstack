import json

from tstack.approval import create_approval_request, decide_approval, evaluate_readiness
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


def test_approval_readiness_stays_blocked_without_executor(tmp_path) -> None:
    request_path = tmp_path / "approval.json"
    decision_path = tmp_path / "decision.json"
    assert main(["approval", "request", "Update README", "--format", "json", "--output", str(request_path)]) == 0
    assert main(["approval", "decide", str(request_path), "--approved", "--approver", "Mosin", "--reason", "Reviewed.", "--format", "json", "--output", str(decision_path)]) == 0
    readiness = evaluate_readiness(request_path, decision_path)
    assert readiness.schema == "tstack-approval-readiness/v1"
    assert readiness.approved is True
    assert readiness.ready is False
    assert readiness.execution_allowed is False
    assert "execution executor is not implemented" in readiness.blockers


def test_approval_readiness_cli_json(tmp_path, capsys) -> None:
    request_path = tmp_path / "approval.json"
    decision_path = tmp_path / "decision.json"
    assert main(["approval", "request", "Deploy to production", "--format", "json", "--output", str(request_path)]) == 0
    assert main(["approval", "decide", str(request_path), "--approved", "--approver", "Mosin", "--reason", "Reviewed.", "--format", "json", "--output", str(decision_path)]) == 0
    capsys.readouterr()
    assert main(["approval", "readiness", str(request_path), str(decision_path), "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-approval-readiness/v1"
    assert payload["ready"] is False
    assert payload["execution_allowed"] is False

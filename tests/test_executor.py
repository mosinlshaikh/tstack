import json

from tstack.cli import main
from tstack.executor import plan_execution


def _approval_pair(tmp_path, action: str):
    request = tmp_path / "request.json"
    decision = tmp_path / "decision.json"
    assert main(["approval", "request", action, "--format", "json", "--output", str(request)]) == 0
    assert main(["approval", "decide", str(request), "--approved", "--approver", "Mosin", "--reason", "Reviewed.", "--format", "json", "--output", str(decision)]) == 0
    return request, decision


def test_executor_allows_low_risk_documentation_dry_run_plan(tmp_path) -> None:
    request, decision = _approval_pair(tmp_path, "Update README documentation")
    plan = plan_execution(request, decision)
    assert plan.schema == "tstack-execution-plan/v1"
    assert plan.executable is True
    assert plan.execution_allowed is False
    assert plan.mode == "dry-run"


def test_executor_blocks_high_risk_action(tmp_path) -> None:
    request, decision = _approval_pair(tmp_path, "Deploy to production over SSH")
    plan = plan_execution(request, decision)
    assert plan.executable is False
    assert "only low-risk actions are eligible for executor planning" in plan.blockers


def test_executor_cli_returns_blocked_exit_for_high_risk(tmp_path, capsys) -> None:
    request, decision = _approval_pair(tmp_path, "Deploy to production over SSH")
    capsys.readouterr()
    assert main(["execute", "plan", str(request), str(decision), "--format", "json"]) == 15
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-execution-plan/v1"
    assert payload["executable"] is False
    assert payload["execution_allowed"] is False

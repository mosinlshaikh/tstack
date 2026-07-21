import json

from tstack.cli import main
from tstack.sandbox import default_sandbox_policy, plan_sandbox_command, run_sandbox_command
from tstack.runtime import approve_runtime_request, create_process_run_request, create_runtime_request, runtime_json


def _process_approval(tmp_path, command=("python", "-c", "print('ok')")):
    request = create_process_run_request("Run sandboxed command", command, request_id="RUNTIME-PROCESS-1")
    request_path = tmp_path / "request.json"
    decision_path = tmp_path / "decision.json"
    request_path.write_text(runtime_json(request), encoding="utf-8")
    decision = approve_runtime_request(request_path, approved=True, approver="Mosin", reason="Reviewed sandbox command.")
    decision_path.write_text(runtime_json(decision), encoding="utf-8")
    return request_path, decision_path


def test_sandbox_plan_blocks_unlisted_command(tmp_path) -> None:
    policy = default_sandbox_policy(tmp_path)
    plan = plan_sandbox_command(policy, ("powershell", "Remove-Item", "x"))
    assert plan.schema == "tstack-sandbox-plan/v1"
    assert plan.execution_allowed is False
    assert any("not allowlisted" in blocker for blocker in plan.blockers)


def test_sandbox_plan_blocks_workspace_escape(tmp_path) -> None:
    policy = default_sandbox_policy(tmp_path)
    outside = tmp_path.parent
    plan = plan_sandbox_command(policy, ("python", "-m", "pytest"), cwd=outside)
    assert any("escapes" in blocker for blocker in plan.blockers)


def test_sandbox_plan_blocks_shell_metacharacters(tmp_path) -> None:
    policy = default_sandbox_policy(tmp_path)
    plan = plan_sandbox_command(policy, ("python", "-c", "print(1); rm -rf x"))
    assert any("shell metacharacters" in blocker for blocker in plan.blockers)


def test_sandbox_cli_plan_json(capsys, tmp_path) -> None:
    policy_path = tmp_path / "policy.json"
    assert main(["sandbox", "init", str(tmp_path), "--output", str(policy_path)]) == 0
    capsys.readouterr()
    assert main(["sandbox", "plan", str(policy_path), "--format", "json", "--cmd", "python", "-m", "pytest"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-sandbox-plan/v1"
    assert payload["execution_allowed"] is False
    assert payload["blockers"] == []


def test_sandbox_run_executes_allowlisted_command(tmp_path) -> None:
    policy = default_sandbox_policy(tmp_path)
    request_path, decision_path = _process_approval(tmp_path)
    result = run_sandbox_command(policy, ("python", "-c", "print('ok')"), request_path=request_path, decision_path=decision_path)
    assert result.schema == "tstack-sandbox-result/v1"
    assert result.executed is True
    assert result.exit_code == 0
    assert result.stdout.strip() == "ok"


def test_sandbox_run_refuses_blocked_command(tmp_path) -> None:
    policy = default_sandbox_policy(tmp_path)
    request_path, decision_path = _process_approval(tmp_path)
    result = run_sandbox_command(policy, ("powershell", "Get-ChildItem"), request_path=request_path, decision_path=decision_path)
    assert result.executed is False
    assert result.exit_code is None
    assert result.blockers


def test_sandbox_run_refuses_action_payload_mismatch(tmp_path) -> None:
    policy = default_sandbox_policy(tmp_path)
    request_path, decision_path = _process_approval(tmp_path, command=("python", "-c", "print('approved')"))
    result = run_sandbox_command(policy, ("python", "-c", "print('different')"), request_path=request_path, decision_path=decision_path)
    assert result.executed is False
    assert any("approved action payload does not match" in blocker for blocker in result.blockers)


def test_sandbox_run_refuses_generic_process_approval(tmp_path) -> None:
    policy = default_sandbox_policy(tmp_path)
    request = create_runtime_request("process.run", "Generic command approval", request_id="RUNTIME-GENERIC")
    request_path = tmp_path / "request.json"
    decision_path = tmp_path / "decision.json"
    request_path.write_text(runtime_json(request), encoding="utf-8")
    decision = approve_runtime_request(request_path, approved=True, approver="Mosin", reason="Generic approval")
    decision_path.write_text(runtime_json(decision), encoding="utf-8")
    result = run_sandbox_command(policy, ("python", "-c", "print('ok')"), request_path=request_path, decision_path=decision_path)
    assert result.executed is False
    assert any("action-bound runtime request v2" in blocker for blocker in result.blockers)


def test_sandbox_cli_run_json(capsys, tmp_path) -> None:
    policy_path = tmp_path / "policy.json"
    request_path, decision_path = _process_approval(tmp_path)
    assert main(["sandbox", "init", str(tmp_path), "--output", str(policy_path)]) == 0
    capsys.readouterr()
    assert main(["sandbox", "run", str(policy_path), str(request_path), str(decision_path), "--format", "json", "--cmd", "python", "-c", "print('ok')"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-sandbox-result/v1"
    assert payload["executed"] is True
    assert payload["stdout"].strip() == "ok"

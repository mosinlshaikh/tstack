import json

from tstack.cli import main
from tstack.sandbox import default_sandbox_policy, plan_sandbox_command


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

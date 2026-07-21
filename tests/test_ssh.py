import json

from tstack.cli import main
from tstack.ssh import default_ssh_policy_json, plan_ssh_command


def test_default_ssh_policy_is_plan_only() -> None:
    policy = json.loads(default_ssh_policy_json())
    assert policy["schema"] == "tstack-ssh-policy/v1"
    assert policy["mode"] == "plan-only"
    assert policy["approval_required"] is True
    assert policy["allowed_targets"] == []
    assert policy["allowed_commands"] == []


def test_ssh_plan_blocks_unallowlisted_target_and_command() -> None:
    policy = json.loads(default_ssh_policy_json())
    plan = plan_ssh_command(policy, target="prod", command="uptime")
    assert plan.valid is False
    assert plan.execution_allowed is False
    assert any("target is not allowlisted" in reason for reason in plan.reasons)
    assert any("command is not allowlisted" in reason for reason in plan.reasons)


def test_ssh_plan_passes_when_target_and_command_are_allowlisted() -> None:
    policy = json.loads(default_ssh_policy_json())
    policy["allowed_targets"] = ["prod"]
    policy["allowed_commands"] = ["uptime"]
    plan = plan_ssh_command(policy, target="prod", command="uptime", user="deploy")
    assert plan.valid is True
    assert plan.user == "deploy"
    assert plan.port == 22
    assert plan.approval_required is True
    assert plan.execution_allowed is False


def test_ssh_plan_blocks_dangerous_command_pattern() -> None:
    policy = json.loads(default_ssh_policy_json())
    policy["allowed_targets"] = ["prod"]
    policy["allowed_commands"] = [".*"]
    plan = plan_ssh_command(policy, target="prod", command="sudo rm -rf /")
    assert plan.valid is False
    assert any("blocked pattern" in reason for reason in plan.reasons)


def test_ssh_init_and_plan_cli(tmp_path, capsys) -> None:
    assert main(["ssh", "init", str(tmp_path)]) == 0
    policy_path = tmp_path / ".tstack" / "ssh-policy.json"
    assert policy_path.is_file()
    assert "Written:" in capsys.readouterr().out

    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy["allowed_targets"] = ["prod"]
    policy["allowed_commands"] = ["uptime"]
    policy_path.write_text(json.dumps(policy, indent=2), encoding="utf-8")

    assert main(["ssh", "plan", "prod", "uptime", "--policy", str(policy_path), "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-ssh-plan/v1"
    assert payload["valid"] is True
    assert payload["execution_allowed"] is False


def test_ssh_plan_cli_returns_policy_failure(tmp_path, capsys) -> None:
    assert main(["ssh", "init", str(tmp_path)]) == 0
    capsys.readouterr()
    policy_path = tmp_path / ".tstack" / "ssh-policy.json"
    assert main(["ssh", "plan", "prod", "uptime", "--policy", str(policy_path)]) == 13
    assert "Verdict: **HOLD**" in capsys.readouterr().out

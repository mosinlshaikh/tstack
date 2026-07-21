import json

from tstack.agentic import build_agent_plan
from tstack.cli import main


def test_agent_plan_includes_uiux_and_deployment() -> None:
    plan = build_agent_plan("Build a SaaS CRM from scratch")
    names = [phase.name for phase in plan.phases]
    assert "Advanced UI/UX Design" in names
    assert "Deployment Plan" in names
    assert all(phase.approval_required for phase in plan.phases)
    assert all(not phase.execution_allowed for phase in plan.phases)
    assert plan.mode == "plan-only"


def test_agent_plan_can_disable_optional_phases() -> None:
    plan = build_agent_plan("Build API", include_uiux=False, include_deployment=False)
    names = [phase.name for phase in plan.phases]
    assert "Advanced UI/UX Design" not in names
    assert "Deployment Plan" not in names


def test_agent_plan_rejects_empty_goal() -> None:
    try:
        build_agent_plan(" ")
    except ValueError as exc:
        assert "agent goal is required" in str(exc)
    else:
        raise AssertionError("empty goal should fail")


def test_agent_plan_cli_json(capsys) -> None:
    assert main(["agent", "plan", "Build advanced UI product", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-agent-plan/v1"
    assert payload["mode"] == "plan-only"
    assert any(phase["name"] == "Advanced UI/UX Design" for phase in payload["phases"])
    assert all(phase["execution_allowed"] is False for phase in payload["phases"])

import json

from tstack.agentic import build_orchestration_plan
from tstack.cli import main


def test_orchestration_maps_agents_to_delivery_phases() -> None:
    plan = build_orchestration_plan("Medical Store Management System website with admin panel and deployment")
    assert plan.schema == "tstack-agent-orchestration/v1"
    assert plan.selected_agent_count >= 20
    phase_names = [phase.phase_name for phase in plan.phases]
    assert "Advanced UI/UX" in phase_names
    assert "Release and Deployment" in phase_names
    deployment_phase = next(phase for phase in plan.phases if phase.phase_name == "Release and Deployment")
    assert "deployment-agent" in deployment_phase.agents
    assert all(not phase.execution_allowed for phase in plan.phases)


def test_agent_orchestrate_cli_json(capsys) -> None:
    assert main(["agent", "orchestrate", "AI chatbot with semantic search and analytics dashboard", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-agent-orchestration/v1"
    assert payload["execution_allowed"] is False
    phases = {phase["phase_name"]: phase for phase in payload["phases"]}
    assert "Business and AI Features" in phases
    assert "ai-chatbot-agent" in phases["Business and AI Features"]["agents"]

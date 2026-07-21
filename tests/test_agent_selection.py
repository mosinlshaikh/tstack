import json

from tstack.agentic import select_agents_for_goal
from tstack.cli import main


def test_select_agents_for_website_management_system() -> None:
    selection = select_agents_for_goal("Medical Store Management System website with admin panel and deployment")
    ids = {agent.id for agent in selection.selected_agents}
    assert "website-builder-agent" in ids
    assert "ui-ux-agent" in ids
    assert "frontend-agent" in ids
    assert "backend-agent" in ids
    assert "database-agent" in ids
    assert "deployment-agent" in ids
    assert selection.execution_allowed is False


def test_select_agents_for_ai_analytics_goal() -> None:
    selection = select_agents_for_goal("AI chatbot with semantic search and analytics dashboard")
    ids = {agent.id for agent in selection.selected_agents}
    assert "ai-chatbot-agent" in ids
    assert "semantic-search-agent" in ids
    assert "analytics-agent" in ids
    assert "ui-ux-agent" in ids


def test_agent_select_cli_json(capsys) -> None:
    assert main(["agent", "select", "CRM website with billing and deployment", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-agent-selection/v1"
    ids = {agent["id"] for agent in payload["selected_agents"]}
    assert {"crm-agent", "finance-agent", "website-builder-agent", "deployment-agent"}.issubset(ids)

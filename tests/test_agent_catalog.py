import json

from tstack.agentic import get_agent, list_agents
from tstack.cli import main


def test_agent_catalog_has_50_specialized_agents() -> None:
    agents = list_agents()
    assert len(agents) >= 50
    ids = {agent.id for agent in agents}
    assert {"architect-agent", "developer-agent", "ui-ux-agent", "orchestrator-agent", "website-builder-agent"}.issubset(ids)
    assert all(agent.approval_required for agent in agents)
    assert all(not agent.execution_allowed for agent in agents)
    assert all(isinstance(agent.permissions, tuple) for agent in agents)


def test_agent_catalog_categories_are_present() -> None:
    categories = {agent.category for agent in list_agents()}
    assert {"engineering", "business", "data-ai", "operations", "governance", "design", "orchestration"}.issubset(categories)


def test_get_unknown_agent_fails() -> None:
    try:
        get_agent("missing-agent")
    except KeyError as exc:
        assert "unknown agent" in str(exc)
    else:
        raise AssertionError("unknown agent should fail")


def test_agent_catalog_cli_json(capsys) -> None:
    assert main(["agent", "catalog", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-agent-catalog/v1"
    assert payload["count"] >= 50


def test_agent_show_cli_json(capsys) -> None:
    assert main(["agent", "show", "ui-ux-agent", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["count"] == 1
    assert payload["agents"][0]["name"] == "UI/UX Agent"

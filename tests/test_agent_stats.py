import json

from tstack.agentic import agent_stats
from tstack.cli import main


def test_agent_stats_counts_catalog_and_boundaries() -> None:
    stats = agent_stats()
    assert stats.schema == "tstack-agent-stats/v1"
    assert stats.total_agents >= 50
    assert stats.approval_required == stats.total_agents
    assert stats.execution_allowed == 0
    assert stats.categories["engineering"] >= 10
    assert stats.categories["governance"] >= 5


def test_agent_stats_cli_json(capsys) -> None:
    assert main(["agent", "stats", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-agent-stats/v1"
    assert payload["total_agents"] >= 50
    assert payload["execution_allowed"] == 0

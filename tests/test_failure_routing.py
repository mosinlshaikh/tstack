import json

from tstack.agentic import route_failure
from tstack.cli import main


def test_routes_pytest_failure_to_qa_agent() -> None:
    route = route_failure("pytest failed: assertion error in test_cli")
    assert route.schema == "tstack-failure-route/v1"
    assert route.failure_type == "test"
    assert route.primary_agent == "qa-agent"
    assert "developer-agent" in route.supporting_agents
    assert route.execution_allowed is False


def test_routes_security_failure_to_security_agent() -> None:
    route = route_failure("secret scanning found exposed token")
    assert route.failure_type == "security"
    assert route.primary_agent == "security-agent"
    assert "policy-agent" in route.supporting_agents


def test_route_failure_cli_json(capsys) -> None:
    assert main(["agent", "route-failure", "GitHub Actions build workflow failed", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-failure-route/v1"
    assert payload["failure_type"] == "devops"
    assert payload["primary_agent"] == "devops-agent"
    assert payload["execution_allowed"] is False

import json

from tstack.bug import find_bugs
from tstack.cli import main


def test_bug_finder_routes_failure_to_owner_agent(tmp_path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    report = find_bugs(tmp_path, failure="pytest failed assertion in test_app")
    assert report.schema == "tstack-bug-report/v1"
    assert report.verdict == "REVIEW"
    assert report.findings[0].owner_agent == "qa-agent"
    assert report.execution_allowed is False


def test_bug_finder_includes_scan_findings(tmp_path) -> None:
    (tmp_path / ".env").write_text("PASSWORD=unsafe-example\n", encoding="utf-8")
    report = find_bugs(tmp_path)
    assert report.verdict in {"REVIEW", "HOLD"}
    assert any(item.id.startswith("BUG-SCAN") for item in report.findings)


def test_bug_find_cli_json_returns_review_exit(capsys, tmp_path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    assert main(["bug", "find", str(tmp_path), "--failure", "GitHub Actions build failed", "--format", "json"]) == 16
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-bug-report/v1"
    assert payload["findings"][0]["owner_agent"] == "devops-agent"
    assert payload["execution_allowed"] is False

"""Policy, baseline, diff, and SARIF regression tests."""

from __future__ import annotations

import json

from tstack.cli import main
from tstack.policy import Policy, diff_report, evaluate_policy, finding_key, report_sarif
from tstack.scanner import scan_project


def _project(root) -> None:
    (root / "app.py").write_text("print('ok')\n", encoding="utf-8")


def test_policy_can_suppress_rule_without_deleting_audit_evidence(tmp_path) -> None:
    _project(tmp_path)
    report = scan_project(tmp_path)
    target = report.findings[0].rule_id
    result = evaluate_policy(report, Policy(fail_on="critical", max_risk_score=100, allow_rules=(target,)))
    assert any(item.rule_id == target for item in result.suppressed_findings)
    assert all(item.rule_id != target for item in result.active_findings)


def test_policy_threshold_blocks_high_findings(tmp_path) -> None:
    (tmp_path / ".env").write_text("PASSWORD=unsafe-example\n", encoding="utf-8")
    report = scan_project(tmp_path)
    result = evaluate_policy(report, Policy(fail_on="high", max_risk_score=100))
    assert result.passed is False
    assert result.reasons


def test_baseline_diff_detects_new_and_resolved_findings(tmp_path, capsys) -> None:
    _project(tmp_path)
    baseline = tmp_path / "baseline.json"
    assert main(["baseline", str(tmp_path), "--output", str(baseline)]) == 0
    capsys.readouterr()
    (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")
    (tmp_path / ".env").write_text("PASSWORD=unsafe-example\n", encoding="utf-8")
    assert main(["diff", str(tmp_path), "--baseline", str(baseline), "--format", "json", "--fail-on-new"]) == 4
    payload = json.loads(capsys.readouterr().out)
    assert payload["new"]
    assert payload["resolved"]


def test_sarif_is_valid_and_does_not_embed_secret_value(tmp_path) -> None:
    secret = "ghp_" + "abcdefghijklmnopqrstuvwxyz1234567890"
    fixture_line = "tok" + f'en = "{secret}"\n'
    (tmp_path / "app.py").write_text(fixture_line, encoding="utf-8")
    report = scan_project(tmp_path)
    payload_text = report_sarif(report)
    payload = json.loads(payload_text)
    assert payload["version"] == "2.1.0"
    assert payload["runs"][0]["results"]
    assert secret not in payload_text


def test_policy_init_and_scan_sarif_cli(tmp_path, capsys) -> None:
    _project(tmp_path)
    assert main(["policy-init", str(tmp_path)]) == 0
    assert (tmp_path / ".tstack" / "policy.json").is_file()
    capsys.readouterr()
    assert main(["scan", str(tmp_path), "--format", "sarif", "--fail-on", "never"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["runs"][0]["tool"]["driver"]["name"] == "TStack"


def test_finding_key_is_stable(tmp_path) -> None:
    _project(tmp_path)
    report = scan_project(tmp_path)
    assert finding_key(report.findings[0]) == finding_key(report.findings[0])

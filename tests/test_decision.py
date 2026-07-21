"""Regression tests for the explainable decision brain."""
from __future__ import annotations

from tstack.decision import build_plan


def test_decision_plan_ranks_critical_first_and_requires_approval() -> None:
    scan = {"fingerprint": "abc", "findings": [
        {"rule_id": "QA001", "severity": "high", "title": "Tests missing", "path": None, "evidence": "No tests", "remediation": "Add tests."},
        {"rule_id": "SEC002", "severity": "critical", "title": "Secret", "path": "app.py", "evidence": "Pattern matched", "remediation": "Rotate secret."},
    ]}
    memory = {"schema": "tstack-learning-memory/v1", "records": {}}
    plan = build_plan(scan, memory)
    assert plan.verdict == "HOLD"
    assert plan.actions[0].rule_id == "SEC002"
    assert all(item.approval_required for item in plan.actions)
    assert all(not item.execution_allowed for item in plan.actions)


def test_learning_history_increases_priority() -> None:
    scan = {"findings": [
        {"rule_id": "QA001", "severity": "medium", "title": "Tests", "path": None, "evidence": "Missing", "remediation": "Add tests."},
        {"rule_id": "OPS001", "severity": "medium", "title": "Ignore", "path": None, "evidence": "Missing", "remediation": "Add ignore."},
    ]}
    memory = {"schema": "tstack-learning-memory/v1", "records": {
        "QA001\u0000": {"rule_id": "QA001", "path": None, "severity": "medium", "occurrences": 10, "accepted": 3, "rejected": 0, "resolved": 2, "last_title": "Tests", "last_remediation": "Add tests."}
    }}
    plan = build_plan(scan, memory)
    assert plan.actions[0].rule_id == "QA001"
    assert plan.actions[0].confidence > 0.5


def test_empty_findings_produce_pass() -> None:
    plan = build_plan({"findings": []}, {"schema": "tstack-learning-memory/v1", "records": {}})
    assert plan.verdict == "PASS"
    assert plan.actions == ()

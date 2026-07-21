from __future__ import annotations

import json

import pytest

from tstack.learning import apply_feedback, learn_findings, load_memory, recommendations, save_memory


def test_learning_counts_recurrence_and_ranks(tmp_path) -> None:
    memory = load_memory(tmp_path / "memory.json")
    finding = {"rule_id": "QA001", "severity": "high", "title": "Tests missing", "path": None, "remediation": "Add tests."}
    learn_findings(memory, [finding])
    learn_findings(memory, [finding])
    items = recommendations(memory)
    assert len(items) == 1
    assert items[0].rule_id == "QA001"
    assert items[0].priority > 0


def test_feedback_changes_confidence(tmp_path) -> None:
    memory = load_memory(tmp_path / "memory.json")
    finding = {"rule_id": "OPS001", "severity": "medium", "title": ".gitignore missing", "path": None}
    learn_findings(memory, [finding, finding])
    before = recommendations(memory)[0].confidence
    apply_feedback(memory, rule_id="OPS001", path=None, outcome="resolved")
    after = recommendations(memory)[0].confidence
    assert after > before


def test_unknown_feedback_fails_closed(tmp_path) -> None:
    memory = load_memory(tmp_path / "memory.json")
    with pytest.raises(KeyError):
        apply_feedback(memory, rule_id="UNKNOWN", path=None, outcome="accepted")


def test_memory_round_trip(tmp_path) -> None:
    target = tmp_path / "memory.json"
    memory = load_memory(target)
    learn_findings(memory, [{"rule_id": "SEC003", "severity": "low", "title": "Policy missing", "path": None}])
    save_memory(target, memory)
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["schema"] == "tstack-learning-memory/v1"
    assert load_memory(target) == payload

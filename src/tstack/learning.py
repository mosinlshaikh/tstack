"""Local, explainable learning memory for TStack.

This module learns from scan findings and explicit human feedback. It does not
train a neural model, modify source code, deploy changes, or execute commands.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class LearningRecord:
    rule_id: str
    path: str | None
    severity: str
    occurrences: int
    accepted: int
    rejected: int
    resolved: int
    last_title: str
    last_remediation: str


@dataclass(frozen=True)
class Recommendation:
    rule_id: str
    path: str | None
    confidence: float
    priority: float
    rationale: str
    remediation: str


def _key(rule_id: str, path: str | None) -> str:
    return f"{rule_id}\0{path or ''}"


def load_memory(path: Path) -> dict:
    source = path.expanduser().resolve()
    if not source.exists():
        return {"schema": "tstack-learning-memory/v1", "records": {}}
    payload = json.loads(source.read_text(encoding="utf-8"))
    if payload.get("schema") != "tstack-learning-memory/v1" or not isinstance(payload.get("records"), dict):
        raise ValueError("invalid TStack learning memory schema")
    return payload


def save_memory(path: Path, memory: dict) -> None:
    destination = path.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(memory, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def learn_findings(memory: dict, findings: Iterable[dict]) -> dict:
    records = memory.setdefault("records", {})
    for item in findings:
        rule_id = str(item["rule_id"])
        path = str(item["path"]) if item.get("path") is not None else None
        key = _key(rule_id, path)
        current = records.get(key, {})
        records[key] = {
            "rule_id": rule_id,
            "path": path,
            "severity": str(item.get("severity", "medium")),
            "occurrences": int(current.get("occurrences", 0)) + 1,
            "accepted": int(current.get("accepted", 0)),
            "rejected": int(current.get("rejected", 0)),
            "resolved": int(current.get("resolved", 0)),
            "last_title": str(item.get("title", rule_id)),
            "last_remediation": str(item.get("remediation", "Review and resolve the finding.")),
        }
    return memory


def apply_feedback(memory: dict, *, rule_id: str, path: str | None, outcome: str) -> dict:
    if outcome not in {"accepted", "rejected", "resolved"}:
        raise ValueError("outcome must be accepted, rejected, or resolved")
    key = _key(rule_id, path)
    record = memory.setdefault("records", {}).get(key)
    if record is None:
        raise KeyError(f"learning record not found: {rule_id} {path or ''}".strip())
    record[outcome] = int(record.get(outcome, 0)) + 1
    return memory


def recommendations(memory: dict, *, minimum_occurrences: int = 2) -> tuple[Recommendation, ...]:
    weights = {"low": 1.0, "medium": 2.0, "high": 4.0, "critical": 8.0}
    result: list[Recommendation] = []
    for raw in memory.get("records", {}).values():
        occurrences = int(raw.get("occurrences", 0))
        if occurrences < minimum_occurrences:
            continue
        accepted = int(raw.get("accepted", 0))
        rejected = int(raw.get("rejected", 0))
        resolved = int(raw.get("resolved", 0))
        feedback_total = accepted + rejected + resolved
        confidence = (accepted + resolved + 1) / (feedback_total + 2)
        recurrence = min(1.0, occurrences / 10.0)
        priority = weights.get(str(raw.get("severity", "medium")), 2.0) * (0.5 + recurrence) * confidence
        rationale = f"Seen {occurrences} times; accepted={accepted}, resolved={resolved}, rejected={rejected}."
        result.append(Recommendation(str(raw["rule_id"]), raw.get("path"), round(confidence, 4), round(priority, 4), rationale, str(raw.get("last_remediation", "Review finding."))))
    result.sort(key=lambda item: (-item.priority, item.rule_id, item.path or ""))
    return tuple(result)


def memory_json(memory: dict) -> str:
    return json.dumps(memory, indent=2, sort_keys=True) + "\n"


def recommendations_json(items: Iterable[Recommendation]) -> str:
    return json.dumps([asdict(item) for item in items], indent=2, sort_keys=True) + "\n"

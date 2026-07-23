import json

import pytest

from tstack.audited_execution import execute_with_journal
from tstack.execution_journal import append_execution_event, verify_execution_journal
from tstack.secure_execution import SecureExecutionReceipt


def test_execution_journal_detects_tampering(tmp_path) -> None:
    journal = tmp_path / "execution.jsonl"
    append_execution_event(
        journal,
        execution_id="EXEC-1",
        request_id="REQ-1",
        capability="process.run",
        state="started",
    )
    valid, errors = verify_execution_journal(journal)
    assert valid is True
    assert errors == ()

    payload = json.loads(journal.read_text(encoding="utf-8").splitlines()[0])
    payload["state"] = "tampered"
    journal.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    valid, errors = verify_execution_journal(journal)
    assert valid is False
    assert errors


def test_audited_execution_records_completed_result_hash(tmp_path) -> None:
    journal = tmp_path / "execution.jsonl"

    def operation() -> SecureExecutionReceipt:
        return SecureExecutionReceipt(
            "tstack-secure-execution/v1",
            "EXEC-2",
            "REQ-2",
            "process.run",
            "succeeded",
            {"exit_code": 0},
        )

    receipt = execute_with_journal(
        operation,
        journal_path=journal,
        execution_id="EXEC-2",
        request_id="REQ-2",
        capability="process.run",
    )
    assert receipt.status == "succeeded"
    entries = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines()]
    assert [entry["state"] for entry in entries] == ["started", "completed"]
    assert entries[-1]["result_hash"]
    valid, errors = verify_execution_journal(journal)
    assert valid is True
    assert errors == ()


def test_audited_execution_records_failure_before_reraise(tmp_path) -> None:
    journal = tmp_path / "execution.jsonl"

    def operation() -> SecureExecutionReceipt:
        raise RuntimeError("simulated failure")

    with pytest.raises(RuntimeError, match="simulated failure"):
        execute_with_journal(
            operation,
            journal_path=journal,
            execution_id="EXEC-3",
            request_id="REQ-3",
            capability="filesystem.move",
        )
    entries = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines()]
    assert [entry["state"] for entry in entries] == ["started", "failed"]
    assert entries[-1]["details"]["error_type"] == "RuntimeError"

"""Automatic durable journaling around signed secure execution."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Callable

from tstack.execution_journal import append_execution_event
from tstack.secure_execution import SecureExecutionReceipt


def execute_with_journal(
    operation: Callable[[], SecureExecutionReceipt],
    *,
    journal_path: Path,
    execution_id: str,
    request_id: str,
    capability: str,
) -> SecureExecutionReceipt:
    """Run one secure action with mandatory started/completed/failed events.

    The caller supplies identifiers from the signed request context. A durable
    started event is fsynced before the operation begins. Completion includes a
    SHA-256 digest of the exact receipt. Failures are journaled before being
    re-raised so recovery tooling can locate interrupted or failed executions.
    """
    append_execution_event(
        journal_path,
        execution_id=execution_id,
        request_id=request_id,
        capability=capability,
        state="started",
        details={"authorization": "signed-single-use"},
    )
    try:
        receipt = operation()
    except Exception as exc:
        append_execution_event(
            journal_path,
            execution_id=execution_id,
            request_id=request_id,
            capability=capability,
            state="failed",
            details={"error_type": type(exc).__name__, "error": str(exc)[:1000]},
        )
        raise
    append_execution_event(
        journal_path,
        execution_id=receipt.execution_id,
        request_id=receipt.request_id,
        capability=receipt.capability,
        state="completed",
        details={"status": receipt.status},
        result=asdict(receipt),
    )
    return receipt

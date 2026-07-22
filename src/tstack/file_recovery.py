"""Crash-recovery journal for approved file move transactions."""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FILE_RECOVERY_SCHEMA = "tstack-file-recovery/v1"
TERMINAL_STATES = {"COMMITTED", "ROLLED_BACK", "FAILED"}


@dataclass(frozen=True)
class RecoveryEvent:
    schema: str
    sequence: int
    transaction_id: str
    state: str
    source: str | None
    destination: str | None
    details: dict[str, Any]
    previous_hash: str
    event_hash: str
    timestamp_utc: str


@dataclass(frozen=True)
class RecoveryReport:
    transaction_id: str
    valid: bool
    terminal: bool
    latest_state: str | None
    moved_pairs: tuple[tuple[str, str], ...]
    errors: tuple[str, ...]


def _canonical(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(payload)).hexdigest()


def append_recovery_event(
    journal_path: Path,
    *,
    transaction_id: str,
    state: str,
    source: str | None = None,
    destination: str | None = None,
    details: dict[str, Any] | None = None,
) -> RecoveryEvent:
    events = read_recovery_events(journal_path)
    previous_hash = events[-1].event_hash if events else "0" * 64
    sequence = len(events) + 1
    base = {
        "schema": FILE_RECOVERY_SCHEMA,
        "sequence": sequence,
        "transaction_id": transaction_id,
        "state": state,
        "source": source,
        "destination": destination,
        "details": details or {},
        "previous_hash": previous_hash,
        "timestamp_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    event = RecoveryEvent(**base, event_hash=_hash(base))
    resolved = journal_path.expanduser().resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with resolved.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(event), sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return event


def read_recovery_events(journal_path: Path) -> list[RecoveryEvent]:
    resolved = journal_path.expanduser().resolve()
    if not resolved.exists():
        return []
    result: list[RecoveryEvent] = []
    for line_number, line in enumerate(resolved.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if payload.get("schema") != FILE_RECOVERY_SCHEMA:
            raise ValueError(f"invalid recovery schema at line {line_number}")
        result.append(RecoveryEvent(**payload))
    return result


def inspect_recovery_journal(journal_path: Path) -> RecoveryReport:
    try:
        events = read_recovery_events(journal_path)
    except Exception as exc:
        return RecoveryReport("unknown", False, False, None, (), (str(exc),))
    if not events:
        return RecoveryReport("unknown", False, False, None, (), ("journal is empty",))
    errors: list[str] = []
    previous_hash = "0" * 64
    transaction_id = events[0].transaction_id
    moved: list[tuple[str, str]] = []
    for expected_sequence, event in enumerate(events, 1):
        if event.sequence != expected_sequence:
            errors.append(f"sequence mismatch at {expected_sequence}")
        if event.transaction_id != transaction_id:
            errors.append(f"transaction id mismatch at {expected_sequence}")
        if event.previous_hash != previous_hash:
            errors.append(f"previous hash mismatch at {expected_sequence}")
        unsigned = asdict(event)
        supplied_hash = unsigned.pop("event_hash")
        if _hash(unsigned) != supplied_hash:
            errors.append(f"event hash mismatch at {expected_sequence}")
        if event.state == "MOVED" and event.source and event.destination:
            moved.append((event.source, event.destination))
        previous_hash = event.event_hash
    latest_state = events[-1].state
    return RecoveryReport(transaction_id, not errors, latest_state in TERMINAL_STATES, latest_state, tuple(moved), tuple(errors))


def recover_interrupted_transaction(journal_path: Path, *, root: Path) -> RecoveryReport:
    report = inspect_recovery_journal(journal_path)
    if not report.valid:
        raise ValueError("recovery journal validation failed: " + "; ".join(report.errors))
    if report.terminal:
        return report
    resolved_root = root.expanduser().resolve()
    for source_text, destination_text in reversed(report.moved_pairs):
        source = (resolved_root / source_text).resolve()
        destination = (resolved_root / destination_text).resolve()
        if resolved_root != source and resolved_root not in source.parents:
            raise ValueError("recovery source escapes root")
        if resolved_root != destination and resolved_root not in destination.parents:
            raise ValueError("recovery destination escapes root")
        if destination.exists() and not source.exists():
            source.parent.mkdir(parents=True, exist_ok=True)
            destination.rename(source)
            append_recovery_event(
                journal_path,
                transaction_id=report.transaction_id,
                state="RESTORED",
                source=destination_text,
                destination=source_text,
            )
    append_recovery_event(journal_path, transaction_id=report.transaction_id, state="ROLLED_BACK")
    return inspect_recovery_journal(journal_path)

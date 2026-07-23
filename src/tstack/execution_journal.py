"""Durable execution journal for secure runtime actions."""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

EXECUTION_JOURNAL_SCHEMA = "tstack-execution-journal/v1"
GENESIS_HASH = "0" * 64


@dataclass(frozen=True)
class ExecutionJournalEntry:
    schema: str
    index: int
    execution_id: str
    request_id: str
    capability: str
    state: str
    result_hash: str | None
    details: dict[str, Any]
    previous_hash: str
    entry_hash: str
    timestamp_utc: str


def canonical_json(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def result_digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload)).hexdigest()


def _entry_digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload)).hexdigest()


def _read(path: Path) -> list[dict[str, Any]]:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        return []
    entries: list[dict[str, Any]] = []
    for number, line in enumerate(resolved.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if payload.get("schema") != EXECUTION_JOURNAL_SCHEMA:
            raise ValueError(f"invalid execution journal schema at line {number}")
        entries.append(payload)
    return entries


def append_execution_event(
    path: Path,
    *,
    execution_id: str,
    request_id: str,
    capability: str,
    state: str,
    details: Mapping[str, Any] | None = None,
    result: Mapping[str, Any] | None = None,
) -> ExecutionJournalEntry:
    entries = _read(path)
    previous_hash = entries[-1]["entry_hash"] if entries else GENESIS_HASH
    result_hash = result_digest(result) if result is not None else None
    unsigned = {
        "schema": EXECUTION_JOURNAL_SCHEMA,
        "index": len(entries) + 1,
        "execution_id": execution_id,
        "request_id": request_id,
        "capability": capability,
        "state": state,
        "result_hash": result_hash,
        "details": dict(details or {}),
        "previous_hash": previous_hash,
        "timestamp_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    entry = ExecutionJournalEntry(**unsigned, entry_hash=_entry_digest(unsigned))
    resolved = path.expanduser().resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with resolved.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(entry), sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return entry


def verify_execution_journal(path: Path) -> tuple[bool, tuple[str, ...]]:
    errors: list[str] = []
    try:
        entries = _read(path)
    except Exception as exc:
        return False, (str(exc),)
    previous_hash = GENESIS_HASH
    for expected_index, entry in enumerate(entries, 1):
        if int(entry.get("index", 0)) != expected_index:
            errors.append(f"entry {expected_index}: invalid index")
        if entry.get("previous_hash") != previous_hash:
            errors.append(f"entry {expected_index}: previous hash mismatch")
        unsigned = dict(entry)
        supplied_hash = str(unsigned.pop("entry_hash", ""))
        expected_hash = _entry_digest(unsigned)
        if supplied_hash != expected_hash:
            errors.append(f"entry {expected_index}: entry hash mismatch")
        previous_hash = supplied_hash
    return not errors, tuple(errors)

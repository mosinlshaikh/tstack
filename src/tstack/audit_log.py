"""Tamper-evident JSONL audit log for runtime events."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from tstack.runtime import RUNTIME_AUDIT_SCHEMA

AUDIT_LOG_ENTRY_SCHEMA = "tstack-audit-log-entry/v1"
AUDIT_LOG_VERIFY_SCHEMA = "tstack-audit-log-verify/v1"
GENESIS_HASH = "0" * 64


@dataclass(frozen=True)
class AuditLogEntry:
    schema: str
    index: int
    event: dict
    previous_hash: str
    entry_hash: str


@dataclass(frozen=True)
class AuditLogVerification:
    schema: str
    path: str
    valid: bool
    entries: int
    head_hash: str
    errors: tuple[str, ...]


def _canonical(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _entry_hash(index: int, event: dict, previous_hash: str) -> str:
    payload = {"index": index, "event": event, "previous_hash": previous_hash}
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def _read_entries(path: Path) -> list[AuditLogEntry]:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        return []
    entries: list[AuditLogEntry] = []
    for line_number, line in enumerate(resolved.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if payload.get("schema") != AUDIT_LOG_ENTRY_SCHEMA:
            raise ValueError(f"invalid audit log entry schema at line {line_number}")
        entries.append(AuditLogEntry(payload["schema"], int(payload["index"]), dict(payload["event"]), str(payload["previous_hash"]), str(payload["entry_hash"])))
    return entries


def append_audit_event(log_path: Path, event_path: Path) -> AuditLogEntry:
    event = json.loads(event_path.expanduser().resolve().read_text(encoding="utf-8"))
    if event.get("schema") != RUNTIME_AUDIT_SCHEMA:
        raise ValueError("invalid runtime audit event schema")
    entries = _read_entries(log_path)
    previous_hash = entries[-1].entry_hash if entries else GENESIS_HASH
    index = len(entries) + 1
    entry_hash = _entry_hash(index, event, previous_hash)
    entry = AuditLogEntry(AUDIT_LOG_ENTRY_SCHEMA, index, event, previous_hash, entry_hash)
    resolved = log_path.expanduser().resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with resolved.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(entry), sort_keys=True, separators=(",", ":")) + "\n")
    return entry


def verify_audit_log(log_path: Path) -> AuditLogVerification:
    resolved = log_path.expanduser().resolve()
    errors: list[str] = []
    try:
        entries = _read_entries(resolved)
    except Exception as exc:
        return AuditLogVerification(AUDIT_LOG_VERIFY_SCHEMA, str(resolved), False, 0, GENESIS_HASH, (str(exc),))
    previous = GENESIS_HASH
    for expected_index, entry in enumerate(entries, 1):
        if entry.index != expected_index:
            errors.append(f"entry {expected_index}: index is {entry.index}")
        if entry.previous_hash != previous:
            errors.append(f"entry {expected_index}: previous hash mismatch")
        expected_hash = _entry_hash(entry.index, entry.event, entry.previous_hash)
        if entry.entry_hash != expected_hash:
            errors.append(f"entry {expected_index}: entry hash mismatch")
        previous = entry.entry_hash
    return AuditLogVerification(AUDIT_LOG_VERIFY_SCHEMA, str(resolved), not errors, len(entries), previous, tuple(errors))


def audit_log_json(item: AuditLogEntry | AuditLogVerification) -> str:
    return json.dumps(asdict(item), indent=2, sort_keys=True) + "\n"


def audit_log_markdown(item: AuditLogEntry | AuditLogVerification) -> str:
    if isinstance(item, AuditLogEntry):
        return "\n".join([
            "# TStack Audit Log Entry",
            "",
            f"- Index: {item.index}",
            f"- Previous hash: `{item.previous_hash}`",
            f"- Entry hash: `{item.entry_hash}`",
            f"- Event ID: `{item.event.get('event_id')}`",
            "",
        ])
    lines = [
        "# TStack Audit Log Verification",
        "",
        f"- Path: `{item.path}`",
        f"- Valid: {'yes' if item.valid else 'no'}",
        f"- Entries: {item.entries}",
        f"- Head hash: `{item.head_hash}`",
        "",
        "## Errors",
        "",
    ]
    lines.extend(f"- {error}" for error in item.errors or ("none",))
    return "\n".join(lines) + "\n"

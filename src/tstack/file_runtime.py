"""Transactional file runtime for approved organize plans."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from tstack.file_agent import FILE_ORGANIZE_PLAN_SCHEMA
from tstack.runtime import RUNTIME_DECISION_SCHEMA, RUNTIME_REQUEST_SCHEMA

FILE_TRANSACTION_SCHEMA = "tstack-file-transaction/v1"
FILE_UNDO_SCHEMA = "tstack-file-undo/v1"


@dataclass(frozen=True)
class FileMoveRecord:
    source: str
    destination: str
    status: str


@dataclass(frozen=True)
class FileTransaction:
    schema: str
    transaction_id: str
    root: str
    request_id: str
    applied: bool
    dry_run: bool
    moves: tuple[FileMoveRecord, ...]
    manifest_path: str | None
    timestamp_utc: str


@dataclass(frozen=True)
class FileUndoResult:
    schema: str
    transaction_id: str
    root: str
    restored: bool
    moves: tuple[FileMoveRecord, ...]
    timestamp_utc: str


def _load_json(path: Path) -> dict:
    return json.loads(path.expanduser().resolve().read_text(encoding="utf-8"))


def _ensure_inside(root: Path, relative: str) -> Path:
    if Path(relative).is_absolute():
        raise ValueError("file transaction paths must be relative")
    resolved = (root / relative).resolve()
    if root != resolved and root not in resolved.parents:
        raise ValueError("file transaction path escapes root")
    return resolved


def _validate_approval(request: dict, decision: dict) -> None:
    if request.get("schema") != RUNTIME_REQUEST_SCHEMA:
        raise ValueError("invalid runtime request schema")
    if decision.get("schema") != RUNTIME_DECISION_SCHEMA:
        raise ValueError("invalid runtime decision schema")
    if request.get("capability") != "filesystem.move":
        raise ValueError("runtime request must use filesystem.move capability")
    if decision.get("request_id") != request.get("request_id"):
        raise ValueError("runtime request and decision ids do not match")
    if decision.get("request_hash") != request.get("request_hash"):
        raise ValueError("runtime decision is not bound to request hash")
    if decision.get("approved") is not True:
        raise ValueError("runtime decision is not approved")


def apply_file_transaction(plan_path: Path, request_path: Path, decision_path: Path, *, dry_run: bool = True, manifest: Path | None = None) -> FileTransaction:
    plan = _load_json(plan_path)
    request = _load_json(request_path)
    decision = _load_json(decision_path)
    if plan.get("schema") != FILE_ORGANIZE_PLAN_SCHEMA:
        raise ValueError("invalid file organize plan schema")
    _validate_approval(request, decision)

    root = Path(str(plan["root"])).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("file transaction root must exist")
    if int(plan.get("conflicts", 0)) > 0:
        raise ValueError("file transaction refuses plans with destination conflicts")

    records: list[FileMoveRecord] = []
    for move in plan.get("moves", []):
        source = _ensure_inside(root, str(move["source"]))
        destination = _ensure_inside(root, str(move["destination"]))
        if not source.is_file():
            records.append(FileMoveRecord(str(move["source"]), str(move["destination"]), "missing-source"))
            continue
        if destination.exists():
            records.append(FileMoveRecord(str(move["source"]), str(move["destination"]), "destination-exists"))
            continue
        if dry_run:
            records.append(FileMoveRecord(str(move["source"]), str(move["destination"]), "planned"))
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        records.append(FileMoveRecord(str(move["source"]), str(move["destination"]), "moved"))

    transaction_id = f"FILETX-{str(request['request_id'])}"
    result = FileTransaction(
        FILE_TRANSACTION_SCHEMA,
        transaction_id,
        str(root),
        str(request["request_id"]),
        applied=not dry_run,
        dry_run=dry_run,
        moves=tuple(records),
        manifest_path=str(manifest.expanduser().resolve()) if manifest else None,
        timestamp_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    )
    if manifest:
        manifest.expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        manifest.expanduser().resolve().write_text(file_transaction_json(result), encoding="utf-8")
    return result


def undo_file_transaction(manifest_path: Path) -> FileUndoResult:
    payload = _load_json(manifest_path)
    if payload.get("schema") != FILE_TRANSACTION_SCHEMA:
        raise ValueError("invalid file transaction schema")
    if payload.get("applied") is not True:
        raise ValueError("only applied transactions can be undone")
    root = Path(str(payload["root"])).expanduser().resolve()
    records: list[FileMoveRecord] = []
    for move in reversed(payload.get("moves", [])):
        if move.get("status") != "moved":
            continue
        source = _ensure_inside(root, str(move["destination"]))
        destination = _ensure_inside(root, str(move["source"]))
        if not source.exists():
            records.append(FileMoveRecord(str(move["destination"]), str(move["source"]), "missing-source"))
            continue
        if destination.exists():
            records.append(FileMoveRecord(str(move["destination"]), str(move["source"]), "destination-exists"))
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        records.append(FileMoveRecord(str(move["destination"]), str(move["source"]), "restored"))
    return FileUndoResult(FILE_UNDO_SCHEMA, str(payload["transaction_id"]), str(root), True, tuple(records), datetime.now(timezone.utc).replace(microsecond=0).isoformat())


def file_transaction_json(result: FileTransaction | FileUndoResult) -> str:
    return json.dumps(asdict(result), indent=2, sort_keys=True) + "\n"


def file_transaction_markdown(result: FileTransaction | FileUndoResult) -> str:
    title = "File Transaction" if isinstance(result, FileTransaction) else "File Undo"
    lines = [f"# TStack {title}", "", f"- Transaction ID: `{result.transaction_id}`", f"- Root: `{result.root}`", f"- Timestamp UTC: `{result.timestamp_utc}`", ""]
    if isinstance(result, FileTransaction):
        lines.extend([f"- Applied: {'yes' if result.applied else 'no'}", f"- Dry run: {'yes' if result.dry_run else 'no'}", f"- Manifest: `{result.manifest_path or 'not written'}`", ""])
    else:
        lines.extend([f"- Restored: {'yes' if result.restored else 'no'}", ""])
    lines.extend(["## Moves", ""])
    lines.extend(f"- `{move.source}` -> `{move.destination}` ({move.status})" for move in result.moves)
    return "\n".join(lines) + "\n"

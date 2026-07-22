"""Secure execution bindings for exact, signed, single-use actions."""
from __future__ import annotations

import json
import subprocess
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from tstack.file_runtime import FILE_TRANSACTION_SCHEMA, FileMoveRecord, FileTransaction, _ensure_inside
from tstack.runtime_auth import ActionRequest, SignedApproval, verify_signed_approval
from tstack.runtime_store import consume_approval
from tstack.sandbox import SANDBOX_RESULT_SCHEMA, SandboxPolicy, SandboxResult, _redacted_env, plan_sandbox_command

SECURE_EXECUTION_SCHEMA = "tstack-secure-execution/v1"


@dataclass(frozen=True)
class SecureExecutionReceipt:
    schema: str
    execution_id: str
    request_id: str
    capability: str
    status: str
    result: dict[str, Any]


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.expanduser().resolve().read_text(encoding="utf-8"))


def _authorize(
    request_path: Path,
    approval_path: Path,
    public_key_raw: bytes,
    store_path: Path,
    *,
    expected_capability: str,
    expected_parameters: dict[str, Any],
) -> tuple[ActionRequest, SignedApproval, str]:
    request = verify_signed_approval(_load(request_path), _load(approval_path), public_key_raw)
    checked_request = ActionRequest(**_load(request_path))
    if checked_request.capability != expected_capability:
        raise ValueError(f"signed request must use {expected_capability} capability")
    if checked_request.parameters != expected_parameters:
        raise ValueError("signed approval does not match exact execution parameters")
    execution_id = f"EXEC-{uuid.uuid4().hex}"
    consume_approval(
        store_path,
        request_id=checked_request.request_id,
        request_hash=checked_request.request_hash,
        parameters_hash=checked_request.parameters_hash,
        nonce=checked_request.nonce,
        execution_id=execution_id,
    )
    return checked_request, request, execution_id


def execute_signed_sandbox(
    policy: SandboxPolicy,
    command: tuple[str, ...],
    *,
    request_path: Path,
    approval_path: Path,
    public_key_raw: bytes,
    store_path: Path,
    cwd: Path | None = None,
    write: bool = False,
    network: bool = False,
) -> SecureExecutionReceipt:
    plan = plan_sandbox_command(policy, command, cwd=cwd, write=write, network=network)
    if plan.blockers:
        raise ValueError("sandbox policy blocked action: " + "; ".join(plan.blockers))
    parameters = {
        "command": list(plan.command),
        "cwd": plan.workspace,
        "timeout_seconds": plan.timeout_seconds,
        "write": plan.writable,
        "network": plan.network_allowed,
    }
    request, _, execution_id = _authorize(
        request_path,
        approval_path,
        public_key_raw,
        store_path,
        expected_capability="process.run",
        expected_parameters=parameters,
    )
    try:
        completed = subprocess.run(
            list(plan.command), cwd=plan.workspace, env=_redacted_env(), shell=False,
            capture_output=True, text=True, timeout=plan.timeout_seconds,
        )
        result = SandboxResult(
            SANDBOX_RESULT_SCHEMA, plan.command, plan.workspace, True,
            completed.returncode, False, completed.stdout[-4000:], completed.stderr[-4000:], (),
            plan.redacted_env_markers,
        )
        status = "succeeded" if completed.returncode == 0 else "failed"
    except subprocess.TimeoutExpired as exc:
        result = SandboxResult(
            SANDBOX_RESULT_SCHEMA, plan.command, plan.workspace, True, None, True,
            (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "command timed out",
            (), plan.redacted_env_markers,
        )
        status = "timed-out"
    return SecureExecutionReceipt(SECURE_EXECUTION_SCHEMA, execution_id, request.request_id, request.capability, status, asdict(result))


def execute_signed_file_plan(
    plan_path: Path,
    *,
    request_path: Path,
    approval_path: Path,
    public_key_raw: bytes,
    store_path: Path,
    dry_run: bool = True,
    manifest: Path | None = None,
) -> SecureExecutionReceipt:
    plan = _load(plan_path)
    root = Path(str(plan["root"])).expanduser().resolve()
    parameters = {
        "plan": plan,
        "dry_run": dry_run,
        "root": str(root),
    }
    request, _, execution_id = _authorize(
        request_path,
        approval_path,
        public_key_raw,
        store_path,
        expected_capability="filesystem.move",
        expected_parameters=parameters,
    )
    if int(plan.get("conflicts", 0)) > 0:
        raise ValueError("file transaction refuses plans with destination conflicts")
    records: list[FileMoveRecord] = []
    moved: list[tuple[Path, Path]] = []
    try:
        for move in plan.get("moves", []):
            source = _ensure_inside(root, str(move["source"]))
            destination = _ensure_inside(root, str(move["destination"]))
            if source.is_symlink() or destination.is_symlink():
                raise ValueError("symlink paths are not allowed")
            if not source.is_file():
                raise ValueError(f"missing source: {move['source']}")
            if destination.exists():
                raise ValueError(f"destination exists: {move['destination']}")
            if dry_run:
                records.append(FileMoveRecord(str(move["source"]), str(move["destination"]), "planned"))
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            source.rename(destination)
            moved.append((source, destination))
            records.append(FileMoveRecord(str(move["source"]), str(move["destination"]), "moved"))
    except Exception:
        for source, destination in reversed(moved):
            if destination.exists() and not source.exists():
                source.parent.mkdir(parents=True, exist_ok=True)
                destination.rename(source)
        raise
    transaction = FileTransaction(
        FILE_TRANSACTION_SCHEMA, f"FILETX-{request.request_id}", str(root), request.request_id,
        applied=not dry_run, dry_run=dry_run, moves=tuple(records),
        manifest_path=str(manifest.expanduser().resolve()) if manifest else None,
        timestamp_utc=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).replace(microsecond=0).isoformat(),
    )
    if manifest:
        manifest.expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        manifest.expanduser().resolve().write_text(json.dumps(asdict(transaction), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return SecureExecutionReceipt(SECURE_EXECUTION_SCHEMA, execution_id, request.request_id, request.capability, "succeeded", asdict(transaction))


def secure_execution_json(receipt: SecureExecutionReceipt) -> str:
    return json.dumps(asdict(receipt), indent=2, sort_keys=True) + "\n"

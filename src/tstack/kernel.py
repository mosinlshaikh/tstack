"""SQLite-backed runtime kernel vertical slice."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import shutil
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

KERNEL_SCHEMA = "tstack-kernel/v1"
TASK_SCHEMA = "tstack-task/v1"
APPROVAL_SCHEMA = "tstack-signed-approval/v1"
ROLLBACK_SCHEMA = "tstack-rollback-result/v1"
TASK_STATES = (
    "CREATED",
    "VALIDATING",
    "WAITING_FOR_APPROVAL",
    "QUEUED",
    "RUNNING",
    "PAUSED",
    "BLOCKED",
    "RETRYING",
    "SUCCEEDED",
    "FAILED",
    "CANCELLED",
    "ROLLED_BACK",
)


@dataclass(frozen=True)
class KernelWorkspace:
    schema: str
    root: str
    database: str
    initialized: bool


@dataclass(frozen=True)
class KernelTask:
    schema: str
    task_id: str
    capability: str
    target: str
    content: str
    state: str
    request_hash: str
    approval_required: bool


@dataclass(frozen=True)
class SignedApproval:
    schema: str
    approval_id: str
    task_id: str
    request_hash: str
    actor: str
    mode: str
    expires_at: str | None
    max_uses: int
    nonce: str
    timestamp_utc: str
    signature: str


@dataclass(frozen=True)
class KernelRunResult:
    schema: str
    task_id: str
    state: str
    executed: bool
    audit_hash: str | None
    snapshot_path: str | None
    verification: tuple[str, ...]


@dataclass(frozen=True)
class KernelRollbackResult:
    schema: str
    task_id: str
    restored: bool
    state: str
    audit_hash: str | None
    verification: tuple[str, ...]


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _db_path(root: Path) -> Path:
    return root.expanduser().resolve() / ".tstack" / "state.db"


def _key_path(root: Path) -> Path:
    return root.expanduser().resolve() / ".tstack" / "approval.key"


def _connect(root: Path) -> sqlite3.Connection:
    return sqlite3.connect(_db_path(root))


def _canonical(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _sha(payload: dict | str | bytes) -> str:
    if isinstance(payload, dict):
        data = _canonical(payload).encode("utf-8")
    elif isinstance(payload, str):
        data = payload.encode("utf-8")
    else:
        data = payload
    return hashlib.sha256(data).hexdigest()


def _load_key(root: Path) -> bytes:
    path = _key_path(root)
    if not path.exists():
        raise ValueError("workspace approval key missing; run workspace init")
    return bytes.fromhex(path.read_text(encoding="utf-8").strip())


def _sign(root: Path, payload: dict) -> str:
    return hmac.new(_load_key(root), _canonical(payload).encode("utf-8"), hashlib.sha256).hexdigest()


def _inside(root: Path, target: Path) -> bool:
    resolved = target.expanduser().resolve()
    return resolved == root or root in resolved.parents


def init_workspace(path: Path) -> KernelWorkspace:
    root = path.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    tstack_dir = root / ".tstack"
    tstack_dir.mkdir(exist_ok=True)
    key = _key_path(root)
    if not key.exists():
        key.write_text(secrets.token_hex(32), encoding="utf-8")
    with _connect(root) as db:
        db.executescript(
            """
            create table if not exists migrations (version integer primary key, applied_at text not null);
            insert or ignore into migrations(version, applied_at) values (1, datetime('now'));
            create table if not exists tasks (
              task_id text primary key,
              capability text not null,
              target text not null,
              content text not null,
              state text not null,
              request_hash text not null,
              created_at text not null,
              updated_at text not null
            );
            create table if not exists approvals (
              approval_id text primary key,
              task_id text not null,
              request_hash text not null,
              actor text not null,
              mode text not null,
              expires_at text,
              max_uses integer not null,
              nonce text not null,
              timestamp_utc text not null,
              signature text not null,
              uses integer not null default 0
            );
            create table if not exists audit_records (
              id integer primary key autoincrement,
              task_id text not null,
              capability text not null,
              input_digest text not null,
              output_digest text not null,
              approval_id text,
              status text not null,
              previous_hash text not null,
              record_hash text not null,
              created_at text not null
            );
            create table if not exists snapshots (
              snapshot_id text primary key,
              task_id text not null,
              target text not null,
              snapshot_path text,
              existed integer not null,
              created_at text not null
            );
            """
        )
    return KernelWorkspace(KERNEL_SCHEMA, str(root), str(_db_path(root)), True)


def submit_task(root_path: Path, *, capability: str, target: str, content: str) -> KernelTask:
    root = root_path.expanduser().resolve()
    if capability != "filesystem.write":
        raise ValueError("kernel vertical slice only supports filesystem.write")
    target_path = (root / target).resolve()
    if not _inside(root, target_path):
        raise ValueError("task target escapes workspace")
    payload = {"capability": capability, "target": target, "content_hash": _sha(content)}
    request_hash = _sha(payload)
    task_id = "TASK-" + _sha(request_hash)[:16]
    now = _now()
    with _connect(root) as db:
        db.execute(
            "insert or replace into tasks(task_id, capability, target, content, state, request_hash, created_at, updated_at) values (?, ?, ?, ?, ?, ?, ?, ?)",
            (task_id, capability, target, content, "WAITING_FOR_APPROVAL", request_hash, now, now),
        )
    return KernelTask(TASK_SCHEMA, task_id, capability, target, content, "WAITING_FOR_APPROVAL", request_hash, True)


def approve_task(root_path: Path, task_id: str, *, actor: str, mode: str = "ONCE", expires_at: str | None = None, max_uses: int = 1) -> SignedApproval:
    root = root_path.expanduser().resolve()
    task = get_task(root, task_id)
    if mode not in {"ONCE", "SESSION", "WORKSPACE", "ALWAYS_DENY", "POLICY_PREAPPROVED_LOW_RISK"}:
        raise ValueError("unsupported approval mode")
    if not actor.strip():
        raise ValueError("approval actor is required")
    nonce = secrets.token_hex(16)
    timestamp = _now()
    approval_id = "APP-" + _sha(f"{task_id}:{task.request_hash}:{nonce}")[:16]
    unsigned = {
        "schema": APPROVAL_SCHEMA,
        "approval_id": approval_id,
        "task_id": task_id,
        "request_hash": task.request_hash,
        "actor": actor.strip(),
        "mode": mode,
        "expires_at": expires_at,
        "max_uses": max_uses,
        "nonce": nonce,
        "timestamp_utc": timestamp,
    }
    approval = SignedApproval(**unsigned, signature=_sign(root, unsigned))
    with _connect(root) as db:
        db.execute(
            "insert into approvals(approval_id, task_id, request_hash, actor, mode, expires_at, max_uses, nonce, timestamp_utc, signature) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (approval.approval_id, approval.task_id, approval.request_hash, approval.actor, approval.mode, approval.expires_at, approval.max_uses, approval.nonce, approval.timestamp_utc, approval.signature),
        )
    return approval


def get_task(root_path: Path, task_id: str) -> KernelTask:
    root = root_path.expanduser().resolve()
    with _connect(root) as db:
        row = db.execute("select task_id, capability, target, content, state, request_hash from tasks where task_id = ?", (task_id,)).fetchone()
    if row is None:
        raise ValueError("task not found")
    return KernelTask(TASK_SCHEMA, row[0], row[1], row[2], row[3], row[4], row[5], row[4] == "WAITING_FOR_APPROVAL")


def list_tasks(root_path: Path) -> tuple[KernelTask, ...]:
    root = root_path.expanduser().resolve()
    with _connect(root) as db:
        rows = db.execute("select task_id from tasks order by created_at, task_id").fetchall()
    return tuple(get_task(root, row[0]) for row in rows)


def _verified_approval(root: Path, task: KernelTask) -> SignedApproval:
    with _connect(root) as db:
        row = db.execute(
            "select approval_id, task_id, request_hash, actor, mode, expires_at, max_uses, nonce, timestamp_utc, signature, uses from approvals where task_id = ? order by timestamp_utc desc limit 1",
            (task.task_id,),
        ).fetchone()
    if row is None:
        raise ValueError("task has no approval")
    approval = SignedApproval(APPROVAL_SCHEMA, row[0], row[1], row[2], row[3], row[4], row[5], int(row[6]), row[7], row[8], row[9])
    unsigned = asdict(approval)
    unsigned.pop("signature")
    if not hmac.compare_digest(_sign(root, unsigned), approval.signature):
        raise ValueError("approval signature mismatch")
    if approval.request_hash != task.request_hash:
        raise ValueError("approval does not match task request hash")
    if approval.mode == "ALWAYS_DENY":
        raise ValueError("approval mode denies execution")
    if int(row[10]) >= approval.max_uses:
        raise ValueError("approval maximum uses exceeded")
    return approval


def _audit(root: Path, task: KernelTask, approval_id: str | None, status: str, output_digest: str) -> str:
    with _connect(root) as db:
        row = db.execute("select record_hash from audit_records order by id desc limit 1").fetchone()
        previous = row[0] if row else "0" * 64
        payload = {"task_id": task.task_id, "capability": task.capability, "input_digest": task.request_hash, "output_digest": output_digest, "approval_id": approval_id, "status": status, "previous_hash": previous}
        record_hash = _sha(payload)
        db.execute(
            "insert into audit_records(task_id, capability, input_digest, output_digest, approval_id, status, previous_hash, record_hash, created_at) values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (task.task_id, task.capability, task.request_hash, output_digest, approval_id, status, previous, record_hash, _now()),
        )
    return record_hash


def run_task(root_path: Path, task_id: str) -> KernelRunResult:
    root = root_path.expanduser().resolve()
    task = get_task(root, task_id)
    approval = _verified_approval(root, task)
    target = (root / task.target).resolve()
    if not _inside(root, target):
        raise ValueError("task target escapes workspace")
    snapshots_dir = root / ".tstack" / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    snapshot_id = "SNAP-" + _sha(f"{task.task_id}:{task.request_hash}")[:16]
    existed = target.exists()
    snapshot_path = snapshots_dir / f"{snapshot_id}.bak" if existed else None
    if existed and snapshot_path:
        shutil.copy2(target, snapshot_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(task.content, encoding="utf-8")
    output_digest = _sha(target.read_bytes())
    with _connect(root) as db:
        db.execute("update tasks set state = ?, updated_at = ? where task_id = ?", ("SUCCEEDED", _now(), task.task_id))
        db.execute("update approvals set uses = uses + 1 where approval_id = ?", (approval.approval_id,))
        db.execute(
            "insert or replace into snapshots(snapshot_id, task_id, target, snapshot_path, existed, created_at) values (?, ?, ?, ?, ?, ?)",
            (snapshot_id, task.task_id, task.target, str(snapshot_path) if snapshot_path else None, 1 if existed else 0, _now()),
        )
    audit_hash = _audit(root, task, approval.approval_id, "SUCCEEDED", output_digest)
    return KernelRunResult(KERNEL_SCHEMA, task.task_id, "SUCCEEDED", True, audit_hash, str(snapshot_path) if snapshot_path else None, ("target written", "snapshot recorded", "audit hash recorded"))


def rollback_task(root_path: Path, task_id: str) -> KernelRollbackResult:
    root = root_path.expanduser().resolve()
    task = get_task(root, task_id)
    with _connect(root) as db:
        row = db.execute("select target, snapshot_path, existed from snapshots where task_id = ?", (task_id,)).fetchone()
    if row is None:
        raise ValueError("task has no snapshot")
    target = (root / row[0]).resolve()
    if not _inside(root, target):
        raise ValueError("rollback target escapes workspace")
    if int(row[2]) == 1 and row[1]:
        shutil.copy2(Path(row[1]), target)
        output_digest = _sha(target.read_bytes())
    else:
        if target.exists():
            target.unlink()
        output_digest = _sha(b"deleted")
    with _connect(root) as db:
        db.execute("update tasks set state = ?, updated_at = ? where task_id = ?", ("ROLLED_BACK", _now(), task.task_id))
    audit_hash = _audit(root, task, None, "ROLLED_BACK", output_digest)
    return KernelRollbackResult(ROLLBACK_SCHEMA, task.task_id, True, "ROLLED_BACK", audit_hash, ("target restored", "rollback audit hash recorded"))


def verify_audit_chain(root_path: Path) -> bool:
    root = root_path.expanduser().resolve()
    previous = "0" * 64
    with _connect(root) as db:
        rows = db.execute("select task_id, capability, input_digest, output_digest, approval_id, status, previous_hash, record_hash from audit_records order by id").fetchall()
    for row in rows:
        payload = {"task_id": row[0], "capability": row[1], "input_digest": row[2], "output_digest": row[3], "approval_id": row[4], "status": row[5], "previous_hash": row[6]}
        if row[6] != previous or _sha(payload) != row[7]:
            return False
        previous = row[7]
    return True


def kernel_json(item) -> str:
    if isinstance(item, tuple):
        return json.dumps([asdict(entry) for entry in item], indent=2, sort_keys=True) + "\n"
    return json.dumps(asdict(item), indent=2, sort_keys=True) + "\n"

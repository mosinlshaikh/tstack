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
class ApprovalRevocation:
    schema: str
    approval_id: str
    task_id: str
    actor: str
    reason: str
    timestamp_utc: str


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


@dataclass(frozen=True)
class KernelEvent:
    schema: str
    event_id: str
    task_id: str
    event_type: str
    state: str
    message: str
    timestamp_utc: str


@dataclass(frozen=True)
class KernelDaemonStatus:
    schema: str
    workspace: str
    database_exists: bool
    background_process_running: bool
    mode: str
    task_counts: dict[str, int]
    queued_tasks: int
    audit_chain_valid: bool
    health: str
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class KernelRecoveryResult:
    schema: str
    workspace: str
    policy: str
    recovered: int
    task_ids: tuple[str, ...]
    audit_hashes: tuple[str, ...]


@dataclass(frozen=True)
class KernelWorkerRun:
    schema: str
    workspace: str
    requested_workers: int
    effective_workers: int
    tasks_attempted: int
    succeeded: int
    failed: int
    remaining_queued: int
    mode: str
    task_ids: tuple[str, ...]


@dataclass(frozen=True)
class KernelStateBundle:
    schema: str
    workspace: str
    exported_at: str
    tables: dict[str, list[dict]]
    approval_key_exported: bool
    audit_chain_valid: bool


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


def _record_event(db: sqlite3.Connection, task_id: str, event_type: str, state: str, message: str) -> KernelEvent:
    timestamp = _now()
    event_id = "EVT-" + _sha(f"{task_id}:{event_type}:{state}:{message}:{timestamp}")[:16]
    db.execute(
        "insert into events(event_id, task_id, event_type, state, message, created_at) values (?, ?, ?, ?, ?, ?)",
        (event_id, task_id, event_type, state, message, timestamp),
    )
    return KernelEvent("tstack-kernel-event/v1", event_id, task_id, event_type, state, message, timestamp)


def _set_state(db: sqlite3.Connection, task_id: str, state: str, message: str) -> None:
    if state not in TASK_STATES:
        raise ValueError("invalid task state")
    db.execute("update tasks set state = ?, updated_at = ? where task_id = ?", (state, _now(), task_id))
    _record_event(db, task_id, "state", state, message)


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
            create table if not exists approval_revocations (
              approval_id text primary key,
              task_id text not null,
              actor text not null,
              reason text not null,
              timestamp_utc text not null
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
            create table if not exists events (
              event_id text primary key,
              task_id text not null,
              event_type text not null,
              state text not null,
              message text not null,
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
        _record_event(db, task_id, "created", "WAITING_FOR_APPROVAL", "task submitted and waiting for approval")
    return KernelTask(TASK_SCHEMA, task_id, capability, target, content, "WAITING_FOR_APPROVAL", request_hash, True)


def approve_task(root_path: Path, task_id: str, *, actor: str, mode: str = "ONCE", expires_at: str | None = None, max_uses: int = 1) -> SignedApproval:
    root = root_path.expanduser().resolve()
    task = get_task(root, task_id)
    if mode not in {"ONCE", "SESSION", "WORKSPACE", "ALWAYS_DENY", "POLICY_PREAPPROVED_LOW_RISK"}:
        raise ValueError("unsupported approval mode")
    if not actor.strip():
        raise ValueError("approval actor is required")
    if max_uses <= 0:
        raise ValueError("approval max_uses must be positive")
    if expires_at is not None:
        try:
            expires = datetime.fromisoformat(expires_at)
        except ValueError as exc:
            raise ValueError("approval expires_at must be ISO-8601") from exc
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires <= datetime.now(timezone.utc):
            raise ValueError("approval expiry must be in the future")
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


def revoke_approval(root_path: Path, approval_id: str, *, actor: str, reason: str) -> ApprovalRevocation:
    root = root_path.expanduser().resolve()
    if not actor.strip():
        raise ValueError("revocation actor is required")
    if not reason.strip():
        raise ValueError("revocation reason is required")
    with _connect(root) as db:
        row = db.execute("select task_id from approvals where approval_id = ?", (approval_id,)).fetchone()
        if row is None:
            raise ValueError("approval not found")
        revocation = ApprovalRevocation("tstack-approval-revocation/v1", approval_id, row[0], actor.strip(), reason.strip(), _now())
        db.execute(
            "insert or replace into approval_revocations(approval_id, task_id, actor, reason, timestamp_utc) values (?, ?, ?, ?, ?)",
            (revocation.approval_id, revocation.task_id, revocation.actor, revocation.reason, revocation.timestamp_utc),
        )
        _record_event(db, revocation.task_id, "approval_revoked", get_task(root, revocation.task_id).state, reason.strip())
    return revocation


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


def list_events(root_path: Path, task_id: str | None = None) -> tuple[KernelEvent, ...]:
    root = root_path.expanduser().resolve()
    query = "select event_id, task_id, event_type, state, message, created_at from events"
    params: tuple[str, ...] = ()
    if task_id:
        query += " where task_id = ?"
        params = (task_id,)
    query += " order by created_at, event_id"
    with _connect(root) as db:
        rows = db.execute(query, params).fetchall()
    return tuple(KernelEvent("tstack-kernel-event/v1", row[0], row[1], row[2], row[3], row[4], row[5]) for row in rows)


def daemon_status(root_path: Path) -> KernelDaemonStatus:
    root = root_path.expanduser().resolve()
    database = _db_path(root)
    if not database.exists():
        return KernelDaemonStatus(
            "tstack-kernel-daemon-status/v1",
            str(root),
            False,
            False,
            "not-initialized",
            {},
            0,
            False,
            "NOT_INITIALIZED",
            ("run `tstack workspace init` or `tstack daemon start` first", "background daemon process is not implemented"),
        )
    with _connect(root) as db:
        rows = db.execute("select state, count(*) from tasks group by state order by state").fetchall()
    counts = {row[0]: int(row[1]) for row in rows}
    audit_valid = verify_audit_chain(root)
    health = "HEALTHY" if audit_valid else "DEGRADED"
    return KernelDaemonStatus(
        "tstack-kernel-daemon-status/v1",
        str(root),
        True,
        False,
        "sqlite-local-control",
        counts,
        counts.get("QUEUED", 0),
        audit_valid,
        health,
        ("no background daemon process yet", "no worker pool yet", "status is read from SQLite workspace state"),
    )


def start_daemon_foundation(root_path: Path) -> KernelDaemonStatus:
    init_workspace(root_path)
    return daemon_status(root_path)


def recover_stuck_tasks(root_path: Path, *, policy: str = "fail") -> KernelRecoveryResult:
    if policy not in {"fail", "requeue"}:
        raise ValueError("recovery policy must be fail or requeue")
    root = root_path.expanduser().resolve()
    with _connect(root) as db:
        rows = db.execute("select task_id from tasks where state = ? order by updated_at, task_id", ("RUNNING",)).fetchall()
    recovered: list[str] = []
    audit_hashes: list[str] = []
    for row in rows:
        task = get_task(root, row[0])
        new_state = "FAILED" if policy == "fail" else "QUEUED"
        message = "recovered stale RUNNING task after restart"
        with _connect(root) as db:
            _set_state(db, task.task_id, new_state, message)
        audit_hashes.append(_audit(root, task, None, f"RECOVERED_{new_state}", _sha(f"recovery:{policy}:{task.task_id}")))
        recovered.append(task.task_id)
    return KernelRecoveryResult("tstack-kernel-recovery-result/v1", str(root), policy, len(recovered), tuple(recovered), tuple(audit_hashes))


def enqueue_task(root_path: Path, task_id: str) -> KernelTask:
    root = root_path.expanduser().resolve()
    task = get_task(root, task_id)
    if task.state != "WAITING_FOR_APPROVAL":
        raise ValueError("only waiting tasks can be queued")
    _verified_approval(root, task)
    with _connect(root) as db:
        _set_state(db, task_id, "QUEUED", "task queued for scheduler")
    return get_task(root, task_id)


def cancel_task(root_path: Path, task_id: str, *, reason: str = "cancelled by user") -> KernelTask:
    root = root_path.expanduser().resolve()
    task = get_task(root, task_id)
    if task.state in {"SUCCEEDED", "FAILED", "ROLLED_BACK"}:
        raise ValueError("terminal task cannot be cancelled")
    with _connect(root) as db:
        _set_state(db, task_id, "CANCELLED", reason)
    return get_task(root, task_id)


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
    if approval.expires_at is not None:
        expires = datetime.fromisoformat(approval.expires_at)
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires <= datetime.now(timezone.utc):
            raise ValueError("approval expired")
    with _connect(root) as db:
        revoked = db.execute("select 1 from approval_revocations where approval_id = ?", (approval.approval_id,)).fetchone()
    if revoked is not None:
        raise ValueError("approval revoked")
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


def run_task(root_path: Path, task_id: str, *, timeout_seconds: int = 30) -> KernelRunResult:
    root = root_path.expanduser().resolve()
    task = get_task(root, task_id)
    if timeout_seconds <= 0:
        with _connect(root) as db:
            _set_state(db, task_id, "FAILED", "task timed out before execution")
        audit_hash = _audit(root, task, None, "FAILED", _sha(b"timeout"))
        return KernelRunResult(KERNEL_SCHEMA, task.task_id, "FAILED", False, audit_hash, None, ("timeout enforced", "audit hash recorded"))
    if task.state == "CANCELLED":
        raise ValueError("cancelled task cannot run")
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
    with _connect(root) as db:
        _set_state(db, task_id, "RUNNING", "task execution started")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(task.content, encoding="utf-8")
    output_digest = _sha(target.read_bytes())
    with _connect(root) as db:
        _set_state(db, task.task_id, "SUCCEEDED", "task execution succeeded")
        db.execute("update approvals set uses = uses + 1 where approval_id = ?", (approval.approval_id,))
        db.execute(
            "insert or replace into snapshots(snapshot_id, task_id, target, snapshot_path, existed, created_at) values (?, ?, ?, ?, ?, ?)",
            (snapshot_id, task.task_id, task.target, str(snapshot_path) if snapshot_path else None, 1 if existed else 0, _now()),
        )
    audit_hash = _audit(root, task, approval.approval_id, "SUCCEEDED", output_digest)
    return KernelRunResult(KERNEL_SCHEMA, task.task_id, "SUCCEEDED", True, audit_hash, str(snapshot_path) if snapshot_path else None, ("target written", "snapshot recorded", "audit hash recorded"))


def run_next_task(root_path: Path, *, timeout_seconds: int = 30) -> KernelRunResult:
    root = root_path.expanduser().resolve()
    with _connect(root) as db:
        row = db.execute("select task_id from tasks where state = ? order by created_at, task_id limit 1", ("QUEUED",)).fetchone()
    if row is None:
        raise ValueError("no queued task")
    return run_task(root, row[0], timeout_seconds=timeout_seconds)


def run_worker_pool(root_path: Path, *, workers: int = 1, limit: int | None = None, timeout_seconds: int = 30) -> KernelWorkerRun:
    if workers <= 0:
        raise ValueError("workers must be positive")
    root = root_path.expanduser().resolve()
    effective_workers = min(workers, 32)
    attempted = succeeded = failed = 0
    task_ids: list[str] = []
    max_tasks = limit if limit is not None else 10_000
    while attempted < max_tasks:
        with _connect(root) as db:
            row = db.execute("select task_id from tasks where state = ? order by created_at, task_id limit 1", ("QUEUED",)).fetchone()
        if row is None:
            break
        task_id = row[0]
        task_ids.append(task_id)
        attempted += 1
        try:
            result = run_task(root, task_id, timeout_seconds=timeout_seconds)
        except Exception:
            task = get_task(root, task_id)
            with _connect(root) as db:
                _set_state(db, task_id, "FAILED", "worker execution failed")
            _audit(root, task, None, "FAILED", _sha(b"worker-failure"))
            failed += 1
            continue
        if result.state == "SUCCEEDED":
            succeeded += 1
        else:
            failed += 1
    with _connect(root) as db:
        remaining = db.execute("select count(*) from tasks where state = ?", ("QUEUED",)).fetchone()[0]
    return KernelWorkerRun(
        "tstack-kernel-worker-run/v1",
        str(root),
        workers,
        effective_workers,
        attempted,
        succeeded,
        failed,
        int(remaining),
        "same-process-bounded-simulation",
        tuple(task_ids),
    )


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
        _set_state(db, task.task_id, "ROLLED_BACK", "task rollback completed")
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


def export_workspace_state(root_path: Path) -> KernelStateBundle:
    root = root_path.expanduser().resolve()
    tables: dict[str, list[dict]] = {}
    table_names = ("tasks", "approvals", "approval_revocations", "audit_records", "snapshots", "events")
    with _connect(root) as db:
        db.row_factory = sqlite3.Row
        for table in table_names:
            rows = db.execute(f"select * from {table}").fetchall()
            tables[table] = [dict(row) for row in rows]
    return KernelStateBundle("tstack-kernel-state-bundle/v1", str(root), _now(), tables, False, verify_audit_chain(root))


def import_workspace_state(root_path: Path, bundle_path: Path) -> KernelWorkspace:
    workspace = init_workspace(root_path)
    bundle = json.loads(bundle_path.expanduser().resolve().read_text(encoding="utf-8"))
    if bundle.get("schema") != "tstack-kernel-state-bundle/v1":
        raise ValueError("invalid kernel state bundle schema")
    if bundle.get("approval_key_exported") is not False:
        raise ValueError("kernel state bundle must not include approval key material")
    tables = bundle.get("tables", {})
    with _connect(root_path.expanduser().resolve()) as db:
        for table in ("events", "snapshots", "audit_records", "approval_revocations", "approvals", "tasks"):
            db.execute(f"delete from {table}")
        for row in tables.get("tasks", []):
            db.execute(
                "insert into tasks(task_id, capability, target, content, state, request_hash, created_at, updated_at) values (?, ?, ?, ?, ?, ?, ?, ?)",
                (row["task_id"], row["capability"], row["target"], row["content"], row["state"], row["request_hash"], row["created_at"], row["updated_at"]),
            )
        for row in tables.get("approvals", []):
            db.execute(
                "insert into approvals(approval_id, task_id, request_hash, actor, mode, expires_at, max_uses, nonce, timestamp_utc, signature, uses) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (row["approval_id"], row["task_id"], row["request_hash"], row["actor"], row["mode"], row["expires_at"], row["max_uses"], row["nonce"], row["timestamp_utc"], row["signature"], row["uses"]),
            )
        for row in tables.get("approval_revocations", []):
            db.execute(
                "insert into approval_revocations(approval_id, task_id, actor, reason, timestamp_utc) values (?, ?, ?, ?, ?)",
                (row["approval_id"], row["task_id"], row["actor"], row["reason"], row["timestamp_utc"]),
            )
        for row in tables.get("audit_records", []):
            db.execute(
                "insert into audit_records(id, task_id, capability, input_digest, output_digest, approval_id, status, previous_hash, record_hash, created_at) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (row["id"], row["task_id"], row["capability"], row["input_digest"], row["output_digest"], row["approval_id"], row["status"], row["previous_hash"], row["record_hash"], row["created_at"]),
            )
        for row in tables.get("snapshots", []):
            db.execute(
                "insert into snapshots(snapshot_id, task_id, target, snapshot_path, existed, created_at) values (?, ?, ?, ?, ?, ?)",
                (row["snapshot_id"], row["task_id"], row["target"], row["snapshot_path"], row["existed"], row["created_at"]),
            )
        for row in tables.get("events", []):
            db.execute(
                "insert into events(event_id, task_id, event_type, state, message, created_at) values (?, ?, ?, ?, ?, ?)",
                (row["event_id"], row["task_id"], row["event_type"], row["state"], row["message"], row["created_at"]),
            )
    return workspace


def kernel_json(item) -> str:
    if isinstance(item, tuple):
        return json.dumps([asdict(entry) for entry in item], indent=2, sort_keys=True) + "\n"
    return json.dumps(asdict(item), indent=2, sort_keys=True) + "\n"

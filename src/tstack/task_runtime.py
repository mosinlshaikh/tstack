"""Persistent SQLite task lifecycle and worker leasing foundation.

This module provides the first restart-safe task runtime for TStack. It stores
logical tasks in SQLite, enforces explicit state transitions, supports atomic
worker leasing, cancellation, lease expiry recovery, and bounded retry state.
It intentionally does not execute capabilities directly; workers must route
operational actions through the signed capability authorization layer.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping

TASK_SCHEMA = "tstack-task/v1"
TASK_STORE_SCHEMA_VERSION = 1

CREATED = "CREATED"
QUEUED = "QUEUED"
RUNNING = "RUNNING"
CANCEL_REQUESTED = "CANCEL_REQUESTED"
CANCELLED = "CANCELLED"
SUCCEEDED = "SUCCEEDED"
FAILED = "FAILED"
RETRYING = "RETRYING"
BLOCKED = "BLOCKED"

TERMINAL_STATES = frozenset({CANCELLED, SUCCEEDED, FAILED})
ACTIVE_STATES = frozenset({QUEUED, RUNNING, CANCEL_REQUESTED, RETRYING})
VALID_STATES = frozenset({
    CREATED, QUEUED, RUNNING, CANCEL_REQUESTED, CANCELLED, SUCCEEDED,
    FAILED, RETRYING, BLOCKED,
})

_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    CREATED: frozenset({QUEUED, CANCELLED, BLOCKED}),
    QUEUED: frozenset({RUNNING, CANCELLED, BLOCKED}),
    RUNNING: frozenset({SUCCEEDED, FAILED, RETRYING, CANCEL_REQUESTED, CANCELLED, BLOCKED}),
    CANCEL_REQUESTED: frozenset({CANCELLED, FAILED}),
    RETRYING: frozenset({QUEUED, CANCELLED, FAILED, BLOCKED}),
    BLOCKED: frozenset({QUEUED, CANCELLED, FAILED}),
    CANCELLED: frozenset(),
    SUCCEEDED: frozenset(),
    FAILED: frozenset(),
}


class TaskNotFoundError(KeyError):
    """Raised when a task id is not present in the runtime store."""


class InvalidTaskTransitionError(RuntimeError):
    """Raised when a requested task state transition is not allowed."""


class TaskLeaseError(RuntimeError):
    """Raised when task lease ownership or validity checks fail."""


@dataclass(frozen=True)
class TaskRecord:
    schema: str
    task_id: str
    workspace_id: str
    capability: str
    intent: str
    parameters: dict[str, Any]
    state: str
    priority: int
    max_attempts: int
    attempt_count: int
    created_at: str
    updated_at: str
    queued_at: str | None
    started_at: str | None
    completed_at: str | None
    lease_owner: str | None
    lease_expires_at: str | None
    cancellation_requested_at: str | None
    last_error: str | None
    result: dict[str, Any] | None


def _utc_now(now: datetime | None = None) -> datetime:
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise ValueError("runtime timestamps must be timezone-aware")
    return value.astimezone(timezone.utc).replace(microsecond=0)


def _iso(now: datetime | None = None) -> str:
    return _utc_now(now).isoformat()


@contextmanager
def _connection(path: Path) -> Iterator[sqlite3.Connection]:
    resolved = path.expanduser().resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(resolved, timeout=10, isolation_level=None)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = FULL")
        connection.execute("PRAGMA busy_timeout = 10000")
        yield connection
    finally:
        connection.close()


def initialize_task_store(path: Path) -> None:
    with _connection(path) as connection:
        connection.executescript(
            """
            BEGIN IMMEDIATE;
            CREATE TABLE IF NOT EXISTS task_runtime_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                schema TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                capability TEXT NOT NULL,
                intent TEXT NOT NULL,
                parameters_json TEXT NOT NULL,
                state TEXT NOT NULL,
                priority INTEGER NOT NULL,
                max_attempts INTEGER NOT NULL CHECK(max_attempts >= 1),
                attempt_count INTEGER NOT NULL DEFAULT 0 CHECK(attempt_count >= 0),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                queued_at TEXT,
                started_at TEXT,
                completed_at TEXT,
                lease_owner TEXT,
                lease_expires_at TEXT,
                cancellation_requested_at TEXT,
                last_error TEXT,
                result_json TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_tasks_queue
                ON tasks(state, priority DESC, created_at ASC);
            CREATE INDEX IF NOT EXISTS idx_tasks_lease
                ON tasks(state, lease_expires_at);
            INSERT INTO task_runtime_meta(key, value)
            VALUES ('schema_version', '1')
            ON CONFLICT(key) DO UPDATE SET value = excluded.value;
            COMMIT;
            """
        )


def _decode(row: sqlite3.Row) -> TaskRecord:
    return TaskRecord(
        schema=str(row["schema"]),
        task_id=str(row["task_id"]),
        workspace_id=str(row["workspace_id"]),
        capability=str(row["capability"]),
        intent=str(row["intent"]),
        parameters=json.loads(str(row["parameters_json"])),
        state=str(row["state"]),
        priority=int(row["priority"]),
        max_attempts=int(row["max_attempts"]),
        attempt_count=int(row["attempt_count"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        queued_at=row["queued_at"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
        lease_owner=row["lease_owner"],
        lease_expires_at=row["lease_expires_at"],
        cancellation_requested_at=row["cancellation_requested_at"],
        last_error=row["last_error"],
        result=json.loads(str(row["result_json"])) if row["result_json"] else None,
    )


def submit_task(
    path: Path,
    *,
    workspace_id: str,
    capability: str,
    intent: str,
    parameters: Mapping[str, Any],
    priority: int = 0,
    max_attempts: int = 1,
    task_id: str | None = None,
    now: datetime | None = None,
) -> TaskRecord:
    if not workspace_id.strip():
        raise ValueError("workspace_id is required")
    if not capability.strip():
        raise ValueError("capability is required")
    if not intent.strip():
        raise ValueError("intent is required")
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    normalized = json.loads(json.dumps(dict(parameters), sort_keys=True))
    timestamp = _iso(now)
    identifier = task_id or f"TASK-{uuid.uuid4().hex}"
    initialize_task_store(path)
    with _connection(path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            connection.execute(
                """
                INSERT INTO tasks(
                    task_id, schema, workspace_id, capability, intent,
                    parameters_json, state, priority, max_attempts,
                    attempt_count, created_at, updated_at, queued_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
                """,
                (
                    identifier, TASK_SCHEMA, workspace_id.strip(), capability.strip().lower(),
                    intent.strip(), json.dumps(normalized, sort_keys=True, separators=(",", ":")),
                    QUEUED, int(priority), int(max_attempts), timestamp, timestamp, timestamp,
                ),
            )
            row = connection.execute("SELECT * FROM tasks WHERE task_id = ?", (identifier,)).fetchone()
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise
    assert row is not None
    return _decode(row)


def get_task(path: Path, task_id: str) -> TaskRecord:
    initialize_task_store(path)
    with _connection(path) as connection:
        row = connection.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
    if row is None:
        raise TaskNotFoundError(task_id)
    return _decode(row)


def list_tasks(path: Path, *, state: str | None = None, limit: int = 100) -> tuple[TaskRecord, ...]:
    if limit < 1 or limit > 10000:
        raise ValueError("limit must be between 1 and 10000")
    initialize_task_store(path)
    query = "SELECT * FROM tasks"
    values: tuple[Any, ...] = ()
    if state is not None:
        if state not in VALID_STATES:
            raise ValueError("invalid task state")
        query += " WHERE state = ?"
        values = (state,)
    query += " ORDER BY priority DESC, created_at ASC LIMIT ?"
    values += (limit,)
    with _connection(path) as connection:
        rows = connection.execute(query, values).fetchall()
    return tuple(_decode(row) for row in rows)


def _transition(
    connection: sqlite3.Connection,
    task_id: str,
    target: str,
    *,
    timestamp: str,
    extra_sql: str = "",
    extra_values: tuple[Any, ...] = (),
) -> None:
    row = connection.execute("SELECT state FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
    if row is None:
        raise TaskNotFoundError(task_id)
    current = str(row["state"])
    if target not in _ALLOWED_TRANSITIONS[current]:
        raise InvalidTaskTransitionError(f"cannot transition task {task_id} from {current} to {target}")
    connection.execute(
        f"UPDATE tasks SET state = ?, updated_at = ?{extra_sql} WHERE task_id = ?",
        (target, timestamp, *extra_values, task_id),
    )


def request_cancellation(path: Path, task_id: str, *, now: datetime | None = None) -> TaskRecord:
    timestamp = _iso(now)
    initialize_task_store(path)
    with _connection(path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            row = connection.execute("SELECT state FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
            if row is None:
                raise TaskNotFoundError(task_id)
            state = str(row["state"])
            if state in TERMINAL_STATES:
                connection.execute("COMMIT")
                return get_task(path, task_id)
            if state in {QUEUED, CREATED, RETRYING, BLOCKED}:
                _transition(
                    connection, task_id, CANCELLED, timestamp=timestamp,
                    extra_sql=", completed_at = ?, cancellation_requested_at = ?",
                    extra_values=(timestamp, timestamp),
                )
            elif state == RUNNING:
                _transition(
                    connection, task_id, CANCEL_REQUESTED, timestamp=timestamp,
                    extra_sql=", cancellation_requested_at = ?",
                    extra_values=(timestamp,),
                )
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise
    return get_task(path, task_id)


def lease_next_task(
    path: Path,
    *,
    worker_id: str,
    lease_seconds: int = 60,
    now: datetime | None = None,
) -> TaskRecord | None:
    if not worker_id.strip():
        raise ValueError("worker_id is required")
    if lease_seconds < 1 or lease_seconds > 3600:
        raise ValueError("lease_seconds must be between 1 and 3600")
    current = _utc_now(now)
    timestamp = current.isoformat()
    expires = (current + timedelta(seconds=lease_seconds)).isoformat()
    initialize_task_store(path)
    with _connection(path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            row = connection.execute(
                """
                SELECT task_id FROM tasks
                WHERE state = ?
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
                """,
                (QUEUED,),
            ).fetchone()
            if row is None:
                connection.execute("COMMIT")
                return None
            task_id = str(row["task_id"])
            cursor = connection.execute(
                """
                UPDATE tasks
                SET state = ?, updated_at = ?, started_at = COALESCE(started_at, ?),
                    lease_owner = ?, lease_expires_at = ?, attempt_count = attempt_count + 1
                WHERE task_id = ? AND state = ?
                """,
                (RUNNING, timestamp, timestamp, worker_id.strip(), expires, task_id, QUEUED),
            )
            if cursor.rowcount != 1:
                connection.execute("ROLLBACK")
                return None
            leased = connection.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise
    assert leased is not None
    return _decode(leased)


def heartbeat_task(
    path: Path,
    task_id: str,
    *,
    worker_id: str,
    lease_seconds: int = 60,
    now: datetime | None = None,
) -> TaskRecord:
    current = _utc_now(now)
    expires = (current + timedelta(seconds=lease_seconds)).isoformat()
    initialize_task_store(path)
    with _connection(path) as connection:
        cursor = connection.execute(
            """
            UPDATE tasks SET updated_at = ?, lease_expires_at = ?
            WHERE task_id = ? AND state IN (?, ?) AND lease_owner = ?
            """,
            (current.isoformat(), expires, task_id, RUNNING, CANCEL_REQUESTED, worker_id),
        )
        if cursor.rowcount != 1:
            raise TaskLeaseError(f"task {task_id} is not leased by {worker_id}")
    return get_task(path, task_id)


def finish_task(
    path: Path,
    task_id: str,
    *,
    worker_id: str,
    success: bool,
    result: Mapping[str, Any] | None = None,
    error: str | None = None,
    now: datetime | None = None,
) -> TaskRecord:
    timestamp = _iso(now)
    result_json = json.dumps(dict(result), sort_keys=True, separators=(",", ":")) if result is not None else None
    initialize_task_store(path)
    with _connection(path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            row = connection.execute(
                "SELECT state, lease_owner, attempt_count, max_attempts FROM tasks WHERE task_id = ?",
                (task_id,),
            ).fetchone()
            if row is None:
                raise TaskNotFoundError(task_id)
            if row["lease_owner"] != worker_id:
                raise TaskLeaseError(f"task {task_id} is not leased by {worker_id}")
            state = str(row["state"])
            if state == CANCEL_REQUESTED:
                target = CANCELLED
            elif success:
                target = SUCCEEDED
            elif int(row["attempt_count"]) < int(row["max_attempts"]):
                target = RETRYING
            else:
                target = FAILED
            if target == RETRYING:
                _transition(
                    connection, task_id, target, timestamp=timestamp,
                    extra_sql=", lease_owner = NULL, lease_expires_at = NULL, last_error = ?",
                    extra_values=((error or "task failed")[:2000],),
                )
                _transition(connection, task_id, QUEUED, timestamp=timestamp, extra_sql=", queued_at = ?", extra_values=(timestamp,))
            else:
                _transition(
                    connection, task_id, target, timestamp=timestamp,
                    extra_sql=", completed_at = ?, lease_owner = NULL, lease_expires_at = NULL, last_error = ?, result_json = ?",
                    extra_values=(timestamp, (error or None), result_json),
                )
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise
    return get_task(path, task_id)


def recover_expired_leases(path: Path, *, now: datetime | None = None) -> tuple[str, ...]:
    """Requeue or fail tasks whose worker lease expired before completion."""
    timestamp = _iso(now)
    initialize_task_store(path)
    recovered: list[str] = []
    with _connection(path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            rows = connection.execute(
                """
                SELECT task_id, state, attempt_count, max_attempts FROM tasks
                WHERE state IN (?, ?) AND lease_expires_at IS NOT NULL AND lease_expires_at <= ?
                ORDER BY task_id
                """,
                (RUNNING, CANCEL_REQUESTED, timestamp),
            ).fetchall()
            for row in rows:
                task_id = str(row["task_id"])
                if str(row["state"]) == CANCEL_REQUESTED:
                    target = CANCELLED
                    completed = timestamp
                elif int(row["attempt_count"]) < int(row["max_attempts"]):
                    target = QUEUED
                    completed = None
                else:
                    target = FAILED
                    completed = timestamp
                connection.execute(
                    """
                    UPDATE tasks
                    SET state = ?, updated_at = ?, queued_at = CASE WHEN ? = ? THEN ? ELSE queued_at END,
                        completed_at = ?, lease_owner = NULL, lease_expires_at = NULL,
                        last_error = ?
                    WHERE task_id = ?
                    """,
                    (
                        target, timestamp, target, QUEUED, timestamp, completed,
                        "worker lease expired", task_id,
                    ),
                )
                recovered.append(task_id)
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise
    return tuple(recovered)


def task_json(task: TaskRecord) -> str:
    return json.dumps(asdict(task), indent=2, sort_keys=True) + "\n"

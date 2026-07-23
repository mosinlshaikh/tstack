"""SQLite persistence for single-use runtime approvals."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from tstack.runtime_auth import ActionRequest, SignedApproval

SCHEMA_VERSION = 1


class ApprovalAlreadyConsumedError(RuntimeError):
    """Raised when an approval nonce has already authorized an execution."""


class ApprovalNotRegisteredError(RuntimeError):
    """Raised when an approval is not present in the trusted runtime store."""


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
        yield connection
    finally:
        connection.close()


def initialize_runtime_store(path: Path) -> None:
    with _connection(path) as connection:
        connection.executescript(
            """
            BEGIN IMMEDIATE;
            CREATE TABLE IF NOT EXISTS runtime_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS action_requests (
                request_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                capability TEXT NOT NULL,
                request_hash TEXT NOT NULL UNIQUE,
                parameters_hash TEXT NOT NULL,
                nonce TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS signed_approvals (
                request_id TEXT PRIMARY KEY REFERENCES action_requests(request_id) ON DELETE CASCADE,
                approver TEXT NOT NULL,
                key_id TEXT NOT NULL,
                request_hash TEXT NOT NULL,
                parameters_hash TEXT NOT NULL,
                nonce TEXT NOT NULL UNIQUE,
                issued_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                max_uses INTEGER NOT NULL CHECK(max_uses = 1),
                signature TEXT NOT NULL,
                consumed_at TEXT,
                execution_id TEXT UNIQUE
            );
            INSERT INTO runtime_meta(key, value)
            VALUES ('schema_version', '1')
            ON CONFLICT(key) DO UPDATE SET value = excluded.value;
            COMMIT;
            """
        )


def register_approval(path: Path, request: ActionRequest, approval: SignedApproval) -> None:
    if approval.request_id != request.request_id:
        raise ValueError("request and approval ids do not match")
    if approval.request_hash != request.request_hash:
        raise ValueError("approval request hash mismatch")
    if approval.parameters_hash != request.parameters_hash:
        raise ValueError("approval parameter hash mismatch")
    if approval.nonce != request.nonce:
        raise ValueError("approval nonce mismatch")
    initialize_runtime_store(path)
    request_payload = asdict(request)
    approval_payload = asdict(approval)
    with _connection(path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            connection.execute(
                """
                INSERT INTO action_requests(
                    request_id, workspace_id, capability, request_hash,
                    parameters_hash, nonce, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request_payload["request_id"],
                    request_payload["workspace_id"],
                    request_payload["capability"],
                    request_payload["request_hash"],
                    request_payload["parameters_hash"],
                    request_payload["nonce"],
                    request_payload["created_at"],
                ),
            )
            connection.execute(
                """
                INSERT INTO signed_approvals(
                    request_id, approver, key_id, request_hash, parameters_hash,
                    nonce, issued_at, expires_at, max_uses, signature
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    approval_payload["request_id"],
                    approval_payload["approver"],
                    approval_payload["key_id"],
                    approval_payload["request_hash"],
                    approval_payload["parameters_hash"],
                    approval_payload["nonce"],
                    approval_payload["issued_at"],
                    approval_payload["expires_at"],
                    approval_payload["max_uses"],
                    approval_payload["signature"],
                ),
            )
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise


def consume_approval(
    path: Path,
    *,
    request_id: str,
    request_hash: str,
    parameters_hash: str,
    nonce: str,
    execution_id: str,
    consumed_at: datetime | None = None,
) -> None:
    """Atomically consume an approval exactly once.

    The exact request, action parameters, and nonce must match the registered
    signed approval. Concurrent consumers cannot both succeed.
    """

    timestamp = (consumed_at or datetime.now(timezone.utc)).astimezone(timezone.utc).replace(microsecond=0).isoformat()
    initialize_runtime_store(path)
    with _connection(path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            """
            SELECT request_hash, parameters_hash, nonce, expires_at, consumed_at
            FROM signed_approvals
            WHERE request_id = ?
            """,
            (request_id,),
        ).fetchone()
        if row is None:
            connection.execute("ROLLBACK")
            raise ApprovalNotRegisteredError(request_id)
        if row["consumed_at"] is not None:
            connection.execute("ROLLBACK")
            raise ApprovalAlreadyConsumedError(request_id)
        if row["request_hash"] != request_hash:
            connection.execute("ROLLBACK")
            raise ValueError("stored approval request hash mismatch")
        if row["parameters_hash"] != parameters_hash:
            connection.execute("ROLLBACK")
            raise ValueError("stored approval parameter hash mismatch")
        if row["nonce"] != nonce:
            connection.execute("ROLLBACK")
            raise ValueError("stored approval nonce mismatch")
        expires_at = datetime.fromisoformat(str(row["expires_at"])).astimezone(timezone.utc)
        current = datetime.fromisoformat(timestamp).astimezone(timezone.utc)
        if current >= expires_at:
            connection.execute("ROLLBACK")
            raise ValueError("stored approval has expired")
        cursor = connection.execute(
            """
            UPDATE signed_approvals
            SET consumed_at = ?, execution_id = ?
            WHERE request_id = ? AND consumed_at IS NULL
            """,
            (timestamp, execution_id, request_id),
        )
        if cursor.rowcount != 1:
            connection.execute("ROLLBACK")
            raise ApprovalAlreadyConsumedError(request_id)
        connection.execute("COMMIT")


def approval_status(path: Path, request_id: str) -> dict[str, str | bool | None]:
    initialize_runtime_store(path)
    with _connection(path) as connection:
        row = connection.execute(
            """
            SELECT request_id, key_id, expires_at, consumed_at, execution_id
            FROM signed_approvals WHERE request_id = ?
            """,
            (request_id,),
        ).fetchone()
    if row is None:
        raise ApprovalNotRegisteredError(request_id)
    return {
        "request_id": str(row["request_id"]),
        "key_id": str(row["key_id"]),
        "expires_at": str(row["expires_at"]),
        "consumed": row["consumed_at"] is not None,
        "consumed_at": row["consumed_at"],
        "execution_id": row["execution_id"],
    }

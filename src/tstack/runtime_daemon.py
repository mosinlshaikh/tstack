"""Persistent local daemon foundation for the TStack task runtime.

The daemon owns worker leasing, startup recovery, cooperative cancellation,
heartbeats, durable health state, and graceful shutdown. It intentionally
uses a dispatcher callback: capability authorization and execution remain
separate security boundaries and are connected in the next broker phase.
"""
from __future__ import annotations

import json
import os
import signal
import socket
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from tstack.task_runtime import (
    CANCEL_REQUESTED,
    TaskRecord,
    finish_task,
    get_task,
    heartbeat_task,
    lease_next_task,
    list_tasks,
    recover_expired_leases,
)

DAEMON_SCHEMA = "tstack-daemon-status/v1"
DispatchResult = Mapping[str, Any] | None
Dispatcher = Callable[[TaskRecord], DispatchResult]


@dataclass(frozen=True)
class DaemonConfig:
    database: Path
    state_directory: Path
    worker_count: int = 1
    poll_interval_seconds: float = 0.25
    lease_seconds: int = 30
    heartbeat_interval_seconds: float = 5.0
    idle_exit_seconds: float | None = None

    def validate(self) -> None:
        if not 1 <= self.worker_count <= 64:
            raise ValueError("worker_count must be between 1 and 64")
        if not 0.05 <= self.poll_interval_seconds <= 60:
            raise ValueError("poll_interval_seconds must be between 0.05 and 60")
        if not 2 <= self.lease_seconds <= 3600:
            raise ValueError("lease_seconds must be between 2 and 3600")
        if not 0.25 <= self.heartbeat_interval_seconds < self.lease_seconds:
            raise ValueError("heartbeat interval must be positive and shorter than lease")
        if self.idle_exit_seconds is not None and self.idle_exit_seconds < 0.1:
            raise ValueError("idle_exit_seconds must be at least 0.1")


@dataclass(frozen=True)
class DaemonStatus:
    schema: str
    daemon_id: str
    pid: int
    hostname: str
    started_at: str
    updated_at: str
    state: str
    worker_count: int
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    recovered_tasks: tuple[str, ...]
    last_error: str | None


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class RuntimeDaemon:
    """Bounded local worker supervisor backed by the SQLite task store."""

    def __init__(self, config: DaemonConfig, dispatcher: Dispatcher) -> None:
        config.validate()
        self.config = config
        self.dispatcher = dispatcher
        self.daemon_id = f"DAEMON-{uuid.uuid4().hex}"
        self.started_at = _utc_now()
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._workers: list[threading.Thread] = []
        self._active_tasks: set[str] = set()
        self._completed_tasks = 0
        self._failed_tasks = 0
        self._last_error: str | None = None
        self._recovered_tasks: tuple[str, ...] = ()

    @property
    def status_path(self) -> Path:
        return self.config.state_directory.expanduser().resolve() / "status.json"

    @property
    def stop_path(self) -> Path:
        return self.config.state_directory.expanduser().resolve() / "stop.request"

    def request_stop(self) -> None:
        self._stop.set()

    def _status(self, state: str) -> DaemonStatus:
        with self._lock:
            return DaemonStatus(
                schema=DAEMON_SCHEMA,
                daemon_id=self.daemon_id,
                pid=os.getpid(),
                hostname=socket.gethostname(),
                started_at=self.started_at,
                updated_at=_utc_now(),
                state=state,
                worker_count=self.config.worker_count,
                active_tasks=len(self._active_tasks),
                completed_tasks=self._completed_tasks,
                failed_tasks=self._failed_tasks,
                recovered_tasks=self._recovered_tasks,
                last_error=self._last_error,
            )

    def _write_status(self, state: str) -> None:
        status = self._status(state)
        target = self.status_path
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(".tmp")
        temporary.write_text(json.dumps(asdict(status), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, target)

    def _heartbeat_until_done(self, task_id: str, worker_id: str, done: threading.Event) -> None:
        while not done.wait(self.config.heartbeat_interval_seconds):
            try:
                task = get_task(self.config.database, task_id)
                if task.state == CANCEL_REQUESTED:
                    return
                heartbeat_task(
                    self.config.database,
                    task_id,
                    worker_id=worker_id,
                    lease_seconds=self.config.lease_seconds,
                )
            except Exception as exc:  # worker completion handles lease failure
                with self._lock:
                    self._last_error = f"heartbeat {task_id}: {type(exc).__name__}: {exc}"[:2000]
                return

    def _execute_task(self, task: TaskRecord, worker_id: str) -> None:
        done = threading.Event()
        heartbeat = threading.Thread(
            target=self._heartbeat_until_done,
            args=(task.task_id, worker_id, done),
            name=f"tstack-heartbeat-{task.task_id}",
            daemon=True,
        )
        heartbeat.start()
        try:
            current = get_task(self.config.database, task.task_id)
            if current.state == CANCEL_REQUESTED:
                finish_task(self.config.database, task.task_id, worker_id=worker_id, success=True, result={})
                return
            result = self.dispatcher(task)
            finish_task(
                self.config.database,
                task.task_id,
                worker_id=worker_id,
                success=True,
                result=dict(result or {}),
            )
            with self._lock:
                self._completed_tasks += 1
        except Exception as exc:
            try:
                finish_task(
                    self.config.database,
                    task.task_id,
                    worker_id=worker_id,
                    success=False,
                    error=f"{type(exc).__name__}: {exc}"[:2000],
                )
            finally:
                with self._lock:
                    self._failed_tasks += 1
                    self._last_error = f"task {task.task_id}: {type(exc).__name__}: {exc}"[:2000]
        finally:
            done.set()
            heartbeat.join(timeout=self.config.heartbeat_interval_seconds + 1)
            with self._lock:
                self._active_tasks.discard(task.task_id)
            self._write_status("RUNNING")

    def _worker_loop(self, index: int) -> None:
        worker_id = f"{self.daemon_id}-worker-{index}"
        while not self._stop.is_set():
            task = lease_next_task(
                self.config.database,
                worker_id=worker_id,
                lease_seconds=self.config.lease_seconds,
            )
            if task is None:
                self._stop.wait(self.config.poll_interval_seconds)
                continue
            with self._lock:
                self._active_tasks.add(task.task_id)
            self._write_status("RUNNING")
            self._execute_task(task, worker_id)

    def run(self) -> DaemonStatus:
        """Run until stop is requested or optional idle timeout elapses."""
        self.config.state_directory.expanduser().resolve().mkdir(parents=True, exist_ok=True)
        self.stop_path.unlink(missing_ok=True)
        self._recovered_tasks = recover_expired_leases(self.config.database)
        self._write_status("STARTING")

        previous_handlers: dict[int, Any] = {}
        if threading.current_thread() is threading.main_thread():
            for signum in (signal.SIGINT, signal.SIGTERM):
                previous_handlers[signum] = signal.getsignal(signum)
                signal.signal(signum, lambda _signum, _frame: self.request_stop())

        self._workers = [
            threading.Thread(target=self._worker_loop, args=(index,), name=f"tstack-worker-{index}", daemon=True)
            for index in range(self.config.worker_count)
        ]
        for worker in self._workers:
            worker.start()
        self._write_status("RUNNING")

        idle_since: float | None = None
        try:
            while not self._stop.wait(self.config.poll_interval_seconds):
                if self.stop_path.exists():
                    self.request_stop()
                    break
                queued_or_running = list_tasks(self.config.database, limit=10000)
                active = any(task.state in {"QUEUED", "RUNNING", "RETRYING", "CANCEL_REQUESTED"} for task in queued_or_running)
                if active:
                    idle_since = None
                elif self.config.idle_exit_seconds is not None:
                    idle_since = idle_since or time.monotonic()
                    if time.monotonic() - idle_since >= self.config.idle_exit_seconds:
                        self.request_stop()
                        break
                self._write_status("RUNNING")
        finally:
            self._write_status("STOPPING")
            self._stop.set()
            for worker in self._workers:
                worker.join(timeout=max(2.0, self.config.lease_seconds + 1.0))
            self.stop_path.unlink(missing_ok=True)
            self._write_status("STOPPED")
            for signum, handler in previous_handlers.items():
                signal.signal(signum, handler)
        return self._status("STOPPED")


def read_daemon_status(state_directory: Path) -> DaemonStatus:
    payload = json.loads((state_directory.expanduser().resolve() / "status.json").read_text(encoding="utf-8"))
    if payload.get("schema") != DAEMON_SCHEMA:
        raise ValueError("unsupported daemon status schema")
    payload["recovered_tasks"] = tuple(payload.get("recovered_tasks", ()))
    return DaemonStatus(**payload)


def request_daemon_stop(state_directory: Path) -> Path:
    target = state_directory.expanduser().resolve() / "stop.request"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_utc_now() + "\n", encoding="utf-8")
    return target

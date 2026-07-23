from __future__ import annotations

import json
import threading
import time

from tstack.runtime_daemon import DaemonConfig, RuntimeDaemon, read_daemon_status, request_daemon_stop
from tstack.task_runtime import FAILED, SUCCEEDED, get_task, submit_task


def _wait_for(predicate, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.02)
    raise AssertionError("condition did not become true before timeout")


def test_daemon_executes_queued_task_and_stops_when_idle(tmp_path) -> None:
    database = tmp_path / "tasks.db"
    state = tmp_path / "daemon"
    submit_task(
        database,
        workspace_id="w",
        capability="runtime.noop",
        intent="acknowledge",
        parameters={"value": 7},
        task_id="TASK-1",
    )
    daemon = RuntimeDaemon(
        DaemonConfig(
            database=database,
            state_directory=state,
            worker_count=2,
            poll_interval_seconds=0.05,
            lease_seconds=3,
            heartbeat_interval_seconds=0.25,
            idle_exit_seconds=0.15,
        ),
        lambda task: {"task": task.task_id, "value": task.parameters["value"]},
    )
    status = daemon.run()
    task = get_task(database, "TASK-1")
    assert task.state == SUCCEEDED
    assert task.result == {"task": "TASK-1", "value": 7}
    assert status.state == "STOPPED"
    assert status.completed_tasks == 1
    assert read_daemon_status(state).state == "STOPPED"


def test_daemon_records_dispatch_failure(tmp_path) -> None:
    database = tmp_path / "tasks.db"
    state = tmp_path / "daemon"
    submit_task(
        database,
        workspace_id="w",
        capability="runtime.noop",
        intent="fail",
        parameters={},
        max_attempts=1,
        task_id="TASK-FAIL",
    )

    def fail(_task):
        raise RuntimeError("expected failure")

    daemon = RuntimeDaemon(
        DaemonConfig(
            database=database,
            state_directory=state,
            poll_interval_seconds=0.05,
            lease_seconds=3,
            heartbeat_interval_seconds=0.25,
            idle_exit_seconds=0.15,
        ),
        fail,
    )
    status = daemon.run()
    task = get_task(database, "TASK-FAIL")
    assert task.state == FAILED
    assert "expected failure" in (task.last_error or "")
    assert status.failed_tasks == 1


def test_stop_request_terminates_foreground_daemon(tmp_path) -> None:
    database = tmp_path / "tasks.db"
    state = tmp_path / "daemon"
    daemon = RuntimeDaemon(
        DaemonConfig(
            database=database,
            state_directory=state,
            poll_interval_seconds=0.05,
            lease_seconds=3,
            heartbeat_interval_seconds=0.25,
        ),
        lambda _task: {},
    )
    thread = threading.Thread(target=daemon.run)
    thread.start()
    _wait_for(lambda: (state / "status.json").exists())
    _wait_for(lambda: json.loads((state / "status.json").read_text())["state"] == "RUNNING")
    request_daemon_stop(state)
    thread.join(timeout=5)
    assert not thread.is_alive()
    assert read_daemon_status(state).state == "STOPPED"

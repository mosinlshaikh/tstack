from datetime import datetime, timedelta, timezone
from threading import Barrier, Thread

import pytest

from tstack.task_runtime import (
    CANCEL_REQUESTED,
    CANCELLED,
    FAILED,
    QUEUED,
    RUNNING,
    SUCCEEDED,
    InvalidTaskTransitionError,
    TaskLeaseError,
    finish_task,
    get_task,
    heartbeat_task,
    lease_next_task,
    list_tasks,
    recover_expired_leases,
    request_cancellation,
    submit_task,
)


def _now() -> datetime:
    return datetime(2026, 7, 22, 12, 0, tzinfo=timezone.utc)


def test_submit_and_read_task(tmp_path) -> None:
    database = tmp_path / "runtime.db"
    task = submit_task(
        database,
        workspace_id="workspace-1",
        capability="project.scan",
        intent="Scan repository",
        parameters={"root": ".", "mode": "read-only"},
        priority=5,
        max_attempts=2,
        task_id="TASK-1",
        now=_now(),
    )
    assert task.state == QUEUED
    assert task.parameters == {"mode": "read-only", "root": "."}
    assert get_task(database, "TASK-1") == task
    assert list_tasks(database) == (task,)


def test_highest_priority_task_is_leased_first(tmp_path) -> None:
    database = tmp_path / "runtime.db"
    submit_task(database, workspace_id="w", capability="a", intent="low", parameters={}, priority=1, task_id="LOW", now=_now())
    submit_task(database, workspace_id="w", capability="a", intent="high", parameters={}, priority=10, task_id="HIGH", now=_now())
    leased = lease_next_task(database, worker_id="worker-1", now=_now())
    assert leased is not None
    assert leased.task_id == "HIGH"
    assert leased.state == RUNNING
    assert leased.attempt_count == 1


def test_task_can_complete_successfully(tmp_path) -> None:
    database = tmp_path / "runtime.db"
    submit_task(database, workspace_id="w", capability="project.scan", intent="scan", parameters={}, task_id="TASK", now=_now())
    lease_next_task(database, worker_id="worker", now=_now())
    completed = finish_task(database, "TASK", worker_id="worker", success=True, result={"findings": 0}, now=_now() + timedelta(seconds=1))
    assert completed.state == SUCCEEDED
    assert completed.result == {"findings": 0}
    assert completed.lease_owner is None


def test_failed_task_retries_until_attempt_budget_exhausted(tmp_path) -> None:
    database = tmp_path / "runtime.db"
    submit_task(database, workspace_id="w", capability="project.scan", intent="scan", parameters={}, max_attempts=2, task_id="TASK", now=_now())
    lease_next_task(database, worker_id="worker-1", now=_now())
    retry = finish_task(database, "TASK", worker_id="worker-1", success=False, error="temporary", now=_now() + timedelta(seconds=1))
    assert retry.state == QUEUED
    assert retry.last_error == "temporary"

    lease_next_task(database, worker_id="worker-2", now=_now() + timedelta(seconds=2))
    failed = finish_task(database, "TASK", worker_id="worker-2", success=False, error="permanent", now=_now() + timedelta(seconds=3))
    assert failed.state == FAILED
    assert failed.attempt_count == 2


def test_running_task_cancellation_is_cooperative(tmp_path) -> None:
    database = tmp_path / "runtime.db"
    submit_task(database, workspace_id="w", capability="project.scan", intent="scan", parameters={}, task_id="TASK", now=_now())
    lease_next_task(database, worker_id="worker", now=_now())
    requested = request_cancellation(database, "TASK", now=_now() + timedelta(seconds=1))
    assert requested.state == CANCEL_REQUESTED
    cancelled = finish_task(database, "TASK", worker_id="worker", success=True, result={}, now=_now() + timedelta(seconds=2))
    assert cancelled.state == CANCELLED


def test_queued_task_cancellation_is_immediate(tmp_path) -> None:
    database = tmp_path / "runtime.db"
    submit_task(database, workspace_id="w", capability="project.scan", intent="scan", parameters={}, task_id="TASK", now=_now())
    cancelled = request_cancellation(database, "TASK", now=_now() + timedelta(seconds=1))
    assert cancelled.state == CANCELLED
    assert lease_next_task(database, worker_id="worker", now=_now() + timedelta(seconds=2)) is None


def test_wrong_worker_cannot_heartbeat_or_finish(tmp_path) -> None:
    database = tmp_path / "runtime.db"
    submit_task(database, workspace_id="w", capability="project.scan", intent="scan", parameters={}, task_id="TASK", now=_now())
    lease_next_task(database, worker_id="owner", now=_now())
    with pytest.raises(TaskLeaseError):
        heartbeat_task(database, "TASK", worker_id="intruder", now=_now() + timedelta(seconds=1))
    with pytest.raises(TaskLeaseError):
        finish_task(database, "TASK", worker_id="intruder", success=True, now=_now() + timedelta(seconds=1))


def test_expired_lease_is_requeued_when_attempts_remain(tmp_path) -> None:
    database = tmp_path / "runtime.db"
    submit_task(database, workspace_id="w", capability="project.scan", intent="scan", parameters={}, max_attempts=2, task_id="TASK", now=_now())
    lease_next_task(database, worker_id="worker", lease_seconds=10, now=_now())
    recovered = recover_expired_leases(database, now=_now() + timedelta(seconds=11))
    assert recovered == ("TASK",)
    assert get_task(database, "TASK").state == QUEUED


def test_expired_final_attempt_is_failed(tmp_path) -> None:
    database = tmp_path / "runtime.db"
    submit_task(database, workspace_id="w", capability="project.scan", intent="scan", parameters={}, max_attempts=1, task_id="TASK", now=_now())
    lease_next_task(database, worker_id="worker", lease_seconds=10, now=_now())
    recover_expired_leases(database, now=_now() + timedelta(seconds=11))
    assert get_task(database, "TASK").state == FAILED


def test_atomic_leasing_allows_only_one_worker(tmp_path) -> None:
    database = tmp_path / "runtime.db"
    submit_task(database, workspace_id="w", capability="project.scan", intent="scan", parameters={}, task_id="TASK", now=_now())
    barrier = Barrier(8)
    results = []

    def lease(worker: str) -> None:
        barrier.wait()
        results.append(lease_next_task(database, worker_id=worker, now=_now()))

    threads = [Thread(target=lease, args=(f"worker-{index}",)) for index in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    winners = [item for item in results if item is not None]
    assert len(winners) == 1
    assert winners[0].task_id == "TASK"

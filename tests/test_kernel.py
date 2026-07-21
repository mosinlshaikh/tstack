import json

import pytest

from tstack.cli import main
from tstack.kernel import approve_task, cancel_task, enqueue_task, get_task, init_workspace, list_events, rollback_task, run_next_task, run_task, submit_task, verify_audit_chain


def test_kernel_vertical_slice_write_audit_and_rollback(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    init_workspace(workspace)
    target = workspace / "note.txt"
    target.write_text("before", encoding="utf-8")

    task = submit_task(workspace, capability="filesystem.write", target="note.txt", content="after")
    assert task.state == "WAITING_FOR_APPROVAL"
    approval = approve_task(workspace, task.task_id, actor="Mosin")
    assert approval.signature

    result = run_task(workspace, task.task_id)
    assert result.executed is True
    assert target.read_text(encoding="utf-8") == "after"
    assert get_task(workspace, task.task_id).state == "SUCCEEDED"
    assert verify_audit_chain(workspace) is True

    rollback = rollback_task(workspace, task.task_id)
    assert rollback.restored is True
    assert target.read_text(encoding="utf-8") == "before"
    assert get_task(workspace, task.task_id).state == "ROLLED_BACK"
    assert verify_audit_chain(workspace) is True


def test_kernel_rejects_unapproved_execution(tmp_path) -> None:
    init_workspace(tmp_path)
    task = submit_task(tmp_path, capability="filesystem.write", target="note.txt", content="after")
    with pytest.raises(ValueError, match="no approval"):
        run_task(tmp_path, task.task_id)


def test_kernel_rejects_approval_replay(tmp_path) -> None:
    init_workspace(tmp_path)
    task = submit_task(tmp_path, capability="filesystem.write", target="note.txt", content="after")
    approve_task(tmp_path, task.task_id, actor="Mosin", max_uses=1)
    run_task(tmp_path, task.task_id)
    with pytest.raises(ValueError, match="maximum uses"):
        run_task(tmp_path, task.task_id)


def test_kernel_queue_run_next_and_events(tmp_path) -> None:
    init_workspace(tmp_path)
    task = submit_task(tmp_path, capability="filesystem.write", target="queued.txt", content="queued")
    approve_task(tmp_path, task.task_id, actor="Mosin")
    queued = enqueue_task(tmp_path, task.task_id)
    assert queued.state == "QUEUED"
    result = run_next_task(tmp_path)
    assert result.state == "SUCCEEDED"
    events = list_events(tmp_path, task.task_id)
    states = [event.state for event in events]
    assert "QUEUED" in states
    assert "RUNNING" in states
    assert "SUCCEEDED" in states


def test_kernel_cancels_waiting_task(tmp_path) -> None:
    init_workspace(tmp_path)
    task = submit_task(tmp_path, capability="filesystem.write", target="note.txt", content="after")
    cancelled = cancel_task(tmp_path, task.task_id, reason="user stopped task")
    assert cancelled.state == "CANCELLED"
    with pytest.raises(ValueError, match="cancelled"):
        run_task(tmp_path, task.task_id)


def test_kernel_timeout_marks_task_failed(tmp_path) -> None:
    init_workspace(tmp_path)
    task = submit_task(tmp_path, capability="filesystem.write", target="note.txt", content="after")
    approve_task(tmp_path, task.task_id, actor="Mosin")
    result = run_task(tmp_path, task.task_id, timeout_seconds=0)
    assert result.executed is False
    assert result.state == "FAILED"
    assert get_task(tmp_path, task.task_id).state == "FAILED"
    assert verify_audit_chain(tmp_path) is True


def test_kernel_cli_vertical_slice(tmp_path, capsys) -> None:
    workspace = tmp_path / "workspace"
    assert main(["workspace", "init", str(workspace)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-kernel/v1"

    assert main(["task", "submit", "--workspace", str(workspace), "--target", "note.txt", "--content", "hello"]) == 0
    task = json.loads(capsys.readouterr().out)
    task_id = task["task_id"]
    assert task["state"] == "WAITING_FOR_APPROVAL"

    assert main(["kernel-approval", "approve", task_id, "--workspace", str(workspace), "--actor", "Mosin"]) == 0
    approval = json.loads(capsys.readouterr().out)
    assert approval["schema"] == "tstack-signed-approval/v1"

    assert main(["task", "run", task_id, "--workspace", str(workspace)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["state"] == "SUCCEEDED"
    assert (workspace / "note.txt").read_text(encoding="utf-8") == "hello"

    assert main(["kernel-audit", "verify", "--workspace", str(workspace)]) == 0
    audit = json.loads(capsys.readouterr().out)
    assert audit["valid"] is True

    assert main(["kernel-rollback", "apply", task_id, "--workspace", str(workspace)]) == 0
    rollback = json.loads(capsys.readouterr().out)
    assert rollback["restored"] is True
    assert not (workspace / "note.txt").exists()


def test_kernel_cli_queue_events_and_cancel(tmp_path, capsys) -> None:
    workspace = tmp_path / "workspace"
    assert main(["workspace", "init", str(workspace)]) == 0
    capsys.readouterr()
    assert main(["task", "submit", "--workspace", str(workspace), "--target", "queued.txt", "--content", "hello"]) == 0
    task = json.loads(capsys.readouterr().out)
    task_id = task["task_id"]
    assert main(["kernel-approval", "approve", task_id, "--workspace", str(workspace), "--actor", "Mosin"]) == 0
    capsys.readouterr()
    assert main(["task", "queue", task_id, "--workspace", str(workspace)]) == 0
    queued = json.loads(capsys.readouterr().out)
    assert queued["state"] == "QUEUED"
    assert main(["task", "events", "--workspace", str(workspace), "--task-id", task_id]) == 0
    events = json.loads(capsys.readouterr().out)
    assert any(event["state"] == "QUEUED" for event in events)

    assert main(["task", "submit", "--workspace", str(workspace), "--target", "cancel.txt", "--content", "no"]) == 0
    second = json.loads(capsys.readouterr().out)
    assert main(["task", "cancel", second["task_id"], "--workspace", str(workspace), "--reason", "not needed"]) == 0
    cancelled = json.loads(capsys.readouterr().out)
    assert cancelled["state"] == "CANCELLED"

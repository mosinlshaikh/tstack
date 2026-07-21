import json

import pytest

from tstack.cli import main
from tstack.kernel import approve_task, get_task, init_workspace, rollback_task, run_task, submit_task, verify_audit_chain


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

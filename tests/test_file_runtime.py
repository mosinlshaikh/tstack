import json

from tstack.cli import main
from tstack.file_agent import organize_plan_json, plan_organize
from tstack.file_runtime import apply_file_transaction, undo_file_transaction
from tstack.runtime import approve_runtime_request, create_runtime_request, runtime_json


def _approved_runtime_pair(tmp_path, target):
    request = create_runtime_request("filesystem.move", "Organize files", target=str(target), request_id="RUNTIME-FILE-1")
    request_path = tmp_path / "request.json"
    decision_path = tmp_path / "decision.json"
    request_path.write_text(runtime_json(request), encoding="utf-8")
    decision = approve_runtime_request(request_path, approved=True, approver="Mosin", reason="Reviewed transaction.")
    decision_path.write_text(runtime_json(decision), encoding="utf-8")
    return request_path, decision_path


def test_file_transaction_applies_and_undoes_moves(tmp_path) -> None:
    root = tmp_path / "files"
    root.mkdir()
    (root / "a.txt").write_text("a", encoding="utf-8")
    plan = plan_organize(root)
    plan_path = tmp_path / "plan.json"
    manifest = tmp_path / "manifest.json"
    plan_path.write_text(organize_plan_json(plan), encoding="utf-8")
    request_path, decision_path = _approved_runtime_pair(tmp_path, root)

    result = apply_file_transaction(plan_path, request_path, decision_path, dry_run=False, manifest=manifest)
    assert result.applied is True
    assert (root / "TXT" / "a.txt").is_file()
    assert manifest.is_file()

    undo = undo_file_transaction(manifest)
    assert undo.restored is True
    assert (root / "a.txt").is_file()


def test_file_transaction_dry_run_writes_nothing(tmp_path) -> None:
    root = tmp_path / "files"
    root.mkdir()
    (root / "a.txt").write_text("a", encoding="utf-8")
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(organize_plan_json(plan_organize(root)), encoding="utf-8")
    request_path, decision_path = _approved_runtime_pair(tmp_path, root)
    result = apply_file_transaction(plan_path, request_path, decision_path, dry_run=True)
    assert result.applied is False
    assert result.moves[0].status == "planned"
    assert (root / "a.txt").is_file()


def test_file_runtime_cli_apply_json(tmp_path, capsys) -> None:
    root = tmp_path / "files"
    root.mkdir()
    (root / "a.txt").write_text("a", encoding="utf-8")
    plan_path = tmp_path / "plan.json"
    request_path, decision_path = _approved_runtime_pair(tmp_path, root)
    assert main(["file", "organize-plan", str(root), "--format", "json", "--output", str(plan_path)]) == 0
    capsys.readouterr()
    assert main(["file-runtime", "apply", str(plan_path), str(request_path), str(decision_path), "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-file-transaction/v1"
    assert payload["dry_run"] is True

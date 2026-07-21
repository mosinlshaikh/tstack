import json

from tstack.cli import main
from tstack.file_agent import build_inventory, plan_organize


def test_file_inventory_detects_duplicates(tmp_path) -> None:
    (tmp_path / "a.txt").write_text("same", encoding="utf-8")
    (tmp_path / "b.txt").write_text("same", encoding="utf-8")
    (tmp_path / "c.md").write_text("different", encoding="utf-8")
    inventory = build_inventory(tmp_path)
    assert inventory.schema == "tstack-file-inventory/v1"
    assert inventory.files_scanned == 3
    assert inventory.extensions[".txt"] == 2
    assert len(inventory.duplicates) == 1
    assert inventory.execution_allowed is False


def test_file_inventory_cli_json(capsys, tmp_path) -> None:
    (tmp_path / "a.txt").write_text("same", encoding="utf-8")
    (tmp_path / "b.txt").write_text("same", encoding="utf-8")
    assert main(["file", "inventory", str(tmp_path), "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-file-inventory/v1"
    assert payload["files_scanned"] == 2
    assert len(payload["duplicates"]) == 1
    assert payload["execution_allowed"] is False


def test_file_organize_plan_groups_by_extension(tmp_path) -> None:
    (tmp_path / "invoice.pdf").write_text("pdf", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("txt", encoding="utf-8")
    plan = plan_organize(tmp_path)
    assert plan.schema == "tstack-file-organize-plan/v1"
    assert plan.moves_planned == 2
    assert plan.execution_allowed is False
    destinations = {item.destination for item in plan.moves}
    assert {"PDF/invoice.pdf", "TXT/notes.txt"}.issubset(destinations)


def test_file_organize_plan_cli_json(capsys, tmp_path) -> None:
    (tmp_path / "invoice.pdf").write_text("pdf", encoding="utf-8")
    assert main(["file", "organize-plan", str(tmp_path), "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-file-organize-plan/v1"
    assert payload["moves_planned"] == 1
    assert payload["execution_allowed"] is False

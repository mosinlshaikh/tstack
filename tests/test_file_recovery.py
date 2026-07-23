import json

import pytest

from tstack.file_recovery import append_recovery_event, inspect_recovery_journal, recover_interrupted_transaction


def test_recovery_rolls_back_interrupted_moves(tmp_path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    source = root / "source.txt"
    destination = root / "archive" / "source.txt"
    source.write_text("payload", encoding="utf-8")

    journal = tmp_path / "recovery.jsonl"
    append_recovery_event(journal, transaction_id="TX-1", state="PREPARED")
    destination.parent.mkdir(parents=True)
    source.rename(destination)
    append_recovery_event(
        journal,
        transaction_id="TX-1",
        state="MOVED",
        source="source.txt",
        destination="archive/source.txt",
    )

    before = inspect_recovery_journal(journal)
    assert before.valid is True
    assert before.terminal is False

    after = recover_interrupted_transaction(journal, root=root)
    assert after.valid is True
    assert after.terminal is True
    assert after.latest_state == "ROLLED_BACK"
    assert source.read_text(encoding="utf-8") == "payload"
    assert not destination.exists()


def test_terminal_journal_is_not_replayed(tmp_path) -> None:
    journal = tmp_path / "recovery.jsonl"
    append_recovery_event(journal, transaction_id="TX-2", state="PREPARED")
    append_recovery_event(journal, transaction_id="TX-2", state="COMMITTED")
    report = recover_interrupted_transaction(journal, root=tmp_path)
    assert report.latest_state == "COMMITTED"


def test_recovery_detects_tampering(tmp_path) -> None:
    journal = tmp_path / "recovery.jsonl"
    append_recovery_event(journal, transaction_id="TX-3", state="PREPARED")
    payload = json.loads(journal.read_text(encoding="utf-8"))
    payload["state"] = "COMMITTED"
    journal.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    report = inspect_recovery_journal(journal)
    assert report.valid is False
    with pytest.raises(ValueError, match="validation failed"):
        recover_interrupted_transaction(journal, root=tmp_path)

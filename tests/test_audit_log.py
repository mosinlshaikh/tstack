import json

from tstack.audit_log import append_audit_event, verify_audit_log
from tstack.cli import main
from tstack.runtime import create_audit_event, create_runtime_request, runtime_json


def _event_file(tmp_path):
    request = create_runtime_request("project.scan", "Scan repository")
    request_path = tmp_path / "request.json"
    event_path = tmp_path / "event.json"
    request_path.write_text(runtime_json(request), encoding="utf-8")
    event_path.write_text(runtime_json(create_audit_event(request_path)), encoding="utf-8")
    return event_path


def test_audit_log_append_and_verify(tmp_path) -> None:
    log = tmp_path / "audit.jsonl"
    first = append_audit_event(log, _event_file(tmp_path))
    second = append_audit_event(log, _event_file(tmp_path))
    result = verify_audit_log(log)
    assert first.index == 1
    assert second.previous_hash == first.entry_hash
    assert result.valid is True
    assert result.entries == 2
    assert result.head_hash == second.entry_hash


def test_audit_log_detects_tampering(tmp_path) -> None:
    log = tmp_path / "audit.jsonl"
    append_audit_event(log, _event_file(tmp_path))
    payload = json.loads(log.read_text(encoding="utf-8").splitlines()[0])
    payload["event"]["outcome"] = "tampered"
    log.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    result = verify_audit_log(log)
    assert result.valid is False
    assert result.errors


def test_audit_log_cli_verify_json(tmp_path, capsys) -> None:
    log = tmp_path / "audit.jsonl"
    event = _event_file(tmp_path)
    assert main(["audit-log", "append", str(log), str(event), "--format", "json"]) == 0
    capsys.readouterr()
    assert main(["audit-log", "verify", str(log), "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-audit-log-verify/v1"
    assert payload["valid"] is True

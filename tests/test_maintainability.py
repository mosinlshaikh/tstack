import json

from tstack.cli import main
from tstack.maintainability import audit_maintainability


def test_maintainability_audit_flags_oversized_module(tmp_path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "large.py").write_text("\n".join("print('x')" for _ in range(12)), encoding="utf-8")
    (tmp_path / "tests" / "test_large.py").write_text("def test_ok(): assert True\n", encoding="utf-8")
    report = audit_maintainability(tmp_path, warn_lines=10, hold_lines=20)
    assert report.schema == "tstack-maintainability-report/v1"
    assert report.verdict == "REVIEW"
    assert report.oversized_modules[0].path == "src/large.py"
    assert report.execution_allowed is False


def test_maintainability_cli_json_returns_nonzero_for_review(capsys, tmp_path) -> None:
    (tmp_path / "app.py").write_text("\n".join("print('x')" for _ in range(6)), encoding="utf-8")
    assert main(["maintainability", "audit", str(tmp_path), "--warn-lines", "5", "--hold-lines", "20", "--format", "json"]) == 17
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "tstack-maintainability-report/v1"
    assert payload["verdict"] == "REVIEW"

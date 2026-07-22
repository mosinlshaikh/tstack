from pathlib import Path

from tstack.sandbox import default_sandbox_policy, run_sandbox_command


def test_legacy_unsigned_execution_is_denied_by_default(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("TSTACK_ALLOW_LEGACY_UNSIGNED_EXECUTION", raising=False)
    policy = default_sandbox_policy(tmp_path)

    result = run_sandbox_command(policy, ("python", "--version"))

    assert result.executed is False
    assert any("legacy unsigned sandbox execution is disabled" in item for item in result.blockers)
    assert any("tstack-secure sandbox-run" in item for item in result.blockers)
